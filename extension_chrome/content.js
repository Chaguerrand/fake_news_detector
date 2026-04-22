document.getElementById("analyzeBtn").addEventListener("click", async () => {
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

    const response = await fetch("https://fake-news-detector-210894584132.europe-west1.run.app/predict_chrome", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: tab.url}),
    });

    const data = await response.json();
    const verdict = data["Verdict"] === "FAKE" ? "🚨 FAKE NEWS" : "✅ ARTICLE FIABLE";
    const score = (data["Indice de confiance"] * 100).toFixed(1) + "%";
    document.getElementById("resultTitle").style.display = "block";
    const cssClass = data["Verdict"] === "FAKE" ? "verdict-fake" : "verdict-real";
    document.getElementById("result").className = cssClass;
    document.getElementById("result").innerHTML = verdict + "<br>" + score;
  } catch(e) {
    document.getElementById("result").textContent = "Erreur : " + e.message;
  }
});
