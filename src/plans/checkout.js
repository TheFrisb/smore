import { Notyf } from "notyf";
import { getCsrfToken } from "../utils";

let notyf = new Notyf({
  duration: 5000,
  position: {
    x: "right",
    y: "top",
  },
  dismissible: true,
});
const planCards = document.querySelectorAll(".planCard");
const checkoutButton = document.getElementById("checkoutButton");
const ownedProductIds = getListOfOwnedProductIds();

let selectedPriceId = null;

function initCheckoutJs() {
  if (!planCards) {
    return;
  }

  planCards.forEach((card) => {
    card.addEventListener("click", () => {
      const priceId = card.dataset.priceId;

      if (selectedPriceId === priceId) {
        selectedPriceId = null;
      } else {
        selectedPriceId = priceId;
      }

      updatePlanCards();
      updateButtonState();
    });
  });

  checkoutButton.addEventListener("click", async () => {
    if (selectedPriceId === null) {
      return;
    }

    checkoutButton.disabled = true;
    const checkoutUrl = checkoutButton.dataset.url;
    const requestMethod = checkoutButton.dataset.method;

    const arrowRightIcon = checkoutButton.querySelector(".arrowRightIcon");
    const spinnerIcon = checkoutButton.querySelector(".buttonSpinnerIcon");

    arrowRightIcon.classList.add("hidden");
    spinnerIcon.classList.remove("hidden");

    if (requestMethod === "GET") {
      window.location.href = checkoutUrl;
      return;
    }

    try {
      const apiResponse = await makeApiRequest(checkoutUrl);
      window.location.href = apiResponse.url;
    } catch (error) {
      notyf.error(error.message);
    }

    arrowRightIcon.classList.remove("hidden");
    spinnerIcon.classList.add("hidden");
    checkoutButton.disabled = false;
  });

  async function makeApiRequest(url) {
    const data = { product_price: parseInt(selectedPriceId) };

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Something went wrong");
    }

    return response.json();
  }
}

function updatePlanCards() {
  planCards.forEach((card) => {
    const priceId = card.dataset.priceId;

    if (priceId === selectedPriceId) {
      card.classList.add("active");
    } else {
      card.classList.remove("active");
    }
  });
}
function getListOfOwnedProductIds() {
  const ownedProductIdsInput = document.getElementById("ownedProductIds");
  if (!ownedProductIdsInput) return [];

  return ownedProductIdsInput.value.split(",");
}
function updateButtonState() {
  checkoutButton.disabled =
    selectedPriceId === null || ownedProductIds.includes(selectedPriceId);
}

function clearSelectedProductId() {
  selectedPriceId = null;
  updatePlanCards();
  updateButtonState();
}

export { initCheckoutJs, clearSelectedProductId };
