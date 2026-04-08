from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from dotenv import load_dotenv
import os
import pandas as pd
import re
import shutil
import requests
from bs4 import BeautifulSoup

# LOAD ENV
load_dotenv()

EXCEL_FILE = os.getenv("EXCEL_FILE", "leads.xlsx")

# EXISTING MODULES
from indiafilings_scraper import scrape_indiafilings
from input_handler import get_companies

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL SCRAPER
def scrape_site(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()

        company = ""
        if soup.title:
            company = soup.title.string.strip()

        email = "not_found"
        phone = "not_found"

        # --------------------
        # EMAIL
        # --------------------
        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", res.text)
        if emails:
            email = emails[0]

        # --------------------
        # PHONE (ADVANCED)
        # --------------------
        phones = set()

        # Indian format
        phones.update(re.findall(r"\+91[\s\-]?\d{10}", text))

        # Basic 10 digit
        phones.update(re.findall(r"\b[6-9]\d{9}\b", text))

# Flexible formats
        phones.update(re.findall(r"\+?\d{1,3}[\s\-]?\d{2,5}[\s\-]?\d{2,5}[\s\-]?\d{2,5}", text))

# Clean invalid matches
        phones = [p for p in phones if len(re.sub(r"\D", "", p)) >= 10]

        if phones:
            phone = list(phones)[0]

        # --------------------
        # TEL LINK EXTRACTION
        # --------------------
        for a in soup.find_all("a", href=True):
            if "tel:" in a["href"]:
                phone = a["href"].replace("tel:", "")
                break

        # --------------------
        # CONTACT PAGE FALLBACK
        # --------------------
        if email == "not_found" or phone == "not_found":
            for path in [
                "/contact", "/contact-us", "/about", "/about-us",
                "/reach-us", "/get-in-touch", "/support"
            ]:
                try:
                    res2 = requests.get(url.rstrip("/") + path, headers=headers, timeout=10)
                    text2 = res2.text

            # EMAIL
                    if email == "not_found":
                        emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text2)
                        if emails:
                            email = emails[0]

            # PHONE
                    if phone == "not_found":
                        phones = re.findall(r"(?:\+?\d{1,3}[\s\-]?)?[6-9]\d{9}", text2)
                        if phones:
                            phone = phones[0]

                except:
                    pass

        # --------------------
        # DESCRIPTION
        # --------------------
        description = ""
        desc_tag = soup.find("meta", attrs={"name": "description"})
        if desc_tag:
            description = desc_tag.get("content", "")

        return {
            "company": company,
            "cin":"",
            "url": url,
            "email": email,
            "phone": phone,
            "ceo": "not_found",
            "description": description
        }

    except Exception as e:
        return {
            "company": "",
            "cin": "",
            "url": url,
            "email": "",
            "phone": "",
            "ceo": "",
            "description": "",
            "error": str(e)
        }
    
# SAVE TO EXCEL
def save_to_excel(data):
    df = pd.DataFrame([data])

    if os.path.exists(EXCEL_FILE):
        try:
            old = pd.read_excel(EXCEL_FILE)
            df = pd.concat([old, df], ignore_index=True)
        except:
            pass

    if "url" in df.columns:
        df.drop_duplicates(subset=["url"], inplace=True)

    df.to_excel(EXCEL_FILE, index=False)
    print("Saved:", data.get("url"))

# API MODE 1
class URLData(BaseModel):
    url: str

@app.post("/scrape-url")
def scrape_url(data: URLData):
    result = scrape_site(data.url)
    save_to_excel(result)
    return result

class URLList(BaseModel):
    urls: list[str]


@app.post("/scrape-multiple")
def scrape_multiple(data: URLList):

    results = []

    for url in data.urls:
        result = scrape_site(url)
        save_to_excel(result)
        results.append(result)

    return results

# API MODE 2
class CompanyData(BaseModel):
    company: str
    cin: str

@app.post("/scrape-company")
def scrape_company(data: CompanyData):
    result = scrape_indiafilings(data.company, data.cin)

    if not result:
        return {"error": "Not found"}

    save_to_excel(result)
    return result

# API MODE 3
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    companies = get_companies(file_path)

    for c in companies:
        result = scrape_indiafilings(c["Company Name"], c["CIN"])
        if result:
            save_to_excel(result)

    return {"message": "Bulk processing done"}

# DOWNLOAD
@app.get("/download")
def download():
    if os.path.exists(EXCEL_FILE):
        return FileResponse(EXCEL_FILE, filename=EXCEL_FILE)
    return {"error": "File not found"}

# RENDER ENTRY
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)