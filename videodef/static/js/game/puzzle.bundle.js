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

/***/ "./puzzle/index.js":
/*!*************************!*\
  !*** ./puzzle/index.js ***!
  \*************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   createPuzzleOnBoard: () => (/* binding */ createPuzzleOnBoard),\n/* harmony export */   puzzleParams: () => (/* binding */ puzzleParams)\n/* harmony export */ });\n/* harmony import */ var _puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./puzzle-logic.js */ \"./puzzle/puzzle-logic.js\");\nfunction _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }\nfunction _nonIterableRest() { throw new TypeError(\"Invalid attempt to destructure non-iterable instance.\\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.\"); }\nfunction _unsupportedIterableToArray(r, a) { if (r) { if (\"string\" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return \"Object\" === t && r.constructor && (t = r.constructor.name), \"Map\" === t || \"Set\" === t ? Array.from(r) : \"Arguments\" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }\nfunction _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }\nfunction _iterableToArrayLimit(r, l) { var t = null == r ? null : \"undefined\" != typeof Symbol && r[Symbol.iterator] || r[\"@@iterator\"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t[\"return\"] && (u = t[\"return\"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }\nfunction _arrayWithHoles(r) { if (Array.isArray(r)) return r; }\n\nvar puzzleParams = {\n  onWhiteboard: false\n};\nwindow.createPuzzleSeparately = createPuzzleSeparately;\nfunction createPuzzleOnBoard(gameWrapper) {\n  var _getPuzzleParts = (0,_puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__.getPuzzleParts)(),\n    _getPuzzleParts2 = _slicedToArray(_getPuzzleParts, 3),\n    puzzleParams = _getPuzzleParts2[0],\n    puzzleContainer = _getPuzzleParts2[1],\n    message = _getPuzzleParts2[2];\n  (0,_puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__.createPuzzle)(puzzleContainer, puzzleParams, message);\n  puzzleContainer.querySelectorAll('.puzzle-piece').forEach(function (piece) {\n    piece.style.backgroundImage = \"url(\\\"\".concat(puzzleParams.selectedImage, \"\\\")\");\n  });\n  gameWrapper.appendChild(puzzleContainer);\n  gameWrapper.appendChild(message);\n}\nfunction createPuzzleSeparately() {\n  var _getPuzzleParts3 = (0,_puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__.getPuzzleParts)(),\n    _getPuzzleParts4 = _slicedToArray(_getPuzzleParts3, 3),\n    puzzleParams = _getPuzzleParts4[0],\n    puzzleContainer = _getPuzzleParts4[1],\n    message = _getPuzzleParts4[2];\n  document.body.appendChild(puzzleContainer);\n  document.body.appendChild(message);\n  var modal = document.getElementById('start-modal');\n  var startBtn = document.getElementById('start-game');\n  startBtn.addEventListener('click', function () {\n    if (!puzzleParams.selectedImage) {\n      alert(\"Пожалуйста, выберите или загрузите изображение.\");\n      return;\n    }\n    document.querySelectorAll('.puzzle-piece').forEach(function (piece) {\n      piece.style.backgroundImage = \"url(\\\"\".concat(puzzleParams.selectedImage, \"\\\")\");\n    });\n    (0,_puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__.placePieces)(puzzleContainer, puzzleParams);\n    modal.style.display = 'none';\n  });\n  var customInput = document.getElementById('custom-image');\n  customInput.addEventListener('change', function (e) {\n    var file = e.target.files[0];\n    if (file) {\n      var reader = new FileReader();\n      reader.onload = function () {\n        puzzleParams.selectedImage = reader.result;\n      };\n      reader.readAsDataURL(file);\n    }\n  });\n  var presets = document.querySelectorAll('.preset');\n  presets.forEach(function (preset) {\n    preset.addEventListener('click', function () {\n      presets.forEach(function (p) {\n        return p.classList.remove('selected');\n      });\n      preset.classList.add('selected');\n      puzzleParams.selectedImage = preset.dataset.src;\n    });\n  });\n  (0,_puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__.createPuzzle)(puzzleContainer, puzzleParams, message);\n  var difficultySelect = document.getElementById('difficulty');\n  difficultySelect.addEventListener('change', function (e) {\n    puzzleParams.gridSize = parseInt(e.target.value, 10);\n    (0,_puzzle_logic_js__WEBPACK_IMPORTED_MODULE_0__.createPuzzle)(puzzleContainer, puzzleParams, message);\n  });\n}\n\n//# sourceURL=webpack://frontend/./puzzle/index.js?");

/***/ }),

/***/ "./puzzle/puzzle-logic.js":
/*!********************************!*\
  !*** ./puzzle/puzzle-logic.js ***!
  \********************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   createPuzzle: () => (/* binding */ createPuzzle),\n/* harmony export */   getPuzzleParts: () => (/* binding */ getPuzzleParts),\n/* harmony export */   placePieces: () => (/* binding */ placePieces)\n/* harmony export */ });\nfunction _slicedToArray(r, e) { return _arrayWithHoles(r) || _iterableToArrayLimit(r, e) || _unsupportedIterableToArray(r, e) || _nonIterableRest(); }\nfunction _nonIterableRest() { throw new TypeError(\"Invalid attempt to destructure non-iterable instance.\\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.\"); }\nfunction _iterableToArrayLimit(r, l) { var t = null == r ? null : \"undefined\" != typeof Symbol && r[Symbol.iterator] || r[\"@@iterator\"]; if (null != t) { var e, n, i, u, a = [], f = !0, o = !1; try { if (i = (t = t.call(r)).next, 0 === l) { if (Object(t) !== t) return; f = !1; } else for (; !(f = (e = i.call(t)).done) && (a.push(e.value), a.length !== l); f = !0); } catch (r) { o = !0, n = r; } finally { try { if (!f && null != t[\"return\"] && (u = t[\"return\"](), Object(u) !== u)) return; } finally { if (o) throw n; } } return a; } }\nfunction _arrayWithHoles(r) { if (Array.isArray(r)) return r; }\nfunction _toConsumableArray(r) { return _arrayWithoutHoles(r) || _iterableToArray(r) || _unsupportedIterableToArray(r) || _nonIterableSpread(); }\nfunction _nonIterableSpread() { throw new TypeError(\"Invalid attempt to spread non-iterable instance.\\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.\"); }\nfunction _unsupportedIterableToArray(r, a) { if (r) { if (\"string\" == typeof r) return _arrayLikeToArray(r, a); var t = {}.toString.call(r).slice(8, -1); return \"Object\" === t && r.constructor && (t = r.constructor.name), \"Map\" === t || \"Set\" === t ? Array.from(r) : \"Arguments\" === t || /^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(t) ? _arrayLikeToArray(r, a) : void 0; } }\nfunction _iterableToArray(r) { if (\"undefined\" != typeof Symbol && null != r[Symbol.iterator] || null != r[\"@@iterator\"]) return Array.from(r); }\nfunction _arrayWithoutHoles(r) { if (Array.isArray(r)) return _arrayLikeToArray(r); }\nfunction _arrayLikeToArray(r, a) { (null == a || a > r.length) && (a = r.length); for (var e = 0, n = Array(a); e < a; e++) n[e] = r[e]; return n; }\nfunction getPuzzleParts() {\n  var puzzleParams = {\n    gridSize: 2,\n    piecePositions: [],\n    selectedImage: images + '/puzzle_test.png',\n    selectedPiece: null\n  };\n  var puzzleContainer = createPuzzleContainer();\n  var message = createGameMessage();\n  return [puzzleParams, puzzleContainer, message];\n}\nfunction createPuzzle(puzzleContainer, puzzleParams, message) {\n  puzzleContainer.innerHTML = '';\n  puzzleParams.piecePositions = shuffle(_toConsumableArray(Array(puzzleParams.gridSize * puzzleParams.gridSize).keys()));\n  var _loop = function _loop() {\n    var piece = document.createElement('div');\n    piece.classList.add('puzzle-piece');\n    piece.id = \"piece-\".concat(i + 1);\n    piece.setAttribute('data-index', i);\n    piece.style.width = \"\".concat(300 / puzzleParams.gridSize, \"px\");\n    piece.style.height = \"\".concat(300 / puzzleParams.gridSize, \"px\");\n    piece.style.backgroundSize = \"\".concat(300, \"px \", 300, \"px\");\n    piece.addEventListener('click', function () {\n      return handlePieceClick(puzzleContainer, puzzleParams, piece, message);\n    });\n    puzzleContainer.appendChild(piece);\n  };\n  for (var i = 0; i < puzzleParams.gridSize * puzzleParams.gridSize; i++) {\n    _loop();\n  }\n  placePieces(puzzleContainer, puzzleParams);\n}\nfunction createPuzzleContainer() {\n  var container = document.createElement('div');\n  container.classList.add('puzzle-container');\n  var ids = '123456789'.split('');\n  ids.forEach(function (id, index) {\n    var piece = document.createElement('div');\n    piece.classList.add('puzzle-piece');\n    piece.id = \"piece-\".concat(id);\n    piece.setAttribute('draggable', 'true');\n    piece.setAttribute('data-index', id);\n    container.appendChild(piece);\n  });\n  return container;\n}\nfunction placePieces(puzzleContainer, puzzleParams) {\n  var pieces = puzzleContainer.querySelectorAll('.puzzle-piece');\n  var gridPositions = [];\n  for (var row = 0; row < puzzleParams.gridSize; row++) {\n    for (var col = 0; col < puzzleParams.gridSize; col++) {\n      gridPositions.push([col * (300 / puzzleParams.gridSize), row * (300 / puzzleParams.gridSize)]);\n    }\n  }\n  pieces.forEach(function (piece, idx) {\n    var _gridPositions$puzzle = _slicedToArray(gridPositions[puzzleParams.piecePositions[idx]], 2),\n      x = _gridPositions$puzzle[0],\n      y = _gridPositions$puzzle[1];\n    piece.style.left = \"\".concat(x, \"px\");\n    piece.style.top = \"\".concat(y, \"px\");\n    var row = Math.floor(idx / puzzleParams.gridSize);\n    var col = idx % puzzleParams.gridSize;\n    piece.style.backgroundPosition = \"-\".concat(col * (300 / puzzleParams.gridSize), \"px \\n            -\").concat(row * (300 / puzzleParams.gridSize), \"px\");\n  });\n}\nfunction shuffle(array) {\n  for (var i = array.length - 1; i > 0; i--) {\n    var j = Math.floor(Math.random() * (i + 1));\n    var _ref = [array[j], array[i]];\n    array[i] = _ref[0];\n    array[j] = _ref[1];\n  }\n  return array;\n}\nfunction handlePieceClick(puzzleContainer, puzzleParams, piece, message) {\n  if (!puzzleParams.selectedPiece) {\n    puzzleParams.selectedPiece = piece;\n    piece.style.outline = '2px solid red';\n  } else if (puzzleParams.selectedPiece === piece) {\n    piece.style.outline = '';\n    puzzleParams.selectedPiece = null;\n  } else {\n    swapPieces(puzzleContainer, puzzleParams, puzzleParams.selectedPiece, piece);\n    puzzleParams.selectedPiece.style.outline = '';\n    puzzleParams.selectedPiece = null;\n    checkVictory(puzzleParams, message);\n  }\n}\nfunction swapPieces(puzzleContainer, puzzleParams, p1, p2) {\n  var i1 = Array.from(document.querySelectorAll('.puzzle-piece')).indexOf(p1);\n  var i2 = Array.from(document.querySelectorAll('.puzzle-piece')).indexOf(p2);\n  var _ref2 = [puzzleParams.piecePositions[i2], puzzleParams.piecePositions[i1]];\n  puzzleParams.piecePositions[i1] = _ref2[0];\n  puzzleParams.piecePositions[i2] = _ref2[1];\n  placePieces(puzzleContainer, puzzleParams);\n}\nfunction checkVictory(puzzleParams, message) {\n  var isVictory = puzzleParams.piecePositions.every(function (val, idx) {\n    return val === idx;\n  });\n  if (isVictory) {\n    message.style.display = 'block';\n  }\n}\nfunction createGameMessage() {\n  var message = document.createElement('div');\n  message.id = 'game-message';\n  message.style.display = 'none';\n  message.style.textAlign = 'center';\n  message.style.fontSize = '1.5em';\n  message.style.marginTop = '20px';\n  message.textContent = 'Поздравляем! Вы собрали пазл!';\n  return message;\n}\n\n//# sourceURL=webpack://frontend/./puzzle/puzzle-logic.js?");

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
/******/ 	var __webpack_exports__ = __webpack_require__("./puzzle/index.js");
/******/ 	
/******/ })()
;