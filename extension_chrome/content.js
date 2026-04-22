document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

  const response = await fetch("https://fake-news-detector-210894584132.europe-west1.run.app/predict_chrome", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({url: tab.url}),
  });

  const data = await response.json();
  document.getElementById("result").textContent = data["Verdict"] + " " + data["Indice de confiance"];
});
