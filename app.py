import streamlit as st
import requests
import time
from dotenv import load_dotenv
import os

# -----------------------------
# CONFIG
# -----------------------------
load_dotenv()

API_URL = "https://lead-extractor-8uc5.onrender.com"

if not API_URL:
    st.error("API_URL not set")
    st.stop()

st.set_page_config(page_title="Lead Extractor", layout="centered")

st.title("Lead Extraction Tool")

# -----------------------------
# 1️⃣ COMPANY + CIN
# -----------------------------
st.header("1 Company + CIN")

company = st.text_input("Company Name")
cin = st.text_input("CIN Number")

if st.button("Extract Company Data"):
    if not company or not cin:
        st.warning("Enter both fields")
    else:
        with st.spinner("Fetching company data..."):
            try:
                res = requests.post(
                    f"{API_URL}/scrape-company",
                    json={"company": company, "cin": cin},
                    timeout=30
                )

                if res.status_code == 200:
                    st.success("Data fetched successfully")
                    st.json(res.json())
                else:
                    st.error(f"API Error: {res.status_code}")
                    st.text(res.text)

            except Exception as e:
                st.error(f"Request failed: {e}")

# -----------------------------
# 2️⃣ WEBSITE URLs (MULTI-LINE INPUT)
# -----------------------------
st.header("2 Website URLs (Bulk Paste)")

urls_input = st.text_area(
    "Paste multiple URLs (one per line)",
    height=150
)

if st.button("Extract Website Data"):

    if not urls_input.strip():
        st.warning("Enter at least one URL")

    else:
        with st.spinner("Scraping websites..."):

            try:
                # 🔥 Wake up Render (avoid cold start issue)
                try:
                    requests.get(f"{API_URL}/health", timeout=10)
                except:
                    pass

                # 🔥 Retry logic (3 attempts)
                res = None
                for i in range(3):
                    try:
                        res = requests.post(
                            f"{API_URL}/scrape-url",
                            data=urls_input,
                            headers={"Content-Type": "text/plain"},
                            timeout=60
                        )

                        if res.status_code == 200:
                            break

                    except:
                        pass

                    time.sleep(5)

                # 🔥 Handle response safely
                if res is None:
                    st.error("Server not responding")
                
                elif res.status_code != 200:
                    st.error(f"API Error: {res.status_code}")
                    st.text(res.text)

                else:
                    try:
                        data = res.json()

                        st.success(f"Processed: {data['processed']} URLs")
                        st.json(data["data"])

                        # 🔽 DOWNLOAD FILE
                        download = requests.get(f"{API_URL}/download", timeout=30)

                        if download.status_code == 200:
                            st.download_button(
                                label="⬇ Download Excel",
                                data=download.content,
                                file_name="leads.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.warning("Download failed")

                    except:
                        st.error("Invalid response from server")
                        st.text(res.text)

            except Exception as e:
                st.error(f"Request failed: {e}")

# -----------------------------
# 3️⃣ UPLOAD EXCEL
# -----------------------------
st.header("3 Upload Excel")

file = st.file_uploader("Upload Excel File", type=["xlsx"])

if st.button("Process File"):

    if file is None:
        st.warning("Please upload a file")

    else:
        with st.spinner("Processing..."):
            try:
                files = {"file": file}

                res = requests.post(
                    f"{API_URL}/upload",
                    files=files,
                    timeout=60
                )

                if res.status_code == 200:
                    st.success("File processed successfully")
                    st.json(res.json())
                else:
                    st.error(f"API Error: {res.status_code}")
                    st.text(res.text)

            except Exception as e:
                st.error(f"Upload failed: {e}")

# -----------------------------
# 4️⃣ DOWNLOAD EXCEL
# -----------------------------
st.header("4 Download Output")

if st.button("Download Latest Excel"):
    try:
        res = requests.get(f"{API_URL}/download", timeout=30)

        if res.status_code == 200:
            st.download_button(
                label="⬇ Download Excel",
                data=res.content,
                file_name="leads.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Download failed")

    except Exception as e:
        st.error(f"Download error: {e}")

# -----------------------------
# INFO
# -----------------------------
st.info("Paste multiple URLs → click → download Excel")