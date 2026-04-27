const API_URL = "https://fake-news-detector-210894584132.europe-west1.run.app";

function sendFeedback(rowIndex, feedback) {
  fetch(`${API_URL}/feedback`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({row_index: rowIndex, feedback: feedback})
  });
  document.getElementById("feedback").style.display = "none";
  document.getElementById("feedbackDone").style.display = "block";
}

document.getElementById("analyzeBtn").addEventListener("click", async () => {
  document.getElementById("loadingMsg").style.display = "block";
  document.getElementById("feedback").style.display = "none";
  document.getElementById("feedbackDone").style.display = "none";
  document.getElementById("elapsed").style.display = "none";
  document.getElementById("result").className = "";
  document.getElementById("result").innerHTML = "";

  const start = Date.now();
  try {
    const [tab] = await chrome.tabs.query({active: true, currentWindow: true});

    const response = await fetch(`${API_URL}/predict_chrome`, {
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

    const labelHint = data["Label"] === "REAL" ? "Relativement fiable" : "Relativement fake";
    const hintText = data["Verdict"] === "NON CONCLUANT" ? `<br><small>${labelHint}</small>` : "";

    document.getElementById("loadingMsg").style.display = "none";
    document.getElementById("resultTitle").style.display = "block";
    document.getElementById("result").className = cssClass;
    document.getElementById("result").innerHTML = verdictText + "<br>" + score + hintText;
    document.getElementById("elapsed").textContent = "⏱️ Analyse effectuée en " + elapsed + "s";
    document.getElementById("elapsed").style.display = "block";

    // feedback
    const rowIndex = data["row_index"];
    if (rowIndex) {
      document.getElementById("feedback").style.display = "block";
      document.getElementById("feedbackGood").onclick = () => sendFeedback(rowIndex, "good");
      document.getElementById("feedbackBad").onclick = () => sendFeedback(rowIndex, "bad");
    }

  } catch(e) {
    document.getElementById("loadingMsg").style.display = "none";
    document.getElementById("result").textContent = "Erreur : " + e.message;
  }
});
