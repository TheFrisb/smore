export function initMobileMenu() {
  const menuButton = document.querySelector("#mobileMenuButton");
  const menu = document.querySelector("#mobileMenuDropdownContainer");

  if (!menuButton || !menu) return;

  menuButton.addEventListener("click", () => {
    if (menu.classList.contains("active")) {
      hideMenu();
      toggleCloseIcon();
    } else {
      showMenu();
      toggleCloseIcon();
    }
  });

  function showMenu() {
    menu.classList.add("max-h-screen", "opacity-100", "active");
    menu.classList.remove("max-h-0", "opacity-0", "opacity-hidden");
  }

  function hideMenu() {
    menu.classList.add("max-h-0", "opacity-0", "opacity-hidden");
    menu.classList.remove("max-h-screen", "opacity-100", "active");
  }

  function toggleCloseIcon() {
    const closeIcon = menuButton.querySelector(".closeIcon");
    const hamburgerIcon = menuButton.querySelector(".hamburgerIcon");

    hamburgerIcon.classList.toggle("hidden");
    closeIcon.classList.toggle("hidden");
  }
}
