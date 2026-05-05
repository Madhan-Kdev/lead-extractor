#  Lead Extraction System

##  Overview

The Lead Extraction System is a complete solution designed to automatically collect business contact information from websites and company records.

This system supports:

* Website scraping (email, phone, description)
* Company lookup using CIN number
* Bulk Excel processing
* Chrome Extension automation
* Web-based UI (Streamlit)

---

##  Key Features

### 1. Website Scraping

Extracts the following from company websites:

* Email addresses
* Phone numbers
* Company description

---

###  2. Company + CIN Lookup

Fetches company details using:

* Company Name
* CIN (Corporate Identification Number)

---

###  3. Bulk Processing (Excel Upload)

Upload Excel files containing:

* Website URLs
  OR
* Company Name + CIN

The system will:

* Automatically detect input type
* Process data in batches (25 records)
* Introduce delay to prevent overload

---

### 4. Chrome Extension Automation

* Automatically detects active website
* Sends URL to backend API
* Extracts data in real-time

---

### 5. Excel Output

All extracted data is stored in:

leads.xlsx

---
## System Architecture

Chrome Extension / Streamlit App
|
FastAPI Backend
|
Web Scraper Engine
|
Excel Output


##  Tech Stack

* **Backend**: FastAPI
* **Frontend**: Streamlit
* **Web Scraping**: BeautifulSoup, Requests
* **Automation**: Chrome Extension (Manifest v3)
* **Data Processing**: Pandas
* **Deployment**: Render

---

##  Live URLs

* **API Backend**
  https://lead-extractor-8uc5.onrender.com

* **Web Application**
  https://lead-extractor-app.onrender.com

---

##  How to Use

### Option 1: Web Application

1. Open the deployed Streamlit app
2. Choose one of the options:

   * Enter Website URL
   * Enter Company Name + CIN
   * Upload Excel file
3. Click Extract
4. Download results

---

###  Option 2: Chrome Extension

1. Open Chrome → chrome://extensions/
2. Enable Developer Mode
3. Click "Load unpacked"
4. Select the `Chrome_extension` folder
5. Open any website
6. Data will be extracted automatically

---

##  Option 3: API Usage

#### Scrape Single URL

POST /scrape-url

{
"url": "https://example.com"
}


#### Scrape Multiple URLs

POST /scrape-multiple


#### Company + CIN Lookup

POST /scrape-company

#### Bulk Upload

POST /upload

#### Download Output

GET /download

##  Input Format

###  URL File Format

| URL                 |
| ------------------- |
| https://example.com |

---

### Company + CIN Format

| Company Name | CIN |
| ------------ | --- |

## Important Notes

* Some websites may not expose email or phone numbers
* Free hosting (Render) may have initial delay (cold start)
* Batch processing is used to prevent timeout
* System prioritizes small and medium business websites


## Project Structure

lead-extractor/
│
├── Chrome_extension/
│   ├── manifest.json
│   ├── background.js
│   ├── popup.html
│   ├── popup.js
│   └── styles.css
│
├── app.py
├── main.py
├── excel_handler.py
├── indiafilings_scraper.py
├── input_handler.py
├── requirements.txt
├── README.md

## Use Cases

* Lead Generation
* Sales Prospecting
* Business Intelligence
* Market Research
* Startup Discovery

## Project Status

 Fully Deployed
 Production Ready
 Supports Bulk Processing
 Integrated Extension + App
 Real-time Data Extraction
 
## REALISTIC ACCURACY

### FOR  SMALL START UP /MEDIUM LEVEL COMPANIES
| Data Type   | Accuracy |
| ----------- | -------- |
| Email       | ~70–90%  |
| Phone       | ~75–95%  |
| Description | ~90%     |

## For LARGE / MODERN WEBSITES
Problem	                      Reason
No email	                    Hidden / JS rendered
No phone	                    Dynamic loading
Wrong extraction	            Complex HTML

Accuracy drops to:
~30% – 60%
The system achieves high accuracy (70–90%) for small and medium business websites
where contact data is publicly available in HTML. For larger or dynamic websites,
accuracy may vary due to JavaScript rendering and data protection mechanisms.

## Developed By

Madhan K