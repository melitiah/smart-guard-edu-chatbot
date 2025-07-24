// 💬 Handle form submission
document.getElementById("chat-form").addEventListener("submit", async function (e) {
  e.preventDefault();

  const inputField = document.getElementById("user-input");
  const message = inputField.value.trim();
  const chatLog = document.getElementById("chat-log");
  const selectedLanguage = document.getElementById("language-selector").value;

  if (!message) return;

  // Display user message
  const userMsg = document.createElement("div");
  userMsg.className = "user";
  userMsg.innerText = "You: " + message;
  chatLog.appendChild(userMsg);
  chatLog.scrollTop = chatLog.scrollHeight;

  // Show typing placeholder
  const botMsg = document.createElement("div");
  botMsg.className = "bot";
  botMsg.innerText = "SmartGuard is typing...";
  chatLog.appendChild(botMsg);
  chatLog.scrollTop = chatLog.scrollHeight;

  const endpoint = selectedLanguage === "en-US" ? "/chat" : "/chat-with-language";

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, language: selectedLanguage })
    });

    const data = await response.json();
    botMsg.innerHTML = "<strong>SmartGuard:</strong> " + data.reply;

  // Speak only a friendly message if links are included
if ('speechSynthesis' in window) {
  const spokenText = data.reply.includes("http")
    ? "Here are some great resources."
    : data.reply.replace(/<[^>]+>/g, ""); // Strip HTML tags for regular replies

  const utterance = new SpeechSynthesisUtterance(data.reply);
utterance.lang = selectedLanguage; // "fr", "de", "hi" etc.
speechSynthesis.speak(utterance);

}

  } catch (error) {
    botMsg.innerText = "Oops! Something went wrong.";
    console.error("Chat error:", error);
  }

  inputField.value = "";
});

// 🎤 Voice input
const micButton = document.getElementById("mic-button");
const inputField = document.getElementById("user-input");
const languageSelector = document.getElementById("language-selector");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
  const recognition = new SpeechRecognition();
  recognition.lang = languageSelector.value;
  recognition.interimResults = false;
  recognition.maxAlternatives = 1;

  // Update language on dropdown change
  languageSelector.addEventListener("change", function () {
    recognition.lang = this.value;
  });

  micButton.addEventListener("click", () => {
    recognition.start();
    micButton.innerText = "🎙️ Listening...";
  });

  recognition.addEventListener("result", (event) => {
    const transcript = event.results[0][0].transcript;
    inputField.value = transcript;

    // Auto-submit the form
    document.getElementById("chat-form").dispatchEvent(new Event("submit"));
    micButton.innerText = "🎤";
  });

  recognition.addEventListener("end", () => {
    micButton.innerText = "🎤";
  });

  recognition.addEventListener("error", (event) => {
    micButton.innerText = "🎤";
    alert("Voice input failed: " + event.error);
  });
} else {
  micButton.disabled = true;
  micButton.title = "Speech recognition not supported in this browser.";
}

/// 👋 Welcome message on page load
window.addEventListener("load", () => {
  const introMessage = "Hello! I'm SmartGuard EDU, your learning assistant. How can I help you with your school work today?";
  const chatLog = document.getElementById("chat-log");

  const botMessage = document.createElement("div");
  botMessage.className = "bot";
  botMessage.innerText = introMessage;
  chatLog.appendChild(botMessage);

  // ✅ Get selected language
  const languageSelector = document.getElementById("language-selector");
  const selectedLanguage = languageSelector ? languageSelector.value : "en-US";

  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(introMessage);
    utterance.lang = selectedLanguage;  // "en-US", "es", etc.
    speechSynthesis.speak(utterance);
  }
});
