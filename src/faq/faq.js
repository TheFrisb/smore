const faqWrapperEls = document.querySelectorAll(".faqItemWrapper");

function initFaq() {
  if (!faqWrapperEls.length) {
    return;
  }

  faqWrapperEls.forEach((faqWrapperEl) => {
    faqWrapperEl.addEventListener("click", () => {
      const faqButton = faqWrapperEl.querySelector(".faqItemButton");
      const faqItemIcon = faqWrapperEl.querySelector(".faqItemIcon");
      const faqItemContent = faqWrapperEl.querySelector(".faqItemContent");

      if (faqWrapperEl.classList.contains("active")) {
        makeInactive(faqWrapperEl, faqButton, faqItemIcon, faqItemContent);
      } else {
        makeActive(faqWrapperEl, faqButton, faqItemIcon, faqItemContent);
      }
    });
  });
}

function makeActive(faqWrapperEl, faqButton, faqItemIcon, faqItemContent) {
  faqWrapperEl.classList.add(
    "active",
    "border-secondary-500/30",
    "bg-primary-800/70",
  );
  faqWrapperEl.classList.remove(
    "border-primary-700/30",
    "hover:border-secondary-500/20",
  );

  faqButton.classList.add("bg-primary-800/70");
  faqButton.classList.remove(
    "group-hover:bg-primary-800/70",
    "bg-primary-800/50",
  );

  faqItemIcon.classList.add("rotate-180");

  faqItemContent.classList.add("max-h-96");
  faqItemContent.classList.remove("max-h-0");
}

function makeInactive(faqWrapperEl, faqButton, faqItemIcon, faqItemContent) {
  faqWrapperEl.classList.remove(
    "active",
    "border-secondary-500/30",
    "bg-primary-800/70",
  );
  faqWrapperEl.classList.add(
    "border-primary-700/30",
    "hover:border-secondary-500/20",
  );

  faqButton.classList.remove("bg-primary-800/70");
  faqButton.classList.add("group-hover:bg-primary-800/70", "bg-primary-800/50");

  faqItemIcon.classList.remove("rotate-180");

  faqItemContent.classList.remove("max-h-96", "overflow-auto");
  faqItemContent.classList.add("max-h-0", "overflow-hidden");
}

export default initFaq;
