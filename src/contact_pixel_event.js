import { getCsrfToken } from "./utils";

const contactActionElements = document.querySelectorAll(".contactAction");

function initContactPixelEvent() {
  if (!contactActionElements) return;

  contactActionElements.forEach((element) => {
    element.addEventListener("click", () => {
      // make a post request to /facebook/pixel/events/contact
      fetch("/facebook/pixel/events/contact/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
      }).then((r) => console.log("Contact pixel event request sent"));
    });
  });
}

export { initContactPixelEvent };
