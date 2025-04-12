function initDateItems() {
  const dateElements = document.querySelectorAll(
    ".dateItem, .dateItem--short, .dateItem--hours",
  );

  dateElements.forEach((item) => {
    const dateStr = item.getAttribute("data-date");
    const date = new Date(dateStr);

    if (isNaN(date)) return;

    if (item.classList.contains("dateItem")) {
      // Original format: YYYY-MM-DD, HH:mm
      item.textContent = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}, ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    } else if (item.classList.contains("dateItem--short")) {
      // Short format: Wed 04 Jul (D d M)
      item.textContent = date
        .toLocaleDateString("en-US", {
          weekday: "short",
          day: "2-digit",
          month: "short",
        })
        .replace(/,/g, "");
    } else if (item.classList.contains("dateItem--hours")) {
      // Time format: 15:30 (H:i)
      item.textContent = `${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
    }
  });
}

export { initDateItems };
