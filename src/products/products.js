import { getCsrfToken } from "../utils";

const products = document.querySelectorAll(".product");
const checkoutSummarySection = document.querySelector(
  ".checkoutSummarySection",
);

const checkoutSummaryItemsSection = document.querySelector(
  ".checkoutSummary__items",
);

const checkoutButton = document.querySelector("#checkoutButton");
const chooseSubscriptionFrequencyButton = document.querySelector(
  "#chooseSubscriptionFrequencyButton",
);

let selectedProducts = [];
let frequencyType = "month";

function initChooseSubscriptionFrequencyButton() {
  if (!chooseSubscriptionFrequencyButton) {
    return;
  }

  chooseSubscriptionFrequencyButton.addEventListener("click", () => {
    const toggleButton =
      chooseSubscriptionFrequencyButton.querySelector(".toggleButton");
    const annualLabelEl = document.querySelector(".annualLabel");
    const monthlyLabelEl = document.querySelector(".monthlyLabel");
    if (toggleButton.classList.contains("left-1")) {
      toggleButton.classList.remove("left-1");
      toggleButton.classList.add("right-1");
      frequencyType = "year";

      annualLabelEl.classList.remove("text-primary-300");
      annualLabelEl.classList.add("text-white");
      monthlyLabelEl.classList.add("text-primary-300");
      monthlyLabelEl.classList.remove("text-white");
    } else {
      toggleButton.classList.remove("right-1");
      toggleButton.classList.add("left-1");
      frequencyType = "month";

      monthlyLabelEl.classList.remove("text-primary-300");
      monthlyLabelEl.classList.add("text-white");
      annualLabelEl.classList.add("text-primary-300");
      annualLabelEl.classList.remove("text-white");
    }

    updatePrices();
  });
}

function updatePrices() {
  const products = document.querySelectorAll(".product");

  products.forEach((product) => {
    const priceEl = product.querySelector(".product__price");

    let monthlyPrice = product.getAttribute("data-product-monthly-price");
    let yearlyPrice = product.getAttribute("data-product-annual-price");

    let price = frequencyType === "month" ? monthlyPrice : yearlyPrice;

    priceEl.textContent = `$${price}`;
  });

  updateCheckoutSummaryUI();
}

function initProducts() {
  if (!products || !checkoutSummarySection) {
    return;
  }
  initChooseSubscriptionFrequencyButton();

  products.forEach((product) => {
    product.addEventListener("click", () => {
      const productId = product.getAttribute("data-product-id");

      const productCheckboxContainer = product.querySelector(
        ".product__checkboxContainer",
      );
      const productCheckboxEl = product.querySelector(".product__checkboxIcon");

      updateClickedProductUI(
        product,
        productCheckboxContainer,
        productCheckboxEl,
      );

      pushOrRemoveProduct(productId);
      updateCheckoutSummaryUI();
    });
  });

  checkoutButton.addEventListener("click", () => {
    if (checkoutButton.disabled) {
      return;
    }

    const csrfToken = getCsrfToken();

    fetch("/api/payments/checkout/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({
        products: selectedProducts.map(Number),
        frequency: frequencyType,
      }),
    })
      .then((response) => response.json())
      .then((data) => {
        window.location.href = data.checkout_url;
      })
      .catch((error) => {
        console.error("Error:", error);
      });
  });
}

function updateCheckoutSummaryUI() {
  let checkoutSummary = "";

  let total_price = 0;

  selectedProducts.forEach((productId) => {
    const productEl = document.querySelector(
      `.product[data-product-id="${productId}"]`,
    );
    const productName = productEl.getAttribute("data-product-name");
    const productPrice = productEl.querySelector(".product__price").textContent;

    total_price += parseFloat(productPrice.replace("$", ""));

    checkoutSummary += `
    <div class="space-y-4 mb-8 divide-y divide-primary-700/30">
    <div class="flex justify-between items-center text-primary-200 py-3">
    <span class="capitalize">${productName}</span>
    <span>${productPrice}</span>
    </div>
    </div>
    `;
  });

  if (selectedProducts.length > 1) {
    checkoutSummary += `
    <div class="flex justify-between items-center text-secondary-500 py-3">
    <span>Multi-sport Discount</span>
    <span>-$${(selectedProducts.length - 1) * 20}</span> 
    </div>
    `;
  }
  checkoutSummaryItemsSection.innerHTML = checkoutSummary;

  if (selectedProducts.length === 0) {
    checkoutButton.disabled = true;
  } else {
    checkoutButton.disabled = false;
  }

  let totalPriceEl = document.querySelector(
    ".checkoutSummarySection__totalPrice",
  );
  totalPriceEl.textContent = `$${total_price.toFixed(2)}`;
}

function pushOrRemoveProduct(id) {
  const productIndex = selectedProducts.indexOf(id);

  if (productIndex === -1) {
    selectedProducts.push(id);
  } else {
    selectedProducts.splice(productIndex, 1);
  }
}

function updateClickedProductUI(
  productElement,
  productCheckboxContainer,
  productCheckboxEl,
) {
  if (productElement.classList.contains("selected")) {
    productElement.classList.remove("selected");
    productElement.classList.remove(
      "bg-secondary-500/20",
      "border-secondary-500/50",
    );
    productElement.classList.add(
      "hover:border-primary-500/30",
      "hover:shadow-lg",
      "hover:shadow-primary-500/10",
      "bg-primary-800/50",
    );

    productCheckboxContainer.classList.remove(
      "bg-primary-500",
      "border-primary-500",
    );
    productCheckboxEl.classList.add("hidden");
  } else {
    productElement.classList.add("selected");
    productElement.classList.add(
      "bg-secondary-500/20",
      "border-secondary-500/50",
    );
    productElement.classList.remove(
      "hover:border-primary-500/30",
      "hover:shadow-lg",
      "hover:shadow-primary-500/10",
      "bg-primary-800/50",
    );

    productCheckboxContainer.classList.add(
      "bg-primary-500",
      "border-primary-500",
    );
    productCheckboxEl.classList.remove("hidden");
  }
}

export default initProducts;
