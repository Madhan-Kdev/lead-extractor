chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {

    if (
        changeInfo.status === "complete" &&
        tab.url &&
        tab.url.startsWith("http")
    ) {
        console.log("Scraping:", tab.url);

        fetch("http://127.0.0.1:8000/scrape-url", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                url: tab.url
            })
        })
        .then(res => res.json())
        .then(data => console.log("Response:", data))
        .catch(err => console.error("Error:", err));
    }
});