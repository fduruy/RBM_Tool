"""
portfolio_matcher.py - Matching des sub-portfolios internes avec des trades externes.

Principe
--------
1. Les trades internes sont regroupés en sub-portfolios (CCY, PricingModel, Way).
   Un sub-portfolio est un agrégat de sensibilités {(Index, Tenor): Delta}.
2. Pour chaque sub-portfolio, on cherche itérativement le trade externe
   (Way opposé, même CCY / PricingModel par défaut) qui réduit le plus la
   sensibilité absolue totale  sum_k |S_k|.
3. La part du trade externe utilisée (0..1) est l'optimum exact du problème
   convexe  min_x sum_k |S_k + x * E_k|,  x dans [0, part restante].
4. L'usage des trades externes est cumulé entre sub-portfolios (jamais > 100 %).

Règle de priorité : à gain égal (à `gain_tol` près), le trade avec le Gpt_Id
maximal est choisi.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd

from models import TradeInfo
from utils import parse_numeric_value

logger = logging.getLogger(__name__)

Bucket = Tuple[object, object]            # (Index, Tenor)
Sensitivities = Dict[Bucket, float]       # {(Index, Tenor): Delta}
GroupKey = Tuple[str, str, str]           # (CCY, PricingModel, Way)


# --------------------------------------------------------------------------- #
# Configuration et structures de données
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class MatcherConfig:
    max_iterations: int = 100        # garde-fou par sub-portfolio
    zero_tol: float = 0.01           # un bucket sous ce seuil est considéré nul
    min_usage: float = 1e-6          # usage minimal d'un match (évite les micro-matchs)
    min_gain: float = 1e-9           # gain minimal de la norme L1 pour accepter un match
    gain_tol: float = 1e-9           # tolérance d'égalité des gains (départage par Gpt_Id)
    match_ccy_pm: bool = True        # l'externe doit avoir même CCY et PricingModel
    full_impact: bool = True         # True : l'externe impacte TOUS ses buckets
                                     # False : seuls les buckets qu'il compense sont impactés
    largest_first: bool = True       # traiter les sub-portfolios du plus gros au plus petit


@dataclass
class SubPortfolioState:
    ccy: str
    pricing_model: str
    way: str
    trades: List[TradeInfo]
    initial: Sensitivities
    current: Sensitivities

    @property
    def key(self) -> GroupKey:
        return (self.ccy, self.pricing_model, self.way)

    @property
    def name(self) -> str:
        return f"{self.ccy}_{self.pricing_model}_{self.way}"

    @property
    def l1(self) -> float:
        return sum(abs(v) for v in self.current.values())

    @property
    def initial_l1(self) -> float:
        return sum(abs(v) for v in self.initial.values())

    def apply(self, impact: Sensitivities, usage: float, zero_tol: float) -> None:
        """Ajoute usage * impact aux sensibilités courantes."""
        for bucket, e in impact.items():
            value = self.current.get(bucket, 0.0) + usage * e
            if abs(value) < zero_tol:
                self.current.pop(bucket, None)
            else:
                self.current[bucket] = value


@dataclass(frozen=True)
class Match:
    sub_portfolio: str
    external_tran_num: int
    usage: float          # fraction 0..1 du trade externe consommée par ce match
    reduction: float      # baisse réelle de sum|S_k| obtenue par ce match
    iteration: int


@dataclass(frozen=True)
class _Candidate:
    trade: TradeInfo
    usage: float
    gain: float
    impact: Sensitivities


# --------------------------------------------------------------------------- #
# Fonctions pures (faciles à tester)
# --------------------------------------------------------------------------- #
def l1_change(s: Sensitivities, e: Sensitivities, x: float) -> float:
    """Variation de sum|S_k| (sur les buckets de E) si on ajoute x * E."""
    return sum(abs(s.get(k, 0.0) + x * ek) - abs(s.get(k, 0.0)) for k, ek in e.items())


def offsetting_buckets(s: Sensitivities, e: Sensitivities) -> Sensitivities:
    """Sous-ensemble de E dont les buckets sont de signe opposé à S."""
    return {k: ek for k, ek in e.items() if s.get(k, 0.0) * ek < 0}


def optimal_usage(s: Sensitivities, e: Sensitivities, x_max: float) -> float:
    """
    Argmin sur x dans [0, x_max] de  f(x) = sum_k |S_k + x * E_k|.

    f est convexe et linéaire par morceaux : on part de la pente en x = 0 et
    on la fait croître de 2*|E_k| à chaque point de rupture x_k = -S_k / E_k.
    Retourne 0.0 si aucun usage ne réduit la norme L1.
    """
    if x_max <= 0:
        return 0.0
    slope = 0.0
    breaks: List[Tuple[float, float]] = []
    for k, ek in e.items():
        if ek == 0:
            continue
        sk = s.get(k, 0.0)
        if sk == 0:
            slope += abs(ek)                  # bucket neuf : f augmente dès x = 0+
        else:
            slope += ek if sk > 0 else -ek
            xk = -sk / ek
            if xk > 0:
                breaks.append((xk, abs(ek)))
    if slope >= 0:
        return 0.0
    for xk, w in sorted(breaks):
        if xk >= x_max:
            return x_max
        slope += 2.0 * w
        if slope >= 0:
            return xk
    return x_max


# --------------------------------------------------------------------------- #
# Matcher
# --------------------------------------------------------------------------- #
class PortfolioMatcher:
    """
    Args:
        internal_trades: trades internes.
        external_trades: trades externes candidats.
        rep_sensi: DataFrame (TranNum, Index, Tenor, Delta[, Gpt_Id]).
        offsetting: conservé pour compatibilité, non utilisé ici.
        config: paramètres de l'algorithme (voir MatcherConfig).
    """

    def __init__(
        self,
        internal_trades: List[TradeInfo],
        external_trades: List[TradeInfo],
        rep_sensi: pd.DataFrame,
        offsetting: Optional[pd.DataFrame] = None,
        config: Optional[MatcherConfig] = None,
    ):
        self.internal_trades = internal_trades
        self.external_trades = external_trades
        self.offsetting = offsetting
        self.config = config or MatcherConfig()

        # Agrégation unique des sensibilités par trade (un seul groupby)
        self._sensi_by_trade, self._max_gpt = self._aggregate(rep_sensi)

        # Externes triés par Gpt_Id décroissant, indexés par (CCY, PricingModel)
        self._externals_sorted: List[TradeInfo] = sorted(
            external_trades, key=lambda t: self._max_gpt.get(t.TranNum, 0), reverse=True
        )
        self._externals_by_group: Dict[Tuple[str, str], List[TradeInfo]] = defaultdict(list)
        for t in self._externals_sorted:
            self._externals_by_group[(t.CCY, t.PricingModel)].append(t)

        # État du matching (réinitialisé à chaque run)
        self.sub_portfolios: Dict[GroupKey, SubPortfolioState] = {}
        self.matches: List[Match] = []
        self.external_usage: Dict[int, float] = {}
        self._cap_reached: Dict[GroupKey, bool] = {}

    # ------------------------------------------------------------------ #
    # Préparation des données
    # ------------------------------------------------------------------ #
    @staticmethod
    def _aggregate(rep_sensi: pd.DataFrame) -> Tuple[Dict[int, Sensitivities], Dict[int, int]]:
        df = rep_sensi[["TranNum", "Index", "Tenor", "Delta"]].copy()
        df["Delta"] = df["Delta"].map(parse_numeric_value)
        agg = df.groupby(["TranNum", "Index", "Tenor"], sort=False)["Delta"].sum()

        by_trade: Dict[int, Sensitivities] = defaultdict(dict)
        for (tran, index, tenor), delta in agg.items():
            by_trade[tran][(index, tenor)] = float(delta)

        max_gpt: Dict[int, int] = {}
        if "Gpt_Id" in rep_sensi.columns:
            gpt = pd.to_numeric(rep_sensi["Gpt_Id"], errors="coerce").fillna(0).astype(int)
            max_gpt = gpt.groupby(rep_sensi["TranNum"]).max().to_dict()
        return dict(by_trade), max_gpt

    def create_sub_portfolios(self) -> Dict[GroupKey, SubPortfolioState]:
        groups: Dict[GroupKey, List[TradeInfo]] = defaultdict(list)
        for trade in self.internal_trades:
            groups[(trade.CCY, trade.PricingModel, trade.Way)].append(trade)

        self.sub_portfolios = {}
        for (ccy, pm, way), trades in groups.items():
            total: Sensitivities = defaultdict(float)
            for trade in trades:
                for bucket, delta in self._sensi_by_trade.get(trade.TranNum, {}).items():
                    total[bucket] += delta
            sub = SubPortfolioState(ccy, pm, way, trades, dict(total), dict(total))
            self.sub_portfolios[sub.key] = sub
            logger.info("Sub-portfolio %s : %d trades, %d buckets",
                        sub.name, len(trades), len(total))
        return self.sub_portfolios

    # ------------------------------------------------------------------ #
    # Algorithme
    # ------------------------------------------------------------------ #
    def _candidates(self, sub: SubPortfolioState) -> Iterable[TradeInfo]:
        pool = (self._externals_by_group.get((sub.ccy, sub.pricing_model), [])
                if self.config.match_ccy_pm else self._externals_sorted)
        for trade in pool:
            if trade.Way == sub.way:
                continue
            if self.external_usage[trade.TranNum] >= 1.0 - self.config.min_usage:
                continue
            yield trade

    def _evaluate(self, sub: SubPortfolioState, trade: TradeInfo) -> Optional[_Candidate]:
        e = self._sensi_by_trade.get(trade.TranNum)
        if not e:
            return None
        if not self.config.full_impact:
            e = offsetting_buckets(sub.current, e)
            if not e:
                return None

        remaining = 1.0 - self.external_usage[trade.TranNum]
        usage = optimal_usage(sub.current, e, remaining)
        if usage < self.config.min_usage:
            return None

        gain = -l1_change(sub.current, e, usage)
        if gain <= self.config.min_gain:
            return None
        return _Candidate(trade, usage, gain, e)

    def _find_best_match(self, sub: SubPortfolioState) -> Optional[_Candidate]:
        best: Optional[_Candidate] = None
        # Les candidats arrivent triés par Gpt_Id décroissant : un candidat ne
        # remplace le meilleur que s'il est strictement meilleur (> gain_tol).
        for trade in self._candidates(sub):
            cand = self._evaluate(sub, trade)
            if cand is not None and (best is None or cand.gain > best.gain + self.config.gain_tol):
                best = cand
        return best

    def _match_sub_portfolio(self, sub: SubPortfolioState) -> None:
        cfg = self.config
        for iteration in range(1, cfg.max_iterations + 1):
            best = self._find_best_match(sub)
            if best is None:
                return
            tran = best.trade.TranNum
            self.external_usage[tran] = min(1.0, self.external_usage[tran] + best.usage)
            sub.apply(best.impact, best.usage, cfg.zero_tol)
            self.matches.append(Match(sub.name, tran, best.usage, best.gain, iteration))
            logger.debug("%s it.%d : trade %s usage=%.4f gain=%.4f L1=%.4f",
                         sub.name, iteration, tran, best.usage, best.gain, sub.l1)
        self._cap_reached[sub.key] = True
        logger.warning("%s : plafond de %d itérations atteint, matching potentiellement incomplet",
                       sub.name, cfg.max_iterations)

    def match_portfolios(self) -> Dict[str, pd.DataFrame]:
        """Exécute le matching complet (réinitialise l'état) et retourne les résultats."""
        self.matches = []
        self._cap_reached = {}
        self.external_usage = {t.TranNum: 0.0 for t in self.external_trades}
        self.create_sub_portfolios()

        subs = list(self.sub_portfolios.values())
        if self.config.largest_first:
            subs.sort(key=lambda s: s.initial_l1, reverse=True)

        for sub in subs:
            logger.info("Matching %s (L1 initial = %.2f)", sub.name, sub.initial_l1)
            self._match_sub_portfolio(sub)
            logger.info("  -> L1 final = %.2f", sub.l1)

        logger.info("Matching terminé : %d matchs", len(self.matches))
        return self.get_results()

    run = match_portfolios

    # ------------------------------------------------------------------ #
    # Résultats
    # ------------------------------------------------------------------ #
    def get_results(self) -> Dict[str, pd.DataFrame]:
        """
        Clés :
          - internal_sub_portfolios : sensibilités INITIALES
          - matched_trades          : un enregistrement par match (Usage = fraction 0..1)
          - external_usage          : usage cumulé par trade externe (fraction 0..1)
          - unmatched_sensitivities : sensibilités RESTANTES (0 si soldé)
          - sub_portfolio_summary   : L1 initial / final par sub-portfolio
        """
        initial_rows, remaining_rows, summary_rows = [], [], []
        n_matches = defaultdict(int)
        for m in self.matches:
            n_matches[m.sub_portfolio] += 1

        for sub in self.sub_portfolios.values():
            for (idx, ten), d in sub.initial.items():
                initial_rows.append((sub.name, idx, ten, d))
            for (idx, ten) in sub.initial.keys() | sub.current.keys():
                remaining_rows.append((sub.name, idx, ten, sub.current.get((idx, ten), 0.0)))
            summary_rows.append((sub.name, sub.initial_l1, sub.l1, n_matches[sub.name],
                                 self._cap_reached.get(sub.key, False)))

        cols = ["SubPortfolio", "Index", "Tenor", "Delta"]
        return {
            "internal_sub_portfolios": pd.DataFrame(initial_rows, columns=cols),
            "matched_trades": pd.DataFrame(
                [(m.sub_portfolio, m.external_tran_num, m.usage, m.reduction, m.iteration)
                 for m in self.matches],
                columns=["SubPortfolio", "External_TranNum", "Usage", "Reduction", "Iteration"]),
            "external_usage": pd.DataFrame(
                [(t.TranNum, getattr(t, "InsNum", None), getattr(t, "ExternalParty", None),
                  t.CCY, t.PricingModel, t.Way, self.external_usage.get(t.TranNum, 0.0))
                 for t in self.external_trades],
                columns=["TranNum", "InsNum", "ExternalParty", "CCY", "PricingModel", "Way", "Usage"]),
            "unmatched_sensitivities": pd.DataFrame(remaining_rows, columns=cols),
            "sub_portfolio_summary": pd.DataFrame(
                summary_rows,
                columns=["SubPortfolio", "Initial_L1", "Final_L1", "Nb_Matches", "Iteration_Cap_Reached"]),
        }