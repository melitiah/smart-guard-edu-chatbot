document.getElementById("chat-form").addEventListener("submit", function(e) {
  e.preventDefault();
  const input = document.getElementById("user-input");
  const message = input.value.trim();
  const chatLog = document.getElementById("chat-log");

  if (!message) return;

  // Show user message
  const userMessage = document.createElement("div");
  userMessage.className = "user";
  userMessage.textContent = "You: " + message;
  chatLog.appendChild(userMessage);
  chatLog.scrollTop = chatLog.scrollHeight;

  // Show placeholder bot reply
  const userMessage = document.getElementById("user-input").value;
  const selectedLanguage = document.getElementById("language").value;

  const botReply = document.createElement("div");
  botReply.className = "bot";
  botReply.textContent = "LearnBuddy is typing...";
  chatLog.appendChild(botReply);

  // Send to backend
  fetch("/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    message: userMessage,
    language: selectedLanguage
  })
})
.then(response => response.json())
.then(data => {
  // display bot response in chat
});

    // Optional: speak reply
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(data.reply);
      speechSynthesis.speak(utterance);
    }
  })
  .catch(err => {
    botReply.textContent = "Oops! Something went wrong.";
    console.error("Chat error:", err);
  });

  input.value = "";
});
