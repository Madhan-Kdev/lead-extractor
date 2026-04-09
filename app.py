import streamlit as st
import requests
from dotenv import load_dotenv
import os


# LOAD ENV

load_dotenv()
API_URL = os.getenv("API_URL")


# VALIDATION

if not API_URL:
    st.error("API_URL not set in .env file")
    st.stop()

st.set_page_config(page_title="Lead Extractor", layout="centered")

st.title(" Lead Extraction Tool")


# 1️ COMPANY + CIN

st.header("1 Company + CIN")

company = st.text_input("Company Name")
cin = st.text_input("CIN Number")

if st.button("Extract Company Data", key="company_btn"):
    if not company or not cin:
        st.warning("Enter both fields")
    else:
        with st.spinner("Fetching company data..."):
            try:
                res = requests.post(
                    f"{API_URL}/scrape-company",
                    json={"company": company, "cin": cin}
                )

                if res.status_code == 200:
                    st.success("Data fetched successfully")
                    st.json(res.json())
                else:
                    st.error(f"Error: {res.text}")

            except Exception as e:
                st.error(f"Request failed: {e}")


# 2️ WEBSITE URL

st.header("2 Website URL")

url = st.text_input("Website URL")

if st.button("Extract Website Data", key="url_btn"):
    if not url:
        st.warning("Enter URL")
    else:
        with st.spinner("Scraping website..."):
            try:
                if not url.startswith("http"):
                    url = "https://" + url

                res = requests.post(
                    f"{API_URL}/scrape-url",
                    json={"url": url}
                )

                if res.status_code == 200:
                    st.success("Data extracted successfully")
                    st.json(res.json())
                else:
                    st.error(f"Error: {res.text}")

            except Exception as e:
                st.error(f"Request failed: {e}")


# 3️ BULK UPLOAD

st.header("3 Upload Excel")

file = st.file_uploader("Upload Excel File", type=["xlsx"])

if st.button("Process File", key="upload_btn"):
    if file is None:
        st.warning("Please upload a file first")
    else:
        with st.spinner("Processing bulk data..."):
            try:
                files = {"file": file}
                res = requests.post(f"{API_URL}/upload", files=files)

                if res.status_code == 200:
                    st.success(res.json())
                else:
                    st.error(f"Error: {res.text}")

            except Exception as e:
                st.error(f"Upload failed: {e}")


# 4️ DOWNLOAD EXCEL

st.header("4 Download Output")

if st.button("Get Excel File", key="download_btn"):
    with st.spinner("Preparing download..."):
        try:
            res = requests.get(f"{API_URL}/download")

            if res.status_code == 200:
                st.success("File ready")

                st.download_button(
                    label=" Download Excel",
                    data=res.content,
                    file_name="leads.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("Download failed")

        except Exception as e:
            st.error(f"Download error: {e}")


# INFO

st.info(" Chrome Extension will automatically scrape data while browsing.")