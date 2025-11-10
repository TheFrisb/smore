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
const ownedProductPriceIds = getListOfOwnedProductPriceIds();
const ownedProductIds = getListOfOwnedProductIds();

let selectedPriceId = null;

function initCheckoutJs() {
  if (!planCards || !checkoutButton) {
    return;
  }

  planCards.forEach((card) => {
    card.addEventListener("click", () => {
      if (card.classList.contains("planCard--owned")) return;

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
    const checkoutRequestDetails = getCheckoutRequestDetails();
    const requestMethod = checkoutButton.dataset.method;

    const arrowRightIcon = checkoutButton.querySelector(".arrowRightIcon");
    const spinnerIcon = checkoutButton.querySelector(".buttonSpinnerIcon");

    arrowRightIcon.classList.add("hidden");
    spinnerIcon.classList.remove("hidden");

    if (requestMethod === "GET") {
      window.location.href = checkoutRequestDetails.url;
      return;
    }

    try {
      const apiResponse = await makeApiRequest(
        checkoutRequestDetails.url,
        checkoutRequestDetails.data,
      );

      if (apiResponse.url) window.location.href = apiResponse.url;

      if (apiResponse.message) {
        const currentPlanCard = document.querySelector(
          `.planCard[data-price-id="${selectedPriceId}"]`,
        );
        const oldPlanCard = document.querySelector(
          `.planCard[data-product-id="${CSS.escape(currentPlanCard.dataset.productId)}"].planCard--owned`,
        );

        oldPlanCard.classList.remove("planCard--owned");
        currentPlanCard.classList.add("planCard--owned");

        notyf.success(apiResponse.message);
      }
    } catch (error) {
      notyf.error(error.message);
    }

    arrowRightIcon.classList.remove("hidden");
    spinnerIcon.classList.add("hidden");
    checkoutButton.disabled = false;
  });

  function getCheckoutRequestDetails() {
    const requestDetails = {
      url: null,
      data: null,
    };

    if (checkoutButton.dataset.method === "GET") {
      requestDetails.url = checkoutButton.dataset.url;
      return requestDetails;
    }

    const selectedPlanCard = document.querySelector(
      `.planCard[data-price-id="${selectedPriceId}"]`,
    );

    if (!selectedPlanCard) {
      return requestDetails;
    }

    const productId = selectedPlanCard.dataset.productId;

    if (ownedProductIds.includes(productId)) {
      console.log("Returning update url");
      requestDetails.url = checkoutButton.dataset.updateUrl;
      requestDetails.data = {
        old_product_price: findOwnedProductPrice(productId),
        new_product_price: selectedPriceId,
      };
    } else {
      requestDetails.url = checkoutButton.dataset.url;
      requestDetails.data = {
        product_price: selectedPriceId,
      };
    }

    return requestDetails;
  }

  function findOwnedProductPrice(productId) {
    if (productId == null) return null;
    const pid = String(productId).trim();

    // fast single-query: a card for the product that also has the "planCard--owned" class
    const ownedCard = document.querySelector(
      `.planCard[data-product-id="${CSS.escape(pid)}"].planCard--owned`,
    );

    if (ownedCard) {
      const priceId = ownedCard.dataset.priceId;
      return priceId ? String(priceId).trim() : null;
    }

    // fallback: iterate planCards NodeList (in case class markers are different)
    for (const card of planCards) {
      if (String(card.dataset.productId).trim() === pid) {
        // check visually-marked owned badge or class; prefer class, then check ownedPriceIds
        if (card.classList.contains("planCard--owned")) {
          return card.dataset.priceId
            ? String(card.dataset.priceId).trim()
            : null;
        }
      }
    }

    return null;
  }

  async function makeApiRequest(url, data) {
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

function getListOfOwnedProductPriceIds() {
  const ownedProductPriceIdsInput = document.getElementById("ownedPriceIds");
  if (!ownedProductPriceIdsInput) return [];

  return ownedProductPriceIdsInput.value.split(",");
}

function getListOfOwnedProductIds() {
  const ownedProductIdsInput = document.getElementById("ownedProductIds");
  if (!ownedProductIdsInput) return [];

  return ownedProductIdsInput.value.split(",");
}

function getListOfPurchasedProductIds() {
  const purchasedProductIdsInput = document.getElementById(
    "purchasedProductIds",
  );
  if (!purchasedProductIdsInput) return [];

  return purchasedProductIdsInput.value.split(",");
}

function updateButtonState() {
  checkoutButton.disabled =
    selectedPriceId === null || ownedProductPriceIds.includes(selectedPriceId);

  const newButtonText = getCheckoutButtonText(
    selectedPriceId,
    ownedProductIds,
    getListOfPurchasedProductIds(),
  );

  const buttonTextElements = checkoutButton.querySelectorAll(".buttonText");
  buttonTextElements.forEach((el) => (el.textContent = newButtonText));
}

function clearSelectedProductId() {
  selectedPriceId = null;
  updatePlanCards();
  updateButtonState();
}

function getCheckoutButtonText(
  selectedPriceId,
  ownedProductIds,
  purchasedProductIds,
) {
  if (!selectedPriceId) {
    return "Select a Plan";
  }

  const selectedPlanCard = document.querySelector(
    `.planCard[data-price-id="${selectedPriceId}"]`,
  );

  if (!selectedPlanCard) {
    return "Subscribe Now";
  }

  const selectedProductId = selectedPlanCard.dataset.productId;

  const isFirstPurchaseOfProduct =
    !purchasedProductIds.includes(selectedProductId);

  if (isFirstPurchaseOfProduct) {
    return "Try 3 days FREE";
  }

  if (ownedProductIds.includes(selectedProductId)) {
    const ownedPriceCard = document.querySelector(
      `.planCard[data-product-id="${CSS.escape(selectedProductId)}"].planCard--owned`,
    );

    if (
      !ownedPriceCard ||
      !ownedPriceCard.dataset.priceAmount ||
      !selectedPlanCard.dataset.priceAmount
    ) {
      return "Update Plan";
    }

    const ownedAmount = parseFloat(ownedPriceCard.dataset.priceAmount);
    const selectedAmount = parseFloat(selectedPlanCard.dataset.priceAmount);

    if (selectedAmount > ownedAmount) {
      return "Upgrade";
    } else if (selectedAmount < ownedAmount) {
      return "Downgrade";
    } else {
      return "Update Plan";
    }
  }

  return "Subscribe Now";
}

export { initCheckoutJs, clearSelectedProductId };
