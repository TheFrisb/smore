const copyButtons = document.querySelectorAll(".copyButton");

function initCopyButtons() {
  if (!copyButtons.length) return;

  copyButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const dataToCopy = button.getAttribute("data-value");
      const checkmarkIcon = button.querySelector(".checkmarkIcon");
      const copyIcon = button.querySelector(".copyIcon");

      navigator.clipboard.writeText(dataToCopy).then(() => {
        checkmarkIcon.classList.remove("hidden");
        copyIcon.classList.add("hidden");

        setTimeout(() => {
          checkmarkIcon.classList.add("hidden");
          copyIcon.classList.remove("hidden");
        }, 1000);
      });
    });
  });
}

export { initCopyButtons };
