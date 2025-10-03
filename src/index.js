import { initMobileMenu } from "./menu/menu";
import Aos from "aos/src/js/aos";
import { initCopyButtons } from "./referral/copyButton";
import { initCloseButtons } from "./closeButton";
import initWithdrawalRequest from "./withdrawals/withdrawals";
import initFaq from "./faq/faq";
import { initUserMobileMenu } from "./menu/userMenu";
import initWithdrawalHistory from "./withdrawals/withdrawalHistory";
import { initResendEmailButtons } from "./resendEmailButton";
import { initLoginForm } from "./loginForm";
import { initRegisterForm } from "./registerForm";
import initLanguageSelectionButton from "./languageSelection";
import { initContactPixelEvent } from "./contact_pixel_event";
import { initLeadPixelEvent } from "./lead_pixel_event";
import initAiAssistant from "./aiAssistant";
import { initDateItems } from "./dateItem";
import { initPeekButtons } from "./passwordPeek";
import initSportToggler from "./sportToggler";
import { initLoadMorePredictionsButton } from "./history/loadMoreButton";
import { initStakeButtons } from "./stakeModal";
import { initPlanPage } from "./plans/planPage";

document.addEventListener("DOMContentLoaded", () => {
  Aos.init();
  initDateItems();
  initMobileMenu();
  initCopyButtons();
  initCloseButtons();
  initPlanPage();
  initWithdrawalRequest();
  initFaq();
  initUserMobileMenu();

  initWithdrawalHistory();
  initResendEmailButtons();

  initLoadMorePredictionsButton();

  initLoginForm();
  initRegisterForm();

  initLanguageSelectionButton();

  initContactPixelEvent();
  initLeadPixelEvent();

  initAiAssistant();
  initPeekButtons();

  initSportToggler();
  initStakeButtons();

  const container = document.querySelector("#aiAssistantRelativeContainer");
  const aiAssistant = document.querySelector("#aiAssistantIcon");

  if (container && aiAssistant) {
    function updatePosition() {
      const rect = container.getBoundingClientRect();
      document.body.style.setProperty(
        "--container-left",
        `${rect.left + 16}px`,
      );
    }

    // Update position on load and resize
    window.addEventListener("resize", updatePosition);
    updatePosition();
    aiAssistant.classList.remove("invisible");
  }
});
