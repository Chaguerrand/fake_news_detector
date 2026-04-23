document.getElementById("analyzeBtn").addEventListener("click", async () => {
  document.getElementById("loadingMsg").style.display = "block";
  const start = Date.now();
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

    const response = await fetch("https://fake-news-detector-210894584132.europe-west1.run.app/predict_chrome", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({url: tab.url}),
    });

    if (!response.ok) {
      document.getElementById("loadingMsg").style.display = "none";
      document.getElementById("result").className = "verdict-error";
      document.getElementById("result").innerHTML = "❌ Récupération du contenu bloquée.<br>Analyse impossible.";
      return;
}

    const data = await response.json();
    const score = (data["Indice de confiance"] * 100).toFixed(1) + "%";
    const elapsed = ((Date.now() - start) / 1000).toFixed(2);

    let verdictText, cssClass;
    if (data["Verdict"] === "FAKE") { verdictText = "🚨 FAKE NEWS"; cssClass = "verdict-fake"; }
    else if (data["Verdict"] === "REAL") { verdictText = "✅ ARTICLE FIABLE"; cssClass = "verdict-real"; }
    else { verdictText = "⚠️ NON CONCLUANT"; cssClass = "verdict-inconclusive"; }

    document.getElementById("loadingMsg").style.display = "none";
    document.getElementById("resultTitle").style.display = "block";
    document.getElementById("result").className = cssClass;
    document.getElementById("result").innerHTML = verdictText + "<br>" + score + "<br><small>⏱️ " + elapsed + "s</small>";
  } catch(e) {
    document.getElementById("loadingMsg").style.display = "none";
    document.getElementById("result").textContent = "Erreur : " + e.message;
  }
});
