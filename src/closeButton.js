export function initCloseButtons() {
  const closeButtons = document.querySelectorAll(".closeButton");

  closeButtons.forEach((closeButton) => {
    closeButton.addEventListener("click", () => {
      const selector = closeButton.getAttribute("data-close-element-selector");
      const element = document.querySelector(selector);

      element.classList.add("hidden");
    });
  });
}
