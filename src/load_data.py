import pandas as pd
import numpy as np
from rapidfuzz import fuzz

def detect_and_skip_header(df):
    """
    Detects and skips header rows in Nigerian bank statement format.
    Looks for the row containing 'Trans. Date' or similar transaction headers.
    """
    # Look for the header row (check first 20 rows)
    max_rows = min(20, len(df))
    
    for idx in range(max_rows):
        try:
            row = df.iloc[idx]
            row_str = ' '.join([str(val).lower() for val in row.values if pd.notna(val)])
            
            # Check if this row contains transaction headers
            if any(keyword in row_str for keyword in ['trans', 'date', 'description', 'debit', 'credit', 'narration']):
                # Found the header row, use it
                new_df = df.iloc[idx:].copy()
                new_df.columns = new_df.iloc[0].values
                new_df = new_df.iloc[1:].reset_index(drop=True)
                return new_df
        except Exception:
            continue
    
    # If no header found, return as-is
    return df

# --- Category keywords ---
CATEGORIES = {
    "Food & Dining": ["restaurant", "shawarma", "kfc", "mcdonald", "eat", "shoprite", 
                      "ubereats", "food", "cafe", "pizza", "chicken", "burger"],
    "Transport": ["uber", "bolt", "taxi", "fuel", "gas", "bus", "transport", "fare"],
    "Utilities": ["electricity", "water", "internet", "dstv", "mtn", "data", "airtime",
                  "nepa", "phcn", "ikedc", "ekedc"],
    "Shopping": ["amazon", "jumia", "mall", "shop", "konga", "store", "market"],
    "Income": ["salary", "payroll", "interest earned", "bonus", "credit", "deposit", "transfer in", "earned"],
    "Savings": ["owealth", "auto-save", "auto save", "withdrawal(transaction payment)", 
                "save", "investment", "balance"],
    "Entertainment": ["netflix", "dstv", "cinema", "movie", "game", "spotify"],
    "Healthcare": ["hospital", "pharmacy", "doctor", "clinic", "medical", "health"],
    "Other": []
}

def load_and_clean_expenses(file_path=None, df_override=None, skip_header_detection=False):
    """
    Loads CSV, detects header automatically (or accepts dataframe override),
    and cleans columns to standard ['date', 'description', 'amount'].
    
    Parameters:
    -----------
    file_path : str, optional
        Path to CSV file
    df_override : DataFrame, optional
        Pre-loaded dataframe to process
    skip_header_detection : bool, optional
        If True, skip automatic header detection
        
    Returns:
    --------
    DataFrame with columns: date, description, amount
    """
    if df_override is not None:
        df = df_override.copy()
    else:
        if file_path is None:
            raise ValueError("No CSV file provided")
        df = pd.read_csv(file_path)
    
    # Auto-detect header row for Nigerian bank statements (unless skipped)
    if not skip_header_detection:
        try:
            df = detect_and_skip_header(df)
        except Exception as e:
            print(f"Header detection error: {e}")
            # Continue with original df if detection fails

    # Basic cleaning: standardize column names
    new_columns = []
    for c in df.columns:
        try:
            new_col = str(c).strip().lower()
            new_columns.append(new_col)
        except:
            new_columns.append(str(c))
    
    df.columns = new_columns
    
    # Handle duplicate columns by appending .1, .2 etc.
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols[cols == dup].index.values.tolist()] = [dup + '.' + str(i) if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    
    # Remove any completely empty columns FIRST
    df = df.dropna(axis=1, how='all')
    
    # Remove unnamed columns that are mostly empty
    cols_to_drop = []
    for col in df.columns:
        if 'unnamed' in str(col).lower():
            # Check if this column is mostly empty
            if df[col].isna().sum() > len(df) * 0.5:
                cols_to_drop.append(col)
    
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    
    # Also drop the first column if it's just row numbers or empty
    if len(df.columns) > 0:
        first_col = df.columns[0]
        if 'unnamed' in str(first_col).lower():
            # Check if it's sequential numbers (row index)
            try:
                if df[first_col].dropna().astype(int).equals(pd.Series(range(len(df[first_col].dropna())))):
                    df = df.drop(columns=[first_col])
            except:
                pass

    # Map expected columns with more flexible matching
    mapping = {}
    for col in df.columns:
        try:
            col_clean = str(col).strip().lower()
            
            # Remove special characters for matching
            col_clean_simple = col_clean.replace('(', '').replace(')', '').replace('?', '')
            
            # Check for description
            if "desc" in col_clean_simple or "narration" in col_clean_simple or "details" in col_clean_simple or "particular" in col_clean_simple:
                mapping[col] = "description"
            
            # Check for date (prefer trans date over value date)
            elif ("trans" in col_clean_simple and "date" in col_clean_simple) or "transdate" in col_clean_simple:
                if "value" not in col_clean_simple:
                    mapping[col] = "date"
            
            # Check for debit - look for "debit" but not "credit"
            elif "debit" in col_clean_simple and "credit" not in col_clean_simple:
                mapping[col] = "debit"
            
            # Check for credit - look for "credit" but not "debit"
            elif "credit" in col_clean_simple and "debit" not in col_clean_simple:
                mapping[col] = "credit"
                
        except Exception as e:
            continue

    if mapping:
        df = df.rename(columns=mapping)
    
    # Handle separate debit/credit columns
    if 'debit' in df.columns and 'credit' in df.columns:
        try:
            # Clean debit column
            df['debit_clean'] = df['debit'].fillna('0')
            df['debit_clean'] = df['debit_clean'].replace('--', '0')
            df['debit_clean'] = df['debit_clean'].astype(str)
            
            # Remove commas and convert to float
            debit_values = []
            for val in df['debit_clean']:
                try:
                    clean_val = val.replace(',', '').replace('--', '0').strip()
                    if clean_val == '' or clean_val == '--':
                        debit_values.append(0.0)
                    else:
                        debit_values.append(float(clean_val))
                except:
                    debit_values.append(0.0)
            
            df['debit_amount'] = debit_values
            
            # Clean credit column
            df['credit_clean'] = df['credit'].fillna('0')
            df['credit_clean'] = df['credit_clean'].replace('--', '0')
            df['credit_clean'] = df['credit_clean'].astype(str)
            
            # Remove commas and convert to float
            credit_values = []
            for val in df['credit_clean']:
                try:
                    clean_val = val.replace(',', '').replace('--', '0').strip()
                    if clean_val == '' or clean_val == '--':
                        credit_values.append(0.0)
                    else:
                        credit_values.append(float(clean_val))
                except:
                    credit_values.append(0.0)
            
            df['credit_amount'] = credit_values
            
            # Combine: credits are positive (income), debits are negative (expenses)
            df['amount'] = df['credit_amount'] - df['debit_amount']
            
            # Clean up temporary columns
            df = df.drop(columns=['debit', 'credit', 'debit_clean', 'credit_clean', 'debit_amount', 'credit_amount'])
            
        except Exception as e:
            raise ValueError(f"Error processing debit/credit columns: {e}")
            
    elif 'debit' in df.columns:
        try:
            df_debit = df['debit'].fillna('0')
            debit_values = []
            
            for val in df_debit:
                try:
                    val_str = str(val).replace(',', '').replace('--', '').strip()
                    if val_str == '' or val_str == '0':
                        debit_values.append(0.0)
                    else:
                        debit_values.append(float(val_str))
                except:
                    debit_values.append(0.0)
            
            # Make sure we have the right number of values
            if len(debit_values) != len(df):
                raise ValueError(f"Processed {len(debit_values)} debit values but dataframe has {len(df)} rows")
            
            df['amount'] = [-x for x in debit_values]
            df = df.drop(columns=['debit'])
        except Exception as e:
            raise ValueError(f"Error processing debit column: {e}")
            
    elif 'credit' in df.columns:
        try:
            credit_values = []
            for val in df['credit'].fillna('0').astype(str):
                try:
                    clean_val = val.replace(',', '').replace('--', '0').strip()
                    credit_values.append(float(clean_val) if clean_val else 0.0)
                except:
                    credit_values.append(0.0)
            df['amount'] = credit_values
            df = df.drop(columns=['credit'])
        except Exception as e:
            raise ValueError(f"Error processing credit column: {e}")

    # Only keep required columns
    required = ["date", "description", "amount"]
    if not all(c in df.columns for c in required):
        available = list(df.columns)
        raise ValueError(
            f"CSV must contain columns like: {required}\n"
            f"Available columns: {available}"
        )

    df = df[required].copy()

    # Amount should already be processed above, but ensure it's numeric
    if 'amount' not in df.columns:
        raise ValueError("Could not find or create 'amount' column. Make sure your CSV has Debit/Credit or Amount columns.")

    # Convert date
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    
    # Drop invalid rows
    df = df.dropna(subset=["date", "amount", "description"])
    df = df[df["amount"] != 0]  # Remove zero-amount transactions

    return df

def categorize_transaction(description):
    """
    Categorize transaction using fuzzy matching against keywords.
    
    Parameters:
    -----------
    description : str
        Transaction description
        
    Returns:
    --------
    str : Category name
    """
    desc = str(description).lower()
    best_cat = "Other"
    best_score = 0

    for cat, keywords in CATEGORIES.items():
        if cat == "Other":
            continue
        for kw in keywords:
            score = fuzz.partial_ratio(kw.lower(), desc)
            if score > best_score and score > 70:
                best_score = score
                best_cat = cat
                
    return best_cat

def detect_anomalies(df, column="amount", threshold=3):
    """
    Detect anomalies using Z-score method.
    
    Parameters:
    -----------
    df : DataFrame
        Transaction data
    column : str
        Column to check for anomalies
    threshold : float
        Number of standard deviations for anomaly threshold
        
    Returns:
    --------
    Series : Boolean series indicating anomalies
    """
    mean = df[column].mean()
    std = df[column].std()
    
    if std == 0:  # Handle case where all values are the same
        return pd.Series([False] * len(df), index=df.index)
    
    z_scores = np.abs((df[column] - mean) / std)
    return z_scores > threshold

def calculate_monthly_stats(df):
    """
    Calculate monthly spending statistics.
    
    Parameters:
    -----------
    df : DataFrame
        Transaction data with 'date', 'amount', and 'category' columns
        
    Returns:
    --------
    DataFrame : Monthly statistics
    """
    df = df.copy()
    df['year_month'] = df['date'].dt.to_period('M')
    
    monthly = df.groupby('year_month').agg({
        'amount': ['sum', 'mean', 'count']
    }).round(2)
    
    monthly.columns = ['Total', 'Average', 'Count']
    monthly.index = monthly.index.astype(str)
    
    return monthly

def calculate_category_stats(df):
    """
    Calculate spending by category.
    
    Parameters:
    -----------
    df : DataFrame
        Transaction data with 'category' and 'amount' columns
        
    Returns:
    --------
    DataFrame : Category statistics
    """
    cat_stats = df.groupby('category').agg({
        'amount': ['sum', 'mean', 'count']
    }).round(2)
    
    cat_stats.columns = ['Total', 'Average', 'Transactions']
    cat_stats = cat_stats.sort_values('Total', ascending=False)
    
    return cat_stats

def calculate_net_flow(df):
    """
    Calculate net cash flow (Income - Expenses).
    
    Parameters:
    -----------
    df : DataFrame
        Transaction data with 'amount' and 'category' columns
        
    Returns:
    --------
    dict : Net flow statistics
    """
    # Positive amounts are income/credits, negative are expenses/debits
    income = df[df['amount'] > 0]['amount'].sum()
    expenses = abs(df[df['amount'] < 0]['amount'].sum())
    net = income - expenses
    
    return {
        'income': income,
        'expenses': expenses,
        'net': net,
        'savings_rate': (net / income * 100) if income > 0 else 0
    }
