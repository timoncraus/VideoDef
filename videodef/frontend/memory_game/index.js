/**
 * Главный модуль игры "Поиск пар".
 * Инициализирует интерфейс и логику для отдельной страницы и доски.
 */

import { getGameParts, initializeBoard, stopTimer, getFullPresetImageUrls, PRESET_IMAGE_SETS_CONFIG, applyRemoteCardClick } from './logic.js';
import { displayMemoryGameList, findPresetNameByUrl, prepareMemoryGameSaveData, createMemoryGameFormData, prepareMemoryGameSaveDataForWhiteboard } from './save-load.js';
import { SaveLoadManager } from '../common/save-load.js';
import { MemoryGameGame } from './game-class.js';

/**
 * Инициализирует интерфейс и логику для отдельной страницы игры "Поиск пар".
 */
function createMemoryGameSeparately() {
    const gameWrapper = document.getElementById('memory-game-wrapper');
    const settingsPanel = document.querySelector('.game-settings-panel');
    const startButton = settingsPanel?.querySelector('#start-memory-game');
    
    if (!gameWrapper || !settingsPanel || !startButton) {
        console.error("Не найдены основные элементы для отдельной страницы игры 'Поиск пар'.");
        return;
    }
    
    let localGameParams = getGameParts();
    
    const saveButton = document.getElementById('save-memory-game-btn');
    const loadButton = document.getElementById('load-memory-game-btn');
    const loadModal = document.getElementById('load-game-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');
    
    const handleSettingsChange = () => {
        localGameParams.id = null;
        localGameParams.card_layout = [];
        if (saveButton) saveButton.textContent = 'Сохранить';
        gameWrapper.innerHTML = '<p class="initial-message">Настройки изменены. Нажмите "Начать игру".</p>';
    };
    
    setupGameControls(settingsPanel, localGameParams, handleSettingsChange);
    
    startButton.onclick = () => {
        const useExistingLayout = !!(localGameParams.id && localGameParams.card_layout && localGameParams.card_layout.length > 0);
        initializeBoard(gameWrapper, localGameParams, useExistingLayout);
    };
    
    const getGameState = (skipAlerts = false) => {
        const gameNameInput = settingsPanel.querySelector('#game-name');
        localGameParams.name = gameNameInput.value.trim();
        return prepareMemoryGameSaveData(localGameParams, skipAlerts);
    };
    
    const applyLoadedState = (loadedData, showStartMessage = true) => {
        const isUpdateConfirmation = Object.keys(loadedData).length === 1 && loadedData.id && !showStartMessage;
        if (isUpdateConfirmation) {
            localGameParams.id = loadedData.id;
            return;
        }
        
        const mappedLoadedData = { ...loadedData, pairCount: loadedData.pair_count };
        delete mappedLoadedData.pair_count;
        Object.assign(localGameParams, mappedLoadedData);
        
        localGameParams.isCustomSet = !!loadedData.custom_image_urls;
        if (localGameParams.isCustomSet) {
            localGameParams.selectedImageSet = loadedData.custom_image_urls;
            localGameParams.customImageObjects = loadedData.custom_image_urls.map(url => ({ url, file: null }));
        } else {
            localGameParams.selectedImageSet = getFullPresetImageUrls(loadedData.preset_name);
            localGameParams.customImageObjects = [];
        }
        
        setupGameControls(settingsPanel, localGameParams, handleSettingsChange);
        
        if (saveButton) saveButton.textContent = 'Обновить';
        
        if (showStartMessage) {
            alert(`Игра "${localGameParams.name}" загружена. Нажмите "Начать игру" для запуска.`);
            gameWrapper.innerHTML = '<p class="initial-message">Игра загружена. Нажмите "Начать игру".</p>';
        }
    };
    
    const saveUrl = typeof saveMemoryGameUrl !== 'undefined' ? saveMemoryGameUrl : '/games/api/save-memory-game/';
    const loadUrl = typeof loadMemoryGamesUrl !== 'undefined' ? loadMemoryGamesUrl : '/games/api/load-memory-games/';
    const updateTemplate = typeof updateMemoryGameBaseUrl !== 'undefined' ? updateMemoryGameBaseUrl.replace('0', '{gameId}') : '/games/api/update-memory-game/{gameId}/';

    const saveLoadManager = new SaveLoadManager({
        saveUrl: saveUrl,
        loadUrl: loadUrl,
        updateUrlTemplate: updateTemplate,
        getState: getGameState,
        applyState: applyLoadedState,
        controls: { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
    });
    
    saveLoadManager.displayGameList = (games) => displayMemoryGameList(loadListContainer, games);
    saveLoadManager.formatGameListItem = (game) => `${game.name} (${game.pair_count} пар)`;
    saveLoadManager.prepareFormData = (gameState) => createMemoryGameFormData(gameState);
    
    console.log("Страница игры 'Поиск пар' инициализирована.");
}

/**
 * Создает интерактивную игру "Поиск пар" внутри контейнера на доске.
 * 
 * @param {HTMLElement} gameWrapper - Родительский контейнер для игры
 * @param {string | null} boardRoomName - Имя комнаты доски
 * @param {string} gameInstanceId - Уникальный ID этого экземпляра игры на доске
 */
function createMemoryGameOnBoard(gameWrapper, boardRoomName, gameInstanceId) {
    // Создаём экземпляр класса MemoryGameGame (наследник GameBase)
    const memoryGameGame = new MemoryGameGame({
        gameId: gameInstanceId,
        boardRoomName: boardRoomName,
        name: `Поиск пар ${gameInstanceId.split('-')[1] || ''}`,
        type: 'memory_game',
        onWhiteboard: true
    });
    
    // Сохраняем экземпляр класса для доступа из других функций
    gameWrapper.memoryGameGame = memoryGameGame;
    
    // Для обратной совместимости сохраняем ссылку на параметры
    gameWrapper.memoryGameParams = memoryGameGame.params;
    
    //Создаем новый контейнер явно и очищаем wrapper перед добавлением
    const gameContainer = document.createElement('div');
    gameContainer.className = "memory-game-wrapper";
    
    // Очищаем wrapper от старого содержимого, но сохраняем кнопку закрытия и resize-handle если они есть
    const closeButton = gameWrapper.querySelector('.paste-game-close');
    const resizeHandle = gameWrapper.querySelector('.resize-handle');
    
    gameWrapper.innerHTML = '';
    
    if (closeButton) gameWrapper.appendChild(closeButton);
    if (resizeHandle) gameWrapper.appendChild(resizeHandle);
    
    gameWrapper.appendChild(gameContainer);
    
    // Сохраняем ссылку на контейнер в wrapper и в игре
    gameWrapper.gameContainer = gameContainer;
    memoryGameGame.gameContainer = gameContainer;
    
    gameContainer.innerHTML = '<p class="initial-message">Активируйте игру и выберите настройки в панели справа.</p>';
    
    // Инициализация WebSocket через метод базового класса
    if (boardRoomName && gameInstanceId) {
        memoryGameGame.initWebSocket();
        gameWrapper.memoryGameWebSocket = memoryGameGame.ws;
        memoryGameGame.params.ws = memoryGameGame.ws;
    } else {
        console.log(`[MemoryGame INSTANCE: ${gameInstanceId}] Running in local mode (no WebSocket).`);
    }
    
    console.log(`Экземпляр игры "Поиск пар" ${gameInstanceId} инициализирован на доске.`);
}

/**
 * Настраивает панель настроек для активной игры "Поиск пар" на доске.
 * 
 * @param {HTMLElement} activeGameWrapper - Активный игровой контейнер.
 */
function setupWhiteboardMemoryGame(activeGameWrapper) {
    if (!activeGameWrapper || !activeGameWrapper.memoryGameGame) {
        console.warn("Активная игра 'Поиск пар' не найдена или не инициализирована.");
        return;
    }
    
    const memoryGameGame = activeGameWrapper.memoryGameGame;
    const activeGameParams = memoryGameGame.params;
    const settingsPanel = document.querySelector('.settings-panel');
    
    if (!settingsPanel) {
        console.error("Панель настроек не найдена.");
        return;
    }
    
    const startButton = settingsPanel.querySelector('#start-memory-game');
    const saveButton = settingsPanel.querySelector('#save-memory-game-btn');
    const loadButton = settingsPanel.querySelector('#load-memory-game-btn');
    const loadModal = document.getElementById('load-game-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');
    
    if (!startButton || !saveButton || !loadButton || !loadModal) {
        console.error("Ключевые элементы управления отсутствуют на панели настроек!");
        return;
    }
    
    const handleGameStateChangeForBoard = () => {
        if (activeGameParams.onWhiteboard && activeGameParams.ws && activeGameParams.ws.readyState === WebSocket.OPEN) {
            activeGameParams.card_layout = [];
            activeGameParams.attempts = 0;
            
            const imageSetToSend = activeGameParams.isCustomSet ? activeGameParams.customImageObjects.map(obj => obj.url) : activeGameParams.selectedImageSet;
            const stateToSend = {
                id: activeGameParams.id,
                name: activeGameParams.name,
                pairCount: activeGameParams.pairCount,
                selectedImageSet: imageSetToSend,
                isCustomSet: activeGameParams.isCustomSet,
                card_layout: [],
                attempts: 0,
            };
            
            activeGameParams.ws.send(JSON.stringify({ type: 'game_state_change', gameState: stateToSend }));
        }
    };
    
    setupGameControls(settingsPanel, activeGameParams, handleGameStateChangeForBoard);
    
    const startButtonClickHandler = () => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');
        
        if (currentActiveWrapper && currentActiveWrapper === activeGameWrapper && currentActiveWrapper.memoryGameGame) {
            initializeBoard(currentActiveWrapper.gameContainer, currentActiveWrapper.memoryGameGame.params, false);
        } else {
            console.warn("Активная игра изменилась, действие 'Перемешать' отменено.");
        }
    };
    
    startButton.removeEventListener('click', startButton.clickHandler);
    startButton.addEventListener('click', startButtonClickHandler);
    startButton.clickHandler = startButtonClickHandler;
    
    const getGameStateForWhiteboard = (skipAlerts = false) => {
        const gameNameInput = settingsPanel.querySelector('#game-name');
        activeGameParams.name = gameNameInput.value.trim();
        
        if (!activeGameParams.card_layout || activeGameParams.card_layout.length === 0) {
            initializeBoard(activeGameWrapper.gameContainer, activeGameParams, false);
        }
        
        return prepareMemoryGameSaveDataForWhiteboard(activeGameParams, skipAlerts);
    };
    
    const applyLoadedStateForWhiteboard = (loadedData, startNewGame = true) => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');
        if (!currentActiveWrapper || currentActiveWrapper !== activeGameWrapper) {
            alert("Активная игра изменилась. Загрузка отменена.");
            return;
        }
        
        const isUpdateConfirmation = Object.keys(loadedData).length === 1 && loadedData.id && !startNewGame;
        if (isUpdateConfirmation) {
            activeGameParams.id = loadedData.id;
            return; 
        }
        
        const mappedLoadedData = { ...loadedData, pairCount: loadedData.pair_count, attempts: loadedData.attempts || 0 };
        delete mappedLoadedData.pair_count;
        Object.assign(activeGameParams, mappedLoadedData);
        
        activeGameParams.isCustomSet = !!loadedData.custom_image_urls;
        if (activeGameParams.isCustomSet) {
            activeGameParams.selectedImageSet = loadedData.custom_image_urls;
            activeGameParams.customImageObjects = loadedData.custom_image_urls.map(url => ({ url: url, file: null }));
        } else {
            activeGameParams.selectedImageSet = getFullPresetImageUrls(loadedData.preset_name);
            activeGameParams.customImageObjects = [];
        }
        
        setupGameControls(settingsPanel, activeGameParams, handleGameStateChangeForBoard);
        saveButton.textContent = 'Обновить';
        
        if (startNewGame) {
            const useExistingLayout = loadedData.card_layout && loadedData.card_layout.length > 0;
            initializeBoard(activeGameWrapper.gameContainer, activeGameParams, useExistingLayout);
            
            if (activeGameParams.onWhiteboard && activeGameParams.ws && activeGameParams.ws.readyState === WebSocket.OPEN) {
                console.log(`[APPLY LOADED] Отправка загруженного состояния игры ${activeGameParams.gameId}`);
                
                const stateToSend = {
                    id: activeGameParams.id,
                    name: activeGameParams.name,
                    pairCount: activeGameParams.pairCount,
                    selectedImageSet: activeGameParams.selectedImageSet,
                    isCustomSet: activeGameParams.isCustomSet,
                    card_layout: activeGameParams.card_layout || [],
                    attempts: activeGameParams.attempts || 0
                };
                
                activeGameParams.ws.send(JSON.stringify({ type: 'game_state_change', gameState: stateToSend }));
            }
            
            alert(`Игра "${loadedData.name}" загружена в активный контейнер.`);
        }
    };
    
    const saveUrl = typeof saveMemoryGameUrl !== 'undefined' ? saveMemoryGameUrl : '/games/api/save-memory-game/';
    const loadUrl = typeof loadMemoryGamesUrl !== 'undefined' ? loadMemoryGamesUrl : '/games/api/load-memory-games/';
    const updateTemplate = typeof updateMemoryGameBaseUrl !== 'undefined' ? updateMemoryGameBaseUrl.replace('0', '{gameId}') : '/games/api/update-memory-game/{gameId}/';

    const saveLoadManager = new SaveLoadManager({
        saveUrl: saveUrl,
        loadUrl: loadUrl,
        updateUrlTemplate: updateTemplate,
        getState: getGameStateForWhiteboard,
        applyState: applyLoadedStateForWhiteboard,
        controls: { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
    });
    
    saveLoadManager.displayGameList = (games) => displayMemoryGameList(loadListContainer, games);
    saveLoadManager.formatGameListItem = (game) => `${game.name} (${game.pair_count} пар)`;
    saveLoadManager.prepareFormData = (gameState) => createMemoryGameFormData(gameState);
    
    const gameNameInput = settingsPanel.querySelector('#game-name');
    const pairCountSelect = settingsPanel.querySelector('#pair-count-select');
    if (gameNameInput) gameNameInput.value = activeGameParams.name || '';
    if (pairCountSelect) pairCountSelect.value = activeGameParams.pairCount;
    saveButton.textContent = activeGameParams.id ? 'Обновить' : 'Сохранить';
}

/**
 * Универсальная функция для настройки контролов игры "Поиск пар".
 * 
 * @param {HTMLElement} settingsContainer - Контейнер с элементами настроек.
 * @param {Object} gameParams - Объект с параметрами игры для изменения.
 * @param {Function | null} onSettingsChange - Колбэк, вызываемый при изменении настроек.
 */
function setupGameControls(settingsContainer, gameParams, onSettingsChange) {
    const gameNameInput = settingsContainer.querySelector('#game-name');
    const pairCountSelect = settingsContainer.querySelector('#pair-count-select');
    const presetSetElements = settingsContainer.querySelectorAll('.preset-set');
    const customImagesInput = settingsContainer.querySelector('#custom-images-input');
    const customImagesPreviewContainer = settingsContainer.querySelector('#custom-images-preview');
    const previewGrid = customImagesPreviewContainer?.querySelector('.preview-grid');
    const customImagesInfoText = customImagesPreviewContainer?.querySelector('#custom-images-info-text');
    
    if (!gameNameInput || !pairCountSelect || !presetSetElements.length || !customImagesInput || !previewGrid || !customImagesInfoText) {
        console.error("Не удалось найти все элементы управления в 'setupGameControls'.");
        return;
    }
    
    gameNameInput.value = gameParams.name || '';
    pairCountSelect.value = gameParams.pairCount;
    updateCustomImagePreviewUI(gameParams, customImagesPreviewContainer, customImagesInfoText, previewGrid);
    
    const activePresetName = gameParams.isCustomSet ? null : findPresetNameByUrl(gameParams.selectedImageSet[0]);
    presetSetElements.forEach(el => {
        el.classList.toggle('selected', el.dataset.setName === activePresetName);
    });
    
    const gameNameInputHandler = (e) => {
        gameParams.name = e.target.value.trim();
    };
    
    gameNameInput.removeEventListener('input', gameNameInput.inputHandler);
    gameNameInput.addEventListener('input', gameNameInputHandler);
    gameNameInput.inputHandler = gameNameInputHandler;
    
    const pairCountSelectHandler = (e) => {
        gameParams.pairCount = parseInt(e.target.value, 10);
        if (onSettingsChange) onSettingsChange();
    };
    
    pairCountSelect.removeEventListener('change', pairCountSelect.changeHandler);
    pairCountSelect.addEventListener('change', pairCountSelectHandler);
    pairCountSelect.changeHandler = pairCountSelectHandler;
    
    presetSetElements.forEach(presetEl => {
        const presetClickHandler = () => {
            if (presetEl.classList.contains('selected') && !gameParams.isCustomSet) return;
            
            presetSetElements.forEach(el => el.classList.remove('selected'));
            presetEl.classList.add('selected');
            
            gameParams.selectedImageSet = getFullPresetImageUrls(presetEl.dataset.setName);
            gameParams.isCustomSet = false;
            gameParams.customImageObjects = [];
            customImagesInput.value = '';
            
            updateCustomImagePreviewUI(gameParams, customImagesPreviewContainer, customImagesInfoText, previewGrid);
            
            if (onSettingsChange) onSettingsChange();
        };
        
        presetEl.removeEventListener('click', presetEl.clickHandler);
        presetEl.addEventListener('click', presetClickHandler);
        presetEl.clickHandler = presetClickHandler;
    });
    
    const customImagesInputChangeHandler = (event) => {
        const files = event.target.files;
        gameParams.customImageObjects = [];
        
        if (files.length > 0) {
            gameParams.isCustomSet = true;
            presetSetElements.forEach(el => el.classList.remove('selected'));
            
            let loadedCount = 0;
            const totalFiles = files.length;
            
            Array.from(files).forEach(file => {
                if (!file.type.startsWith('image/')) {
                    if (++loadedCount === totalFiles && onSettingsChange) onSettingsChange();
                    return;
                }
                
                const reader = new FileReader();
                reader.onload = (e) => {
                    gameParams.customImageObjects.push({ url: e.target.result, file });
                    
                    if (++loadedCount === totalFiles) {
                        updateCustomImagePreviewUI(gameParams, customImagesPreviewContainer, customImagesInfoText, previewGrid);
                        if (onSettingsChange) onSettingsChange();
                    }
                };
                reader.onerror = () => {
                    if (++loadedCount === totalFiles && onSettingsChange) onSettingsChange();
                };
                reader.readAsDataURL(file);
            });
        } else {
            gameParams.isCustomSet = false;
            const selectedPreset = settingsContainer.querySelector('.preset-set.selected') || presetSetElements[0];
            if (selectedPreset && typeof selectedPreset.clickHandler === 'function') {
                selectedPreset.clickHandler();
            }
        }
    };
    
    customImagesInput.removeEventListener('change', customImagesInput.changeHandler);
    customImagesInput.addEventListener('change', customImagesInputChangeHandler);
    customImagesInput.changeHandler = customImagesInputChangeHandler;
}

/**
 * Обновляет UI для предпросмотра пользовательских изображений на панели настроек.
 * 
 * @param {Object} params - Параметры игры.
 * @param {HTMLElement} previewContainer - Контейнер для предпросмотра.
 * @param {HTMLElement} infoText - Элемент с информацией.
 * @param {HTMLElement} grid - Сетка для превью.
 */
function updateCustomImagePreviewUI(params, previewContainer, infoText, grid) {
    if (!grid || !infoText || !previewContainer) return;
    
    grid.innerHTML = '';
    
    const sourceObjects = params.isCustomSet
        ? (params.customImageObjects.length > 0 ? params.customImageObjects : (params.selectedImageSet || []).map(url => ({url})))
        : [];
    
    if (params.isCustomSet && sourceObjects.length > 0) {
        infoText.innerHTML = `Загружено изображений: <span>${sourceObjects.length}</span>`;
        
        sourceObjects.forEach(imgObj => {
            const imgPreview = document.createElement('img');
            imgPreview.src = imgObj.url;
            imgPreview.alt = "preview";
            imgPreview.classList.add('preview-thumb');
            grid.appendChild(imgPreview);
        });
        
        previewContainer.style.display = 'block';
    } else {
        infoText.innerHTML = 'Загружено изображений: <span id="custom-images-count">0</span>';
        previewContainer.style.display = 'none';
    }
}

// Делаем функцию доступной глобально для вызова из HTML
window.createMemoryGameSeparately = createMemoryGameSeparately;

// Экспорт для использования в whiteboard
export { createMemoryGameOnBoard, setupWhiteboardMemoryGame };