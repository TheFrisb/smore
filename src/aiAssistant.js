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

/** New function to render text between ** as bold */
function setMessageWithBold(element, message) {
  element.innerHTML = ""; // Clear existing content

  const parts = message.split(/\*\*/g); // Split by **
  parts.forEach((part, index) => {
    if (index % 2 === 0) {
      // Even indices are regular text
      element.appendChild(document.createTextNode(part));
    } else {
      // Odd indices are bold text
      const strong = document.createElement("strong");
      strong.textContent = part;
      element.appendChild(strong);
    }
  });
}

function sendMessage() {
  const apiUrl = "/api/ai-assistant/send-message/";
  const message = input.value;

  // Display the user's message
  renderMessage(message, true);
  input.value = "";
  sendButton.disabled = true;

  // Add the "thinking" message with pulse animation
  const aiMessage = renderMessage("AI Assistant is thinking...", false);

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
      const errorMessage = renderMessage(
        "An error occurred. Please try again later.",
        false,
      );
      errorMessage.classList.remove("animate-pulse");
    });
}

function initAiAssistant() {
  if (!messagesContainer || !input || !sendButton) {
    return;
  }

  sendButton.addEventListener("click", sendMessage);

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
    sendButton.disabled = !input.value.trim();
  });
}

export default initAiAssistant;
