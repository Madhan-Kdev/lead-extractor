from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import pandas as pd
import os
import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import shutil
from indiafilings_scraper import scrape_indiafilings

app = FastAPI()

# -------------------------------
# CORS
# -------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

EXCEL_FILE = "leads.xlsx"

@app.get("/")
def home():
    return {"message": "Lead Extractor API is running"}

# -------------------------------
# 🚀 FAST ASYNC SCRAPER
# -------------------------------
async def fetch_site(session, url):
    try:
        if not url.startswith("http"):
            url = "https://" + url

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

        full_text = ""

        for page in pages:
            for attempt in range(2):  # 🔁 retry once
                try:
                    async with session.get(page, headers=headers, timeout=5) as res:
                        html = await res.text()
                        full_text += html

                        soup = BeautifulSoup(html, "html.parser")
                        text = soup.get_text(" ", strip=True)

                        # -------------------------------
                        # COMPANY
                        # -------------------------------
                        if not company and soup.title:
                            company = soup.title.string.strip()

                        # -------------------------------
                        # EMAIL (IMPROVED)
                        # -------------------------------
                        if email == "not_found":
                            emails = set()

                            # from HTML
                            emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", html))

                            # mailto links
                            for a in soup.find_all("a", href=True):
                                if "mailto:" in a["href"]:
                                    emails.add(a["href"].replace("mailto:", "").strip())

                            # from visible text
                            emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))

                            # filter junk emails
                            ignore = ["example", "test", "sample", "yourdomain"]
                            emails = [
                                e for e in emails
                                if not any(k in e.lower() for k in ignore)
                            ]

                            # prioritize business emails
                            priority_keywords = ["contact", "sales", "support", "admin"]
                            priority_emails = [
                                e for e in emails
                                if any(k in e.lower() for k in priority_keywords)
                            ]

                            if priority_emails:
                                email = priority_emails[0]
                            elif emails:
                                email = emails[0]

                        # -------------------------------
                        # PHONE (IMPROVED)
                        # -------------------------------
                        if phone == "not_found":
                            phone_matches = re.findall(r"(\+?\d[\d\s\-]{8,}\d)", html)

                            cleaned_numbers = []
                            for p in phone_matches:
                                num = re.sub(r"\D", "", p)
                                if 9 <= len(num) <= 13:
                                    cleaned_numbers.append(num)

                            if cleaned_numbers:
                                phone = cleaned_numbers[0]

                        # -------------------------------
                        # DESCRIPTION
                        # -------------------------------
                        if not description:
                            meta = soup.find("meta", attrs={"name": "description"})
                            if meta and meta.get("content"):
                                description = meta.get("content")

                        break  # success → exit retry loop

                except:
                    if attempt == 1:
                        continue

        return {
            "company": company,
            "cin": "",
            "url": url,
            "email": email,
            "phone": phone,
            "ceo": "",
            "description": description
        }

    except Exception as e:
        return {"url": url, "error": str(e)}


# -------------------------------
# 🚀 MULTI URL FAST API
# -------------------------------
@app.post("/scrape-url")
async def scrape_url(request: Request):

    body = await request.body()
    raw_input = body.decode("utf-8")

    urls = [
        u.strip()
        for u in raw_input.replace("\r", "\n").split("\n")
        if u.strip()
    ]

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_site(session, url) for url in urls]

        # 🔥 PARALLEL EXECUTION
        results = await asyncio.gather(*tasks)

    # ✅ SAVE ONCE (FAST)
    df = pd.DataFrame(results)
    df.drop_duplicates(subset=["url"], inplace=True)
    df.to_excel(EXCEL_FILE, index=False)

    return {
        "processed": len(results),
        "data": results,
        "file": EXCEL_FILE
    }


# -------------------------------
# COMPANY + CIN
# -------------------------------
class CompanyData(BaseModel):
    company: str
    cin: str

@app.post("/scrape-company")
def scrape_company(data: CompanyData):
    result = scrape_indiafilings(data.company, data.cin)
    if result:
        df = pd.DataFrame([result])
        df.to_excel(EXCEL_FILE, index=False)
    return result


# -------------------------------
# 📂 UPLOAD FILE (FAST)
# -------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df = pd.read_excel(file_path)
    df.columns = df.columns.str.strip().str.upper()

    results = []

    if "URL" in df.columns:
        urls = df["URL"].dropna().tolist()

        async with aiohttp.ClientSession() as session:
            tasks = [fetch_site(session, str(url)) for url in urls]
            results = await asyncio.gather(*tasks)

    elif "COMPANY NAME" in df.columns and "CIN" in df.columns:
        companies = df.to_dict(orient="records")

        for c in companies:
            try:
                result = scrape_indiafilings(c["COMPANY NAME"], c["CIN"])
                if result:
                    results.append(result)
            except:
                continue
    else:
        return {"error": "Invalid file format"}

    # SAVE ONCE
    df = pd.DataFrame(results)
    df.to_excel(EXCEL_FILE, index=False)

    return {
        "processed": len(results),
        "file": EXCEL_FILE
    }


# -------------------------------
# DOWNLOAD
# -------------------------------
@app.get("/download")
def download():
    return FileResponse(EXCEL_FILE, filename=EXCEL_FILE)