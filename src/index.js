import { initMobileMenu } from "./menu/menu";
import initProducts from "./products/products";
import Aos from "aos/src/js/aos";
import { initCopyButtons } from "./referral/copyButton";
import { initCloseButtons } from "./closeButton";

document.addEventListener("DOMContentLoaded", () => {
  Aos.init();
  initMobileMenu();
  initProducts();
  initCopyButtons();
  initCloseButtons();
});
