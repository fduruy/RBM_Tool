"""
database.py - SQLite storage for RBM_Tool results.

Stores the result tables produced by the portfolio matching into a local
SQLite database file, so they can be linked dynamically from Excel
(via an ODBC connection).

Principle
---------
- One table per result DataFrame, named after the key in the results dict.
- Tables are fully REPLACED at each run (design phase: no history kept).
- Uses only the Python standard library (sqlite3) plus pandas to_sql.

Excel dynamic link
------------------
1. Install a SQLite ODBC driver once (e.g. ch-werner.de/sqliteodbc).
2. Excel: Data > Get Data > From Other Sources > From ODBC,
   point it to data/database/rbm_results.db, select the tables.
3. Refresh All in Excel after each run of the tool.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from typing import Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join('data', 'database', 'rbm_results.db')

# Result table keys that are persisted (mirrors get_results() keys)
TABLE_KEYS = [
    'internal_sub_portfolios',
    'matched_trades',
    'external_usage',
    'unmatched_sensitivities',
    'sub_portfolio_summary',
]

# Input table keys that are persisted
INPUT_TABLE_KEYS = ['gt_valo', 'rep_sensi', 'offsetting']


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Open (and create if needed) the SQLite database file.

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        sqlite3.Connection: Open connection (caller must close it)
    """
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    logger.info(f"Connecting to SQLite database: {db_path}")
    return sqlite3.connect(db_path)


def save_results(results: Dict[str, pd.DataFrame],
                 db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Save the result tables into the SQLite database (tables replaced each run).

    Args:
        results (Dict[str, pd.DataFrame]): Result tables from process_all_trades()
        db_path (str): Path to the SQLite database file

    Returns:
        bool: True if all tables were saved successfully
    """
    try:
        conn = get_connection(db_path)
        try:
            for key in TABLE_KEYS:
                df = results.get(key)
                if df is None:
                    logger.warning(f"Table '{key}' missing from results, skipped")
                    continue
                df.to_sql(key, conn, if_exists='replace', index=False)
                logger.info(f"Saved table '{key}': {len(df)} rows")
        finally:
            conn.close()
        logger.info("All result tables saved to SQLite successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving results to SQLite: {str(e)}")
        return False


def save_inputs(data: Dict[str, pd.DataFrame],
                 db_path: str = DEFAULT_DB_PATH) -> bool:
    """
    Save the input tables into the SQLite database (tables replaced each run).

    Args:
        data (Dict[str, pd.DataFrame]): Input DataFrames with keys
            'gt_valo', 'rep_sensi', 'offsetting'
        db_path (str): Path to the SQLite database file

    Returns:
        bool: True if all tables were saved successfully
    """
    try:
        conn = get_connection(db_path)
        try:
            for key in INPUT_TABLE_KEYS:
                df = data.get(key)
                if df is None:
                    logger.warning(f"Input table '{key}' missing, skipped")
                    continue
                df.to_sql(key, conn, if_exists='replace', index=False)
                logger.info(f"Saved input table '{key}': {len(df)} rows")
        finally:
            conn.close()
        logger.info("All input tables saved to SQLite successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving inputs to SQLite: {str(e)}")
        return False


def load_inputs(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, pd.DataFrame]]:
    """
    Load the input tables from the SQLite database.

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        Optional[Dict[str, pd.DataFrame]]: Dictionary with keys
            'gt_valo', 'rep_sensi', 'offsetting', or None if a table is missing
    """
    try:
        conn = get_connection(db_path)
        try:
            available = set(row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"))
            missing = [k for k in INPUT_TABLE_KEYS if k not in available]
            if missing:
                logger.error(f"Input tables missing in database: {missing}")
                logger.error("Run 'python src/main.py --init-db' (or '--samples --init-db') "
                             "once to load the input files into the database")
                return None
            data = {k: pd.read_sql(f"SELECT * FROM {k}", conn) for k in INPUT_TABLE_KEYS}
        finally:
            conn.close()
        logger.info("All input tables loaded from SQLite successfully")
        return data
    except Exception as e:
        logger.error(f"Error loading inputs from SQLite: {str(e)}")
        return None


def read_table(table_name: str,
               db_path: str = DEFAULT_DB_PATH) -> Optional[pd.DataFrame]:
    """
    Read a table from the SQLite database (utility for checks / Excel-less access).

    Args:
        table_name (str): Name of the table to read
        db_path (str): Path to the SQLite database file

    Returns:
        Optional[pd.DataFrame]: The table as a DataFrame, or None on error
    """
    try:
        conn = get_connection(db_path)
        try:
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
        finally:
            conn.close()
        logger.info(f"Read table '{table_name}': {len(df)} rows")
        return df
    except Exception as e:
        logger.error(f"Error reading table '{table_name}': {str(e)}")
        return None


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    print("This module is not meant to be run directly. "
          "Use main.py to run the full workflow.")
