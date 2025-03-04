import { getCsrfToken } from "./utils";
import { marked } from "marked";

const messagesContainer = document.getElementById(
  "aiAssistantMessagesContainer",
);
const input = document.getElementById("aiAssistantInput");
const sendButton = document.getElementById("aiAssistantSendButton");
let isLoading = false;

function renderMessage(message, isUserMessage) {
  const messageContainer = document.createElement("div");
  messageContainer.className = `flex ${isUserMessage ? "justify-end" : "justify-start"}`;

  const messageWrapper = document.createElement("div");
  messageWrapper.className = `max-w-[80%] rounded-2xl p-4 bg-primary-800/50 border border-secondary-700/30 text-primary-200 ${isUserMessage ? "ml-12" : "mr-12"}`;

  const messageContent = document.createElement("div");
  messageContent.className = "whitespace-pre-wrap";
  messageContent.textContent = message;

  if (!isUserMessage && message === "AI Analyst is thinking...") {
    messageContainer.classList.add("animate-pulse");
  }

  messageWrapper.appendChild(messageContent);
  messageContainer.appendChild(messageWrapper);

  messagesContainer.appendChild(messageContainer);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  return messageContainer;
}

function renderNoAccessMessage() {
  const messageContainer = document.createElement("div");
  messageContainer.className = `flex justify-start`;

  const messageWrapper = document.createElement("div");
  messageWrapper.className = `max-w-[80%] rounded-2xl p-4 bg-primary-800/50 border border-secondary-700/30 text-primary-200 mr-12`;

  const messageText = document.createElement("p");
  messageText.className = "whitespace-pre-wrap";
  messageText.textContent =
    "You need to subscribe to the AI Assistant product to use this feature.";

  const buttonContainer = document.createElement("div");
  buttonContainer.className = "mt-2 flex items-center justify-center w-full";
  buttonContainer.innerHTML = `
    <a href="/plans/" class="w-[150px] inline-flex mx-auto gap-2 items-center justify-center px-6 py-3 bg-primary-800/50 text-secondary-400 rounded-lg font-semibold hover:bg-primary-700/50 transition-colors border border-primary-700/50 hover:border-secondary-500/30 ">
      Subscribe
      <svg class="w-5 h-5 text-secondary-400"><use xlink:href="/static/assets/svg/sprite10.svg#arrowRight"></use></svg>
    </a>
  `;

  messageWrapper.appendChild(messageText);
  messageWrapper.appendChild(buttonContainer);
  messageContainer.appendChild(messageWrapper);

  messagesContainer.appendChild(messageContainer);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  return messageContainer;
}

function sendMessage(hasAccess) {
  if (isLoading) {
    return;
  }
  const apiUrl = "/api/ai-assistant/send-message/";
  const message = input.value;

  renderMessage(message, true);
  input.value = "";

  if (!hasAccess) {
    renderNoAccessMessage();
    return;
  }

  isLoading = true;
  sendButton.disabled = true;

  const aiMessage = renderMessage("AI Analyst is thinking...", false);

  fetch(apiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify({ message }),
  })
    .then((response) => response.json())
    .then((data) => {
      aiMessage.classList.remove("animate-pulse");
      const messageContent = aiMessage.querySelector("div.whitespace-pre-wrap");
      messageContent.innerHTML = marked.parse(data.message);
    })
    .catch((error) => {
      aiMessage.classList.remove("animate-pulse");
      const messageContent = aiMessage.querySelector("div.whitespace-pre-wrap");
      messageContent.textContent =
        "An error occurred while processing the message.";
      console.error("An error occurred while processing the message:", error);
    })
    .finally(() => {
      isLoading = false;
      sendButton.disabled = false;
    });
}

function initAiAssistant() {
  if (!messagesContainer || !input || !sendButton) {
    return;
  }

  const hasAccess = document.querySelector("#hasAccessInput").value === "True";

  input.addEventListener("input", () => {
    sendButton.disabled = !input.value.trim();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage(hasAccess);
    }
  });

  sendButton.addEventListener("click", () => sendMessage(hasAccess));
}

export default initAiAssistant;
