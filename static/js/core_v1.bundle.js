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

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _menu_main__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./menu/main */ \"./src/menu/main.js\");\n\ndocument.addEventListener(\"DOMContentLoaded\", function () {\n  console.log(\"Hello World\");\n  (0,_menu_main__WEBPACK_IMPORTED_MODULE_0__.initMobileMenu)();\n});\n\n//# sourceURL=webpack://smore/./src/index.js?");

/***/ }),

/***/ "./src/menu/main.js":
/*!**************************!*\
  !*** ./src/menu/main.js ***!
  \**************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   initMobileMenu: () => (/* binding */ initMobileMenu)\n/* harmony export */ });\nfunction initMobileMenu() {\n  var menuButton = document.querySelector(\"#mobileMenuButton\");\n  var menu = document.querySelector(\"#mobileMenuDropdownContainer\");\n  menuButton.addEventListener(\"click\", function () {\n    if (menu.classList.contains(\"active\")) {\n      hideMenu();\n      toggleCloseIcon();\n    } else {\n      showMenu();\n      toggleCloseIcon();\n    }\n  });\n  function showMenu() {\n    menu.classList.add(\"max-h-screen\", \"opacity-100\", \"active\");\n    menu.classList.remove(\"max-h-0\", \"opacity-0\", \"opacity-hidden\");\n  }\n  function hideMenu() {\n    menu.classList.add(\"max-h-0\", \"opacity-0\", \"opacity-hidden\");\n    menu.classList.remove(\"max-h-screen\", \"opacity-100\", \"active\");\n  }\n  function toggleCloseIcon() {\n    var closeIcon = menuButton.querySelector(\".closeIcon\");\n    var hamburgerIcon = menuButton.querySelector(\".hamburgerIcon\");\n    hamburgerIcon.classList.toggle(\"hidden\");\n    closeIcon.classList.toggle(\"hidden\");\n  }\n}\n\n//# sourceURL=webpack://smore/./src/menu/main.js?");

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