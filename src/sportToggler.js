function initSportToggler() {
  const dropdownButtons = document.querySelectorAll(".sportDropdownButton");

  if (!dropdownButtons) {
    return;
  }

  dropdownButtons.forEach((button) => {
    const dropdownEl = button.parentElement.nextElementSibling;
    console.log(dropdownEl);

    button.addEventListener("click", () => {
      dropdownEl.classList.toggle("hidden");
    });
  });
}

export default initSportToggler;
