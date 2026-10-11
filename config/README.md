# Configuration RBM_Tool

Ce dossier contient les fichiers de configuration pour RBM_Tool qui definissent les regles a respecter pour :
- **Index** : Validation, normalisation et regroupement des index
- **Tenor** : Validation, normalisation, conversion et tri des tenors  
- **Sous-Portefeuilles** : Creation, exclusion et priorites des sous-portefeuilles

## Fichiers de Configuration

### config.json
Fichier principal de configuration au format JSON avec la structure suivante :

```json
{
  "version": "1.0",
  "description": "Description de la configuration",
  "rules": {
    "Index": { ... },
    "Tenor": { ... },
    "SubPortfolio": { ... },
    "InternalTrades": { ... },
    "ExternalTrades": { ... },
    "Output": { ... },
    "Validation": { ... }
  }
}
```

## Structure des Regles

### 1. Regles Index

- **allowed_indexes** : Liste des index autorises
- **case_sensitive** : Sensibilite a la casse
- **normalize_case** : Normalisation (upper/lower/preserve)
- **aliases** : Alias pour les index
- **validation** : Options de validation
- **grouping_rules** : Regles de regroupement

**Exemple :**
```json
"Index": {
  "allowed_indexes": ["Estr", "Sonia", "Euribor"],
  "case_sensitive": false,
  "normalize_case": "upper",
  "aliases": {"EURIBOR": "Euribor"}
}
```

### 2. Regles Tenor

- **allowed_tenors** : Liste des tenors autorises
- **case_sensitive** : Sensibilite a la casse
- **normalize_case** : Normalisation
- **aliases** : Alias pour les tenors
- **conversion** : Conversions automatiques (mois en annees, semaines en mois)
- **sorting** : Ordre de tri

**Exemple :**
```json
"Tenor": {
  "allowed_tenors": ["ON", "TN", "1W", "1M", "1Y"],
  "conversion": {
    "months_to_years": {"12M": "1Y"},
    "weeks_to_months": {"4W": "1M"}
  }
}
```

### 3. Regles Sous-Portefeuilles

- **naming_convention** : Convention de nommage
- **grouping** : Critères de regroupement
- **specific_subportfolios** : Regles specifiques par sous-portefeuille
- **exclusion_rules** : Regles d'exclusion
- **matching** : Regles de matching
- **aggregation** : Regles d'agregation

**Exemple :**
```json
"SubPortfolio": {
  "naming_convention": {
    "format": "{CCY}_{PricingModel}_{Way}",
    "separator": "_"
  },
  "grouping": {
    "primary_key": ["CCY", "PricingModel", "Way"]
  },
  "matching": {
    "algorithm": {"type": "iterative", "max_iterations": 100},
    "sensitivity_matching": {"require_opposite_signs": true}
  }
}
```

### 4. Regles de Validation Globale

- **required_files** : Fichiers obligatoires
- **consistency_checks** : Verifications de coherence
- **data_quality** : Qualite des donnees

## Utilisation

Pour utiliser la configuration, chargez le fichier JSON dans votre code :

```python
import json

with open('config/config.json', 'r') as f:
    config = json.load(f)

# Acces aux regles
index_rules = config['rules']['Index']
tenor_rules = config['rules']['Tenor']
```

## Modification

1. Editez le fichier `config.json` avec un editeur de texte ou un outil JSON
2. Validez le JSON avec un validateur en ligne si necessaire
3. Testez les changements avec vos donnees

## Bonnes Pratiques

- Faites une copie de sauvegarde avant de modifier
- Validez toujours le JSON apres modification
- Testez avec un petit jeu de donnees avant de deployer
- Documentez les changements dans les commits git

## Fichiers Supplementaires

Vous pouvez ajouter d'autres fichiers de configuration :
- `validation_rules.json` : Regles de validation detaillees
- `mapping_rules.json` : Regles de mapping pour les donnees
- `custom_rules.py` : Regles personnalisees en Python
