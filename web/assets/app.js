const chatWindow = document.getElementById("chat-window");
const form = document.getElementById("chat-form");
const input = document.getElementById("message");
let sessionId = null;

function addMessage(text, from) {
  const row = document.createElement("div");
  row.className = "message-row " + (from === "user" ? "message-row--user" : "message-row--assistant");

  const bubble = document.createElement("div");
  bubble.className = "message-bubble " + (from === "user" ? "message-bubble--user" : "message-bubble--assistant");

  if (from === "assistant") {
    bubble.innerHTML = marked.parse(text || "");
  } else {
    bubble.textContent = text;
  }

  row.appendChild(bubble);
  chatWindow.appendChild(row);
  chatWindow.scrollTop = chatWindow.scrollHeight;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";

  const data = new FormData();
  data.append("message", message);
  if (sessionId) data.append("session_id", sessionId);

  try {
    const res = await fetch("/api/chat", { method: "POST", body: data });
    if (!res.ok) {
      const errorText = await res.text();
      console.error("Chat error", res.status, errorText);
      addMessage("⚠️ Error fetching response.", "assistant");
      return;
    }
    const json = await res.json();
    sessionId = json.session_id;
    addMessage(json.answer, "assistant");
  } catch (err) {
    addMessage("⚠️ Error fetching response.", "assistant");
    console.error(err);
  }
});
