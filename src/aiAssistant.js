import { getCsrfToken } from "./utils";
import { marked } from "marked";
import { Notyf } from "notyf";

const messagesContainer = document.getElementById(
  "aiAssistantMessagesContainer",
);
const input = document.getElementById("aiAssistantInput");
const sendButton = document.getElementById("aiAssistantSendButton");
const aiAssitantProductIdInput = document.getElementById(
  "aiAssistantProductId",
);

const suggestedMessagesSection = document.getElementById(
  "aiAssistantSuggestedMessagesContainer",
);
const suggestedMessages = document.querySelectorAll(
  ".aiAssistantSuggestedMessageButton",
);

let isLoading = false;
let notyf = new Notyf({
  duration: 5000,
  position: {
    x: "right",
    y: "top",
  },
  dismissible: true,
});

function renderMessage(message, isUserMessage) {
  const messageContainer = document.createElement("div");
  messageContainer.className = `flex ${isUserMessage ? "justify-end" : "justify-start"}`;

  const messageWrapper = document.createElement("div");
  messageWrapper.className = `max-w-[80%] rounded-2xl p-4 bg-primary-800/50 border border-secondary-700/30 text-primary-200 ${isUserMessage ? "ml-12" : "mr-12"}`;

  const messageContent = document.createElement("div");
  if (isUserMessage) {
    messageContent.className = "whitespace-pre-wrap";
  }
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

function renderNoAccessMessage(message, userSubscription) {
  const messageContainer = document.createElement("div");
  messageContainer.className = `flex justify-start messageContainer`;

  const messageWrapper = document.createElement("div");
  messageWrapper.className = `max-w-[80%] rounded-2xl p-4 bg-primary-800/50 border border-secondary-700/30 text-primary-200 mr-12`;

  const messageText = document.createElement("p");
  messageText.className = "whitespace-pre-wrap";
  messageText.innerHTML = message;

  const buttonContainer = document.createElement("button");
  buttonContainer.className =
    "mt-2 flex items-center justify-center w-full relative disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 disabled:hover:shadow-none disabled:hover-none";
  buttonContainer.innerHTML = `
    <span class="w-full inline-flex mx-auto gap-2 items-center justify-center px-6 py-3 bg-primary-800/50 text-secondary-400 rounded-lg font-semibold hover:bg-primary-700/50 transition-colors border border-primary-700/50 hover:border-secondary-500/30 ">
      Subscribe 
      <svg class="w-5 h-5 text-secondary-400"><use xlink:href="/static/assets/svg/sprite18.svg#arrowRight"></use></svg>
                                      <svg class="w-6 h-6 text-gray-200 animate-spin fill-secondary-400 absolute right-4 buttonSpinner hidden" 
                                     viewBox=" 0 0 100 101
                                " fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M100 50.5908C100 78.2051 77.6142 100.591 50 100.591C22.3858 100.591 0 78.2051 0 50.5908C0 22.9766 22.3858 0.59082 50 0.59082C77.6142 0.59082 100 22.9766 100 50.5908ZM9.08144 50.5908C9.08144 73.1895 27.4013 91.5094 50 91.5094C72.5987 91.5094 90.9186 73.1895 90.9186 50.5908C90.9186 27.9921 72.5987 9.67226 50 9.67226C27.4013 9.67226 9.08144 27.9921 9.08144 50.5908Z"
                                          fill="currentColor"/>
                                    <path d="M93.9676 39.0409C96.393 38.4038 97.8624 35.9116 97.0079 33.5539C95.2932 28.8227 92.871 24.3692 89.8167 20.348C85.8452 15.1192 80.8826 10.7238 75.2124 7.41289C69.5422 4.10194 63.2754 1.94025 56.7698 1.05124C51.7666 0.367541 46.6976 0.446843 41.7345 1.27873C39.2613 1.69328 37.813 4.19778 38.4501 6.62326C39.0873 9.04874 41.5694 10.4717 44.0505 10.1071C47.8511 9.54855 51.7191 9.52689 55.5402 10.0491C60.8642 10.7766 65.9928 12.5457 70.6331 15.2552C75.2735 17.9648 79.3347 21.5619 82.5849 25.841C84.9175 28.9121 86.7997 32.2913 88.1811 35.8758C89.083 38.2158 91.5421 39.6781 93.9676 39.0409Z"
                                          fill="currentFill"/>
                                </svg>
    </span>
  `;

  buttonContainer.addEventListener("click", async () => {
    if (buttonContainer.disabled) {
      notyf.error("The data is being processed. Please wait.");
      return;
    }

    const buttonSpinner = buttonContainer.querySelector(".buttonSpinner");
    buttonSpinner.classList.remove("hidden");
    const userHasSubscription = userSubscription !== null;
    const url = userHasSubscription
      ? "/api/payments/update-subscription/"
      : "/api/payments/checkout/";

    const aiAssitantProductId = aiAssitantProductIdInput.value;

    let products = [];
    let frequency = "monthly";
    let firstProduct = aiAssitantProductId;

    if (userHasSubscription) {
      products = userSubscription.products;
      frequency = userSubscription.frequency;
      firstProduct = userSubscription.firstProduct;
    }

    if (!products.includes(aiAssitantProductId)) {
      products.push(aiAssitantProductId);
    }

    const data = {
      products: products,
      frequency: frequency,
      firstProduct: firstProduct,
    };

    buttonContainer.disabled = true;

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(data),
    });
    const responseData = await response.json();

    if (response.ok) {
      if (userHasSubscription) {
        setTimeout(() => {
          notyf.success("You are now subscribed to the AI Analyst!");
          const aiAssistantFreeMessageContainer = document.getElementById(
            "aiAssistantFreeMessageContainer",
          );
          if (aiAssistantFreeMessageContainer) {
            aiAssistantFreeMessageContainer.classList.add("hidden");
          }
          messageContainer.remove();
        }, 200);
      } else {
        window.location.href = responseData.url;
      }
    } else {
      const errorMessage =
        responseData.message ||
        "An unexpected error has occured. Please try again shortly.";
      notyf.error(errorMessage);
    }

    buttonContainer.disabled = false;
    buttonSpinner.classList.add("hidden");
  });

  messageWrapper.appendChild(messageText);
  messageWrapper.appendChild(buttonContainer);
  console.log(userSubscription);
  if (userSubscription) {
    const newEl = document.createElement("p");
    newEl.className = "mt-4 !text-sm text-center";
    newEl.innerHTML += `
    <span class="text-secondary-500">You will be charged €${userSubscription.productPrice} right now</span>,<br> and then €${userSubscription.productPrice} ${userSubscription.frequency}
    `;
    messageWrapper.appendChild(newEl);
  }

  messageContainer.appendChild(messageWrapper);

  messagesContainer.appendChild(messageContainer);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  return messageContainer;
}

function updateFreeMessagesCountIfExists() {
  const freeMessageCountEl = document.getElementById(
    "aiAssistantFreeMessageCounter",
  );

  if (!freeMessageCountEl) {
    return;
  }

  let count = parseInt(freeMessageCountEl.textContent);

  let updatedCount = count - 1;
  if (updatedCount <= 0) {
    const parentEl = freeMessageCountEl.parentElement;
    parentEl.classList.remove("text-success-500");
    parentEl.classList.add("text-secondary-500");
    parentEl.innerHTML = `You've used up your 3 free messages. Subscribe now to unlock unlimited access to our AI Analyst!`;
  } else {
    freeMessageCountEl.textContent = updatedCount.toString();
  }
}

async function sendMessage() {
  if (isLoading) {
    return;
  }
  const apiUrl = "/api/ai-assistant/send-message/";
  const message = input.value;

  renderMessage(message, true);
  input.value = "";

  isLoading = true;
  sendButton.disabled = true;

  const aiMessage = renderMessage("AI Analyst is thinking...", false);
  if (suggestedMessagesSection) {
    suggestedMessagesSection.classList.add("hidden");
  }

  try {
    const response = await fetch(apiUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ message }),
    });

    if (response.status === 403) {
      const data = await response.json();
      aiMessage.remove();
      renderNoAccessMessage(
        "You've used up your 3 free messages.<br>Subscribe now to unlock unlimited access to our AI Analyst!",
        data.user_subscription,
      );
    } else if (response.ok) {
      const data = await response.json();
      aiMessage.classList.remove("animate-pulse");
      const messageContent = aiMessage.querySelector("div");
      messageContent.innerHTML = marked.parse(data.message);
      updateFreeMessagesCountIfExists();
    } else {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    aiMessage.classList.remove("animate-pulse");
    const messageContent = aiMessage.querySelector("div");
    messageContent.textContent =
      "An error occurred while processing the message.";
    console.error("An error occurred while processing the message:", error);
  } finally {
    isLoading = false;
    sendButton.disabled = false;
  }
}

function initAiAssistant() {
  if (!messagesContainer || !input || !sendButton) {
    // log not found elements
    console.error("AI Assistant elements not found in the DOM.");
    // log the IDs of the elements that were not found
    console.error("Missing elements:", {
      messagesContainer: !!messagesContainer,
      input: !!input,
      sendButton: !!sendButton,
    });

    return;
  }

  input.addEventListener("input", () => {
    sendButton.disabled = !input.value.trim();
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  });

  sendButton.addEventListener("click", () => sendMessage());
  console.log(suggestedMessages);
  suggestedMessages.forEach((button) => {
    button.addEventListener("click", () => {
      const message = button.getAttribute("data-query");
      if (message) {
        input.value = message;
        sendMessage();
      }
    });
  });
}

export default initAiAssistant;
