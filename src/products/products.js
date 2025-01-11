import { getCsrfToken } from "../utils";

const products = document.querySelectorAll(".product");
const checkoutSummarySection = document.querySelector(
  ".checkoutSummarySection",
);

const checkoutSummaryItemsSection = checkoutSummarySection.querySelector(
  ".checkoutSummary__items",
);

const checkoutButton = document.querySelector("#checkoutButton");

let selectedProducts = [];

function initProducts() {
  products.forEach((product) => {
    product.addEventListener("click", () => {
      const productId = product.getAttribute("data-product-id");
      const productPrice = product.getAttribute("data-product-price");
      const discountedProductPrice = product.getAttribute(
        "data-discounted-product-price",
      );
      const productName = product.getAttribute("data-product-name");

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
      updateProductDiscountUI();

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
      body: JSON.stringify({ products: selectedProducts.map(Number) }),
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

  selectedProducts.forEach((productId) => {
    const productEl = document.querySelector(
      `.product[data-product-id="${productId}"]`,
    );
    const productName = productEl.getAttribute("data-product-name");
    const productPrice = productEl.querySelector(".product__price").textContent;

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
    <div class="flex justify-between items-center text-emerald-500 py-3">
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
}

function pushOrRemoveProduct(id) {
  const productIndex = selectedProducts.indexOf(id);

  if (productIndex === -1) {
    selectedProducts.push(id);
  } else {
    selectedProducts.splice(productIndex, 1);
  }
}

function updateProductDiscountUI() {
  const products = document.querySelectorAll(".product");

  products.forEach((product) => {
    const productPriceElement = product.querySelector(".product__price");
    const productDiscountedPriceElement = product.querySelector(
      ".product__discountSection",
    );
    console.log(productPriceElement);
    console.log(productDiscountedPriceElement);

    if (selectedProducts.length === 0) {
      productPriceElement.textContent =
        product.getAttribute("data-product-price");
      productDiscountedPriceElement.classList.add("hidden");
    } else {
      if (selectedProducts[0] === product.getAttribute("data-product-id")) {
        return;
      }
      productPriceElement.textContent = product.getAttribute(
        "data-discounted-product-price",
      );
      productDiscountedPriceElement.classList.remove("hidden");
    }
  });
}

function updateClickedProductUI(
  productElement,
  productCheckboxContainer,
  productCheckboxEl,
) {
  if (productElement.classList.contains("selected")) {
    productElement.classList.remove("selected");
    productElement.classList.remove(
      "bg-emerald-500/20",
      "border-emerald-500/50",
    );
    productElement.classList.add(
      "hover:border-emerald-500/30",
      "hover:shadow-lg",
      "hover:shadow-emerald-500/10",
      "bg-primary-800/50",
    );

    productCheckboxContainer.classList.remove(
      "bg-emerald-500",
      "border-emerald-500",
    );
    productCheckboxEl.classList.add("hidden");
  } else {
    productElement.classList.add("selected");
    productElement.classList.add("bg-emerald-500/20", "border-emerald-500/50");
    productElement.classList.remove(
      "hover:border-emerald-500/30",
      "hover:shadow-lg",
      "hover:shadow-emerald-500/10",
      "bg-primary-800/50",
    );

    productCheckboxContainer.classList.add(
      "bg-emerald-500",
      "border-emerald-500",
    );
    productCheckboxEl.classList.remove("hidden");
  }
}

export default initProducts;
