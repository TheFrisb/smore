import { getCsrfToken } from "./utils";

const leadButtons = document.querySelectorAll(".fireLeadEventButton");

function initLeadPixelEvent() {
  if (!leadButtons) return;

  leadButtons.forEach((element) => {
    element.addEventListener("click", () => {
      fetch("/facebook/pixel/events/lead/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
      }).then((r) => console.log("Lead pixel event request sent"));
    });
  });
}

export { initLeadPixelEvent };
