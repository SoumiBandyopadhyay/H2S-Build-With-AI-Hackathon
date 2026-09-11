const API_BASE = "https://h2s-build-with-ai-hackathon.onrender.com";

const STATES = [
  "Andhra Pradesh", "Assam", "Bihar", "Chhattisgarh", "Delhi", "Gujarat", "Haryana",
  "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Odisha",
  "Punjab", "Rajasthan", "Tamil Nadu", "Telangana", "Uttar Pradesh", "West Bengal",
];

const stateSelect = document.getElementById("state");
STATES.forEach((s) => {
  const opt = document.createElement("option");
  opt.value = s;
  opt.textContent = s;
  stateSelect.appendChild(opt);
});

// --- Voice input using the browser's built-in Web Speech API (no extra API key needed) ---
const micBtn = document.getElementById("micBtn");
const micStatus = document.getElementById("micStatus");
const textArea = document.getElementById("complaintText");
const langSelect = document.getElementById("language");

const LANG_CODES = { en: "en-IN", hi: "hi-IN", bn: "bn-IN", ta: "ta-IN", te: "te-IN", mr: "mr-IN" };

let recognition;
const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
if (SpeechRecognitionAPI) {
  recognition = new SpeechRecognitionAPI();
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    textArea.value += (textArea.value ? " " : "") + transcript;
    micStatus.textContent = "Captured ✅";
  };
  recognition.onerror = (e) => {
    micStatus.textContent = "Mic error: " + e.error;
  };
  recognition.onend = () => {
    micBtn.classList.remove("listening");
  };
} else {
  micBtn.disabled = true;
  micStatus.textContent = "Voice input not supported in this browser (try Chrome).";
}

micBtn.addEventListener("click", () => {
  if (!recognition) return;
  recognition.lang = LANG_CODES[langSelect.value] || "en-IN";
  micBtn.classList.add("listening");
  micStatus.textContent = "Listening...";
  recognition.start();
});

// --- Form submission ---
document.getElementById("complaintForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const payload = {
    raw_text: textArea.value,
    language: langSelect.value,
    state: stateSelect.value,
    district: document.getElementById("district").value,
  };

  try {
    const res = await fetch(`${API_BASE}/api/complaints`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error("Request failed");
    const data = await res.json();

    document.getElementById("resCategory").textContent = data.category;
    document.getElementById("resUrgency").textContent = data.urgency;
    document.getElementById("resSummary").textContent = data.summary;
    document.getElementById("resultCard").classList.remove("hidden");

    document.getElementById("complaintForm").reset();
  } catch (err) {
    alert("Could not submit. Is the backend running at " + API_BASE + " ?");
    console.error(err);
  }
});
