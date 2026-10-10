# RBM_Tool
Projet OFFSETTING
## Objectif
Script qui lit des fichiers de données en entrée (CSV / Excel), applique des règles de calcul, et écrit les résultats dans des fichiers de sortie.

- **INPUTS** : 
[
    #1 read input file(s) : data/input/GT_Valo.csv, data/input/Rep_Sensi.csv, data/input/Offsetting.csv. Files samples are provided in samples.
    GT_Valo.csv contains detailed information about each trades such as : identification number (TranNum), type of trade, currency, PricingModel, MtM, internal or external trade.
    Rep_Sensi.csv contains detailed sensitivities per trade per index_curve per tenor.  
    Offsetting.csv contains detailed Daily_PnL and YtD_PnL per trade.
    #2 Run checks to ensure each trades in GT_Valo.csv have at least one or more corresponding sensitivities in Rep_Sensi.csv and a corresponding PnL and YtD_PnL in Offsetting.csv
]
Code everyting necessary in inputs.py using clear and understandable python language with commented code for beginners. Error handling and proper debug message are mandatory

- **CALCULATIONS** : 
[
    #3 Identify Internal trades (CLF* or FSA* in column ExternalParty of GT_Valo.csv) and regroup them by CCY, PricingModel and WAY (such as EUR_Discounting_Pay or GBP_Discounting_Rec or every possible combination CCY_PricingModel_WAY).
    #4 Identify External trades (using the same way as internal trades). 
    #5 First Step: create a comprehensive tables per internal_sub_portfolio with the sensitivity ordered by Index and Gpt_Id. Sum sensitivity per Index and Gpt_ID. It is called Internal Sub_Portfolios
    #6 Second Step : create a comprehensive table per external_trade 
    
    #7 Third Setp, The portfolio matching and optimization: For each Sub_Portfolios of internal trades we want to find the corresponding external trades that reduce the sensitivity by Index and Tenor amongst the list of external trades within the same group safe the WAY (Pay vs Rec). It is an iterative process. It must start by finding the trade that reduce the maximum of overall sensitivity (index and tenor) starting by the highest GPT_ID and going backward. For any iteration, if the totality of the trade is used then usage will be 100% and the trade cannot be used anymore for future matching. But it is possible to use only a portion of a trade between 0% abnd 100%, thus the remaining portion will be available for future matching if needed. 
    #7 is the most important part of the code and will need clear and dedicated functions or objects
   
    #8 at the end of #7, Create detailed tables of Internal Sub portfolio and their matching and remaining unmatched sensitivities. Create detailed tables of External trades and their % of usage. Create a detailed table for 

]
Code everyting necessary in calculations.py using clear and understandable python language with commented code for beginners. Error handling and proper debug message are mandatory

- **OUTPUTS** : 
[
    #8Create outputs : data/output/resultats[YYYYMMDD.csv], summarize the resultas from Calculations in CSV
] 
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
