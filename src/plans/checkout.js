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

function initCheckoutJs() {
  const planCards = document.querySelectorAll(".planCard");
  const availableProductIdsInput = document.getElementById(
    "availableProductIds",
  );
  const checkoutTotalPrice = document.getElementById(
    "checkoutSummarySection__totalPrice",
  );
  const checkoutCartRows = document.querySelector(".checkoutSummary__items");
  const checkoutButton = document.getElementById("checkoutButton");

  if (!availableProductIdsInput || !planCards) {
    return;
  }

  const cart = initCart(availableProductIdsInput.value);

  planCards.forEach((productCard) => {
    productCard.addEventListener("click", () => {
      const productId = productCard.dataset.productId;
      const frequency = productCard.dataset.frequency;
      addProductToCart(productId, frequency);
    });
  });

  checkoutButton.addEventListener("click", async () => {
    if (cart.size < 1) {
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
      const response = await makeApiRequest(checkoutUrl);
    } catch (error) {
      notyf.error(error.message);
    }

    arrowRightIcon.classList.remove("hidden");
    spinnerIcon.classList.add("hidden");
    checkoutButton.disabled = false;
  });

  function initCart(idsString) {
    const cart = new Map();

    if (idsString) {
      const productIds = idsString.split(",").map((id) => id.trim());

      productIds.forEach((id) => {
        if (id) {
          cart.set(id, null); // default value is null
        }
      });
    }
    return cart;
  }

  function updateProductTabs() {
    planCards.forEach((card) => {
      const frequency = card.dataset.frequency;
      const productId = card.dataset.productId;

      // check if product is in cart and the frequency matches
      if (cart.has(productId) && cart.get(productId) === frequency) {
        card.classList.add("active");
      } else {
        card.classList.remove("active");
      }
    });
  }

  function updateCheckoutSummary() {
    let totalPrice = 0;

    cart.forEach((frequency, productId) => {
      if (frequency) {
        // Assuming a function getProductPrice that fetches the price based on productId and frequency
        const price = getProductPrice(productId, frequency);
        totalPrice += price;
      }
    });

    if (cart.size > 1) {
      const discount = totalPrice * 0.2;
      totalPrice -= discount;
    }

    checkoutButton.disabled = cart.size < 1;

    updateCheckoutCartRows();
    checkoutTotalPrice.textContent = `${totalPrice.toFixed(2)}`;
  }

  function updateCheckoutCartRows() {
    let html = "";
    const totalPriceP = checkoutTotalPrice.parentElement;
    const currencySymbol = totalPriceP.firstChild.textContent.trim();
    let subtotal = 0;
    let itemCount = 0;
    let discount = 0;

    cart.forEach((frequency, productId) => {
      if (!frequency) {
        return;
      }

      const productCard = Array.from(planCards).find(
        (card) =>
          card.dataset.productId === productId &&
          card.dataset.frequency === frequency,
      );

      const price = parseFloat(productCard.dataset.price);
      const frequencyText = frequency.replaceAll("_", " ");
      const productName = productCard.dataset.productName;

      html += `
        <div class="flex justify-between items-center text-primary-200 py-3">
          <span class="capitalize">${productName} - ${frequencyText}</span>
          <span>${currencySymbol}${price.toFixed(2)}</span>
        </div>
      `;

      subtotal += price;
      itemCount++;
    });

    if (itemCount > 1) {
      discount = subtotal * 0.2;
      html += `
        <div class="flex justify-between items-center text-primary-200 py-3">
          <span>Discount (20%)</span>
          <span>-${currencySymbol}${discount.toFixed(2)}</span>
        </div>
      `;
    }

    checkoutCartRows.innerHTML = html;
  }

  function getProductPrice(productId, frequency) {
    // filter all planCards to find the matching productId and frequency
    const productCard = Array.from(planCards).find(
      (card) =>
        card.dataset.productId === productId &&
        card.dataset.frequency === frequency,
    );

    return parseFloat(productCard.dataset.price);
  }

  function addProductToCart(productId, frequency) {
    console.log(
      `Adding product ${productId} with frequency ${frequency} to cart`,
    );
    cart.set(productId, frequency);
    updateProductTabs();
    updateCheckoutSummary();
  }

  async function makeApiRequest(url) {
    const data = [];
    cart.forEach((frequency, productId) => {
      if (frequency) {
        data.push({ product: parseInt(productId), frequency });
      }
    });

    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify({ products: data }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Something went wrong");
    }

    return response.json();
  }
}

/*
  Se dodavat produkti
  -20% discount na cela cena ako ima > 1 produkt
 */
export { initCheckoutJs };
