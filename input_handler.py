import pandas as pd


def get_companies(file_path):
    df = pd.read_excel(file_path)

    df.columns = df.columns.str.strip()

    if "Company Name" not in df.columns or "CIN" not in df.columns:
        raise ValueError("Excel must contain 'Company Name' and 'CIN'")

    df = df.dropna(subset=["Company Name", "CIN"])
    
    df = df[df["CIN"].astype(str).str.len() > 5]
    return df.to_dict(orient="records")