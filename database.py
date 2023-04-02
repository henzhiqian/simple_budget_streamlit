import streamlit as st  # pip install streamlit
# import the sqlite3 library
import sqlite3
import pandas as pd

# create the connection object
conn = sqlite3.connect("new.db")
# get a cursor object used to execute SQL commands
cursor = conn.cursor()

def check_if_table_exists(table_name):
    """Returns True if table exists, otherwise creates table and returns True"""
    check_query = f"""SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';"""
    cursor.execute(check_query)
    result=cursor.fetchone()
    if not result:
        # Creating table
        create_query = """ CREATE TABLE monthly_summary (
                    datetime DATETIME NOT NULL,
                    income_amt REAL NOT NULL,
                    income_type VARCHAR(255) NOT NULL,
                    expense_amt REAL NOT NULL,
                    expense_type VARCHAR(255) NOT NULL,
                    comment VARCHAR(255)
                ); """

        cursor.execute(create_query)
        return True
    return result

def insert_period(df):
    """Returns the report on a successful creation, otherwise raises an error"""
    assert isinstance(df, pd.DataFrame), "df must be a pandas DataFrame"
    assert df.columns == ['datetime', 'income_amt', 'income_type', 'expense_amt', 'expense_type', 'comment'], "df must have the following columns: ['datetime', 'income_amt', 'income_type', 'expense_amt', 'expense_type', 'comment']"

    df.to_sql('monthly_summary', conn, if_exists='append', index=False)

def fetch_all_periods():
    """Returns dataframe of all periods"""
    df = pd.read_sql_query("SELECT * FROM monthly_summary", conn)
    return df


def get_period(start_date, end_date):
    """Returns dataframe of selected periods"""
    df = pd.read_sql_query(f"SELECT * FROM monthly_summary WHERE datetime BETWEEN '{start_date}' AND '{end_date}'", conn)
    return df
