import { getCsrfToken } from "./utils";
import { Notyf } from "notyf";

const buttons = document.querySelectorAll(".resendEmailButton");
let notyf = new Notyf({
  duration: 5000,
  position: {
    x: "right",
    y: "top",
  },
});

function initResendEmailButtons() {
  if (!buttons.length) {
    return;
  }

  buttons.forEach((button) => {
    button.addEventListener("click", () => {
      fetch("/api/accounts/resend-email-confirmation/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
      }).then((response) => {
        if (response.ok) {
          notyf.success(
            "We've resent the email confirmation link. Please check your inbox.",
          );
        } else {
          notyf.error(
            "An unexpected error has occured. Please try again later.",
          );
        }
      });
    });
  });
}

export { initResendEmailButtons };
