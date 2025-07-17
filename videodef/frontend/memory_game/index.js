import { getGameParts, initializeBoard, stopTimer, getFullPresetImageUrls, PRESET_IMAGE_SETS_CONFIG, applyRemoteCardClick } from './memory-game-logic.js';

/**
 * Конвертирует строку Data URL в объект Blob.
 * Необходимо для отправки пользовательских изображений на сервер через FormData.
 * @param {string} dataURL - Строка Data URL
 * @returns {Blob|null} - Объект Blob или null в случае ошибки.
 */
function dataURLtoBlob(dataURL) {
    try {
        // Разделяем строку на метаданные (MIME-тип) и данные Base64
        const parts = dataURL.split(';base64,');
        const contentType = parts[0].split(':')[1];
        // Декодируем Base64 строку в бинарную строку
        const raw = window.atob(parts[1]);
        const rawLength = raw.length;
        // Создаем массив 8-битных беззнаковых целых чисел
        const uInt8Array = new Uint8Array(rawLength);
        for (let i = 0; i < rawLength; ++i) {
            uInt8Array[i] = raw.charCodeAt(i);
        }
        // Создаем и возвращаем Blob с указанным MIME-типом
        return new Blob([uInt8Array], { type: contentType });
    } catch (error) {
        console.error("Ошибка конвертации Data URL в Blob:", error);
        return null;
    }
}

/**
 * Отображает список сохраненных игр "Поиск пар".
 * @param {HTMLElement} container - DOM-элемент для списка.
 * @param {Array<object>} games - Массив объектов игр с сервера.
 */
function displayMemoryGameList(container, games) {
    if (!games || games.length === 0) {
        container.innerHTML = '<p>У вас пока нет сохраненных игр этого типа.</p>';
        return;
    }
    const ul = document.createElement('ul');
    games.forEach(game => {
        const li = document.createElement('li');
        let imageInfo = game.preset_name ? `(набор: ${game.preset_name})` : "(свои фото)";
        li.textContent = `${game.name} (${game.pair_count} пар) ${imageInfo}`;
        li.dataset.gameData = JSON.stringify(game);
        li.dataset.id = game.id;
        ul.appendChild(li);
    });
    container.innerHTML = '';
    container.appendChild(ul);
}

/**
 * Инициализирует общую логику сохранения и загрузки.
 * @param {function} getGameState - Функция, возвращающая объект состояния игры для сохранения.
 * @param {function} applyLoadedState - Функция, применяющая загруженное состояние.
 * @param {object} controls - Объект с DOM-элементами управления.
 * @param {string} gameIdPrefix - Префикс URL для API.
 */
function initSaveLoadFeatures(getGameState, applyLoadedState, controls, gameIdPrefix) {
    const { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn } = controls;
    if (!saveButton || !loadButton || !loadModal || !loadListContainer || !loadConfirmBtn || !loadCancelBtn) {
        console.warn("Элементы для сохранения/загрузки не найдены.");
        return;
    }

    let selectedGameToLoad = null;

    // --- Функции-обработчики ---
    const saveHandler = async () => {
        if (!isAuthenticated) {
            alert("Для сохранения игры необходимо войти в аккаунт.");
            window.location.href = loginUrl;
            return;
        }

        const gameState = getGameState();
        if (!gameState) return;

        const formData = new FormData();
        for (const key in gameState) {
            if (gameState.hasOwnProperty(key)) {
                if (key === 'customImages') {
                    gameState[key].forEach(file => formData.append('customImages[]', file, file.name));
                } else if (gameState[key] !== null && gameState[key] !== undefined) {
                    const value = typeof gameState[key] === 'object' ? JSON.stringify(gameState[key]) : gameState[key];
                    formData.append(key, value);
                }
            }
        }

        const gameId = gameState.id;
        const url = gameId ? updateMemoryGameBaseUrl.replace('0', gameId) : saveMemoryGameUrl;
        const method = gameId ? 'PUT' : 'POST';

        saveButton.textContent = 'Сохранение...';
        saveButton.disabled = true;
        try {
            const response = await fetch(url, { method: method, headers: { 'X-CSRFToken': csrfToken }, body: formData });
            
            const result = await response.json();

            // Проверяем статус ответа
            if (!response.ok) {
                throw new Error(result.message || `Ошибка сервера: ${response.status}`);
            }

            alert(result.message || 'Успех!');

            if (response.ok) {
                applyLoadedState({ id: result.id || gameId }, false);
            }
        } catch (error) {
            console.error("Ошибка при сохранении:", error);
            alert(`Ошибка при сохранении: ${error.message}`);
        } finally {
            const finalGameState = getGameState(true);
            saveButton.textContent = finalGameState && finalGameState.id ? 'Обновить' : 'Сохранить';
            saveButton.disabled = false;
        }
    };

    const loadHandler = async () => {
        if (typeof isAuthenticated === 'undefined' || !isAuthenticated) {
            alert("Для загрузки игры необходимо войти в аккаунт.");
            window.location.href = loginUrl;
            return;
        }

        loadListContainer.innerHTML = '<p>Загрузка...</p>';
        loadConfirmBtn.disabled = true;
        selectedGameToLoad = null;
        loadModal.style.display = 'flex';
        try {
            const response = await fetch(loadMemoryGamesUrl);
            const result = await response.json();
            if (result.status === 'success') {
                if (gameIdPrefix === 'memory_game') displayMemoryGameList(loadListContainer, result.games);
            } else {
                loadListContainer.innerHTML = `<p>Ошибка: ${result.message || 'Не удалось загрузить.'}</p>`;
            }
        } catch (error) {
            console.error("Сетевая ошибка при загрузке:", error);
            loadListContainer.innerHTML = '<p>Сетевая ошибка.</p>';
        }
    };

    const listClickHandler = (event) => {
        const target = event.target.closest('li');
        if (target) {
            loadListContainer.querySelectorAll('li').forEach(item => item.classList.remove('selected'));
            target.classList.add('selected');
            selectedGameToLoad = JSON.parse(target.dataset.gameData);
            loadConfirmBtn.disabled = false;
        }
    };

    const confirmHandler = () => {
        if (selectedGameToLoad) {
            applyLoadedState(selectedGameToLoad, true);
            loadModal.style.display = 'none';
        }
    };
    const cancelHandler = () => {
        loadModal.style.display = 'none';
    };

    // --- Прямое назначение обработчиков с предварительной очисткой ---
    saveButton.removeEventListener('click', saveButton.clickHandler);
    saveButton.addEventListener('click', saveHandler);
    saveButton.clickHandler = saveHandler;

    loadButton.removeEventListener('click', loadButton.clickHandler);
    loadButton.addEventListener('click', loadHandler);
    loadButton.clickHandler = loadHandler;

    loadListContainer.removeEventListener('click', loadListContainer.clickHandler);
    loadListContainer.addEventListener('click', listClickHandler);
    loadListContainer.clickHandler = listClickHandler;

    loadConfirmBtn.removeEventListener('click', loadConfirmBtn.clickHandler);
    loadConfirmBtn.addEventListener('click', confirmHandler);
    loadConfirmBtn.clickHandler = confirmHandler;

    loadCancelBtn.removeEventListener('click', loadCancelBtn.clickHandler);
    loadCancelBtn.addEventListener('click', cancelHandler);
    loadCancelBtn.clickHandler = cancelHandler;
}


/**
 * Инициализирует интерфейс и логику для отдельной страницы игры "Поиск пар".
 */
export function createMemoryGameSeparately() {
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
        if (!skipAlerts && !localGameParams.name) {
            alert("Введите название для сохранения.");
            return null;
        }
        if (!skipAlerts && (!localGameParams.card_layout || localGameParams.card_layout.length === 0)) {
            alert("Сначала начните игру.");
            return null;
        }

        const gameState = {
            id: localGameParams.id,
            name: localGameParams.name,
            pairCount: localGameParams.pairCount,
            cardLayout: localGameParams.card_layout,
        };

        if (localGameParams.isCustomSet) {
            if (localGameParams.customImageObjects?.some(obj => obj.file)) {
                if (!skipAlerts && localGameParams.customImageObjects.length < localGameParams.pairCount) {
                    alert("Недостаточно изображений для сохранения.");
                    return null;
                }
                gameState.customImages = localGameParams.customImageObjects
                    .slice(0, localGameParams.pairCount)
                    .map(imgObj => imgObj.file)
                    .filter(Boolean);
            }
        } else {
            const presetName = findPresetNameByUrl(localGameParams.selectedImageSet[0]);
            if (presetName) {
                gameState.presetName = presetName;
            } else if (!skipAlerts) {
                alert("Не удалось определить имя пресета.");
                return null;
            }
        }
        return gameState;
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

    initSaveLoadFeatures(getGameState, applyLoadedState, { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }, 'memory_game');
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

        memoryGameWs.onopen = () => {
            console.log(`[MemoryGame] WS Open. Синхронизируем начальные настройки для ${gameInstanceId}`);
            const stateToSend = {
                id: null,
                name: localGameParams.name,
                pairCount: localGameParams.pairCount,
                selectedImageSet: localGameParams.selectedImageSet,
                isCustomSet: false,
                card_layout: [],
                attempts: 0
            };
            memoryGameWs.send(JSON.stringify({ type: 'game_state_change', gameState: stateToSend }));
        };

        memoryGameWs.onclose = (e) => console.log(`[MemoryGame INSTANCE: ${gameInstanceId}] WebSocket disconnected.`, e.reason);
        memoryGameWs.onerror = (e) => console.error(`[MemoryGame INSTANCE: ${gameInstanceId}] WebSocket error.`, e);

        memoryGameWs.onmessage = (e) => {
            const data = JSON.parse(e.data);

            if (data.type === 'game_state_change') {
                const receivedState = data.gameState;

                Object.assign(gameWrapper.memoryGameParams, receivedState);

                if (receivedState.isCustomSet) {
                    gameWrapper.memoryGameParams.customImageObjects = (receivedState.selectedImageSet || []).map(url => {
                        return { url: url, file: null };
                    });
                }

                const useExistingLayout = receivedState.card_layout && receivedState.card_layout.length > 0;
                initializeBoard(gameWrapper.gameContainer, gameWrapper.memoryGameParams, useExistingLayout);

                const activeGameWrapper = document.querySelector('.paste-game-wrapper.active-game');
                if (activeGameWrapper === gameWrapper) {
                    setupWhiteboardMemoryGame(gameWrapper);
                }
            } else if (data.type === 'card_click') {
                applyRemoteCardClick(gameWrapper.gameContainer, gameWrapper.memoryGameParams, data.cardDomIndex);
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
    if (!activeGameWrapper || !activeGameWrapper.memoryGameParams) {
        console.warn("Активная игра 'Поиск пар' не найдена или не инициализирована.");
        return;
    }

    const activeGameParams = activeGameWrapper.memoryGameParams;
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
        
        if (currentActiveWrapper && currentActiveWrapper === activeGameWrapper && currentActiveWrapper.memoryGameParams) {
            initializeBoard(currentActiveWrapper.gameContainer, currentActiveWrapper.memoryGameParams, false);
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
        if (!skipAlerts && !activeGameParams.name) {
            alert("Введите название для сохранения.");
            gameNameInput.focus();
            return null;
        }

        if (!activeGameParams.card_layout || activeGameParams.card_layout.length === 0) {
            initializeBoard(activeGameWrapper.gameContainer, activeGameParams, false);
        }

        const gameState = {
            id: activeGameParams.id,
            name: activeGameParams.name,
            pairCount: activeGameParams.pairCount,
            cardLayout: activeGameParams.card_layout,
        };

        if (activeGameParams.isCustomSet) {
            const imageObjects = activeGameParams.customImageObjects || [];
            if (!skipAlerts && imageObjects.length < activeGameParams.pairCount) {
                alert(`Недостаточно изображений для сохранения. Требуется ${activeGameParams.pairCount}, а загружено ${imageObjects.length}.`);
                return null;
            }

            const hasNewFiles = imageObjects.some(obj => obj.file);
            
            if (!activeGameParams.id || hasNewFiles) {
                gameState.customImages = [];
                for (let i = 0; i < activeGameParams.pairCount; i++) {
                    const imgObj = imageObjects[i];
                    if (imgObj.file) {
                        // Если есть исходный файл, используем его
                        gameState.customImages.push(imgObj.file);
                    } else if (imgObj.url && imgObj.url.startsWith('data:image')) {
                        // Если файла нет, но есть data:URL, конвертируем его в Blob
                        const blob = dataURLtoBlob(imgObj.url);
                        if (blob) {
                            const filename = `upload_${i}.${blob.type.split('/')[1] || 'png'}`;
                            gameState.customImages.push(new File([blob], filename, { type: blob.type }));
                        } else {
                            if (!skipAlerts) alert(`Ошибка обработки изображения №${i + 1}. Сохранение прервано.`);
                            return null;
                        }
                    }
                }
                
                if (!skipAlerts && gameState.customImages.length < activeGameParams.pairCount) {
                    alert(`Не удалось подготовить все изображения для сохранения. Требуется ${activeGameParams.pairCount}, готово ${gameState.customImages.length}.`);
                    return null;
                }
            }
        } else {
            const presetName = findPresetNameByUrl(activeGameParams.selectedImageSet[0]);
            if (presetName) {
                gameState.presetName = presetName;
            } else if (!skipAlerts) {
                alert("Не удалось определить имя пресета.");
                return null;
            }
        }
        return gameState;
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
            // Отрисовываем поле у загружающего.
            const useExistingLayout = loadedData.card_layout && loadedData.card_layout.length > 0;
            initializeBoard(activeGameWrapper.gameContainer, activeGameParams, useExistingLayout);
            
            // отправляем новое, загруженное из БД, состояние всем остальным.
            if (activeGameParams.onWhiteboard && activeGameParams.ws && activeGameParams.ws.readyState === WebSocket.OPEN) {
                console.log(`[APPLY LOADED] Отправка загруженного состояния игры ${activeGameParams.gameId}`);
                
                const stateToSend = {
                    id: activeGameParams.id,
                    name: activeGameParams.name,
                    pairCount: activeGameParams.pairCount,
                    selectedImageSet: activeGameParams.selectedImageSet, // Уже содержит либо пресеты, либо data:URL
                    isCustomSet: activeGameParams.isCustomSet,
                    card_layout: activeGameParams.card_layout || [],
                    attempts: activeGameParams.attempts || 0
                };
                
                activeGameParams.ws.send(JSON.stringify({ type: 'game_state_change', gameState: stateToSend }));
            }
            
            alert(`Игра "${loadedData.name}" загружена в активный контейнер.`);
        }
    };

    // Инициализируем функции Сохранения/Загрузки.
    initSaveLoadFeatures(
        getGameStateForWhiteboard,
        applyLoadedStateForWhiteboard,
        { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn },
        'memory_game'
    );

    const gameNameInput = settingsPanel.querySelector('#game-name');
    const pairCountSelect = settingsPanel.querySelector('#pair-count-select');
    if (gameNameInput) gameNameInput.value = activeGameParams.name || '';
    if (pairCountSelect) pairCountSelect.value = activeGameParams.pairCount;

    saveButton.textContent = activeGameParams.id ? 'Обновить' : 'Сохранить';
}

/**
 * Универсальная функция для настройки контролов игры "Поиск пар".
 * @param {HTMLElement} settingsContainer - Контейнер с элементами настроек.
 * @param {object} gameParams - Объект с параметрами игры для изменения.
 * @param {function | null} onSettingsChange - Колбэк, вызываемый при изменении настроек.
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

    // Инициализация UI из текущих параметров
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
            let loadedCount = 0; const totalFiles = files.length;
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

/**
 * Вспомогательная функция для определения имени пресета по URL первого изображения.
 * @param {string} imageUrl - URL изображения.
 * @returns {string|null} Имя пресета или null.
 */
function findPresetNameByUrl(imageUrl) {
    if (!imageUrl || typeof presetImagesBasePath === 'undefined' || typeof PRESET_IMAGE_SETS_CONFIG === 'undefined') return null;
    const pathWithoutBase = imageUrl.replace(presetImagesBasePath, '');
    const setName = pathWithoutBase.split('/')[0];
    return PRESET_IMAGE_SETS_CONFIG.hasOwnProperty(setName) ? setName : null;
}

window.MemoryGameModule = {
    createMemoryGameSeparately,
    createMemoryGameOnBoard,
    setupWhiteboardMemoryGame
};