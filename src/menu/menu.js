export function initMobileMenu() {
  const menuButton = document.querySelector("#mobileMenuButton");
  const menu = document.querySelector("#mobileMenuDropdownContainer");
  const mobileMenuDropdowns = document.querySelectorAll(".mobileMenuDropdown");

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

  mobileMenuDropdowns.forEach((dropdown) => {
    dropdown.addEventListener("click", (event) => {
      event.stopPropagation();
      const target = event.currentTarget;
      const dropdownContent = target.nextElementSibling;
      const icon = target.querySelector(".icon");

      if (dropdownContent.classList.contains("max-h-0")) {
        dropdownContent.classList.remove("max-h-0", "opacity-0");
        dropdownContent.classList.add(
          "max-h-64",
          "opacity-100",
          "mt-1",
          "mb-4",
        );
      } else {
        dropdownContent.classList.add("max-h-0", "opacity-0");
        dropdownContent.classList.remove(
          "max-h-64",
          "opacity-100",
          "mt-1",
          "mb-4",
        );
      }

      icon.classList.toggle("rotate-180");
    });
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
