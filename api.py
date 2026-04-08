from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import shutil
import threading
import os
import time

from input_handler import get_companies
from indiafilings_scraper import scrape_indiafilings
from excel_handler import save_to_excel

app = FastAPI()



status = {
    "total": 0,
    "processed": 0,
    "running": False
}

from threading import Lock 
status_lock = Lock()

OUTPUT_FILE = f"leads_{int(time.time())}.xlsx"


#BACKGROUND PROCESS
def process_file(file_path):
    global status

    companies = get_companies(file_path)
    with status_lock:
        
        status["total"] = len(companies)
        status["processed"] = 0
        status["running"] = True

    for company in companies:
        name = company["Company Name"].strip()
        cin = company["CIN"].strip()

        data = scrape_indiafilings(name,cin)

        if not data:
            data = {
                "company": name,
                "cin": cin,
                "url": "N/A",
                "email": "not_found",
                "description":"",
                "category":""
                  }
        
        save_to_excel(data,OUTPUT_FILE)

        with status_lock:
            status["processed"] +=1
        
        time.sleep(5)
    
    status["running"] = False

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = f"temp_{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    thread = threading.Thread(target=process_file, args=(file_path,))
    thread.start()

    return {"message": "Processing started"}


@app.get("/status")
def get_status():
    return status


@app.get("/download")
def download_file():
    if os.path.exists(OUTPUT_FILE):
        return FileResponse(OUTPUT_FILE, filename=OUTPUT_FILE)

    return {"error": "File not ready"}

    