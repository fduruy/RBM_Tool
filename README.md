# RBM_Tool
Projet OFFSETTING
## Objectif
Script qui lit des fichiers de données en entrée (CSV / Excel), applique des règles de calcul, et écrit les résultats dans des fichiers de sortie.

- **INPUTS** : [data/input/.txt, colonnes attendues, format des dates]
- **CALCULATIONS** : [décrire brièvement les règles de calcul]
- **OUTPUTS** : [data/output/resultatsYYYYMMDD.csv, nom des fichiers produits, colonnes/métriques attendues]

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
