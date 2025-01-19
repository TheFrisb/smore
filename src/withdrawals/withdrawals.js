import { getCsrfToken } from "../utils";
import { Notyf } from "notyf";

const withdrawalPayoutMethodEls = document.querySelectorAll(
  ".withdrawalPayoutMethod",
);
const requestWithdrawalBtn = document.querySelector("#requestWithdrawalButton");
let activeMethod;

let notyf = new Notyf({
  duration: 5000,
  position: {
    x: "right",
    y: "top",
  },
});

function initWithdrawalRequest() {
  if (!withdrawalPayoutMethodEls.length) return;
  console.log("Withdrawal request form found!");

  withdrawalPayoutMethodEls.forEach((payoutMethodEl) => {
    payoutMethodEl.addEventListener("click", () => {
      const methodType = payoutMethodEl.getAttribute("data-method-type");
      const sectionSelector = payoutMethodEl.getAttribute(
        "data-section-selector",
      );
      const sectionEl = document.querySelector(sectionSelector);

      hideAllSections();
      sectionEl.classList.remove("hidden");

      markAllMethodsAsInactive();
      markMethodAsActive(payoutMethodEl);

      activeMethod = methodType;
    });
  });

  requestWithdrawalBtn.addEventListener("click", function (button) {
    if (!activeMethod) {
      return;
    }

    if (button.disabled) {
      return;
    }

    button.disabled = true;
    makeRequest().then((r) => (button.disabled = false));
  });
}

async function makeRequest() {
  const url = "/api/accounts/request-withdrawal/";

  const redirectUrl = document.querySelector("#redirectUrl").value;

  const data = getData();

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
    },
    body: JSON.stringify(data),
  });

  const result = await response.json();

  if (response.ok) {
    window.location.href = redirect;
  } else {
    if (result.errors && Array.isArray(result.errors)) {
      result.errors.forEach((error) => {
        if (error.detail) {
          notyf.error(error.detail);
        }
      });
    } else {
      notyf.error("An unknown error occurred. Please try again.");
    }
  }
}

function getData() {
  if (activeMethod === "bank") {
    return {
      amount: parseFloat(
        document.querySelector("#withdrawalRequest__amount").value,
      ),
      payout_type: activeMethod,
      full_name: document.querySelector(
        "#requestWithdrawal__bankMethod__fullName",
      ).value,
      email: document.querySelector("#requestWithdrawal__bankMethod__email")
        .value,
      country: document.querySelector("#requestWithdrawal__bankMethod__country")
        .value,
      iban: document.querySelector("#requestWithdrawal__bankMethod__iban")
        .value,
    };
  }

  if (activeMethod === "payoneer") {
    return {
      amount: parseFloat(
        document.querySelector("#withdrawalRequest__amount").value,
      ),
      payout_type: activeMethod,
      full_name: document.querySelector(
        "#requestWithdrawal__payoneerMethod__fullName",
      ).value,
      payoneer_customer_id: document.querySelector(
        "#requestWithdrawal__payoneerMethod__payoneer_customer_id",
      ).value,
      email: document.querySelector("#requestWithdrawal__payoneerMethod__email")
        .value,
    };
  }

  if (activeMethod === "cryptocurrency") {
    return {
      amount: parseFloat(
        document.querySelector("#withdrawalRequest__amount").value,
      ),
      payout_type: activeMethod,
      cryptocurrency_address: document.querySelector(
        "#requestWithdrawal__cryptoMethod__address",
      ).value,
    };
  }
}

function markAllMethodsAsInactive() {
  withdrawalPayoutMethodEls.forEach((el) => {
    el.classList.remove("border-secondary-500/30", "text-white");
    el.classList.add("border-primary-700/50", "text-primary-300");
  });
}

function markMethodAsActive(el) {
  el.classList.remove("border-primary-700/50");
  el.classList.add("border-secondary-500/30", "text-white");
}

function hideAllSections() {
  const elements = document.querySelectorAll(".requestWithdrawal__formSection");
  elements.forEach((el) => {
    el.classList.add("hidden");
  });
}

export default initWithdrawalRequest;
