import { getCsrfToken } from "../utils";
import { Notyf } from "notyf";

let notyf = new Notyf({
  duration: 5000,
  position: {
    x: "right",
    y: "top",
  },
});
const products = document.querySelectorAll(".product");
const checkoutSummarySection = document.querySelector(
  ".checkoutSummarySection",
);
const userCurrencyInput = document.querySelector("#userCurrency");

function getUserCurrency() {
  if (userCurrencyInput) {
    return userCurrencyInput.value;
  }
  return "€";
}

const checkoutSummaryItemsSection = document.querySelector(
  ".checkoutSummary__items",
);

const checkoutButton = document.querySelector("#checkoutButton");
const chooseSubscriptionFrequencyButton = document.querySelector(
  "#chooseSubscriptionFrequencyButton",
);

const authenticatedActiveSubscriptionTypeInput = document.querySelector(
  "#userSubscriptionType",
);

const authenticatedActiveSubscriptionFirstChosenProductId =
  document.querySelector("#userFirstChosenProductId");

let selectedProducts = [];
let frequencyType = "monthly";

function initChooseSubscriptionFrequencyButton() {
  if (!chooseSubscriptionFrequencyButton) {
    return;
  }

  chooseSubscriptionFrequencyButton.addEventListener("click", () => {
    const toggleButton =
      chooseSubscriptionFrequencyButton.querySelector(".toggleButton");
    const annualLabelEl = document.querySelector(".annualLabel");
    const monthlyLabelEl = document.querySelector(".monthlyLabel");
    const checkoutSummaryMode =
      checkoutSummarySection.querySelector("#subscriptionMode");

    if (toggleButton.classList.contains("left-1")) {
      toggleButton.classList.remove("left-1");
      toggleButton.classList.add("right-1");
      frequencyType = "yearly";

      annualLabelEl.classList.remove("text-primary-300");
      annualLabelEl.classList.add("text-white");
      monthlyLabelEl.classList.add("text-primary-300");
      monthlyLabelEl.classList.remove("text-white");

      checkoutSummaryMode.textContent = checkoutSummaryMode.getAttribute(
        "data-translated-yearly",
      );

      if (authenticatedActiveSubscriptionTypeInput) {
        const activeSubscriptionType =
          authenticatedActiveSubscriptionTypeInput.value;

        if (activeSubscriptionType === "monthly") {
          const elsToUpdate = document.querySelectorAll(
            ".product__currentPlanDisclaimer",
          );

          elsToUpdate.forEach((el) => {
            el.textContent = el.getAttribute("data-upgrade-plan");
          });
        }
      }
    } else {
      toggleButton.classList.remove("right-1");
      toggleButton.classList.add("left-1");
      frequencyType = "monthly";

      monthlyLabelEl.classList.remove("text-primary-300");
      monthlyLabelEl.classList.add("text-white");
      annualLabelEl.classList.add("text-primary-300");
      annualLabelEl.classList.remove("text-white");

      checkoutSummaryMode.textContent = checkoutSummaryMode.getAttribute(
        "data-translated-monthly",
      );

      if (authenticatedActiveSubscriptionTypeInput) {
        const activeSubscriptionType =
          authenticatedActiveSubscriptionTypeInput.value;

        if (activeSubscriptionType) {
          const elsToUpdate = document.querySelectorAll(
            ".product__currentPlanDisclaimer",
          );
          elsToUpdate.forEach((el) => {
            el.textContent = el.getAttribute("data-current-plan");
          });
        }
      }
    }

    updatePrices();
  });
}

function updatePrices() {
  const products = document.querySelectorAll(".product");

  products.forEach((product) => {
    const priceEl = product.querySelector(".product__price");
    const productNoDiscountPriceEl = product.querySelector(
      ".product__NoDiscountPrice",
    );

    const currentProductId = product.getAttribute("data-product-id");

    let price = getProductMonthlyPrice(product);

    if (frequencyType === "yearly") {
      productNoDiscountPriceEl.classList.remove("hidden");
    } else {
      productNoDiscountPriceEl.classList.add("hidden");
    }

    if (
      shouldApplyDiscount() &&
      currentProductId !== getFirstSelectedSubscriptionProduct()
    ) {
      productNoDiscountPriceEl.classList.remove("hidden");
    }

    priceEl.textContent = `${getUserCurrency()}${price}`;
  });

  updateCheckoutSummaryUI();
}

function shouldApplyDiscount() {
  // check if selectedProducts has at least 1 product
  return selectedProducts.length > 0;
}

function getFirstSelectedSubscriptionProduct() {
  // return the first selected product id if exists, otherwise null
  return selectedProducts.length > 0 ? selectedProducts[0].id : null;
}

function initProducts() {
  if (!products || !checkoutSummarySection) {
    return;
  }

  initChooseSubscriptionFrequencyButton();

  products.forEach((product) => {
    product.addEventListener("click", () => {
      if (product.classList.contains("notSelectable")) {
        return;
      }

      const productId = product.getAttribute("data-product-id");
      const productType = product.getAttribute("data-product-type");

      const productCheckboxContainer = product.querySelector(
        ".product__checkboxContainer",
      );
      const productCheckboxEl = product.querySelector(".product__checkboxIcon");

      updateClickedProductUI(
        product,
        productCheckboxContainer,
        productCheckboxEl,
      );

      pushOrRemoveProduct(productId, productType);
      updatePrices();
      updateCheckoutSummaryUI();

      toggleSoccerDiscountBar();
    });
  });

  if (authenticatedActiveSubscriptionTypeInput) {
    console.log(authenticatedActiveSubscriptionTypeInput.value);
    const activeSubscriptionType =
      authenticatedActiveSubscriptionTypeInput.value;
    if (activeSubscriptionType) {
      const elsToUpdate = document.querySelectorAll(
        ".product__currentPlanDisclaimer",
      );

      let firstChosenProductId = null;
      if (authenticatedActiveSubscriptionFirstChosenProductId) {
        firstChosenProductId =
          authenticatedActiveSubscriptionFirstChosenProductId.value;
      }

      if (firstChosenProductId) {
        const el = document.querySelector(
          `.product[data-product-id="${firstChosenProductId}"]`,
        );

        if (el) {
          el.click();
        }
      }

      elsToUpdate.forEach((el) => {
        if (el.dataset.productId === firstChosenProductId) {
          return;
        }

        el.click();
      });
    }

    if (activeSubscriptionType && activeSubscriptionType === "yearly") {
      chooseSubscriptionFrequencyButton.click();
    }
  }

  if (checkoutButton) {
    checkoutButton.addEventListener("click", async () => {
      if (checkoutButton.disabled) {
        return;
      }

      checkoutButton.disabled = true;
      const buttonSpinner = checkoutButton.querySelector(".buttonSpinner");
      buttonSpinner.classList.remove("hidden");
      const csrfToken = getCsrfToken();
      const url = checkoutButton.getAttribute("data-url");

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            products: selectedProducts.map((product) => product.id),
            firstProduct: getFirstSelectedSubscriptionProduct(),
            frequency: frequencyType,
          }),
        });
        const responseData = await response.json();

        if (!response.ok) {
          throw {
            status: response.status,
            message:
              responseData.message ||
              "An unexpected error has occurred. Please try again or contact support if the issue persists.",
            details: responseData,
          };
        }

        if (responseData.url) {
          window.location.href = responseData.url;
        } else {
          notyf.success("Payment successful! Redirecting...");
          setTimeout(() => {
            window.location.href = "/accounts/manage-plan/";
          }, 2000);
        }
      } catch (error) {
        console.error("Error during checkout:", error);
        checkoutButton.disabled = false;
        buttonSpinner.classList.add("hidden");

        const errorMessage =
          error.message ||
          "An unexpected error has occurred. Please try again or contact support if the issue persists.";
        notyf.error(errorMessage);
      }
    });
  }
}

function getProductTotalPrice(productEl) {
  if (
    shouldApplyDiscount() &&
    productEl.dataset.productId !== getFirstSelectedSubscriptionProduct()
  ) {
    return frequencyType === "monthly"
      ? productEl.getAttribute("data-product-monthly-discounted-price")
      : productEl.getAttribute("data-product-annual-discounted-price");
  } else {
    return frequencyType === "monthly"
      ? productEl.getAttribute("data-product-monthly-price")
      : productEl.getAttribute("data-product-annual-price");
  }
}

function getProductMonthlyPrice(productEl) {
  if (
    shouldApplyDiscount() &&
    productEl.dataset.productId !== getFirstSelectedSubscriptionProduct()
  ) {
    return frequencyType === "monthly"
      ? productEl.getAttribute("data-product-monthly-discounted-price")
      : productEl.getAttribute("data-product-annual-discounted-monthly-price");
  } else {
    return frequencyType === "monthly"
      ? productEl.getAttribute("data-product-monthly-price")
      : productEl.getAttribute("data-product-annual-monthly-price");
  }
}

function updateCheckoutSummaryUI() {
  let checkoutSummary = "";

  let total_price = 0;

  selectedProducts.forEach((product) => {
    const productEl = document.querySelector(
      `.product[data-product-id="${product.id}"]`,
    );

    const productName = productEl.getAttribute("data-product-name");
    const productPrice = getProductTotalPrice(productEl);

    total_price += parseFloat(productPrice.replace(getUserCurrency(), ""));

    checkoutSummary += `
    <div class="space-y-4 mb-8 divide-y divide-primary-700/30">
    <div class="flex justify-between items-center text-primary-200 py-3">
    <span class="capitalize">${productName}</span>
    <span>${getUserCurrency()}${productPrice}</span>
    </div>
    </div>
    `;
  });

  checkoutSummaryItemsSection.innerHTML = checkoutSummary;

  if (checkoutButton) {
    if (selectedProducts.length === 0) {
      checkoutButton.disabled = true;
    } else {
      checkoutButton.disabled = false;
    }
  }
  let totalPriceEl = document.querySelector(
    ".checkoutSummarySection__totalPrice",
  );
  totalPriceEl.textContent = `${getUserCurrency()}${total_price.toFixed(2)}`;
}

function pushOrRemoveProduct(id, productType) {
  const productIndex = selectedProducts.findIndex(
    (product) => product.id === id,
  );

  if (productIndex === -1) {
    selectedProducts.push({ id: id, type: productType });
  } else {
    if (authenticatedActiveSubscriptionTypeInput) {
      console.log(authenticatedActiveSubscriptionTypeInput.value);
      const activeSubscriptionType =
        authenticatedActiveSubscriptionTypeInput.value;
      if (activeSubscriptionType) {
        console.log("Active subscription type: ", activeSubscriptionType);
        const product = document.querySelector(
          `.product[data-product-id="${id}"]`,
        );
        const currentPlanDisclaimer = product.querySelector(
          ".product__currentPlanDisclaimer",
        );

        if (currentPlanDisclaimer) {
          return;
        }
      }
    }
    selectedProducts.splice(productIndex, 1);
  }
}

function toggleSoccerDiscountBar() {
  const soccerDiscountDisclaimerEls = document.querySelectorAll(
    ".product__sportPlanDisclaimer",
  );

  soccerDiscountDisclaimerEls.forEach((el) => {
    const productId = el.getAttribute("data-product-id");

    if (
      shouldApplyDiscount() &&
      productId !== getFirstSelectedSubscriptionProduct()
    ) {
      console.log(
        `Chosen product ID: ${productId}. First selected product ID: ${getFirstSelectedSubscriptionProduct()}`,
      );
      el.classList.remove("hidden");
    } else {
      el.classList.add("hidden");
    }
  });
}

function updateClickedProductUI(
  productElement,
  productCheckboxContainer,
  productCheckboxEl,
) {
  if (productElement.classList.contains("selected")) {
    if (authenticatedActiveSubscriptionTypeInput) {
      console.log(authenticatedActiveSubscriptionTypeInput.value);
      const activeSubscriptionType =
        authenticatedActiveSubscriptionTypeInput.value;
      if (activeSubscriptionType) {
        const currentPlanDisclaimer = productElement.querySelector(
          ".product__currentPlanDisclaimer",
        );
        if (currentPlanDisclaimer) {
          return;
        }
      }
    }

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
