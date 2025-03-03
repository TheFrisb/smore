/**
 * Safely retrieve a cookie value by name.
 *
 * @param {string} name - The name of the cookie (e.g., "csrftoken").
 * @returns {string|null} - The cookie value if found, otherwise null.
 */
function getCookie(name) {
  if (!document.cookie) return null;

  const cookies = document.cookie.split(";");
  for (let i = 0; i < cookies.length; i++) {
    const cookie = cookies[i].trim();
    // Check if this cookie starts with "<name>="
    if (cookie.substring(0, name.length + 1) === `${name}=`) {
      return decodeURIComponent(cookie.substring(name.length + 1));
    }
  }
  return null;
}

/**
 * Retrieve Django's CSRF token.
 *
 * @returns {string|null} - The CSRF token if found, otherwise null.
 */
function getCsrfToken() {
  return getCookie("csrftoken");
}

function formatTime(date = new Date()) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function getElementFromAttribute(elementWithAttribute, attributeToLookUp) {
  const selector = elementWithAttribute.getAttribute(attributeToLookUp);

  if (!selector) {
    throw new Error(
      `No attribute found with name: ${attributeToLookUp} on element: ${elementWithAttribute}`,
    );
  }

  const foundElement = document.querySelector(selector);

  if (!foundElement) {
    throw new Error(`No element found with selector: ${selector}`);
  }

  return foundElement;
}

function formatIsoString(isoString) {
  // format to YYYY-MM-DD HH:MM
  const date = new Date(isoString);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, "0");
  const day = String(date.getUTCDate()).padStart(2, "0");
  const hour = String(date.getUTCHours()).padStart(2, "0");
  const minute = String(date.getUTCMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

export {
  getCookie,
  getCsrfToken,
  formatTime,
  getElementFromAttribute,
  formatIsoString,
};
