const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const chatLog = document.getElementById("chat-log");
const langSelector = document.getElementById("language-selector");
const micButton = document.getElementById("mic-button");

// 🌍 Localized greetings
const greetings = {
  en: "Hello! I am your SmartGuard EDU here to help you with your homework. 😊",
  es: "¡Hola! Soy tu SmartGuard EDU para ayudarte con tu tarea. 😊",
  fr: "Bonjour ! Je suis votre SmartGuard EDU pour vous aider avec vos devoirs. 😊",
  de: "Hallo! Ich bin dein SmartGuard EDU, um dir bei deinen Hausaufgaben zu helfen. 😊",
  ht: "Bonjou! Mwen se SmartGuard EDU ou, la pou ede ou ak devwa ou. 😊",
  zh: "你好！我是你的SmartGuard EDU，来帮助你完成作业。😊",
};

// ✉️ Append messages to chat
function appendMessage(sender, text) {
  const messageElem = document.createElement("div");
  messageElem.className = "chat-message";

  const linkifiedText = text.replace(
    /(https?:\/\/[^\s]+)/g,
    (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
  );

  messageElem.innerHTML = `<strong>${sender}:</strong> ${linkifiedText}`;
  chatLog.appendChild(messageElem);
  chatLog.scrollTop = chatLog.scrollHeight;
}

// 🔊 Speak text aloud
function speakText(text) {
  if ('speechSynthesis' in window) {
    // Remove emojis and other non-verbal Unicode symbols
    const cleanedText = text.replace(/[^\p{L}\p{N}\p{P}\p{Z}]/gu, '');

    const utterance = new SpeechSynthesisUtterance(cleanedText);
    utterance.lang = langSelector.value || "en";
    
     // Optionally select an appropriate voice
    const voices = speechSynthesis.getVoices();
    const selectedVoice = voices.find(v => v.lang.startsWith(utterance.lang));
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }
    
    speechSynthesis.speak(utterance);
  }
}

// 👋 Show greeting message
function showGreeting(lang, speak = false) {
  const greeting = greetings[lang] || greetings["en"];
  appendMessage("🤖 SmartGuard", greeting);
  if (speak) speakText(greeting);
}

// 🎤 Mic Setup
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.interimResults = false;
recognition.maxAlternatives = 1;

langSelector.addEventListener("change", () => {
  recognition.lang = langSelector.value;
  showGreeting(langSelector.value, true); // speak on language change
});

// 🎙️ Mic button
micButton.addEventListener("click", () => {
  recognition.lang = langSelector.value;
  recognition.start();
  micButton.innerText = "🎙️ Listening...";
});

recognition.onresult = (event) => {
  const speechResult = event.results[0][0].transcript;
  userInput.value = speechResult;
  micButton.innerText = "🎤";
  chatForm.dispatchEvent(new Event("submit"));
};

recognition.onend = () => micButton.innerText = "🎤";
recognition.onerror = (event) => {
  micButton.innerText = "🎤";
  alert("Voice input failed: " + event.error);
};

// 🤖 Handle bot reply
function handleBotReply(reply) {
  appendMessage("🤖 SmartGuard", reply);
  speakText(reply);
}

// 📨 On form submit
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const message = userInput.value.trim();
  const lang = langSelector.value;

  if (!message) return;

  appendMessage("🧑‍🎓 You", message);
  userInput.value = "";

  const typingMsg = document.createElement("div");
  typingMsg.className = "bot";
  typingMsg.textContent = "🤖 SmartGuard is typing...";
  chatLog.appendChild(typingMsg);
  chatLog.scrollTop = chatLog.scrollHeight;

  try {
    const response = await fetch("/chat-with-language", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, language: lang })
    });

    const data = await response.json();
    chatLog.removeChild(typingMsg);
    handleBotReply(data.reply || "⚠️ Sorry, something went wrong.");
  } catch (err) {
    console.error("Chat error:", err);
    chatLog.removeChild(typingMsg);
    handleBotReply("⚠️ Sorry, something went wrong processing your question.");
  }
});

// 🏁 Initial greeting
window.addEventListener("DOMContentLoaded", () => {
  const currentLang = langSelector.value || "en";
  showGreeting(currentLang, false); // don't speak until user interacts
});

// ... your existing chatbot logic: speech, mic, chat handling, etc.

// 👤 Profile dropdown toggle
function toggleDropdown() {
  const dropdown = document.getElementById("dropdown");
  dropdown.classList.toggle("show");
  dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
}

document.addEventListener("click", function(event) {
  const menu = document.querySelector(".profile-menu");
  if (!menu.contains(event.target)) {
    document.getElementById("dropdown").style.display = "none";
  }
});

// 🔒 Close dropdown when clicking outside
window.addEventListener("click", function(e) {
  if (!e.target.matches('.profile-pic')) {
    const dropdown = document.getElementById("dropdown");
    if (dropdown && dropdown.classList.contains('show')) {
      dropdown.classList.remove('show');
    }
  }
});


