import { getCookie, getCsrfToken, getUserTimezoneString } from "../utils";

function setCookie(name, value, days = 30) {
  const date = new Date();
  date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value}; expires=${date.toUTCString()}; path=/`;
}

export function initSetTimezone() {
  const timezoneSet = getCookie("timezone_set");
  if (!timezoneSet) {
    const userTz = getUserTimezoneString();
    const formData = new FormData();
    formData.append("timezone", userTz);
    fetch("/api/set-timezone/", {
      method: "POST",
      body: formData,
      credentials: "include",
      headers: { "X-CSRFToken": getCsrfToken() },
    }).then((response) => {
      if (response.ok) {
        setCookie("timezone_set", "1", 30);
      }
    });
  }
}
