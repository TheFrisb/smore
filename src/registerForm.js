const registerForm = document.getElementById("registerForm");

function initRegisterForm() {
  if (!registerForm) {
    return;
  }
  const registerButton = document.getElementById("registerButton");

  registerForm.addEventListener("submit", function (e) {
    registerButton.disabled = true;
  });
}

export { initRegisterForm };
