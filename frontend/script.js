const API_BASE = "http://127.0.0.1:8000";

const ingestBtn = document.getElementById("ingestBtn");
const askBtn = document.getElementById("askBtn");

ingestBtn.onclick = async () => {
  const url = document.getElementById("docUrl").value;
  const status = document.getElementById("ingestStatus");

  if (!url) {
    status.textContent = "Please enter a document URL.";
    status.className = "status error";
    return;
  }

  ingestBtn.classList.add("loading");
  ingestBtn.textContent = "Ingesting…";
  status.textContent = "";

  try {
    const res = await fetch(`${API_BASE}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url })
    });

    const data = await res.json();

    status.textContent = `✅ Document ingested successfully. Chunks: ${data.chunks}`;
    status.className = "status success";
  } catch {
    status.textContent = "❌ Backend not reachable or ingestion failed.";
    status.className = "status error";
  } finally {
    ingestBtn.classList.remove("loading");
    ingestBtn.textContent = "Ingest";
  }
};

askBtn.onclick = async () => {
  const question = document.getElementById("question").value;
  const answer = document.getElementById("answer");

  if (!question) return;

  askBtn.classList.add("loading");
  askBtn.textContent = "Thinking…";
  answer.textContent = "Generating answer…";

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: "demo",
        question
      })
    });

    const data = await res.json();
    answer.textContent = data.answer;
  } catch {
    answer.textContent = "❌ Failed to get response from backend.";
  } finally {
    askBtn.classList.remove("loading");
    askBtn.textContent = "Ask";
  }
};
