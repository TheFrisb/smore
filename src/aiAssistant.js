import { getCsrfToken } from "./utils";

const messagesContainer = document.getElementById(
  "aiAssistantMessagesContainer",
);
const input = document.getElementById("aiAssistantInput");
const sendButton = document.getElementById("aiAssistantSendButton");
let isLoading = false;

function renderMessage(message, isUserMessage) {
  const messageContainer = document.createElement("div");
  messageContainer.className = `flex ${isUserMessage ? "justify-end" : "justify-start animate-pulse"}`;

  const messageWrapper = document.createElement("div");
  messageWrapper.className = `max-w-[80%] rounded-2xl p-4 bg-primary-800/50 border border-secondary-700/30 text-primary-200 ${isUserMessage ? "ml-12" : "mr-12"}`;

  const messageText = document.createElement("p");
  messageText.className = "whitespace-pre-wrap";
  messageText.textContent = message;

  messageWrapper.appendChild(messageText);
  messageContainer.appendChild(messageWrapper);

  messagesContainer.appendChild(messageContainer);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  return messageContainer;
}

function setMessageWithBold(element, message) {
  element.innerHTML = ""; // Clear existing content

  const parts = message.split(/\*\*/g); // Split by **
  parts.forEach((part, index) => {
    if (index % 2 === 0) {
      element.appendChild(document.createTextNode(part));
    } else {
      const strong = document.createElement("strong");
      strong.textContent = part;
      element.appendChild(strong);
    }
  });
}

function sendMessage(hasAccess) {
  if (isLoading) {
    return;
  }
  const apiUrl = "/api/ai-assistant/send-message/";
  const message = input.value;

  renderMessage(message, true);
  input.value = "";
  sendButton.disabled = true;

  if (!hasAccess) {
    const errorMessage = renderMessage(
      "You need to subscribe to the AI Assistant product to use this feature.",
      false,
    );
    errorMessage.classList.remove("animate-pulse");
    return;
  }

  isLoading = true;

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
      setMessageWithBold(aiMessage.querySelector("p"), data.message);
    })
    .catch((error) => {
      aiMessage.classList.remove("animate-pulse");
      setMessageWithBold(
        aiMessage.querySelector("p"),
        "An error occurred while processing the message.",
      );
      console.error("An error occurred while processing the message:", error);
    })
    .finally(() => {
      isLoading = false;
    });
}

function initAiAssistant() {
  if (!messagesContainer || !input || !sendButton) {
    return;
  }

  const hasAccess = document.querySelector("#hasAccessInput").value === "True";

  // Modified event listener to pass hasAccess
  sendButton.addEventListener("click", () => sendMessage(hasAccess));

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && input.value.trim()) {
      event.preventDefault(); // Prevent new line when sending
      sendMessage(hasAccess);
    }
  });

  input.addEventListener("input", () => {
    sendButton.disabled = !input.value.trim();
  });
}

export default initAiAssistant;
