function initWithdrawalHistory() {
  const withdrawalHistoryItems = document.querySelectorAll(
    ".withdrawalRequestItem",
  );

  if (!withdrawalHistoryItems.length) {
    return;
  }

  withdrawalHistoryItems.forEach((item) => {
    item.addEventListener("click", () => {
      const icon = item.querySelector(".withdrawalRequestItem__icon");
      const content = item.querySelector(".withdrawalRequestItem__content");

      icon.classList.toggle("rotate-180");
      content.classList.toggle("hidden");
    });
  });
}

export default initWithdrawalHistory;
