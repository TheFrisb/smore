const loginForm = document.getElementById("loginForm");

function initLoginForm() {
  if (!loginForm) {
    return;
  }

  const loginButton = document.getElementById("loginButton");

  loginForm.addEventListener("submit", function (e) {
    // Disable the submit button to prevent multiple submissions
    loginButton.disabled = true;
  });
}

export { initLoginForm };
