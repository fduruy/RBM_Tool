# RBM_Tool
Projet OFFSETTING
## Objectif
Script qui lit des fichiers de données en entrée (CSV / Excel), applique des règles de calcul, et écrit les résultats dans des fichiers de sortie.

- **INPUTS** : [#1 read input file(s) : data/input/GT_Valo.csv, data/input/Rep_Sensi.csv, data/input/Offsetting.csv. Files samples are provided in samples/] 
Code everyting necessary in inputs.py using clear and understandable python language with commented code for beginners. Error handling and proper debug message are mandatory

- **CALCULATIONS** : [#2 Identify Internal trades (CLF* or FSA* in column ExternalParty of GT_Valo.csv) and regroup them by CCY and WAY (such as EUR_Pay or GBP_Rec or every possible combination CCY_WAY), #3 Identify External trades (using the same way as internal trades), #compute a summary of internal trades and external trades] 
Code everyting necessary in calculations.py using clear and understandable python language with commented code for beginners. Error handling and proper debug message are mandatory

- **OUTPUTS** : [data/output/resultats[YYYYMMDD.csv], summarize the resultas from Calculations in CSV, format attendu :Internal trades et MTM, External trades et MTM] 
Code everyting necessary in outputs.py using clear and understandable python language with commented code for beginners. Error handling and proper debug message are mandatory

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
└── samples/
    └── GT_Valo.csv
    └── Rep_Sensi.csv
    └── Offsetting.csv
