# RBM_Tool
Projet OFFSETTING
## Objectif
Script qui lit des fichiers de données en entrée (CSV / Excel), applique des règles de calcul, et écrit les résultats dans des fichiers de sortie.

- **INPUTS** : [#1 read input file(s) : data/input/GT_Valo.csv, toutes les colonnes]
- **CALCULATIONS** : [#2 Identify Internal trades, #3 Identify External trades, #compute a summary of internal trades and external trades]
- **OUTPUTS** : [data/output/resultats[YYYYMMDD].csv, summarize the resultas from Calculations in CSV, format attendu :Internal trades et MTM, External trades et MTM]

## Structure du projet
```text
RBM_TOOL/
├── README.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── main.py             # point d'entrée : lit, calcule, écrit
│   ├── inputs.py           # lecture et validation des fichiers entrée
│   ├── calculations.py     # toutes les règles de calcul
│   └── outputs.py          # génération des fichiers sortie
├── tests/
│   └── test_calculations.py
├── data/
│   ├── input/
│   └── output/
└── examples/
    └── exemple_entree.csv
