import pandas as pd
from difflib import SequenceMatcher
import io

def clean_name(name):
    return (
        str(name)
        .upper()
        .replace(".", "")
        .replace(",", "")
        .replace("&", "AND")
        .replace("PVT", "PRIVATE")
        .replace("LTD", "LIMITED")
        .replace(" P ", " PRIVATE ")
        .replace("  ", " ")
        .strip()
    )

def is_close(a, b, tol):
    try:
        return abs(float(a) - float(b)) <= tol
    except:
        return False

def group_invoice(df, keys):
    return df.groupby(keys).agg({
        'Taxable Value': 'sum',
        'IGST': 'sum',
        'CGST': 'sum',
        'SGST': 'sum'
    }).reset_index()

def process_reconciliation(file_content):
    # Load Excel sheets
    xls = pd.ExcelFile(io.BytesIO(file_content))
    portal_df = pd.read_excel(xls, sheet_name="Portal data")
    books_df = pd.read_excel(xls, sheet_name="Books data")

    # Standardize column names
    portal_df.columns = portal_df.columns.str.strip()
    books_df.columns = books_df.columns.str.strip()

    # Helper to clean invoice numbers (handle 123.0 vs 123)
    def clean_invoice_number(val):
        s = str(val).strip().upper()
        if s.endswith('.0'):
            return s[:-2]
        return s

    # Define value columns
    value_cols = ['Taxable Value', 'IGST', 'CGST', 'SGST']

    # 1. Clean Data Types
    for df in [portal_df, books_df]:
        # Clean Names
        df['Clean_Name'] = df['Name'].apply(clean_name)
        
        # Clean Key Columns
        df['GSTIN'] = df['GSTIN'].astype(str).str.strip().str.upper()
        df['Invoice number'] = df['Invoice number'].apply(clean_invoice_number)
            
        # Clean Numeric Columns (Handle non-numeric gracefully)
        for col in value_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # Add Remarks
        df['Remarks'] = ''

    # Helper for tolerance checking (Vectorized)
    def close_vec(s1, s2, tol):
        return (s1 - s2).abs() <= tol

    # 1. Exact Match
    # Merge on keys
    merged = pd.merge(
        portal_df.reset_index(), 
        books_df.reset_index(), 
        on=['GSTIN', 'Invoice number'], 
        how='inner', 
        suffixes=('_p', '_b')
    )

    # Vectorized filter
    match_mask = (
        close_vec(merged['Taxable Value_p'], merged['Taxable Value_b'], 5) &
        close_vec(merged['IGST_p'], merged['IGST_b'], 2) &
        close_vec(merged['CGST_p'], merged['CGST_b'], 2) &
        close_vec(merged['SGST_p'], merged['SGST_b'], 2)
    )
    
    exact_matches = merged[match_mask]
    
    # Update Remarks
    if not exact_matches.empty:
        portal_df.loc[exact_matches['index_p'], 'Remarks'] = 'Exact Matched'
        books_df.loc[exact_matches['index_b'], 'Remarks'] = 'Exact Matched'

    # 2. Matched with multiple invoice in Portal data (Many Portal -> One Books)
    books_unmatched = books_df[books_df['Remarks'] == '']
    portal_unmatched = portal_df[portal_df['Remarks'] == '']
    
    # Group portal unmatched
    portal_grouped = portal_unmatched.groupby(['GSTIN', 'Invoice number'])[value_cols].sum().reset_index()
    
    merged_2 = pd.merge(
        books_unmatched.reset_index(),
        portal_grouped,
        on=['GSTIN', 'Invoice number'],
        how='inner',
        suffixes=('_b', '_grp')
    )
    
    match_mask_2 = (
        close_vec(merged_2['Taxable Value_b'], merged_2['Taxable Value_grp'], 5) &
        close_vec(merged_2['IGST_b'], merged_2['IGST_grp'], 2) &
        close_vec(merged_2['CGST_b'], merged_2['CGST_grp'], 2) &
        close_vec(merged_2['SGST_b'], merged_2['SGST_grp'], 2)
    )
    
    matched_2 = merged_2[match_mask_2]
    
    for _, row in matched_2.iterrows():
         # Mark the Book entry
        books_df.at[row['index'], 'Remarks'] = 'Matched with multiple invoice in Portal data'
        
        # Mark the Portal entries
        # Note: We must check 'Remarks' == '' to avoid re-marking already matched rows if loop overlaps?
        # But we filtered portal_unmatched earlier. However, we need indices relative to original df.
        mask = (
            (portal_df['GSTIN'] == row['GSTIN']) & 
            (portal_df['Invoice number'] == row['Invoice number']) & 
            (portal_df['Remarks'] == '')
        )
        if mask.sum() > 1: # Strict adherence to "Multiple" requirement
            portal_df.loc[mask, 'Remarks'] = 'Matched with multiple invoice in Portal data'
        else:
             # If it matched sum but only 1 row exists, it's effectively an exact match that was missed?
             # Or maybe it wasn't exact because of tolerance? logic says "Matched with multiple..."
             # We only mark if > 1 as per original code "if mask.sum() > 1"
             # If sum == 1, we DO NOT mark it here? User code implies that.
             # Reset book remark if condition fails?
             if mask.sum() <= 1:
                 books_df.at[row['index'], 'Remarks'] = '' # Revert

    # 3. Matched with multiple invoice in Books data (One Portal -> Many Books)
    books_unmatched = books_df[books_df['Remarks'] == ''] # Refresh
    portal_unmatched = portal_df[portal_df['Remarks'] == ''] # Refresh
    
    books_grouped = books_unmatched.groupby(['GSTIN', 'Invoice number'])[value_cols].sum().reset_index()
    
    merged_3 = pd.merge(
        portal_unmatched.reset_index(),
        books_grouped,
        on=['GSTIN', 'Invoice number'],
        how='inner',
        suffixes=('_p', '_grp')
    )
    
    match_mask_3 = (
        close_vec(merged_3['Taxable Value_p'], merged_3['Taxable Value_grp'], 5) &
        close_vec(merged_3['IGST_p'], merged_3['IGST_grp'], 2) &
        close_vec(merged_3['CGST_p'], merged_3['CGST_grp'], 2) &
        close_vec(merged_3['SGST_p'], merged_3['SGST_grp'], 2)
    )
    
    matched_3 = merged_3[match_mask_3]
    
    for _, row in matched_3.iterrows():
        portal_df.at[row['index'], 'Remarks'] = 'Matched with multiple invoice in Books data'
        
        mask = (
            (books_df['GSTIN'] == row['GSTIN']) & 
            (books_df['Invoice number'] == row['Invoice number']) & 
            (books_df['Remarks'] == '')
        )
        if mask.sum() > 1:
            books_df.loc[mask, 'Remarks'] = 'Matched with multiple invoice in Books data'
        else:
            if mask.sum() <= 1:
                portal_df.at[row['index'], 'Remarks'] = ''

    # 4. GSTIN Wise Match (Different Invoice Number)
    # Strategy: Group by GSTIN + Amounts. If matches found, mark them.
    # This avoids N^2 complexity.
    
    # We need to find: Same GSTIN, Different Invoice, Same Amounts.
    
    # Create a signature column for amounts
    # Using string representation for rough grouping, then precise check
    # Or just iterate groups.
    
    portal_unmatched = portal_df[portal_df['Remarks'] == '']
    books_unmatched = books_df[books_df['Remarks'] == '']
    
    # Group books by GSTIN for faster access
    books_by_gstin = books_unmatched.groupby('GSTIN')
    
    # Optimizing: We can iterate portal rows, but for 5000 rows it's okay if lookup is fast.
    # But if volumes are high, we need vectorization.
    # Vectorization ideas: Merge on GSTIN. This explodes if one GSTIN has many invoices.
    # Better: Loop small groups.
    
    matched_p_indices = []
    matched_b_indices = []
    
    # To prevent double usage of books in this step, track used book indices
    used_books = set()

    for gstin, p_group in portal_unmatched.groupby('GSTIN'):
        if gstin in books_by_gstin.groups:
            b_group = books_by_gstin.get_group(gstin)
            
            # For each row in p_group, look for match in b_group
            # This is O(N*M) but N and M are small per GSTIN usually.
            
            for p_idx, p_row in p_group.iterrows():
                # Filter books: Diff Invoice AND Same Values
                # Check used_books first
                available_books = b_group.loc[~b_group.index.isin(used_books)]
                
                if available_books.empty:
                    continue
                
                matches = available_books[
                    (available_books['Invoice number'] != p_row['Invoice number']) &
                    close_vec(available_books['Taxable Value'], p_row['Taxable Value'], 5) &
                    close_vec(available_books['IGST'], p_row['IGST'], 2) &
                    close_vec(available_books['CGST'], p_row['CGST'], 2) &
                    close_vec(available_books['SGST'], p_row['SGST'], 2)
                ]
                
                if not matches.empty:
                    # Mark MATCH FOUND
                    # FIX: Take only the FIRST match to ensure 1-to-1 mapping.
                    # Previous logic took ALL matches, causing mismatched totals (1 Portal vs Many Books).
                    
                    best_match_idx = matches.index[0]
                    
                    matched_p_indices.append(p_idx)
                    matched_b_indices.append(best_match_idx)
                    used_books.add(best_match_idx)

    if matched_p_indices:
        portal_df.loc[matched_p_indices, 'Remarks'] = 'GSTIN Wise matched'
        books_df.loc[matched_b_indices, 'Remarks'] = 'GSTIN Wise matched'

    # 5. Party-wise fuzzy matching (Optimized)
    # Pre-calculate sums for unmatched names
    
    # Refresh unmatched
    p_unmatched = portal_df[portal_df['Remarks'] == '']
    b_unmatched = books_df[books_df['Remarks'] == '']
    
    if not p_unmatched.empty and not b_unmatched.empty:
        # Aggregated sums by Clean_Name
        p_sums = p_unmatched.groupby('Clean_Name')[value_cols].sum()
        b_sums = b_unmatched.groupby('Clean_Name')[value_cols].sum()
        
        # Now iterate names - significantly fewer items than rows
        p_names = p_sums.index.tolist()
        b_names = b_sums.index.tolist()
        
        # Sort or index to speed up? 
        # Fuzzy matching 1000 names against 1000 names is 1M comparisons.
        # Still high but better than row-by-row.
        # We can accept this or use a simple heuristic (starts with same letter).
        
        for p_name in p_names:
            p_vals = p_sums.loc[p_name]
            
            # Optimization: Check starts-with to reduce search space? 
            # Risk: 'The Apple' vs 'Apple'.
            # Let's just do full space but break early? No, we need best match?
            # User code: "if ratio > 0.85". Any match > 0.85.
            
            for b_name in b_names:
                # Quick check: Length difference too big?
                if abs(len(p_name) - len(b_name)) > 5 and len(p_name) < 10:
                     continue # Heuristic to skip obviously different
                     
                ratio = SequenceMatcher(None, p_name, b_name).ratio()
                if ratio > 0.85:
                    b_vals = b_sums.loc[b_name]
                    
                    if (is_close(p_vals['Taxable Value'], b_vals['Taxable Value'], 5) and
                        is_close(p_vals['IGST'], b_vals['IGST'], 2) and
                        is_close(p_vals['CGST'], b_vals['CGST'], 2) and
                        is_close(p_vals['SGST'], b_vals['SGST'], 2)):
                        
                        # Apply to original DFs
                        portal_df.loc[(portal_df['Clean_Name'] == p_name) & (portal_df['Remarks'] == ''), 'Remarks'] = 'Party wise matched'
                        books_df.loc[(books_df['Clean_Name'] == b_name) & (books_df['Remarks'] == ''), 'Remarks'] = 'Party wise matched'

    # Calculate Statistics
    def get_stats(df):
        total = len(df)
        unmatched = len(df[df['Remarks'] == ''])
        matched_counts = df[df['Remarks'] != '']['Remarks'].value_counts().to_dict()
        return {
            "total": total,
            "unmatched": unmatched,
            "matched_breakdown": matched_counts
        }

    stats = {
        "portal": get_stats(portal_df),
        "books": get_stats(books_df)
    }

    # Save output
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        portal_df.drop(columns=['Clean_Name']).to_excel(writer, sheet_name='Portal data', index=False)
        books_df.drop(columns=['Clean_Name']).to_excel(writer, sheet_name='Books data', index=False)
    
    output.seek(0)
    return output, stats

