import { clearSelectedProductId } from "./checkout";

function initPlanProductTab() {
  const tabs = document.querySelectorAll(".managePlanProductTabButton");
  const toggleableContents = document.querySelectorAll(
    ".toggleableProductContent",
  );

  if (tabs.length === 0 || toggleableContents.length === 0) {
    return;
  }

  function removeActiveClassFromAllTabs() {
    tabs.forEach((tab) => {
      tab.classList.remove("active");
    });

    toggleableContents.forEach((content) => {
      content.classList.remove("active");
    });
  }

  function activateTab(tab) {
    const productId = tab.getAttribute("data-product-id");

    const tabToActivate = document.querySelector(
      `.managePlanProductTabButton[data-product-id="${productId}"]`,
    );

    const contentToActivate = document.querySelector(
      `.toggleableProductContent[data-product-id="${productId}"]`,
    );

    removeActiveClassFromAllTabs();

    if (tabToActivate && contentToActivate) {
      tabToActivate.classList.add("active");
      contentToActivate.classList.add("active");

      clearSelectedProductId();
    }
  }

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      activateTab(tab);
    });
  });
}

export { initPlanProductTab };
