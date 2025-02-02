import { initMobileMenu } from "./menu/menu";
import initProducts from "./products/products";
import Aos from "aos/src/js/aos";
import { initCopyButtons } from "./referral/copyButton";
import { initCloseButtons } from "./closeButton";
import initWithdrawalRequest from "./withdrawals/withdrawals";
import initFaq from "./faq/faq";
import { initUserMobileMenu } from "./menu/userMenu";
import initWithdrawalHistory from "./withdrawals/withdrawalHistory";
import { initResendEmailButtons } from "./resendEmailButton";
import initLoadMorePredictionsButton from "./loadMorePredictionsButton";
import { initLoginForm } from "./loginForm";
import { initRegisterForm } from "./registerForm";
import initLanguageSelectionButton from "./languageSelection";

document.addEventListener("DOMContentLoaded", () => {
  Aos.init();
  initMobileMenu();
  initProducts();
  initCopyButtons();
  initCloseButtons();

  initWithdrawalRequest();
  initFaq();
  initUserMobileMenu();

  initWithdrawalHistory();
  initResendEmailButtons();
  initLoadMorePredictionsButton();

  initLoginForm();
  initRegisterForm();

  initLanguageSelectionButton();
});
