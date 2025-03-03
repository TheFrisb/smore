const dateItems = document.querySelectorAll(".dateItem");

function initDateItems() {
  if (!dateItems) return;

  dateItems.forEach(function (item) {
    // Get the ISO datetime string from the data-date attribute
    const dateStr = item.getAttribute("data-date");

    // Create a Date object from the string
    const date = new Date(dateStr);

    // Check if the date is valid
    if (!isNaN(date)) {
      // Extract date components
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are 0-based
      const day = String(date.getDate()).padStart(2, "0");

      // Extract time components
      const hours = String(date.getHours()).padStart(2, "0");
      const minutes = String(date.getMinutes()).padStart(2, "0");

      // Format the date and time as "YYYY-MM-DD HH:MM"
      const formattedDate = `${year}-${month}-${day}, ${hours}:${minutes}`;

      // Update the text content
      item.textContent = formattedDate;
    }
  });
}

export { initDateItems };
