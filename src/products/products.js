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
    const checkoutSummaryMode =
      checkoutSummarySection.querySelector("#subscriptionMode");

    if (toggleButton.classList.contains("left-1")) {
      toggleButton.classList.remove("left-1");
      toggleButton.classList.add("right-1");
      frequencyType = "year";

      annualLabelEl.classList.remove("text-primary-300");
      annualLabelEl.classList.add("text-white");
      monthlyLabelEl.classList.add("text-primary-300");
      monthlyLabelEl.classList.remove("text-white");

      checkoutSummaryMode.textContent = checkoutSummaryMode.getAttribute(
        "data-translated-yearly",
      );

      if (authenticatedActiveSubscriptionTypeInput) {
        console.log(authenticatedActiveSubscriptionTypeInput.value);
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
      frequencyType = "month";

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
    const yearlyNoDiscountPrice = product.querySelector(
      ".product__yearlyPriceNoDiscount",
    );

    let monthlyPrice = product.getAttribute("data-product-monthly-price");
    let yearlyPrice = product.getAttribute("data-product-annual-monthly-price");

    let price = frequencyType === "month" ? monthlyPrice : yearlyPrice;

    if (frequencyType === "year") {
      yearlyNoDiscountPrice.classList.remove("hidden");
    } else {
      yearlyNoDiscountPrice.classList.add("hidden");
    }

    priceEl.textContent = `€${price}`;
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
      if (product.classList.contains("notSelectable")) {
        return;
      }

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

  if (authenticatedActiveSubscriptionTypeInput) {
    console.log(authenticatedActiveSubscriptionTypeInput.value);
    const activeSubscriptionType =
      authenticatedActiveSubscriptionTypeInput.value;
    if (activeSubscriptionType) {
      const elsToUpdate = document.querySelectorAll(
        ".product__currentPlanDisclaimer",
      );
      elsToUpdate.forEach((el) => {
        el.click();
      });
    }

    if (activeSubscriptionType && activeSubscriptionType === "yearly") {
      chooseSubscriptionFrequencyButton.click();
    }
  }

  if (checkoutButton) {
    checkoutButton.addEventListener("click", () => {
      if (checkoutButton.disabled) {
        return;
      }

      checkoutButton.disabled = true;
      const buttonSpinner = checkoutButton.querySelector(".buttonSpinner");
      buttonSpinner.classList.remove("hidden");
      const csrfToken = getCsrfToken();
      const url = checkoutButton.getAttribute("data-url");

      fetch(url, {
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
        .then((response) => {
          if (!response.ok) {
            throw new Error(
              `Status: ${response.status}. Body: ${response.body}`,
            );
          }
          return response.json();
        })
        .then((data) => {
          if (data.url) {
            window.location.href = data.url;
          } else {
            setTimeout(() => {
              window.location.href = "/accounts/manage-plan/";
            }, 5000);
          }
        })
        .catch((error) => {
          console.error("Error:", error);
          notyf.error(
            "Something went wrong. Please contact support if the issue persists.",
          );
          checkoutButton.disabled = false;
          buttonSpinner.classList.add("hidden");
        });
    });
  }
}

function updateCheckoutSummaryUI() {
  let checkoutSummary = "";

  let total_price = 0;

  selectedProducts.forEach((productId) => {
    const productEl = document.querySelector(
      `.product[data-product-id="${productId}"]`,
    );
    const productName = productEl.getAttribute("data-product-name");
    const productPrice =
      frequencyType === "month"
        ? productEl.getAttribute("data-product-monthly-price")
        : productEl.getAttribute("data-product-annual-price");

    total_price += parseFloat(productPrice.replace("€", ""));

    checkoutSummary += `
    <div class="space-y-4 mb-8 divide-y divide-primary-700/30">
    <div class="flex justify-between items-center text-primary-200 py-3">
    <span class="capitalize">${productName}</span>
    <span>€${productPrice}</span>
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
  totalPriceEl.textContent = `€${total_price.toFixed(2)}`;
}

function pushOrRemoveProduct(id) {
  const productIndex = selectedProducts.indexOf(id);

  if (productIndex === -1) {
    selectedProducts.push(id);
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
