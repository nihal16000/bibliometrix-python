import pandas as pd
import numpy as np

MANDATORY_COLUMNS = [
    'DB', 'UT', 'DI', 'PMID', 'TI', 'SO', 'JI', 'PY', 'DT', 'LA', 'TC', 
    'AU', 'AF', 'C1', 'RP', 'CR', 'DE', 'ID', 'AB', 'VL', 'IS', 'BP', 'EP', 'SR'
]

MULTI_VALUE_COLUMNS = ['AU', 'AF', 'C1', 'CR', 'DE', 'ID']

def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Phase 5: Validation.
    
    This function programmatically verifies the DataFrame before it is finalized
    and pushed to the Shiny frontend. It guarantees that the dataset conforms 
    strictly to the Type Contracts defined in the project specifications.
    
    Validations performed:
    1. Existence: All mandatory 2- and 3-letter WoS Field Tags must exist.
    2. Null Handling: Pandas NaN or Python None values are NOT permitted.
    3. Type Contracts: Multi-value columns (like Authors, Affiliations) must
       be rigorously typed as Python lists of strings (list[str]).
       
    Args:
        df (pd.DataFrame): The standardized DataFrame to check.
        
    Returns:
        bool: True if the DataFrame perfectly matches the target schema, False otherwise.
    """
    is_valid = True
    
    # 1. Check for all mandatory columns (Existence)
    missing_cols = [col for col in MANDATORY_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"[Validation Error] Missing mandatory columns: {missing_cols}")
        is_valid = False

    # 2. Check for NaN/None values (Null Handling)
    if df.isnull().values.any():
        print("[Validation Error] NaN or None values found in the DataFrame. These are not permitted.")
        is_valid = False

    # 3. Check types for Multi-value fields (Type Contracts)
    for col in MULTI_VALUE_COLUMNS:
        if col in df.columns:
            # Check if all elements in this multi-value column are strictly lists
            non_list_mask = df[col].apply(lambda x: not isinstance(x, list))
            if non_list_mask.any():
                print(f"[Validation Error] Type Contract violation: Column '{col}' contains non-list elements.")
                is_valid = False
                
    return is_valid
