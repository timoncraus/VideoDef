/**
 * Главный модуль игры "Пазл".
 * Инициализирует интерфейс и логику для отдельной страницы и доски.
 */

import { getPuzzleParts, createPuzzle, applyRemotePieceInteraction } from './logic.js';
import { displayPuzzleList, preparePuzzleSaveData, createPuzzleFormData } from './save-load.js';
import { SaveLoadManager } from '../common/save-load.js';
import { PuzzleGame } from './game-class.js';

/**
 * Инициализирует интерфейс и логику для отдельной страницы пазла.
 * Эта функция назначается на window.createPuzzleSeparately в конце файла.
 */
function createPuzzleSeparately() {
    const [localPuzzleParams, puzzleContainer, message] = getPuzzleParts();
    localPuzzleParams.onWhiteboard = false;
    localPuzzleParams.name = "";
    localPuzzleParams.id = null;
    localPuzzleParams.ws = null;
    
    const wrapper = document.getElementById('puzzle-wrapper');
    if (!wrapper) {
        console.error("#puzzle-wrapper not found!");
        return;
    }
    
    wrapper.innerHTML = '';
    wrapper.appendChild(puzzleContainer);
    wrapper.appendChild(message);
    
    const customInput = document.getElementById('custom-image');
    const difficultySelect = document.getElementById('difficulty');
    const presetsNodeList = document.querySelectorAll('.preset');
    const startBtn = document.getElementById('start-game');
    const puzzleNameInput = document.getElementById('puzzle-name');
    const saveButton = document.getElementById('save-puzzle-btn');
    const loadButton = document.getElementById('load-puzzle-btn');
    const loadModal = document.getElementById('load-puzzle-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');
    
    if (!customInput || !difficultySelect || !presetsNodeList?.length || !startBtn || !puzzleNameInput || !saveButton || !loadButton || !loadModal) {
        console.error("Элементы управления на странице пазлов не найдены!");
        return;
    }
    
    const presets = Array.from(presetsNodeList);
    
    setupPuzzleControls({
        customInput, presets, difficultySelect, startBtn,
        puzzleParams: localPuzzleParams,
        puzzleContainer, message,
        instantUpdate: false,
        onStateChange: (params) => {
            if (params && typeof params.name !== 'undefined') {
                puzzleNameInput.value = params.name;
            }
        },
        saveBtnRef: saveButton
    });
    
    const getPuzzleState = () => {
        localPuzzleParams.name = puzzleNameInput.value.trim();
        return preparePuzzleSaveData(localPuzzleParams, presets, customInput);
    };
    
    const applyLoadedState = (puzzleData) => {
        localPuzzleParams.id = puzzleData.id;
        localPuzzleParams.gridSize = puzzleData.grid_size;
        localPuzzleParams.piecePositions = puzzleData.piece_positions || [];
        localPuzzleParams.name = puzzleData.name;
        localPuzzleParams.selectedImage = puzzleData.image_url;
        localPuzzleParams.isPreset = !!puzzleData.preset_path;
        
        difficultySelect.value = puzzleData.grid_size;
        puzzleNameInput.value = puzzleData.name;
        customInput.value = '';
        
        const previewContainer = document.getElementById('image-preview-container');
        if (previewContainer) previewContainer.style.display = 'none';
        
        presets.forEach(p => p.classList.remove('selected'));
        
        if (localPuzzleParams.isPreset) {
            let found = false;
            presets.forEach(preset => {
                const presetSrcRelative = (preset.dataset.src || preset.src).replace(window.location.origin, '');
                const loadedUrlRelative = puzzleData.image_url.replace(window.location.origin, '');
                if (presetSrcRelative === loadedUrlRelative) {
                    preset.classList.add('selected');
                    found = true;
                }
            });
            if (!found) console.warn("Загруженное предустановленное изображение не найдено.");
        } else {
            const previewImg = document.getElementById('image-preview');
            const previewText = document.getElementById('image-preview-text');
            if (previewContainer && previewImg && previewText && puzzleData.image_url) {
                previewImg.src = puzzleData.image_url;
                previewText.textContent = `Загружено: ${puzzleData.name}`;
                previewContainer.style.display = 'block';
            }
        }
        
        if (saveButton) {
            saveButton.textContent = 'Обновить пазл';
            saveButton.dataset.action = 'update';
            saveButton.dataset.puzzleId = puzzleData.id;
        }
        
        alert(`Пазл "${puzzleData.name}" загружен. Нажмите "Начать игру".`);
        puzzleContainer.innerHTML = '<p>Пазл загружен. Нажмите "Начать игру".</p>';
        message.style.display = 'none';
    };
    
    // Проверка наличия глобальных URL, определенных в HTML шаблоне
    const saveUrl = typeof savePuzzleUrl !== 'undefined' ? savePuzzleUrl : '/games/api/save-puzzle/';
    const loadUrl = typeof loadPuzzlesUrl !== 'undefined' ? loadPuzzlesUrl : '/games/api/load-puzzles/';
    const updateTemplate = typeof updatePuzzleBaseUrl !== 'undefined' ? updatePuzzleBaseUrl + '{gameId}/' : '/games/api/update-puzzle/{gameId}/';

    const saveLoadManager = new SaveLoadManager({
        saveUrl: saveUrl,
        loadUrl: loadUrl,
        updateUrlTemplate: updateTemplate,
        getState: getPuzzleState,
        applyState: applyLoadedState,
        controls: { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
    });
    
    saveLoadManager.displayGameList = (puzzles) => displayPuzzleList(loadListContainer, puzzles);
    saveLoadManager.formatGameListItem = (puzzle) => `${puzzle.name} (${puzzle.grid_size}x${puzzle.grid_size})`;
    
    saveLoadManager.prepareFormData = (gameState) => {
        return createPuzzleFormData(gameState);
    };
    
    if (presets.length > 0 && !localPuzzleParams.selectedImage) {
        presets[0].click();
    }
    
    puzzleContainer.innerHTML = '<p class="initial-message">Выберите настройки и нажмите "Начать игру"</p>';
    message.style.display = 'none';
    
    console.log("Страница пазла инициализирована");
}

/**
 * Создает интерактивный пазл внутри игрового контейнера на доске.
 * 
 * @param {HTMLElement} gameWrapper - Родительский контейнер для пазла
 * @param {string | null} boardRoomName - Имя комнаты доски
 * @param {string} gameInstanceId - Уникальный ID этого экземпляра пазла
 */
function createPuzzleOnBoard(gameWrapper, boardRoomName, gameInstanceId) {
    // Создаём экземпляр класса PuzzleGame (наследник GameBase)
    const puzzleGame = new PuzzleGame({
        container: gameWrapper,
        gameId: gameInstanceId,
        boardRoomName: boardRoomName,
        name: `Пазл ${gameInstanceId.split('-')[1] || ''}`,
        gridSize: 2,
        type: 'puzzle',
        onWhiteboard: true
    });
    
    // Сохраняем экземпляр класса для доступа из других функций
    gameWrapper.puzzleGame = puzzleGame;
    
    // Для обратной совместимости сохраняем ссылку на параметры
    gameWrapper.puzzleParams = puzzleGame.params;
    gameWrapper.puzzleContainer = puzzleGame.puzzleContainer;
    gameWrapper.puzzleMessage = puzzleGame.messageElement;
    
    const closeButton = gameWrapper.querySelector('.paste-game-close');
    const resizeHandle = gameWrapper.querySelector('.resize-handle');
    gameWrapper.innerHTML = '';
    
    if (closeButton) gameWrapper.appendChild(closeButton);
    if (resizeHandle) gameWrapper.appendChild(resizeHandle);
    gameWrapper.appendChild(puzzleGame.puzzleContainer);
    gameWrapper.appendChild(puzzleGame.messageElement);
    
    puzzleGame.puzzleContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Активируйте пазл и выберите настройки в панели справа.</p>';
    puzzleGame.messageElement.style.display = 'none';
    
    // Инициализация WebSocket через метод базового класса
    if (boardRoomName && gameInstanceId) {
        puzzleGame.initWebSocket();
        gameWrapper.puzzleWebSocket = puzzleGame.ws;
        puzzleGame.params.ws = puzzleGame.ws;
    } else {
        console.log(`[PUZZLE INSTANCE: ${gameInstanceId}] Running in local mode (no WebSocket).`);
    }
    
    console.log(`Экземпляр пазла ${gameInstanceId} инициализирован на доске.`);
}

/**
 * Настраивает контролы и Save/Load для активного пазла на доске.
 * 
 * @param {HTMLElement} activeGameWrapper - Активный игровой контейнер пазла
 */
function setupWhiteboardPuzzleSaveLoad(activeGameWrapper) {
    if (!activeGameWrapper || !activeGameWrapper.puzzleGame) {
        console.warn("Активный пазл на доске не найден или не инициализирован.");
        return;
    }
    
    const puzzleGame = activeGameWrapper.puzzleGame;
    const activePuzzleParams = puzzleGame.params;
    const settingsPanel = document.querySelector('.settings-panel');
    
    if (!settingsPanel) {
        console.error("Панель настроек не найдена.");
        return;
    }
    
    const puzzleNameInput = settingsPanel.querySelector('#puzzle-name');
    const customInput = settingsPanel.querySelector('#custom-image');
    const difficultySelect = settingsPanel.querySelector('#difficulty');
    const presetsNodeList = settingsPanel.querySelectorAll('.preset');
    const saveButton = settingsPanel.querySelector('#save-puzzle-btn');
    const loadButton = settingsPanel.querySelector('#load-puzzle-btn');
    const startBtnOnPanel = settingsPanel.querySelector('#start-game');
    const loadModal = document.getElementById('load-game-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');
    
    if (!puzzleNameInput || !customInput || !difficultySelect || !presetsNodeList?.length || !saveButton || !loadButton) {
        console.error("Ключевые элементы управления пазлом отсутствуют.");
        return;
    }
    
    const presets = Array.from(presetsNodeList);
    
    if (startBtnOnPanel) {
        startBtnOnPanel.style.display = 'none';
    }
    
    if (activePuzzleParams.id && saveButton) {
        saveButton.textContent = "Обновить пазл";
        saveButton.dataset.action = 'update';
        saveButton.dataset.puzzleId = activePuzzleParams.id;
    } else if (saveButton) {
        saveButton.textContent = "Сохранить";
        saveButton.dataset.action = 'create';
        delete saveButton.dataset.puzzleId;
    }
    
    const handlePuzzleStateChangeForBoard = (changedParams) => {
        if (changedParams.onWhiteboard && changedParams.ws && changedParams.ws.readyState === WebSocket.OPEN) {
            changedParams.ws.send(JSON.stringify({
                type: 'puzzle_state_change',
                puzzleState: {
                    gridSize: changedParams.gridSize,
                    piecePositions: changedParams.piecePositions,
                    selectedImage: changedParams.selectedImage,
                    isPreset: changedParams.isPreset,
                    name: changedParams.name,
                    id: changedParams.id
                }
            }));
        }
        
        if (puzzleNameInput && typeof changedParams.name !== 'undefined') {
            puzzleNameInput.value = changedParams.name;
        }
    };
    
    setupPuzzleControls({
        customInput, presets, difficultySelect, startBtn: null,
        puzzleParams: activePuzzleParams,
        puzzleContainer: activeGameWrapper.puzzleContainer,
        message: activeGameWrapper.puzzleMessage,
        instantUpdate: true,
        onStateChange: handlePuzzleStateChangeForBoard,
        saveBtnRef: saveButton
    });
    
    puzzleNameInput.value = activePuzzleParams.name || '';
    difficultySelect.value = activePuzzleParams.gridSize;
    customInput.value = '';
    
    const previewContainer = settingsPanel.querySelector('#image-preview-container');
    const previewImg = settingsPanel.querySelector('#image-preview');
    const previewText = settingsPanel.querySelector('#image-preview-text');
    presets.forEach(p => p.classList.remove('selected'));
    
    if (previewContainer) previewContainer.style.display = 'none';
    
    if (activePuzzleParams.isPreset && activePuzzleParams.selectedImage) {
        const selectedPresetElement = presets.find(p => (p.dataset.src || p.src) === activePuzzleParams.selectedImage);
        if (selectedPresetElement) selectedPresetElement.classList.add('selected');
    } else if (!activePuzzleParams.isPreset && activePuzzleParams.selectedImage) {
        if (previewContainer && previewImg && previewText) {
            previewImg.src = activePuzzleParams.selectedImage;
            previewText.textContent = activePuzzleParams.imageFile ? `Загружено: ${activePuzzleParams.imageFile.name}` : (activePuzzleParams.name || 'Загруженное изображение');
            previewContainer.style.display = 'block';
        }
    }
    
    const getPuzzleStateForWhiteboard = () => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');
        
        if (!currentActiveWrapper || currentActiveWrapper !== activeGameWrapper || !currentActiveWrapper.puzzleGame) {
            alert("Активный пазл изменился или не найден. Сохранение отменено.");
            return null;
        }
        
        const params = currentActiveWrapper.puzzleGame.params;
        params.name = puzzleNameInput.value.trim();
        
        if (!params.name) {
            alert("Введите название для сохранения.");
            puzzleNameInput.focus();
            return null;
        }
        
        if (!params.piecePositions || params.piecePositions.length !== params.gridSize * params.gridSize) {
            createPuzzle(currentActiveWrapper.puzzleContainer, params, currentActiveWrapper.puzzleMessage, false);
        }
        
        if (!params.piecePositions || params.piecePositions.length !== params.gridSize * params.gridSize) {
            alert("Ошибка: Не удалось инициализировать элементы пазла для сохранения.");
            return null;
        }
        
        return preparePuzzleSaveData(params, presets, customInput, true);
    };
    
    const applyLoadedStateForWhiteboard = (loadedDbPuzzleData) => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');
        
        if (!currentActiveWrapper || currentActiveWrapper !== activeGameWrapper || !currentActiveWrapper.puzzleGame) {
            alert("Активный пазл изменился или не найден. Загрузка отменена.");
            return;
        }
        
        const targetParams = currentActiveWrapper.puzzleGame.params;
        
        targetParams.id = loadedDbPuzzleData.id;
        targetParams.name = loadedDbPuzzleData.name;
        targetParams.gridSize = loadedDbPuzzleData.grid_size;
        targetParams.piecePositions = loadedDbPuzzleData.piece_positions || [];
        targetParams.selectedImage = loadedDbPuzzleData.image_url;
        targetParams.isPreset = !!loadedDbPuzzleData.preset_path;
        targetParams.imageFile = null;
        
        puzzleNameInput.value = targetParams.name;
        difficultySelect.value = targetParams.gridSize;
        customInput.value = '';
        
        const currentSettingsPanel = document.querySelector('.settings-panel');
        if (currentSettingsPanel) {
            const currentSaveButton = currentSettingsPanel.querySelector('#save-puzzle-btn');
            if (currentSaveButton) {
                currentSaveButton.textContent = 'Обновить пазл';
                currentSaveButton.dataset.action = 'update';
                currentSaveButton.dataset.puzzleId = loadedDbPuzzleData.id;
            }
        }
        
        createPuzzle(currentActiveWrapper.puzzleContainer, targetParams, currentActiveWrapper.puzzleMessage, true);
        
        if (targetParams.onWhiteboard && targetParams.ws && targetParams.ws.readyState === WebSocket.OPEN) {
            targetParams.ws.send(JSON.stringify({
                type: 'puzzle_state_change',
                puzzleState: {
                    gridSize: targetParams.gridSize,
                    piecePositions: targetParams.piecePositions,
                    selectedImage: targetParams.selectedImage,
                    isPreset: targetParams.isPreset,
                    name: targetParams.name,
                    id: targetParams.id
                }
            }));
        }
        
        alert(`Пазл "${loadedDbPuzzleData.name}" загружен в активный контейнер.`);
    };
    
    const saveUrl = typeof savePuzzleUrl !== 'undefined' ? savePuzzleUrl : '/games/api/save-puzzle/';
    const loadUrl = typeof loadPuzzlesUrl !== 'undefined' ? loadPuzzlesUrl : '/games/api/load-puzzles/';
    const updateTemplate = typeof updatePuzzleBaseUrl !== 'undefined' ? updatePuzzleBaseUrl + '{gameId}/' : '/games/api/update-puzzle/{gameId}/';

    const saveLoadManager = new SaveLoadManager({
        saveUrl: saveUrl,
        loadUrl: loadUrl,
        updateUrlTemplate: updateTemplate,
        getState: getPuzzleStateForWhiteboard,
        applyState: applyLoadedStateForWhiteboard,
        controls: { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
    });
    
    saveLoadManager.displayGameList = (puzzles) => displayPuzzleList(loadListContainer, puzzles);
    saveLoadManager.formatGameListItem = (puzzle) => `${puzzle.name} (${puzzle.grid_size}x${puzzle.grid_size})`;
    
    saveLoadManager.prepareFormData = (gameState) => {
        return createPuzzleFormData(gameState);
    };
    
    console.log("UI и Save/Load для активного пазла на доске успешно настроены.");
}

/**
 * Назначает обработчики для пользовательского изображения, пресетов и сложности.
 * 
 * @param {Object} options - Объект с параметрами настройки
 */
function setupPuzzleControls(options) {
    const {
        customInput, presets, difficultySelect, startBtn,
        puzzleParams, puzzleContainer, message,
        instantUpdate = false, onStateChange, saveBtnRef
    } = options;
    
    if (!customInput || !presets || !difficultySelect || !puzzleParams || !puzzleContainer || !message) {
        console.error("Настройка элементов управления: отсутствуют необходимые элементы.");
        return;
    }
    
    const resetToCreateModeIfNeeded = () => {
        if (puzzleParams.id && saveBtnRef) {
            if (!saveBtnRef.dataset.originalTextCreate) {
                saveBtnRef.dataset.originalTextCreate = saveBtnRef.textContent;
            }
            puzzleParams.id = null;
            delete saveBtnRef.dataset.puzzleId;
            saveBtnRef.dataset.action = 'create';
            saveBtnRef.textContent = saveBtnRef.dataset.originalTextCreate || 'Сохранить';
        }
    };
    
    const customImageHandler = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                if (puzzleParams.selectedImage !== reader.result) {
                    resetToCreateModeIfNeeded();
                }
                puzzleParams.selectedImage = reader.result;
                puzzleParams.isPreset = false;
                puzzleParams.imageFile = file;
                presets.forEach(p => p.classList.remove('selected'));
                
                const previewContainer = document.getElementById('image-preview-container');
                const previewImg = document.getElementById('image-preview');
                const previewText = document.getElementById('image-preview-text');
                
                if (previewContainer && previewImg && previewText) {
                    previewImg.src = reader.result;
                    previewText.textContent = `Используется: ${file.name}`;
                    previewContainer.style.display = 'block';
                }
                
                if (instantUpdate) {
                    createPuzzle(puzzleContainer, puzzleParams, message, false);
                }
                
                if (onStateChange) onStateChange(puzzleParams);
            };
            reader.readAsDataURL(file);
        } else {
            if (puzzleParams.selectedImage && puzzleParams.selectedImage.startsWith('data:image')) {
                puzzleParams.selectedImage = null;
                puzzleParams.imageFile = null;
                const previewContainer = document.getElementById('image-preview-container');
                if (previewContainer) previewContainer.style.display = 'none';
                if (instantUpdate) puzzleContainer.innerHTML = '<p>Выберите изображение</p>';
            }
            if (onStateChange) onStateChange(puzzleParams);
        }
    };
    
    customInput.removeEventListener('change', customInput.changeHandler);
    customInput.addEventListener('change', customImageHandler);
    customInput.changeHandler = customImageHandler;
    
    presets.forEach(preset => {
        const presetClickHandler = () => {
            presets.forEach(p => p.classList.remove('selected'));
            preset.classList.add('selected');
            
            if (puzzleParams.selectedImage !== preset.dataset.src) {
                resetToCreateModeIfNeeded();
            }
            
            puzzleParams.selectedImage = preset.dataset.src;
            puzzleParams.isPreset = true;
            puzzleParams.imageFile = null;
            customInput.value = '';
            
            const previewContainer = document.getElementById('image-preview-container');
            if (previewContainer) previewContainer.style.display = 'none';
            
            if (instantUpdate) {
                createPuzzle(puzzleContainer, puzzleParams, message, false);
            }
            
            if (onStateChange) onStateChange(puzzleParams);
        };
        
        preset.removeEventListener('click', preset.clickHandler);
        preset.addEventListener('click', presetClickHandler);
        preset.clickHandler = presetClickHandler;
    });
    
    const difficultyHandler = (e) => {
        const newSize = parseInt(e.target.value, 10);
        if (newSize !== puzzleParams.gridSize) {
            resetToCreateModeIfNeeded();
            puzzleParams.gridSize = newSize;
            puzzleParams.piecePositions = [];
            
            if (instantUpdate) {
                createPuzzle(puzzleContainer, puzzleParams, message, false);
            }
            
            if (onStateChange) onStateChange(puzzleParams);
        }
    };
    
    difficultySelect.removeEventListener('change', difficultySelect.changeHandler);
    difficultySelect.addEventListener('change', difficultyHandler);
    difficultySelect.changeHandler = difficultyHandler;
    
    if (startBtn) {
        const startHandler = () => {
            if (!puzzleParams.selectedImage) {
                alert("Пожалуйста, выберите или загрузите изображение.");
                return;
            }
            
            const useLoadedPositions = puzzleParams.piecePositions && puzzleParams.piecePositions.length === puzzleParams.gridSize * puzzleParams.gridSize;
            createPuzzle(puzzleContainer, puzzleParams, message, useLoadedPositions);
            
            if (onStateChange) {
                onStateChange(puzzleParams);
            }
        };
        
        startBtn.removeEventListener('click', startBtn.clickHandler);
        startBtn.addEventListener('click', startHandler);
        startBtn.clickHandler = startHandler;
    }
}

// Делаем функцию доступной глобально для вызова из HTML
window.createPuzzleSeparately = createPuzzleSeparately;

// Экспорт для использования в whiteboard
export { createPuzzleOnBoard, setupWhiteboardPuzzleSaveLoad };