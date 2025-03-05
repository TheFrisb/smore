const peekButtons = document.querySelectorAll(".peekBtn");

function initPeekButtons() {
  if (!peekButtons) return;

  peekButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const passwordInput = button.previousElementSibling;
      const eyeCloseEl = button.querySelector(".eyeClose");
      const eyeOpenEl = button.querySelector(".eyeOpen");

      if (eyeCloseEl.classList.contains("hidden")) {
        eyeCloseEl.classList.remove("hidden");
        eyeOpenEl.classList.add("hidden");
        passwordInput.type = "text";
      } else {
        eyeCloseEl.classList.add("hidden");
        eyeOpenEl.classList.remove("hidden");
        passwordInput.type = "password";
      }
    });
  });
}

export { initPeekButtons };
