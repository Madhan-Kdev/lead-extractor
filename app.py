import streamlit as st
import requests
from dotenv import load_dotenv
import os

# LOAD ENV
load_dotenv()

API_URL = os.getenv("API_URL")

# -----------------------
# VALIDATION
# -----------------------
if not API_URL:
    st.error("API_URL not set in .env file")
    st.stop()

st.set_page_config(page_title="Lead Extractor", layout="centered")

st.title(" Lead Extraction Tool")

# =========================
# COMPANY + CIN
# =========================
st.header("1️ Company + CIN")

company = st.text_input("Company Name")
cin = st.text_input("CIN Number")

if st.button("Extract Company Data"):
    if not company or not cin:
        st.warning("Enter both fields")
    else:
        try:
            res = requests.post(f"{API_URL}/scrape-company", json={
                "company": company,
                "cin": cin
            })

            if res.status_code == 200:
                st.json(res.json())
            else:
                st.error(f"Error: {res.text}")

        except Exception as e:
            st.error(f"Request failed: {e}")

# =========================
# URL
# =========================
st.header("2️ Website URL")

url = st.text_input("Website URL")

if st.button("Extract Website Data"):
    if not url:
        st.warning("Enter URL")
    else:
        try:
            if not url.startswith("http"):
                url = "https://" + url

            res = requests.post(f"{API_URL}/scrape-url", json={"url": url})

            if res.status_code == 200:
                st.json(res.json())
            else:
                st.error(f"Error: {res.text}")

        except Exception as e:
            st.error(f"Request failed: {e}")

# =========================
# UPLOAD
# =========================
st.header("3️ Upload Excel")

file = st.file_uploader("Upload file", type=["xlsx"])

if file and st.button("Process File"):
    try:
        files = {"file": file}
        res = requests.post(f"{API_URL}/upload", files=files)

        if res.status_code == 200:
            st.success(res.json())
        else:
            st.error(f"Error: {res.text}")

    except Exception as e:
        st.error(f"Upload failed: {e}")

# =========================
# DOWNLOAD
# =========================
st.header(" Download")

if st.button("Download Excel"):
    try:
        res = requests.get(f"{API_URL}/download")

        if res.status_code == 200:
            with open("output.xlsx", "wb") as f:
                f.write(res.content)

            st.success("Downloaded output.xlsx")
        else:
            st.error("Download failed")

    except Exception as e:
        st.error(f"Download error: {e}")

# =========================
# INFO
# =========================
st.info("Chrome Extension works automatically while browsing.")