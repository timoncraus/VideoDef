import { getGameParts, initializeBoard, stopTimer, getFullPresetImageUrls, PRESET_IMAGE_SETS_CONFIG } from './memory-game-logic.js'; 

/**
 * Инициализирует интерфейс и логику для отдельной страницы игры "Поиск пар".
 * Находит все необходимые DOM-элементы и назначает им обработчики событий.
 */
export function createMemoryGameSeparately() {
    const gameWrapper = document.getElementById('memory-game-wrapper');
    const settingsPanel = document.querySelector('.game-settings-panel');
    const startButton = settingsPanel?.querySelector('#start-memory-game');
    
    if (!gameWrapper || !settingsPanel || !startButton) {
        console.error("Не найдены основные элементы для отдельной страницы игры 'Поиск пар'.");
        return;
    }

    const localGameParams = getGameParts();
    
    // Настраиваем контролы без мгновенного обновления (onStateChange = null)
    setupGameControls(settingsPanel, localGameParams, null);

    // Кнопка "Начать игру" работает только по клику
    startButton.onclick = () => {
        initializeBoard(gameWrapper, localGameParams);
    };

    console.log("Страница игры 'Поиск пар' инициализирована.");
}

/**
 * Создает интерактивную игру "Поиск пар" внутри контейнера на доске.
 * @param {HTMLElement} gameWrapper - Родительский контейнер для игры (`.paste-game-wrapper`).
 * @param {string | null} boardRoomName - Имя комнаты доски (для URL WebSocket).
 * @param {string} gameInstanceId - Уникальный ID этого экземпляра игры на доске.
 */
export function createMemoryGameOnBoard(gameWrapper, boardRoomName, gameInstanceId) {
    const localGameParams = getGameParts(); 
    
    localGameParams.onWhiteboard = true;
    localGameParams.gameId = gameInstanceId;
    localGameParams.boardRoomName = boardRoomName;
    localGameParams.name = `Поиск пар ${gameInstanceId.split('-')[1] || ''}`;

    gameWrapper.memoryGameParams = localGameParams;
    
    const gameContainer = document.createElement('div');
    gameContainer.className = "memory-game-wrapper"; 
    gameWrapper.gameContainer = gameContainer;

    const closeButton = gameWrapper.querySelector('.paste-game-close');
    const resizeHandle = gameWrapper.querySelector('.resize-handle');
    gameWrapper.innerHTML = '';
    if (closeButton) gameWrapper.appendChild(closeButton);
    if (resizeHandle) gameWrapper.appendChild(resizeHandle);
    
    gameWrapper.appendChild(gameContainer);
    gameContainer.innerHTML = '<p class="initial-message">Активируйте игру и выберите настройки в панели справа.</p>';

    if (boardRoomName && gameInstanceId) {
        const memoryGameWsUrl = `ws://${window.location.host}/ws/memory_game_on_board/${boardRoomName}/${gameInstanceId}/`;
        const memoryGameWs = new WebSocket(memoryGameWsUrl);
        localGameParams.ws = memoryGameWs;
        gameWrapper.memoryGameWebSocket = memoryGameWs;

        memoryGameWs.onopen = () => console.log(`[MemoryGame INSTANCE: ${gameInstanceId}] WebSocket connected.`);
        memoryGameWs.onclose = (e) => console.log(`[MemoryGame INSTANCE: ${gameInstanceId}] WebSocket disconnected.`, e.reason);
        memoryGameWs.onerror = (e) => console.error(`[MemoryGame INSTANCE: ${gameInstanceId}] WebSocket error.`, e);

        memoryGameWs.onmessage = (e) => {
            const data = JSON.parse(e.data);
            console.log(`[MemoryGame INSTANCE: ${gameInstanceId}] WS Received:`, data);

            if (data.type === 'game_state_change') {
                Object.assign(gameWrapper.memoryGameParams, data.gameState); 
                
                if (gameWrapper.classList.contains('active-game')) {
                    setupWhiteboardMemoryGame(gameWrapper); 
                } else {
                    // Если игра не активна, просто перерисовываем ее в фоне
                    initializeBoard(gameWrapper.gameContainer, gameWrapper.memoryGameParams);
                }
            }
        };
    } else {
        // Локальный режим для этого экземпляра поиска пар
        localGameParams.ws = null;
        gameWrapper.memoryGameWebSocket = null;
        console.log(`[MemoryGame INSTANCE: ${gameInstanceId}] Running in local mode (no WebSocket).`);
    }
    console.log(`Экземпляр игры "Поиск пар" ${gameInstanceId} инициализирован на доске.`);
}

/**
 * Настраивает панель настроек для активной игры "Поиск пар" на доске.
 * @param {HTMLElement} activeGameWrapper - Активный игровой контейнер.
 */
export function setupWhiteboardMemoryGame(activeGameWrapper) {
    console.log("Настройка UI для активной игры 'Поиск пар':", activeGameWrapper?.dataset?.id);

    if (!activeGameWrapper || !activeGameWrapper.memoryGameParams || !activeGameWrapper.gameContainer) {
        console.warn("Активная игра 'Поиск пар' не найдена или не инициализирована. Настройка UI пропущена.");
        return;
    }

    const activeGameParams = activeGameWrapper.memoryGameParams;
    const settingsPanel = document.querySelector('.settings-panel');
    const startButton = settingsPanel?.querySelector('#start-memory-game');

    if (!settingsPanel || !startButton) {
        console.error("Панель настроек или кнопка '#start-memory-game' не найдены в DOM!");
        return;
    }
    
    const handleGameStateChangeForBoard = () => {
        if (activeGameParams.onWhiteboard && activeGameParams.ws && activeGameParams.ws.readyState === WebSocket.OPEN) {
            const stateToSend = {
                name: activeGameParams.name,
                pairCount: activeGameParams.pairCount,
                selectedImageSet: activeGameParams.selectedImageSet,
                isCustomSet: activeGameParams.isCustomSet,
                customImageObjects: activeGameParams.isCustomSet ? activeGameParams.customImageObjects.map(obj => ({ url: obj.url })) : [],
            };
            activeGameParams.ws.send(JSON.stringify({
                type: 'game_state_change',
                gameState: stateToSend
            }));
        }
    };

    const updateAndSyncGame = () => {
        initializeBoard(activeGameWrapper.gameContainer, activeGameParams);
        handleGameStateChangeForBoard();
    };

    setupGameControls(settingsPanel, activeGameParams, updateAndSyncGame);
    startButton.onclick = updateAndSyncGame;
    initializeBoard(activeGameWrapper.gameContainer, activeGameParams);
    
    console.log("UI для активной игры 'Поиск пар' настроен и игра отрисована.");
}


/**
 * Универсальная функция для настройки контролов игры "Поиск пар".
 * @param {HTMLElement} settingsContainer - Контейнер с элементами настроек.
 * @param {object} gameParams - Объект с параметрами игры для изменения.
 * @param {function | null} onStateChange - Колбэк для мгновенного обновления. Если null, обновление не происходит.
 */
function setupGameControls(settingsContainer, gameParams, onStateChange) {
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

    // Инициализация UI из текущих параметров
    gameNameInput.value = gameParams.name || '';
    pairCountSelect.value = gameParams.pairCount;
    updateCustomImagePreviewUI(gameParams, customImagesPreviewContainer, customImagesInfoText, previewGrid);
    
    const activePresetName = gameParams.isCustomSet ? null : findPresetNameByUrl(gameParams.selectedImageSet[0]);
    presetSetElements.forEach(el => {
        el.classList.toggle('selected', el.dataset.setName === activePresetName);
    });

    // Назначение обработчиков
    gameNameInput.oninput = (e) => {
        gameParams.name = e.target.value.trim();
        if (onStateChange) onStateChange();
    };

    pairCountSelect.onchange = (e) => {
        gameParams.pairCount = parseInt(e.target.value, 10);
        if (onStateChange) onStateChange();
        else { 
            const gameWrapper = document.getElementById('memory-game-wrapper');
            if (gameWrapper) gameWrapper.innerHTML = '<p class="initial-message">Сложность изменена. Нажмите "Начать игру".</p>';
        }
    };

    presetSetElements.forEach(presetEl => {
        presetEl.onclick = () => {
            presetSetElements.forEach(el => el.classList.remove('selected'));
            presetEl.classList.add('selected');
            const setName = presetEl.dataset.setName;
            gameParams.selectedImageSet = getFullPresetImageUrls(setName);
            gameParams.isCustomSet = false;
            gameParams.customImageObjects = [];
            customImagesInput.value = '';
            updateCustomImagePreviewUI(gameParams, customImagesPreviewContainer, customImagesInfoText, previewGrid);
            if (onStateChange) onStateChange();
        };
    });

    customImagesInput.onchange = (event) => {
        const files = event.target.files;
        gameParams.customImageObjects = [];
        if (files.length > 0) {
            gameParams.isCustomSet = true;
            presetSetElements.forEach(el => el.classList.remove('selected'));
            let loadedCount = 0;
            const totalFiles = files.length;
            Array.from(files).forEach(file => {
                if (!file.type.startsWith('image/')) {
                    if (++loadedCount === totalFiles && onStateChange) onStateChange();
                    return;
                }
                const reader = new FileReader();
                reader.onload = (e) => {
                    gameParams.customImageObjects.push({ url: e.target.result, file });
                    if (++loadedCount === totalFiles) {
                        updateCustomImagePreviewUI(gameParams, customImagesPreviewContainer, customImagesInfoText, previewGrid);
                        if (onStateChange) onStateChange();
                    }
                };
                reader.onerror = () => { if (++loadedCount === totalFiles && onStateChange) onStateChange(); };
                reader.readAsDataURL(file);
            });
        } else {
            gameParams.isCustomSet = false;
            const selectedPreset = settingsContainer.querySelector('.preset-set.selected') || presetSetElements[0];
            if (selectedPreset) selectedPreset.click();
        }
    };
}

/**
 * Обновляет UI для предпросмотра пользовательских изображений на панели настроек.
 */
function updateCustomImagePreviewUI(params, previewContainer, infoText, grid) {
    if (!grid || !infoText || !previewContainer) return;
    grid.innerHTML = '';
    if (params.isCustomSet && params.customImageObjects.length > 0) {
        infoText.innerHTML = `Загружено изображений: <span id="custom-images-count">${params.customImageObjects.length}</span>`;
        params.customImageObjects.forEach(imgObj => {
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

/**
 * Вспомогательная функция для определения имени пресета по URL первого изображения.
 * @param {string} imageUrl - URL изображения.
 * @returns {string|null} Имя пресета или null.
 */
function findPresetNameByUrl(imageUrl) {
    if (!imageUrl || typeof presetImagesBasePath === 'undefined') return null;
    const pathWithoutBase = imageUrl.replace(presetImagesBasePath, '');
    const setName = pathWithoutBase.split('/')[0];
    return PRESET_IMAGE_SETS_CONFIG.hasOwnProperty(setName) ? setName : null;
}

// Экспорт для глобального доступа из whiteboard.js
window.MemoryGameModule = {
    createMemoryGameSeparately,
    createMemoryGameOnBoard,
    setupWhiteboardMemoryGame
};