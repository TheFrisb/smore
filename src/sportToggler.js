function initSportToggler() {
  const dropdownButtons = document.querySelectorAll(".sportDropdownButton");

  if (!dropdownButtons) {
    return;
  }

  dropdownButtons.forEach((button) => {
    const dropdownEl = button.parentElement.nextElementSibling;
    let handleClickOutside = null;
    let handleScroll = null;

    button.addEventListener("click", () => {
      const isHidden = dropdownEl.classList.toggle("hidden");
      
      if (!isHidden) {
        // Dropdown is now open, set up event listeners
        handleClickOutside = (event) => {
          if (!dropdownEl.contains(event.target) && !button.contains(event.target)) {
            dropdownEl.classList.add("hidden");
            document.removeEventListener("click", handleClickOutside);
            window.removeEventListener("scroll", handleScroll);
            handleClickOutside = null;
            handleScroll = null;
          }
        };
        document.addEventListener("click", handleClickOutside);
        
        handleScroll = () => {
          dropdownEl.classList.add("hidden");
          window.removeEventListener("scroll", handleScroll);
          document.removeEventListener("click", handleClickOutside);
          handleClickOutside = null;
          handleScroll = null;
        };
        window.addEventListener("scroll", handleScroll);
      } else {
        // Dropdown is now closed via button, clean up listeners
        if (handleClickOutside) {
          document.removeEventListener("click", handleClickOutside);
          handleClickOutside = null;
        }
        if (handleScroll) {
          window.removeEventListener("scroll", handleScroll);
          handleScroll = null;
        }
      }
    });
  });
}

export default initSportToggler;