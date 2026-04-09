from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import pandas as pd
import os
import re
import requests
import time 
from bs4 import BeautifulSoup
import shutil

from indiafilings_scraper import scrape_indiafilings

app = FastAPI(
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

@app.get("/")
def home():
    return {"message": "Lead Extractor API is running"}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_FILE = "leads.xlsx"

# SCRAPER (FIXED)
def scrape_site(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    pages = [
        url,
        url.rstrip("/") + "/contact",
        url.rstrip("/") + "/contact-us",
        url.rstrip("/") + "/contactus",
        url.rstrip("/") + "/about",
        url.rstrip("/") + "/about-us",
        url.rstrip("/") + "/reach-us",
        url.rstrip("/") + "/support",
        url.rstrip("/") + "/get-in-touch"
    ]

    email = "not_found"
    phone = "not_found"
    description = ""
    company = ""

    for page in pages:
        try:
            res = requests.get(page, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, "html.parser")
            text = soup.get_text(" ", strip=True)

            # COMPANY
            if not company and soup.title:
                company = soup.title.string.strip()

            # EMAIL
            if email == "not_found":
                emails = set()

                emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", res.text))

                for a in soup.find_all("a", href=True):
                    if "mailto:" in a["href"]:
                        emails.add(a["href"].replace("mailto:", "").strip())

                emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))

                priority = ["info", "support", "contact", "sales"]
                selected = None

                for p in priority:
                    for e in emails:
                        if p in e.lower():
                            selected = e
                            break
                    if selected:
                        break

                if selected:
                    email = selected
                elif emails:
                    email = list(emails)[-1]  # footer-based fix

            # PHONE
            if phone == "not_found":
                phones = []

                for a in soup.find_all("a", href=True):
                    if "tel:" in a["href"]:
                        num = re.sub(r"\D", "", a["href"])
                        if len(num) >= 10:
                            phones.append(num[-10:])

                matches = re.findall(r"(?:\+?\d{1,3}[\s-]?)?\(?[6-9]\d{9}\)?", text)
                for m in matches:
                    clean = re.sub(r"\D", "", m)
                    if len(clean) >= 10:
                        phones.append(clean[-10:])

                matches2 = re.findall(r"[6-9]\d{9}", res.text)
                phones.extend(matches2)

                phones = list(set(phones))

                if phones:
                    phone = phones[0]

            # DESCRIPTION
            if not description:
                meta = soup.find("meta", attrs={"name": "description"})
                if meta and meta.get("content"):
                    description = meta.get("content")

        except:
            continue

    # FINAL FALLBACK
    try:
        res = requests.get(url, headers=headers, timeout=5)
        html = res.text

        if email == "not_found":
            emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html)
            if emails:
                email = emails[-1]

        if phone == "not_found":
            phones = re.findall(r"[6-9]\d{9}", html)
            if phones:
                phone = phones[0]

    except:
        pass

    return {
        "company": company,
        "cin": "",
        "url": url,
        "email": email,
        "phone": phone,
        "ceo": "",
        "description": description
    }

# SAVE
def save_to_excel(data):
    df = pd.DataFrame([data])

    if os.path.exists(EXCEL_FILE):
        old = pd.read_excel(EXCEL_FILE)
        df = pd.concat([old, df], ignore_index=True)

    df.drop_duplicates(subset=["url"], inplace=True)
    df.to_excel(EXCEL_FILE, index=False)

# APIs
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
    for url in data.urls[:25]:
        result = scrape_site(url)
        save_to_excel(result)
        results.append(result)
    return results


class CompanyData(BaseModel):
    company: str
    cin: str

@app.post("/scrape-company")
def scrape_company(data: CompanyData):
    result = scrape_indiafilings(data.company, data.cin)
    if result:
        save_to_excel(result)
    return result


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.upper()

    #companies = get_companies(file_path)
    results = []

    #CASE 1 URL BASED FILE 

    if "URL" in df.columns:
        urls = df["URL"].dropna().tolist()
        print(f"Detected URL file with {len(urls)} records")
        batch_size = 25
        for i in range(0,len(urls),batch_size):
            batch = urls[i:i+batch_size]

            print(f"Processing batch {i//25 + 1}")
            
            for url in batch:
                try:
                    url = str(url).strip()
                    
                    if not str(url).startswith("http"):
                        url = "https://"+ url

                    result = scrape_site(url)

                    if result:
                        save_to_excel(result)
                        results.append(result)
                except Exception as e:
                    print("URL Error:", e)
                    continue
            
            if i + batch_size < len(urls):
                print("Sleeping for 20 seconds")

                time.sleep(20)

#CASE-2 COMPANY + CIN 
    elif "COMPANY NAME" in df.columns and "CIN" in df.columns:

        companies = df.to_dict(orient = "records")
        print(f"Detected CIN file with {len(companies)} records")

        batch_size = 25

        for i in range(0, len(companies),batch_size):
            batch = companies[i:i+batch_size]

            print(f"Processing batch {i//25 + 1}")

            for c in batch:
                try:
                    result = scrape_indiafilings(
                        c["Company Name"], c["CIN"]
                    )

                    if result:
                        save_to_excel(result)
                        results.append(result)

                except Exception as e:
                    print("CIN Error:",e)
                    continue

            if i + batch_size < len(companies):
                print("Sleeping for 20 seconds")
                time.sleep(20)

    else:
        return {"error": "Invalid file format"}
    
    return {
        "processed": len(results),
        "message": "Bulk processing completed"
    }


@app.get("/download")
def download():
    return FileResponse(EXCEL_FILE, filename=EXCEL_FILE)