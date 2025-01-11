/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	"use strict";
/******/ 	var __webpack_modules__ = ({

/***/ "./src/index.js":
/*!**********************!*\
  !*** ./src/index.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _menu_main__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./menu/main */ \"./src/menu/main.js\");\n/* harmony import */ var _products_products__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! ./products/products */ \"./src/products/products.js\");\n\n\ndocument.addEventListener(\"DOMContentLoaded\", function () {\n  console.log(\"Hello World\");\n  (0,_menu_main__WEBPACK_IMPORTED_MODULE_0__.initMobileMenu)();\n  (0,_products_products__WEBPACK_IMPORTED_MODULE_1__[\"default\"])();\n});\n\n//# sourceURL=webpack://smore/./src/index.js?");

/***/ }),

/***/ "./src/menu/main.js":
/*!**************************!*\
  !*** ./src/menu/main.js ***!
  \**************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   initMobileMenu: () => (/* binding */ initMobileMenu)\n/* harmony export */ });\nfunction initMobileMenu() {\n  var menuButton = document.querySelector(\"#mobileMenuButton\");\n  var menu = document.querySelector(\"#mobileMenuDropdownContainer\");\n  menuButton.addEventListener(\"click\", function () {\n    if (menu.classList.contains(\"active\")) {\n      hideMenu();\n      toggleCloseIcon();\n    } else {\n      showMenu();\n      toggleCloseIcon();\n    }\n  });\n  function showMenu() {\n    menu.classList.add(\"max-h-screen\", \"opacity-100\", \"active\");\n    menu.classList.remove(\"max-h-0\", \"opacity-0\", \"opacity-hidden\");\n  }\n  function hideMenu() {\n    menu.classList.add(\"max-h-0\", \"opacity-0\", \"opacity-hidden\");\n    menu.classList.remove(\"max-h-screen\", \"opacity-100\", \"active\");\n  }\n  function toggleCloseIcon() {\n    var closeIcon = menuButton.querySelector(\".closeIcon\");\n    var hamburgerIcon = menuButton.querySelector(\".hamburgerIcon\");\n    hamburgerIcon.classList.toggle(\"hidden\");\n    closeIcon.classList.toggle(\"hidden\");\n  }\n}\n\n//# sourceURL=webpack://smore/./src/menu/main.js?");

/***/ }),

/***/ "./src/products/products.js":
/*!**********************************!*\
  !*** ./src/products/products.js ***!
  \**********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\n/* harmony import */ var _utils__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ../utils */ \"./src/utils.js\");\n\nvar products = document.querySelectorAll(\".product\");\nvar checkoutSummarySection = document.querySelector(\".checkoutSummarySection\");\nvar checkoutSummaryItemsSection = checkoutSummarySection.querySelector(\".checkoutSummary__items\");\nvar checkoutButton = document.querySelector(\"#checkoutButton\");\nvar selectedProducts = [];\nfunction initProducts() {\n  products.forEach(function (product) {\n    product.addEventListener(\"click\", function () {\n      var productId = product.getAttribute(\"data-product-id\");\n      var productPrice = product.getAttribute(\"data-product-price\");\n      var discountedProductPrice = product.getAttribute(\"data-discounted-product-price\");\n      var productName = product.getAttribute(\"data-product-name\");\n      var productCheckboxContainer = product.querySelector(\".product__checkboxContainer\");\n      var productCheckboxEl = product.querySelector(\".product__checkboxIcon\");\n      updateClickedProductUI(product, productCheckboxContainer, productCheckboxEl);\n      pushOrRemoveProduct(productId);\n      updateProductDiscountUI();\n      updateCheckoutSummaryUI();\n    });\n  });\n  checkoutButton.addEventListener(\"click\", function () {\n    if (checkoutButton.disabled) {\n      return;\n    }\n    var csrfToken = (0,_utils__WEBPACK_IMPORTED_MODULE_0__.getCsrfToken)();\n    fetch(\"/api/payments/checkout/\", {\n      method: \"POST\",\n      headers: {\n        \"Content-Type\": \"application/json\",\n        \"X-CSRFToken\": csrfToken\n      },\n      body: JSON.stringify({\n        products: selectedProducts.map(Number)\n      })\n    }).then(function (response) {\n      return response.json();\n    }).then(function (data) {\n      window.location.href = data.checkout_url;\n    })[\"catch\"](function (error) {\n      console.error(\"Error:\", error);\n    });\n  });\n}\nfunction updateCheckoutSummaryUI() {\n  var checkoutSummary = \"\";\n  selectedProducts.forEach(function (productId) {\n    var productEl = document.querySelector(\".product[data-product-id=\\\"\".concat(productId, \"\\\"]\"));\n    var productName = productEl.getAttribute(\"data-product-name\");\n    var productPrice = productEl.querySelector(\".product__price\").textContent;\n    checkoutSummary += \"\\n    <div class=\\\"space-y-4 mb-8 divide-y divide-primary-700/30\\\">\\n    <div class=\\\"flex justify-between items-center text-primary-200 py-3\\\">\\n    <span class=\\\"capitalize\\\">\".concat(productName, \"</span>\\n    <span>\").concat(productPrice, \"</span>\\n    </div>\\n    </div>\\n    \");\n  });\n  if (selectedProducts.length > 1) {\n    checkoutSummary += \"\\n    <div class=\\\"flex justify-between items-center text-emerald-500 py-3\\\">\\n    <span>Multi-sport Discount</span>\\n    <span>-$\".concat((selectedProducts.length - 1) * 20, \"</span> \\n    </div>\\n    \");\n  }\n  checkoutSummaryItemsSection.innerHTML = checkoutSummary;\n  if (selectedProducts.length === 0) {\n    checkoutButton.disabled = true;\n  } else {\n    checkoutButton.disabled = false;\n  }\n}\nfunction pushOrRemoveProduct(id) {\n  var productIndex = selectedProducts.indexOf(id);\n  if (productIndex === -1) {\n    selectedProducts.push(id);\n  } else {\n    selectedProducts.splice(productIndex, 1);\n  }\n}\nfunction updateProductDiscountUI() {\n  var products = document.querySelectorAll(\".product\");\n  products.forEach(function (product) {\n    var productPriceElement = product.querySelector(\".product__price\");\n    var productDiscountedPriceElement = product.querySelector(\".product__discountSection\");\n    console.log(productPriceElement);\n    console.log(productDiscountedPriceElement);\n    if (selectedProducts.length === 0) {\n      productPriceElement.textContent = product.getAttribute(\"data-product-price\");\n      productDiscountedPriceElement.classList.add(\"hidden\");\n    } else {\n      if (selectedProducts[0] === product.getAttribute(\"data-product-id\")) {\n        return;\n      }\n      productPriceElement.textContent = product.getAttribute(\"data-discounted-product-price\");\n      productDiscountedPriceElement.classList.remove(\"hidden\");\n    }\n  });\n}\nfunction updateClickedProductUI(productElement, productCheckboxContainer, productCheckboxEl) {\n  if (productElement.classList.contains(\"selected\")) {\n    productElement.classList.remove(\"selected\");\n    productElement.classList.remove(\"bg-emerald-500/20\", \"border-emerald-500/50\");\n    productElement.classList.add(\"hover:border-emerald-500/30\", \"hover:shadow-lg\", \"hover:shadow-emerald-500/10\", \"bg-primary-800/50\");\n    productCheckboxContainer.classList.remove(\"bg-emerald-500\", \"border-emerald-500\");\n    productCheckboxEl.classList.add(\"hidden\");\n  } else {\n    productElement.classList.add(\"selected\");\n    productElement.classList.add(\"bg-emerald-500/20\", \"border-emerald-500/50\");\n    productElement.classList.remove(\"hover:border-emerald-500/30\", \"hover:shadow-lg\", \"hover:shadow-emerald-500/10\", \"bg-primary-800/50\");\n    productCheckboxContainer.classList.add(\"bg-emerald-500\", \"border-emerald-500\");\n    productCheckboxEl.classList.remove(\"hidden\");\n  }\n}\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (initProducts);\n\n//# sourceURL=webpack://smore/./src/products/products.js?");

/***/ }),

/***/ "./src/utils.js":
/*!**********************!*\
  !*** ./src/utils.js ***!
  \**********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   formatTime: () => (/* binding */ formatTime),\n/* harmony export */   getCookie: () => (/* binding */ getCookie),\n/* harmony export */   getCsrfToken: () => (/* binding */ getCsrfToken),\n/* harmony export */   getElementFromAttribute: () => (/* binding */ getElementFromAttribute)\n/* harmony export */ });\n/**\n * Safely retrieve a cookie value by name.\n *\n * @param {string} name - The name of the cookie (e.g., \"csrftoken\").\n * @returns {string|null} - The cookie value if found, otherwise null.\n */\nfunction getCookie(name) {\n  if (!document.cookie) return null;\n  var cookies = document.cookie.split(\";\");\n  for (var i = 0; i < cookies.length; i++) {\n    var cookie = cookies[i].trim();\n    // Check if this cookie starts with \"<name>=\"\n    if (cookie.substring(0, name.length + 1) === \"\".concat(name, \"=\")) {\n      return decodeURIComponent(cookie.substring(name.length + 1));\n    }\n  }\n  return null;\n}\n\n/**\n * Retrieve Django's CSRF token.\n *\n * @returns {string|null} - The CSRF token if found, otherwise null.\n */\nfunction getCsrfToken() {\n  return getCookie(\"csrftoken\");\n}\nfunction formatTime() {\n  var date = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : new Date();\n  return date.toLocaleTimeString([], {\n    hour: \"2-digit\",\n    minute: \"2-digit\"\n  });\n}\nfunction getElementFromAttribute(elementWithAttribute, attributeToLookUp) {\n  var selector = elementWithAttribute.getAttribute(attributeToLookUp);\n  if (!selector) {\n    throw new Error(\"No attribute found with name: \".concat(attributeToLookUp, \" on element: \").concat(elementWithAttribute));\n  }\n  var foundElement = document.querySelector(selector);\n  if (!foundElement) {\n    throw new Error(\"No element found with selector: \".concat(selector));\n  }\n  return foundElement;\n}\n\n\n//# sourceURL=webpack://smore/./src/utils.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	// The module cache
/******/ 	var __webpack_module_cache__ = {};
/******/ 	
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/ 		// Check if module is in cache
/******/ 		var cachedModule = __webpack_module_cache__[moduleId];
/******/ 		if (cachedModule !== undefined) {
/******/ 			return cachedModule.exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = __webpack_module_cache__[moduleId] = {
/******/ 			// no module.id needed
/******/ 			// no module.loaded needed
/******/ 			exports: {}
/******/ 		};
/******/ 	
/******/ 		// Execute the module function
/******/ 		__webpack_modules__[moduleId](module, module.exports, __webpack_require__);
/******/ 	
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/ 	
/************************************************************************/
/******/ 	/* webpack/runtime/define property getters */
/******/ 	(() => {
/******/ 		// define getter functions for harmony exports
/******/ 		__webpack_require__.d = (exports, definition) => {
/******/ 			for(var key in definition) {
/******/ 				if(__webpack_require__.o(definition, key) && !__webpack_require__.o(exports, key)) {
/******/ 					Object.defineProperty(exports, key, { enumerable: true, get: definition[key] });
/******/ 				}
/******/ 			}
/******/ 		};
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/hasOwnProperty shorthand */
/******/ 	(() => {
/******/ 		__webpack_require__.o = (obj, prop) => (Object.prototype.hasOwnProperty.call(obj, prop))
/******/ 	})();
/******/ 	
/******/ 	/* webpack/runtime/make namespace object */
/******/ 	(() => {
/******/ 		// define __esModule on exports
/******/ 		__webpack_require__.r = (exports) => {
/******/ 			if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 				Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 			}
/******/ 			Object.defineProperty(exports, '__esModule', { value: true });
/******/ 		};
/******/ 	})();
/******/ 	
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = __webpack_require__("./src/index.js");
/******/ 	
/******/ })()
;