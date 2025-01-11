import { initMobileMenu } from "./menu/main";
import initProducts from "./products/products";

document.addEventListener("DOMContentLoaded", () => {
  console.log("Hello World");
  initMobileMenu();
  initProducts();
});
