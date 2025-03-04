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

function renderNoAccessMessage() {
  const messageContainer = document.createElement("div");
  messageContainer.className = `flex justify-start`;

  const messageWrapper = document.createElement("div");
  messageWrapper.className = `max-w-[80%] rounded-2xl p-4 bg-primary-800/50 border border-secondary-700/30 text-primary-200 mr-12`;

  const messageText = document.createElement("p");
  messageText.className = "whitespace-pre-wrap";
  messageText.textContent =
    "You need to subscribe to the AI Assistant product to use this feature.";

  const divHtml = `
<div class="mt-2 flex items-center justify-center w-full">
<a href="/plans/" class="w-[150px] inline-flex mx-auto gap-2 items-center justify-center px-6 py-3 bg-primary-800/50 text-secondary-400 rounded-lg font-semibold hover:bg-primary-700/50 transition-colors border border-primary-700/50 hover:border-secondary-500/30 ">
                Subscribe
                <svg class="w-5 h-5 text-secondary-400"><use xlink:href="/static/assets/svg/sprite10.svg#arrowRight"></use></svg>
            </a>
</div>
`;
  messageWrapper.appendChild(messageText);
  messageWrapper.innerHTML += divHtml;
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
    renderNoAccessMessage();
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
