import requests
from bs4 import BeautifulSoup
import re

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


#SLUGIFY
def slugify(name):
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s-]', '', name)
    name = re.sub(r'\s+', '-', name)
    return name.strip('-')


#BUILD URL
def build_url(name, cin):
    name_slug = slugify(name)
    return f"https://www.indiafilings.com/search/{name_slug}-cin-{cin}"


#EMAIL EXTRACTION
def extract_email(text):
    emails = re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)

    for email in emails:
        if any(x in email.lower() for x in ["info", "support", "contact", "admin", "gmail"]):
            return email

    return emails[0] if emails else "not_found"


#DESCRIPTION EXTRACTION 
def extract_description(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        if "industrial classification" in line.lower():
            if i + 1 < len(lines):
                return lines[i + 1]

    return "not_available"


#FALLBACK DESCRIPTION
def fallback_description(name):
    name = name.lower()

    if "foundation" in name:
        return "Non-profit organization"

    if "traders" in name or "suppliers" in name:
        return "Trading / Supply business"

    if "technologies" in name:
        return "Technology services"

    if "associates" in name:
        return "Business consulting / services"
    
    if "enterprises" in name:
        return "General business services"

    return "General business"


#CLASSIFICATION
def classify_business(description):
    desc = description.lower()

    if "software" in desc or "technology" in desc:
        return "IT Services"

    elif "agriculture" in desc:
        return "Agriculture"

    elif "trading" in desc or "supply" in desc:
        return "Trading"

    elif "manufacturing" in desc:
        return "Manufacturing"

    elif "non-profit" in desc:
        return "Non-Profit"

    return "Other"


#MAIN SCRAPER
def scrape_indiafilings(name, cin):
    url = build_url(name, cin)

    print(f"[Opening] {url}")

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            return None

        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text("\n")

        email = extract_email(text)
        

        description = extract_description(text)

        
        if description == "not_available" or "registered office" in description.lower():
            description = fallback_description(name)

        

        return {
            "company": name,
            "cin": cin,
            "url": url,
            "email": email,
            
            "description": description
            
        }

    except Exception as e:
        print(f"[ERROR] {name} → {e}")
        return None