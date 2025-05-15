/*
 * ATTENTION: The "eval" devtool has been used (maybe by default in mode: "development").
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
/******/ (() => { // webpackBootstrap
/******/ 	var __webpack_modules__ = ({

/***/ "./my-games.js":
/*!*********************!*\
  !*** ./my-games.js ***!
  \*********************/
/***/ (() => {

eval("document.addEventListener('DOMContentLoaded', function () {\n  var modal = document.getElementById('deleteConfirmationModal');\n  var confirmDeleteBtn = document.getElementById('confirmDeleteBtn');\n  var cancelDeleteBtn = document.getElementById('cancelDeleteBtn');\n  var closeBtn = modal.querySelector('.modal-close-btn');\n  var gameNameElement = document.getElementById('gameNameToDelete');\n  var noGamesMessage = document.getElementById('no-games-message');\n  var gamesGrid = document.querySelector('.my-saved-games-grid');\n  var gameIdToDelete = null;\n  var gameCardElementToDelete = null;\n\n  // Функция для получения CSRF-токена\n  function getCookie(name) {\n    var cookieValue = null;\n    if (document.cookie && document.cookie !== '') {\n      var cookies = document.cookie.split(';');\n      for (var i = 0; i < cookies.length; i++) {\n        var cookie = cookies[i].trim();\n        if (cookie.substring(0, name.length + 1) === name + '=') {\n          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));\n          break;\n        }\n      }\n    }\n    return cookieValue;\n  }\n  var csrftoken = getCookie('csrftoken');\n\n  // Открытие модального окна\n  document.querySelectorAll('.delete-game-btn').forEach(function (button) {\n    button.addEventListener('click', function (event) {\n      event.preventDefault();\n      event.stopPropagation();\n      gameIdToDelete = this.dataset.gameId;\n      gameCardElementToDelete = this.closest('.saved-game-item-wrapper');\n      var titleElement = gameCardElementToDelete.querySelector('.saved-game-card__title');\n      gameNameElement.textContent = titleElement ? titleElement.textContent.trim() : 'эту игру';\n      modal.style.display = 'flex';\n    });\n  });\n\n  // Закрытие модального окна\n  function closeModal() {\n    modal.style.display = 'none';\n    gameIdToDelete = null;\n    gameCardElementToDelete = null;\n  }\n  if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', closeModal);\n  if (closeBtn) closeBtn.addEventListener('click', closeModal);\n  window.addEventListener('click', function (event) {\n    if (event.target === modal) {\n      closeModal();\n    }\n  });\n\n  // Подтверждение удаления\n  if (confirmDeleteBtn) {\n    confirmDeleteBtn.addEventListener('click', function () {\n      if (!gameIdToDelete || !gameCardElementToDelete) return;\n      var deleteUrl = \"/games/delete/\".concat(gameIdToDelete, \"/\");\n      fetch(deleteUrl, {\n        method: 'DELETE',\n        headers: {\n          'X-CSRFToken': csrftoken\n        }\n      }).then(function (response) {\n        if (response.ok) {\n          if (response.status === 204) {\n            return Promise.resolve({\n              status: 'success',\n              message: 'Игра успешно удалена (204).'\n            });\n          }\n          return response.json();\n        }\n        return response.json().then(function (err) {\n          throw new Error(err.message || 'Не удалось удалить игру.');\n        });\n      }).then(function (data) {\n        if (data.status === 'success') {\n          gameCardElementToDelete.remove();\n          checkIfGamesExist();\n          console.log(data.message || 'Игра успешно удалена.');\n          closeModal();\n        } else {\n          throw new Error(data.message || 'Ошибка при удалении игры на сервере.');\n        }\n      })[\"catch\"](function (error) {\n        console.error('Ошибка при удалении игры:', error);\n        alert(\"\\u041E\\u0448\\u0438\\u0431\\u043A\\u0430: \".concat(error.message));\n        closeModal();\n      });\n    });\n  }\n  function checkIfGamesExist() {\n    if (gamesGrid && noGamesMessage) {\n      var remainingGames = gamesGrid.querySelectorAll('.saved-game-item-wrapper').length;\n      if (remainingGames === 0) {\n        noGamesMessage.style.display = 'block';\n      } else {\n        noGamesMessage.style.display = 'none';\n      }\n    }\n  }\n  checkIfGamesExist();\n});\n\n//# sourceURL=webpack://frontend/./my-games.js?");

/***/ })

/******/ 	});
/************************************************************************/
/******/ 	
/******/ 	// startup
/******/ 	// Load entry module and return exports
/******/ 	// This entry module can't be inlined because the eval devtool is used.
/******/ 	var __webpack_exports__ = {};
/******/ 	__webpack_modules__["./my-games.js"]();
/******/ 	
/******/ })()
;