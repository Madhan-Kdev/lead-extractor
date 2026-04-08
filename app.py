import streamlit as st
import requests
from dotenv import load_dotenv
import os

load_dotenv()

API_URL = os.getenv("API_URL")

st.set_page_config(page_title="Lead Extractor", layout="centered")

st.title("🚀 Lead Extraction Tool")

# COMPANY + CIN
st.header("1️⃣ Company + CIN")

company = st.text_input("Company Name")
cin = st.text_input("CIN Number")

if st.button("Extract Company Data"):
    if not company or not cin:
        st.warning("Enter both fields")
    else:
        res = requests.post(f"{API_URL}/scrape-company", json={
            "company": company,
            "cin": cin
        })
        st.json(res.json())

# URL
st.header("2️⃣ Website URL")

url = st.text_input("Website URL")

if st.button("Extract Website Data"):
    if not url:
        st.warning("Enter URL")
    else:
        if not url.startswith("http"):
            url = "https://" + url

        res = requests.post(f"{API_URL}/scrape-url", json={"url": url})
        st.json(res.json())

# UPLOAD
st.header("3️⃣ Upload Excel")

file = st.file_uploader("Upload file", type=["xlsx"])

if file and st.button("Process File"):
    files = {"file": file}
    res = requests.post(f"{API_URL}/upload", files=files)
    st.success(res.json())

# DOWNLOAD
st.header("📥 Download")

if st.button("Download Excel"):
    res = requests.get(f"{API_URL}/download")

    with open("output.xlsx", "wb") as f:
        f.write(res.content)

    st.success("Downloaded output.xlsx")

# INFO
st.info("Chrome Extension works automatically while browsing.")