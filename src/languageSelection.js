const languageSelectionButton = document.getElementById(
  "languageSelectionButton",
);

function initLanguageSelectionButton() {
  if (!languageSelectionButton) return;

  const dropdown = languageSelectionButton.nextElementSibling;
  const buttonIcon = languageSelectionButton.querySelector(".icon");

  languageSelectionButton.addEventListener("click", () => {
    dropdown.classList.toggle("hidden");
    buttonIcon.classList.toggle("rotate-180");
  });
}

export default initLanguageSelectionButton;
