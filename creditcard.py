import camelot
import pandas as pd
import numpy as np

import ctypes
from ctypes.util import find_library
find_library("".join(("gsdll", str(ctypes.sizeof(ctypes.c_voidp) * 8), ".dll")))

def accounting_format(x):
    if '(' in x and ')' in x:
        x = x.replace('(', '')
        x = x.replace(')', '')
        x = f'-{x}'
        return x
    else:
        return x
        
def read_creditcard(pdf_path):
    """Extract table from pdf and return a dataframe"""
    tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream', edge_tol=500)

    res = pd.DataFrame()
    target_cols = ['DATE', 'DESCRIPTION', 'AMOUNT (SGD)']

    for table in tables:
        table = table.df
        
        # Search for colnames as row
        for col in table.columns:
            x = table[table.loc[:, col] == 'DATE']
            
            if len(x) > 0:
                # Check is desc and amount is also in the same tow
                x_list = x.values.tolist()[0]
                
                if  set(target_cols) <= set(x_list):
                    # Get col index from X-list
                    index_list = [i for i in range(len(x_list)) if x_list[i] in target_cols]
                    COI = [table.columns.tolist()[i] for i in index_list]
                    
                    # Fix column headers
                    df = table[COI]
                    df.columns = df.iloc[x.index[0]]
                    df = df.iloc[x.index[0]+1:]

                    res = res.append(df)
                    
    res = res.reset_index(drop=True)


    # Filter for only payments 
    df = res.replace(r'^\s*$', np.nan, regex=True).replace('',np.nan)
    df = df[df['DATE'].notnull()]

    # Remove incoming payments
    df = df[df['DESCRIPTION'].notnull()]
    df = df[~df['DESCRIPTION'].str.contains('FAST INCOMING PAYMENT', case=False, na=False)]

    # Further cleaning
    df['DESCRIPTION'] = df['DESCRIPTION'].apply(lambda x: x.replace('\nSINGAPORE\nSG',''))
    df['DESCRIPTION'] = df['DESCRIPTION'].apply(lambda x: x.replace('\nSGH\nSG',''))
    df['DESCRIPTION'] = df['DESCRIPTION'].apply(lambda x: x.replace('\nSingapore\nSG',''))

    df['AMOUNT (SGD)'] = df['AMOUNT (SGD)'].apply(accounting_format)
    df['AMOUNT (SGD)'] = df['AMOUNT (SGD)'].astype(float)
    return df