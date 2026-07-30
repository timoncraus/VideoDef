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

/***/ "./common/utils.js":
/*!*************************!*\
  !*** ./common/utils.js ***!
  \*************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   dataURLtoBlob: () => (/* binding */ dataURLtoBlob),\n/* harmony export */   generateUniqueId: () => (/* binding */ generateUniqueId),\n/* harmony export */   getCookie: () => (/* binding */ getCookie),\n/* harmony export */   isAuthenticated: () => (/* binding */ isAuthenticated),\n/* harmony export */   makeDraggable: () => (/* binding */ makeDraggable),\n/* harmony export */   makeResizable: () => (/* binding */ makeResizable),\n/* harmony export */   redirectToLogin: () => (/* binding */ redirectToLogin),\n/* harmony export */   safeJsonParse: () => (/* binding */ safeJsonParse),\n/* harmony export */   shuffle: () => (/* binding */ shuffle)\n/* harmony export */ });\nfunction _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }\nfunction _nonIterableSpread() { throw new TypeError(\"Invalid attempt to spread non-iterable instance.\\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.\"); }\nfunction _unsupportedIterableToArray(r, a) { if (r) { if (\"string\" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return \"Object\" === t && r.constructor && (t = r.constructor.name), \"Map\" === t || \"Set\" === t ? Array.from(r) : \"Arguments\" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }\nfunction _iterableToArray(r) { if (\"undefined\" != typeof Symbol && null != r[Symbol.iterator] || null != r[\"@@iterator\"]) return Array.from(r); }\nfunction _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }\nfunction _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }\n/**\r\n * Общие утилиты для всех модулей игр.\r\n * Содержит вспомогательные функции, используемые в различных частях приложения.\r\n */\n\n/**\r\n * Конвертирует строку Data URL в объект Blob.\r\n * Необходимо для отправки пользовательских изображений на сервер через FormData.\r\n * \r\n * @param {string} dataURL - Строка Data URL (например, \"data:image/png;base64,...\")\r\n * @returns {Blob|null} - Объект Blob или null в случае ошибки\r\n */\nfunction dataURLtoBlob(dataURL) {\n  try {\n    // Разделяем строку на метаданные (MIME-тип) и данные Base64\n    var parts = dataURL.split(';base64,');\n    var contentType = parts[0].split(':')[1];\n\n    // Декодируем Base64 строку в бинарную строку\n    var raw = window.atob(parts[1]);\n    var rawLength = raw.length;\n\n    // Создаем массив 8-битных беззнаковых целых чисел\n    var uInt8Array = new Uint8Array(rawLength);\n    for (var i = 0; i < rawLength; ++i) {\n      uInt8Array[i] = raw.charCodeAt(i);\n    }\n\n    // Создаем и возвращаем Blob с указанным MIME-типом\n    return new Blob([uInt8Array], {\n      type: contentType\n    });\n  } catch (error) {\n    console.error(\"Ошибка конвертации Data URL в Blob:\", error);\n    return null;\n  }\n}\n\n/**\r\n * Перемешивает элементы массива случайным образом (алгоритм Фишера-Йетса).\r\n * \r\n * @param {Array<any>} array - Массив для перемешивания\r\n * @returns {Array<any>} - Новый массив с перемешанными элементами\r\n */\nfunction shuffle(array) {\n  var newArray = _toConsumableArray(array);\n  for (var i = newArray.length - 1; i > 0; i--) {\n    var j = Math.floor(Math.random() * (i + 1));\n    var _ref = [newArray[j], newArray[i]];\n    newArray[i] = _ref[0];\n    newArray[j] = _ref[1];\n  }\n  return newArray;\n}\n\n/**\r\n * Получает CSRF-токен из cookies.\r\n * \r\n * @param {string} name - Имя cookie (обычно 'csrftoken')\r\n * @returns {string|null} - Значение CSRF-токена или null\r\n */\nfunction getCookie(name) {\n  var cookieValue = null;\n  if (document.cookie && document.cookie !== '') {\n    var cookies = document.cookie.split(';');\n    for (var i = 0; i < cookies.length; i++) {\n      var cookie = cookies[i].trim();\n      if (cookie.substring(0, name.length + 1) === name + '=') {\n        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));\n        break;\n      }\n    }\n  }\n  return cookieValue;\n}\n\n/**\r\n * Проверяет, аутентифицирован ли пользователь.\r\n * \r\n * @returns {boolean} - true, если пользователь аутентифицирован\r\n */\nfunction isAuthenticated() {\n  return typeof window.isAuthenticated !== 'undefined' && window.isAuthenticated;\n}\n\n/**\r\n * Перенаправляет на страницу входа.\r\n */\nfunction redirectToLogin() {\n  if (typeof window.loginUrl !== 'undefined') {\n    window.location.href = window.loginUrl;\n  } else {\n    console.error(\"URL для входа не определен\");\n  }\n}\n\n/**\r\n * Генерирует уникальный ID для элемента.\r\n * \r\n * @param {string} prefix - Префикс для ID (например, 'game', 'image')\r\n * @param {number} counter - Счетчик для уникальности\r\n * @returns {string} - Уникальный ID (например, 'game-1', 'image-2')\r\n */\nfunction generateUniqueId(prefix, counter) {\n  return \"\".concat(prefix, \"-\").concat(counter);\n}\n\n/**\r\n * Безопасно парсит JSON строку.\r\n * \r\n * @param {string} jsonString - JSON строка для парсинга\r\n * @param {any} defaultValue - Значение по умолчанию в случае ошибки\r\n * @returns {any} - Распарсенный объект или defaultValue\r\n */\nfunction safeJsonParse(jsonString) {\n  var defaultValue = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;\n  try {\n    return JSON.parse(jsonString);\n  } catch (error) {\n    console.error(\"Ошибка парсинга JSON:\", error);\n    return defaultValue;\n  }\n}\n\n/**\r\n * Делает DOM-элемент перетаскиваемым.\r\n * \r\n * @param {HTMLElement} element - Элемент для перетаскивания\r\n * @param {Function} onDrag - Callback при перетаскивании (x, y)\r\n * @param {Function} onDragEnd - Callback при завершении перетаскивания (x, y)\r\n */\nfunction makeDraggable(element, onDrag, onDragEnd) {\n  var dragStartX, dragStartY, initialLeft, initialTop;\n  var onMouseDown = function onMouseDown(e) {\n    if (e.button !== 0) return; // Только левая кнопка мыши\n\n    dragStartX = e.clientX;\n    dragStartY = e.clientY;\n    initialLeft = parseFloat(element.style.left) || 0;\n    initialTop = parseFloat(element.style.top) || 0;\n    element.style.cursor = 'grabbing';\n    document.body.style.userSelect = 'none';\n    document.addEventListener('mousemove', onMouseMove);\n    document.addEventListener('mouseup', _onMouseUp);\n    e.stopPropagation();\n  };\n  var onMouseMove = function onMouseMove(e) {\n    var dx = e.clientX - dragStartX;\n    var dy = e.clientY - dragStartY;\n    var newLeft = initialLeft + dx;\n    var newTop = initialTop + dy;\n    element.style.left = \"\".concat(newLeft, \"px\");\n    element.style.top = \"\".concat(newTop, \"px\");\n    if (onDrag) {\n      onDrag(newLeft, newTop);\n    }\n  };\n  var _onMouseUp = function onMouseUp() {\n    element.style.cursor = 'grab';\n    document.body.style.userSelect = '';\n    document.removeEventListener('mousemove', onMouseMove);\n    document.removeEventListener('mouseup', _onMouseUp);\n    if (onDragEnd) {\n      var finalLeft = parseFloat(element.style.left) || 0;\n      var finalTop = parseFloat(element.style.top) || 0;\n      onDragEnd(finalLeft, finalTop);\n    }\n  };\n  element.addEventListener('mousedown', onMouseDown);\n  element.style.cursor = 'grab';\n}\n\n/**\r\n * Делает DOM-элемент изменяемым по размеру.\r\n * \r\n * @param {HTMLElement} element - Элемент для изменения размера\r\n * @param {Function} onResize - Callback при изменении размера (width, height)\r\n * @param {Function} onResizeEnd - Callback при завершении изменения (width, height)\r\n */\nfunction makeResizable(element, onResize, onResizeEnd) {\n  var resizeHandle = document.createElement('div');\n  resizeHandle.className = 'resize-handle';\n  element.appendChild(resizeHandle);\n  var resizeStartX, resizeStartY, initialWidth, initialHeight;\n  resizeHandle.addEventListener('mousedown', function (e) {\n    e.stopPropagation();\n    var rect = element.getBoundingClientRect();\n    resizeStartX = e.clientX;\n    resizeStartY = e.clientY;\n    initialWidth = rect.width;\n    initialHeight = rect.height;\n    document.body.style.userSelect = 'none';\n    document.addEventListener('mousemove', onMouseMove);\n    document.addEventListener('mouseup', _onMouseUp2);\n  });\n  var onMouseMove = function onMouseMove(e) {\n    var dx = e.clientX - resizeStartX;\n    var dy = e.clientY - resizeStartY;\n    var newWidth = Math.max(200, initialWidth + dx);\n    var newHeight = Math.max(150, initialHeight + dy);\n    element.style.width = \"\".concat(newWidth, \"px\");\n    element.style.height = \"\".concat(newHeight, \"px\");\n    if (onResize) {\n      onResize(newWidth, newHeight);\n    }\n  };\n  var _onMouseUp2 = function onMouseUp() {\n    document.body.style.userSelect = '';\n    document.removeEventListener('mousemove', onMouseMove);\n    document.removeEventListener('mouseup', _onMouseUp2);\n    if (onResizeEnd) {\n      var finalWidth = parseFloat(element.style.width) || 0;\n      var finalHeight = parseFloat(element.style.height) || 0;\n      onResizeEnd(finalWidth, finalHeight);\n    }\n  };\n}\n\n//# sourceURL=webpack://frontend/./common/utils.js?");

/***/ }),

/***/ "./my-games.js":
/*!*********************!*\
  !*** ./my-games.js ***!
  \*********************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var _common_utils_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./common/utils.js */ \"./common/utils.js\");\n/**\r\n * Модуль для страницы \"Мои игры\".\r\n * Управляет удалением игр через модальное окно подтверждения.\r\n */\n\n\ndocument.addEventListener('DOMContentLoaded', function () {\n  var modal = document.getElementById('deleteConfirmationModal');\n  var confirmDeleteBtn = document.getElementById('confirmDeleteBtn');\n  var cancelDeleteBtn = document.getElementById('cancelDeleteBtn');\n  var closeBtn = modal.querySelector('.modal-close-btn');\n  var gameNameElement = document.getElementById('gameNameToDelete');\n  var noGamesMessage = document.getElementById('no-games-message');\n  var gamesGrid = document.querySelector('.my-saved-games-grid');\n  var gameIdToDelete = null;\n  var gameCardElementToDelete = null;\n  var csrftoken = (0,_common_utils_js__WEBPACK_IMPORTED_MODULE_0__.getCookie)('csrftoken');\n\n  /**\r\n   * Открывает модальное окно подтверждения удаления.\r\n   * \r\n   * @param {Event} event - Событие клика.\r\n   */\n  var openModal = function openModal(event) {\n    event.preventDefault();\n    event.stopPropagation();\n    gameIdToDelete = this.dataset.gameId;\n    gameCardElementToDelete = this.closest('.saved-game-item-wrapper');\n    var titleElement = gameCardElementToDelete.querySelector('.saved-game-card__title');\n    gameNameElement.textContent = titleElement ? titleElement.textContent.trim() : 'эту игру';\n    modal.style.display = 'flex';\n  };\n\n  /**\r\n   * Закрывает модальное окно.\r\n   */\n  var closeModal = function closeModal() {\n    modal.style.display = 'none';\n    gameIdToDelete = null;\n    gameCardElementToDelete = null;\n  };\n\n  // Назначаем обработчики на кнопки удаления\n  document.querySelectorAll('.delete-game-btn').forEach(function (button) {\n    button.addEventListener('click', openModal);\n  });\n\n  // Обработчики закрытия модального окна\n  if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', closeModal);\n  if (closeBtn) closeBtn.addEventListener('click', closeModal);\n  window.addEventListener('click', function (event) {\n    if (event.target === modal) {\n      closeModal();\n    }\n  });\n\n  /**\r\n   * Подтверждает удаление игры и отправляет запрос на сервер.\r\n   */\n  var confirmDelete = function confirmDelete() {\n    if (!gameIdToDelete || !gameCardElementToDelete) return;\n    var deleteUrl = \"/games/api/delete-game/\".concat(gameIdToDelete, \"/\");\n    fetch(deleteUrl, {\n      method: 'DELETE',\n      headers: {\n        'X-CSRFToken': csrftoken\n      }\n    }).then(function (response) {\n      if (response.ok) {\n        if (response.status === 204) {\n          return Promise.resolve({\n            status: 'success',\n            message: 'Игра успешно удалена (204).'\n          });\n        }\n        return response.json();\n      }\n      return response.json().then(function (err) {\n        throw new Error(err.message || 'Не удалось удалить игру.');\n      });\n    }).then(function (data) {\n      if (data.status === 'success') {\n        gameCardElementToDelete.remove();\n        checkIfGamesExist();\n        console.log(data.message || 'Игра успешно удалена.');\n        closeModal();\n      } else {\n        throw new Error(data.message || 'Ошибка при удалении игры на сервере.');\n      }\n    })[\"catch\"](function (error) {\n      console.error('Ошибка при удалении игры:', error);\n      alert(\"\\u041E\\u0448\\u0438\\u0431\\u043A\\u0430: \".concat(error.message));\n      closeModal();\n    });\n  };\n  if (confirmDeleteBtn) {\n    confirmDeleteBtn.addEventListener('click', confirmDelete);\n  }\n\n  /**\r\n   * Проверяет, остались ли игры, и скрывает/показывает сообщение \"Нет игр\".\r\n   */\n  function checkIfGamesExist() {\n    if (gamesGrid && noGamesMessage) {\n      var remainingGames = gamesGrid.querySelectorAll('.saved-game-item-wrapper').length;\n      if (remainingGames === 0) {\n        noGamesMessage.style.display = 'block';\n      } else {\n        noGamesMessage.style.display = 'none';\n      }\n    }\n  }\n  checkIfGamesExist();\n});\n\n//# sourceURL=webpack://frontend/./my-games.js?");

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
/******/ 	var __webpack_exports__ = __webpack_require__("./my-games.js");
/******/ 	
/******/ })()
;