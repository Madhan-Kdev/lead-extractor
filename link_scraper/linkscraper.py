import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# DRIVER
def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver


# INPUT
def load_input():
    df = pd.read_excel("input_links.xlsx")
    df.columns = df.columns.str.strip().str.upper()
    return df


# SCRAPER
def scrape_site(driver, url):

    pages = [
        url,
        url.rstrip("/") + "/contact",
        url.rstrip("/") + "/contact-us",
        url.rstrip("/") + "/about",
        url.rstrip("/") + "/about-us"
    ]

    email = "not_found"
    phone = "not_found"
    person = "not_found"
    description = "not_found"

    for page in pages:
        try:
            print("   ➜ Opening:", page)

            driver.get(page)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            page_source = driver.page_source
            text = driver.find_element(By.TAG_NAME, "body").text

            #EMAIL
            if email == "not_found":
                emails = set()

                emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", page_source))
                emails.update(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text))

                elements = driver.find_elements(By.XPATH, "//a[contains(@href,'mailto')]")
                for el in elements:
                    href = el.get_attribute("href")
                    if href:
                        emails.add(href.replace("mailto:", "").strip())

                # priority selection
                priority = ["info","support","contact","sales"]
                found = False
                for p in priority:
                    for e in emails:
                        if p in e.lower():
                            email = e
                            found = True
                            break
                    if found:
                        break

                if email == "not_found" and emails:
                    email = list(emails)[0]

            #PHONE
            if phone == "not_found":

                phones = []

                #tel links
                elements = driver.find_elements(By.XPATH, "//a[contains(@href,'tel')]")
                for el in elements:
                    href = el.get_attribute("href")
                    if href:
                        num = re.sub(r"\D", "", href)
                        if len(num) >= 10:
                            phones.append(num[-10:])

                # 2. context-based detection
                for line in text.split("\n"):
                    if any(k in line.lower() for k in ["contact","call","phone","support"]):

                        matches = re.findall(r"(?:\+91[\-\s]?)?[6-9]\d{9}", line)

                        for m in matches:
                            clean = re.sub(r"\D", "", m)
                            if len(clean) == 10:
                                phones.append(clean)

                # clean filter
                valid = []
                for p in phones:
                    if not any(x in p for x in ["00000","12345","99999"]):
                        valid.append(p)

                if valid:
                    phone = valid[0]

            # PERSON
            if person == "not_found":
                for line in text.split("\n"):
                    if any(k in line.lower() for k in ["ceo","founder","director"]):
                        if len(line) < 60:
                            person = line.strip()
                            break

            #DESCRIPTION
            if description == "not_found":
                try:
                    meta = driver.find_element(By.XPATH, "//meta[@name='description']")
                    description = meta.get_attribute("content")
                except:
                    pass

        except Exception as e:
            print("Error:", e)
            continue

    return {
        "url": url,
        "email": email,
        "phone": phone,
        "person": person,
        "description": description
    }


# MAIN
def main():

    driver = get_driver()
    df = load_input()

    if "URL" not in df.columns:
        print("Column must be 'URL'")
        return

    results = []

    for url in df["URL"]:

        if pd.isna(url):
            continue

        url = str(url).strip()

        if not url.startswith("http"):
            url = "https://" + url

        print("\nProcessing:", url)

        data = scrape_site(driver, url)
        print("DATA:", data)

        results.append(data)

    driver.quit()

    pd.DataFrame(results).to_excel("leads_links.xlsx", index=False)

    print("\nDONE → leads_links.xlsx created")


if __name__ == "__main__":
    main()