import { initMobileMenu } from "./menu/main";
import initProducts from "./products/products";
import Aos from "aos/src/js/aos";

document.addEventListener("DOMContentLoaded", () => {
  Aos.init();

  initMobileMenu();
  initProducts();
});
