import pandas as pd
import os


def save_to_excel(data, file_name):

    row = {
        "company": data.get("company", ""),
        "cin": data.get("cin", ""),
        "url": data.get("url", ""),
        "email": data.get("email", ""),
        
        "description": data.get("description", "")
        
    }

    df = pd.DataFrame([row])

    if os.path.exists(file_name):
        old = pd.read_excel(file_name)
        df = pd.concat([old, df], ignore_index=True)

    df.to_excel(file_name, index=False)