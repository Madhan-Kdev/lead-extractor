from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import pandas as pd
import os
import re
import requests
from bs4 import BeautifulSoup
import shutil

# EXISTING MODULES
from indiafilings_scraper import scrape_indiafilings
from input_handler import get_companies

app = FastAPI()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_FILE = "leads.xlsx"

# =========================
# URL SCRAPER
# =========================
def scrape_site(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        pages = [
            url,
            url.rstrip("/") + "/contact",
            url.rstrip("/") + "/contact-us",
            url.rstrip("/") + "/about",
            url.rstrip("/") + "/about-us",
            url.rstrip("/") + "/get-in-touch",
            url.rstrip("/") + "/reach-us",
        ]

        email = "not_found"
        phone = "not_found"
        person = "not_found"
        description = "not_found"
        company = ""

        for page in pages:
            try:
                res = requests.get(page, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")
                text = soup.get_text(" ", strip=True)

                # =========================
                # COMPANY NAME
                # =========================
                if not company:
                    if soup.title:
                        company = soup.title.string.strip()

                # =========================
                # EMAIL
                # =========================
                if email == "not_found":
                    emails = set()

                    emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", res.text))
                    emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))

                    # mailto links
                    for a in soup.find_all("a", href=True):
                        if "mailto:" in a["href"]:
                            emails.add(a["href"].replace("mailto:", "").strip())

                    # priority selection
                    priority = ["info", "support", "contact", "sales"]
                    for p in priority:
                        for e in emails:
                            if p in e.lower():
                                email = e
                                break
                        if email != "not_found":
                            break

                    if email == "not_found" and emails:
                        email = list(emails)[0]

                # =========================
                # PHONE
                # =========================
                if phone == "not_found":
                    phones = []

                    # tel links
                    for a in soup.find_all("a", href=True):
                        if "tel:" in a["href"]:
                            num = re.sub(r"\D", "", a["href"])
                            if len(num) >= 10:
                                phones.append(num[-10:])

                    # regex detection
                    matches = re.findall(r"(?:\+?\d{1,3}[\s-]?)?\d{10}", text)
                    for m in matches:
                        clean = re.sub(r"\D", "", m)
                        if len(clean) >= 10:
                            phones.append(clean[-10:])

                    # filter junk numbers
                    valid = []
                    for p in phones:
                        if not any(x in p for x in ["00000", "12345", "99999"]):
                            valid.append(p)

                    if valid:
                        phone = valid[0]

                # =========================
                # CEO / PERSON
                # =========================
                if person == "not_found":
                    for line in text.split("."):
                        if any(k in line.lower() for k in ["ceo", "founder", "director"]):
                            if len(line) < 100:
                                person = line.strip()
                                break

                # =========================
                # DESCRIPTION
                # =========================
                if description == "not_found":
                    meta = soup.find("meta", attrs={"name": "description"})
                    if meta and meta.get("content"):
                        description = meta.get("content")

            except:
                continue

        return {
            "company": company,
            "cin": "",
            "url": url,
            "email": email,
            "phone": phone,
            "ceo": person,
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

# =========================
# SAVE TO EXCEL
# =========================
def save_to_excel(data):
    df = pd.DataFrame([data])

    if os.path.exists(EXCEL_FILE):
        old = pd.read_excel(EXCEL_FILE)
        df = pd.concat([old, df], ignore_index=True)

    df.drop_duplicates(subset=["url"], inplace=True)
    df.to_excel(EXCEL_FILE, index=False)

# =========================
# MODE 1 → SINGLE URL
# =========================
class URLData(BaseModel):
    url: str

@app.post("/scrape-url")
def scrape_url(data: URLData):
    result = scrape_site(data.url)
    save_to_excel(result)
    return result

# =========================
# MODE 1B → MULTIPLE URL
# =========================
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

# =========================
# MODE 2 → COMPANY + CIN
# =========================
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

# =========================
# MODE 3 → BULK UPLOAD
# =========================
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

# =========================
# DOWNLOAD EXCEL
# =========================
@app.get("/download")
def download():
    return FileResponse(EXCEL_FILE, filename=EXCEL_FILE)