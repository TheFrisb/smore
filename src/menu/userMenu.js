export function initUserMobileMenu() {
  const menuButton = document.querySelector("#userDashboardMenuDropdown");
  const menu = document.querySelector("#userDashboardMenu");

  if (!menuButton || !menu) {
    return;
  }

  // if screen is larger than 768px, do not show the mobile menu

  menuButton.addEventListener("click", () => {
    if (window.innerWidth > 1020) {
      return;
    }
    if (menu.classList.contains("active")) {
      menuButton.classList.remove(
        "mb-6",
        "pb-6",
        "border-b",
        "border-primary-700/30",
      );
      hideMenu();
      toggleCloseIcon();
    } else {
      menuButton.classList.add(
        "mb-6",
        "pb-6",
        "border-b",
        "border-primary-700/30",
      );
      showMenu();
      toggleCloseIcon();
    }
  });

  function showMenu() {
    menu.classList.add("h-auto", "active");
    menu.classList.remove("h-0");
  }

  function hideMenu() {
    menu.classList.add("h-0");
    menu.classList.remove("h-auto", "active");
  }

  function toggleCloseIcon() {
    const toggleIcon = menuButton.querySelector(".toggleIcon");
    toggleIcon.classList.toggle("rotate-180");
  }
}
