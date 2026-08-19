/**
 * Главный модуль игры "Звуковое лото".
 * Инициализирует интерфейс и логику для отдельной страницы и доски.
 */
import { getGameParts, initializeBoard, getFullPresetData, findPresetNameByImageUrl, stopTimer, SOUND_LOTO_PRESETS_CONFIG } from './logic.js';
import { displaySoundLotoList, prepareSoundLotoSaveData, createSoundLotoFormData, prepareSoundLotoSaveDataForWhiteboard } from './save-load.js';
import { SaveLoadManager } from '../common/save-load.js';
import { SoundLotoGame } from './game-class.js';

/**
 * Инициализирует интерфейс и логику для отдельной страницы игры "Звуковое лото".
 */
function createSoundLotoSeparately() {
    const gameWrapper = document.getElementById('sound-loto-game-wrapper');
    const settingsPanel = document.querySelector('.game-settings-panel');
    const startButton = settingsPanel?.querySelector('#start-sound-loto');

    if (!gameWrapper || !settingsPanel || !startButton) {
        console.error("Не найдены основные элементы для отдельной страницы игры 'Звуковое лото'.");
        return;
    }

    let localGameParams = getGameParts();

    const saveButton = document.getElementById('save-sound-loto-btn');
    const loadButton = document.getElementById('load-sound-loto-btn');
    const loadModal = document.getElementById('load-game-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');

    const handleSettingsChange = () => {
        gameWrapper.innerHTML = '<p class="initial-message">Настройки изменены. Нажмите "Начать игру".</p>';
    };

    setupGameControls(settingsPanel, localGameParams, handleSettingsChange);

    startButton.onclick = () => {
        initializeBoard(gameWrapper, localGameParams);
    };

    const getGameState = (skipAlerts = false) => {
        const gameNameInput = settingsPanel.querySelector('#game-name');
        localGameParams.name = gameNameInput.value.trim();
        return prepareSoundLotoSaveData(localGameParams, skipAlerts);
    };

    const applyLoadedState = (loadedData, showStartMessage = true) => {
        const isUpdateConfirmation = Object.keys(loadedData).length === 1 && loadedData.id && !showStartMessage;
        if (isUpdateConfirmation) {
            localGameParams.id = loadedData.id;
            localGameParams.audioReorderMap = null;
            if (saveButton) saveButton.textContent = 'Обновить';
            return;
        }

        // Маппинг данных с сервера (snake_case → camelCase)
        localGameParams.id = loadedData.id;
        localGameParams.name = loadedData.name;
        localGameParams.roundsCount = loadedData.rounds_count;
        localGameParams.cardsCount = loadedData.cards_count;
        localGameParams.autoplay = loadedData.autoplay;
        localGameParams.showLabels = loadedData.show_labels;
        localGameParams.audioReorderMap = null;

        if (loadedData.custom_pairs) {
            localGameParams.isCustomSet = true;
            localGameParams.presetName = null;
            localGameParams.customPairs = loadedData.custom_pairs.map(pair => ({
                image: pair.image_url,
                audio: pair.audio_url,
                imageUrl: pair.image_url,
                audioUrl: pair.audio_url,
                label: pair.label
            }));
        } else {
            localGameParams.isCustomSet = false;
            localGameParams.presetName = loadedData.preset_name;
            localGameParams.customPairs = [];
            localGameParams.pairs = getFullPresetData(loadedData.preset_name);
        }

        setupGameControls(settingsPanel, localGameParams, handleSettingsChange);

        if (saveButton) saveButton.textContent = 'Обновить';

        if (showStartMessage) {
            alert(`Игра "${localGameParams.name}" загружена. Нажмите "Начать игру" для запуска.`);
            gameWrapper.innerHTML = '<p class="initial-message">Игра загружена. Нажмите "Начать игру".</p>';
        }
    };

    const saveUrl = typeof saveSoundLotoUrl !== 'undefined' ? saveSoundLotoUrl : '/games/api/save-sound-loto/';
    const loadUrl = typeof loadSoundLotosUrl !== 'undefined' ? loadSoundLotosUrl : '/games/api/load-sound-lotos/';
    const updateTemplate = typeof updateSoundLotoBaseUrl !== 'undefined' ? updateSoundLotoBaseUrl.replace('0', '{gameId}') : '/games/api/update-sound-loto/{gameId}/';

    const saveLoadManager = new SaveLoadManager({
        saveUrl: saveUrl,
        loadUrl: loadUrl,
        updateUrlTemplate: updateTemplate,
        getState: getGameState,
        applyState: applyLoadedState,
        controls: { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
    });

    saveLoadManager.displayGameList = (games) => displaySoundLotoList(loadListContainer, games);
    saveLoadManager.formatGameListItem = (game) => `${game.name} (${game.rounds_count} раундов)`;
    saveLoadManager.prepareFormData = (gameState) => createSoundLotoFormData(gameState);

    console.log("Страница игры 'Звуковое лото' инициализирована.");
}

/**
 * Создает интерактивную игру "Звуковое лото" внутри контейнера на доске.
 */
function createSoundLotoOnBoard(gameWrapper, boardRoomName, gameInstanceId) {
    const soundLotoGame = new SoundLotoGame({
        gameId: gameInstanceId,
        boardRoomName: boardRoomName,
        name: `Звуковое лото ${gameInstanceId.split('-')[1] || ''}`,
        type: 'sound_loto',
        onWhiteboard: true
    });

    gameWrapper.soundLotoGame = soundLotoGame;
    gameWrapper.soundLotoParams = soundLotoGame.params;

    const gameContainer = document.createElement('div');
    gameContainer.className = "sound-loto-game-wrapper";

    const closeButton = gameWrapper.querySelector('.paste-game-close');
    const resizeHandle = gameWrapper.querySelector('.resize-handle');

    gameWrapper.innerHTML = '';

    if (closeButton) gameWrapper.appendChild(closeButton);
    if (resizeHandle) gameWrapper.appendChild(resizeHandle);

    gameWrapper.appendChild(gameContainer);

    gameWrapper.gameContainer = gameContainer;
    soundLotoGame.gameContainer = gameContainer;

    gameContainer.innerHTML = '<p class="initial-message">Активируйте игру и выберите настройки в панели справа.</p>';

    if (boardRoomName && gameInstanceId) {
        soundLotoGame.initWebSocket();
        gameWrapper.soundLotoWebSocket = soundLotoGame.ws;
        soundLotoGame.params.ws = soundLotoGame.ws;
    } else {
        console.log(`[SoundLoto INSTANCE: ${gameInstanceId}] Running in local mode (no WebSocket).`);
    }

    console.log(`Экземпляр игры "Звуковое лото" ${gameInstanceId} инициализирован на доске.`);
}

/**
 * Настраивает панель настроек для активной игры "Звуковое лото" на доске.
 */
function setupWhiteboardSoundLoto(activeGameWrapper) {
    if (!activeGameWrapper || !activeGameWrapper.soundLotoGame) {
        console.warn("Активная игра 'Звуковое лото' не найдена или не инициализирована.");
        return;
    }

    const soundLotoGame = activeGameWrapper.soundLotoGame;
    const activeGameParams = soundLotoGame.params;
    const settingsPanel = document.querySelector('.settings-panel');

    if (!settingsPanel) {
        console.error("Панель настроек не найдена.");
        return;
    }

    const startButton = settingsPanel.querySelector('#start-sound-loto');
    const saveButton = settingsPanel.querySelector('#save-sound-loto-btn');
    const loadButton = settingsPanel.querySelector('#load-sound-loto-btn');
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
            const stateToSend = soundLotoGame.getState();
            activeGameParams.ws.send(JSON.stringify({ type: 'game_state_change', gameState: stateToSend }));
        }
    };

    setupGameControls(settingsPanel, activeGameParams, handleGameStateChangeForBoard);

    const startButtonClickHandler = () => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');

        if (currentActiveWrapper && currentActiveWrapper === activeGameWrapper && currentActiveWrapper.soundLotoGame) {
            initializeBoard(currentActiveWrapper.gameContainer, currentActiveWrapper.soundLotoGame.params);

            if (activeGameParams.onWhiteboard && activeGameParams.ws && activeGameParams.ws.readyState === WebSocket.OPEN) {
                activeGameParams.ws.send(JSON.stringify({
                    type: 'game_state_change',
                    gameState: soundLotoGame.getState()
                }));
            }
        } else {
            console.warn("Активная игра изменилась, действие 'Начать' отменено.");
        }
    };

    startButton.removeEventListener('click', startButton.clickHandler);
    startButton.addEventListener('click', startButtonClickHandler);
    startButton.clickHandler = startButtonClickHandler;

    const getGameStateForWhiteboard = (skipAlerts = false) => {
        const gameNameInput = settingsPanel.querySelector('#game-name');
        activeGameParams.name = gameNameInput.value.trim();
        return prepareSoundLotoSaveDataForWhiteboard(activeGameParams, skipAlerts);
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
            activeGameParams.audioReorderMap = null;
            saveButton.textContent = 'Обновить';
            return;
        }

        // Маппинг данных
        activeGameParams.id = loadedData.id;
        activeGameParams.name = loadedData.name;
        activeGameParams.roundsCount = loadedData.rounds_count;
        activeGameParams.cardsCount = loadedData.cards_count;
        activeGameParams.autoplay = loadedData.autoplay;
        activeGameParams.showLabels = loadedData.show_labels;
        activeGameParams.audioReorderMap = null;

        if (loadedData.custom_pairs) {
            activeGameParams.isCustomSet = true;
            activeGameParams.presetName = null;
            activeGameParams.customPairs = loadedData.custom_pairs.map(pair => ({
                image: pair.image_url,
                audio: pair.audio_url,
                imageUrl: pair.image_url,
                audioUrl: pair.audio_url,
                label: pair.label
            }));
        } else {
            activeGameParams.isCustomSet = false;
            activeGameParams.presetName = loadedData.preset_name;
            activeGameParams.customPairs = [];
            activeGameParams.pairs = getFullPresetData(loadedData.preset_name);
        }

        // Сброс состояния игры
        activeGameParams.currentRound = 0;
        activeGameParams.roundPairs = [];
        activeGameParams.correctPairIndex = null;
        activeGameParams.usedPairIndices = [];
        activeGameParams.correctClicks = 0;
        activeGameParams.totalClicks = 0;
        activeGameParams.secondsElapsed = 0;

        setupGameControls(settingsPanel, activeGameParams, handleGameStateChangeForBoard);
        saveButton.textContent = 'Обновить';

        // Показываем пустую область ожидания
        activeGameWrapper.gameContainer.innerHTML = '<p class="initial-message">Игра загружена. Нажмите "Начать игру".</p>';

        // Синхронизируем состояние со вторым клиентом
        if (activeGameParams.onWhiteboard && activeGameParams.ws && activeGameParams.ws.readyState === WebSocket.OPEN) {
            activeGameParams.ws.send(JSON.stringify({
                type: 'game_state_change',
                gameState: soundLotoGame.getState()
            }));
        }

        alert(`Игра "${loadedData.name}" загружена. Нажмите "Начать игру" для запуска.`);
    };

    const saveUrl = typeof saveSoundLotoUrl !== 'undefined' ? saveSoundLotoUrl : '/games/api/save-sound-loto/';
    const loadUrl = typeof loadSoundLotosUrl !== 'undefined' ? loadSoundLotosUrl : '/games/api/load-sound-lotos/';
    const updateTemplate = typeof updateSoundLotoBaseUrl !== 'undefined' ? updateSoundLotoBaseUrl.replace('0', '{gameId}') : '/games/api/update-sound-loto/{gameId}/';

    const saveLoadManager = new SaveLoadManager({
        saveUrl: saveUrl,
        loadUrl: loadUrl,
        updateUrlTemplate: updateTemplate,
        getState: getGameStateForWhiteboard,
        applyState: applyLoadedStateForWhiteboard,
        controls: { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
    });

    saveLoadManager.displayGameList = (games) => displaySoundLotoList(loadListContainer, games);
    saveLoadManager.formatGameListItem = (game) => `${game.name} (${game.rounds_count} раундов)`;
    saveLoadManager.prepareFormData = (gameState) => createSoundLotoFormData(gameState);

    const gameNameInput = settingsPanel.querySelector('#game-name');
    const roundsCountSelect = settingsPanel.querySelector('#rounds-count-select');
    if (gameNameInput) gameNameInput.value = activeGameParams.name || '';
    if (roundsCountSelect) roundsCountSelect.value = activeGameParams.roundsCount;
    saveButton.textContent = activeGameParams.id ? 'Обновить' : 'Сохранить';
}

/**
 * Универсальная функция для настройки контролов игры "Звуковое лото".
 */
function setupGameControls(settingsContainer, gameParams, onSettingsChange) {
    const gameNameInput = settingsContainer.querySelector('#game-name');
    const roundsCountSelect = settingsContainer.querySelector('#rounds-count-select');
    const cardsCountSelect = settingsContainer.querySelector('#cards-count-select');
    const autoplayCheckbox = settingsContainer.querySelector('#autoplay-checkbox');
    const showLabelsCheckbox = settingsContainer.querySelector('#show-labels-checkbox');
    const presetSetElements = settingsContainer.querySelectorAll('.preset-set');
    const customImagesInput = settingsContainer.querySelector('#custom-images-input');
    const customAudiosInput = settingsContainer.querySelector('#custom-audios-input');

    if (!gameNameInput || !roundsCountSelect || !cardsCountSelect || !autoplayCheckbox || !showLabelsCheckbox || !presetSetElements.length) {
        console.error("Не удалось найти все элементы управления в 'setupGameControls' для 'Звукового лото'.");
        return;
    }

    // Инициализация значений
    gameNameInput.value = gameParams.name || '';
    roundsCountSelect.value = gameParams.roundsCount;
    cardsCountSelect.value = gameParams.cardsCount;
    autoplayCheckbox.checked = gameParams.autoplay;
    showLabelsCheckbox.checked = gameParams.showLabels;

    updatePairPreviewUI(gameParams, settingsContainer);

    const activePresetName = gameParams.isCustomSet ? null : gameParams.presetName;
    presetSetElements.forEach(el => {
        el.classList.toggle('selected', el.dataset.setName === activePresetName);
    });

    // Обработчик названия
    const gameNameInputHandler = (e) => {
        gameParams.name = e.target.value.trim();
    };
    gameNameInput.removeEventListener('input', gameNameInput.inputHandler);
    gameNameInput.addEventListener('input', gameNameInputHandler);
    gameNameInput.inputHandler = gameNameInputHandler;

    // Обработчик количества раундов
    const roundsCountHandler = (e) => {
        gameParams.roundsCount = parseInt(e.target.value, 10);
        if (onSettingsChange) onSettingsChange();
    };
    roundsCountSelect.removeEventListener('change', roundsCountSelect.changeHandler);
    roundsCountSelect.addEventListener('change', roundsCountHandler);
    roundsCountSelect.changeHandler = roundsCountHandler;

    // Обработчик количества карточек
    const cardsCountHandler = (e) => {
        gameParams.cardsCount = parseInt(e.target.value, 10);
        if (onSettingsChange) onSettingsChange();
    };
    cardsCountSelect.removeEventListener('change', cardsCountSelect.changeHandler);
    cardsCountSelect.addEventListener('change', cardsCountHandler);
    cardsCountSelect.changeHandler = cardsCountHandler;

    // Обработчик автовоспроизведения
    const autoplayHandler = (e) => {
        gameParams.autoplay = e.target.checked;
        if (onSettingsChange) onSettingsChange();
    };
    autoplayCheckbox.removeEventListener('change', autoplayCheckbox.changeHandler);
    autoplayCheckbox.addEventListener('change', autoplayHandler);
    autoplayCheckbox.changeHandler = autoplayHandler;

    // Обработчик показа подписей
    const showLabelsHandler = (e) => {
        gameParams.showLabels = e.target.checked;
        if (onSettingsChange) onSettingsChange();
    };
    showLabelsCheckbox.removeEventListener('change', showLabelsCheckbox.changeHandler);
    showLabelsCheckbox.addEventListener('change', showLabelsHandler);
    showLabelsCheckbox.changeHandler = showLabelsHandler;

    // Обработчики пресетов
    presetSetElements.forEach(presetEl => {
        const presetClickHandler = () => {
            if (presetEl.classList.contains('selected') && !gameParams.isCustomSet) return;

            presetSetElements.forEach(el => el.classList.remove('selected'));
            presetEl.classList.add('selected');

            gameParams.presetName = presetEl.dataset.setName;
            gameParams.pairs = getFullPresetData(presetEl.dataset.setName);
            gameParams.isCustomSet = false;
            gameParams.customPairs = [];
            gameParams.audioReorderMap = null;

            if (customImagesInput) customImagesInput.value = '';
            if (customAudiosInput) customAudiosInput.value = '';

            updatePairPreviewUI(gameParams, settingsContainer);

            if (onSettingsChange) onSettingsChange();
        };

        presetEl.removeEventListener('click', presetEl.clickHandler);
        presetEl.addEventListener('click', presetClickHandler);
        presetEl.clickHandler = presetClickHandler;
    });

    // Обработчик загрузки пользовательских файлов
    const customFilesHandler = () => {
        const imageFiles = customImagesInput?.files || [];
        const audioFiles = customAudiosInput?.files || [];

        if (imageFiles.length === 0 && audioFiles.length === 0) {
            if (gameParams.isCustomSet) {
                gameParams.isCustomSet = false;
                gameParams.audioReorderMap = null;
                const selectedPreset = settingsContainer.querySelector('.preset-set.selected') || presetSetElements[0];
                if (selectedPreset && typeof selectedPreset.clickHandler === 'function') {
                    selectedPreset.clickHandler();
                }
            }
            return;
        }

        if (imageFiles.length !== audioFiles.length) {
            alert("Количество изображений и аудиофайлов должно совпадать.");
            return;
        }

        gameParams.isCustomSet = true;
        gameParams.audioReorderMap = null;
        presetSetElements.forEach(el => el.classList.remove('selected'));

        const totalFiles = imageFiles.length;
        let loadedCount = 0;
        const pairs = [];

        Array.from(imageFiles).forEach((file, index) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                pairs[index] = pairs[index] || {};
                pairs[index].image = e.target.result;
                pairs[index].imageUrl = e.target.result;
                pairs[index].imageFile = file;
                pairs[index].label = file.name.replace(/\.[^.]+$/, '');

                loadedCount++;
                if (loadedCount === totalFiles) {
                    let audioLoadedCount = 0;
                    const totalAudios = audioFiles.length;
                    
                    if (totalAudios === 0) {
                        gameParams.customPairs = pairs;
                        updatePairPreviewUI(gameParams, settingsContainer);
                        if (onSettingsChange) onSettingsChange();
                        return;
                    }
                    
                    Array.from(audioFiles).forEach((audioFile, audioIndex) => {
                        if (pairs[audioIndex]) {
                            pairs[audioIndex].audioFile = audioFile;
                            
                            const audioReader = new FileReader();
                            audioReader.onload = (e) => {
                                pairs[audioIndex].audio = e.target.result;
                                pairs[audioIndex].audioUrl = e.target.result;
                                pairs[audioIndex].audioFile = audioFile;
                                audioLoadedCount++;
                                
                                if (audioLoadedCount === totalAudios) {
                                    gameParams.customPairs = pairs;
                                    updatePairPreviewUI(gameParams, settingsContainer);
                                    if (onSettingsChange) onSettingsChange();
                                }
                            };
                            audioReader.onerror = () => {
                                audioLoadedCount++;
                                if (audioLoadedCount === totalAudios) {
                                    gameParams.customPairs = pairs;
                                    updatePairPreviewUI(gameParams, settingsContainer);
                                    if (onSettingsChange) onSettingsChange();
                                }
                            };
                            audioReader.readAsDataURL(audioFile);
                        }
                    });
                }
            };
            reader.readAsDataURL(file);
        });
    };

    if (customImagesInput) {
        customImagesInput.removeEventListener('change', customImagesInput.changeHandler);
        customImagesInput.addEventListener('change', customFilesHandler);
        customImagesInput.changeHandler = customFilesHandler;
    }

    if (customAudiosInput) {
        customAudiosInput.removeEventListener('change', customAudiosInput.changeHandler);
        customAudiosInput.addEventListener('change', customFilesHandler);
        customAudiosInput.changeHandler = customFilesHandler;
    }
}

/**
 * Возвращает отображаемое имя аудиофайла пары.
 * 
 * @param {Object} pair - Объект пары.
 * @returns {string} Имя файла или подпись-заглушка.
 */
function getAudioDisplayName(pair) {
    if (pair.audioFile && pair.audioFile.name) {
        return pair.audioFile.name;
    }

    const url = pair.audioUrl || pair.audio || '';
    if (!url) return 'нет звука';

    try {
        const clean = decodeURIComponent(url.split('?')[0]);
        const fileName = clean.split('/').pop();
        return fileName || 'нет звука';
    } catch (error) {
        return 'нет звука';
    }
}

/**
 * Обновляет UI для предпросмотра пользовательских пар.
 * Строка пары: [картинка] [подпись + кнопка звука + имя файла] [стрелки].
 * 
 * @param {Object} params - Параметры игры.
 * @param {HTMLElement} settingsContainer - Контейнер настроек.
 */
function updatePairPreviewUI(params, settingsContainer) {
    const previewContainer = settingsContainer.querySelector('#pair-preview-container');
    if (!previewContainer) return;

    previewContainer.innerHTML = '';

    const sourcePairs = params.isCustomSet ? params.customPairs : params.pairs;

    if (!sourcePairs || sourcePairs.length === 0) {
        previewContainer.style.display = 'none';
        return;
    }

    previewContainer.style.display = 'block';

    const hint = document.createElement('p');
    hint.className = 'pair-preview-hint';
    hint.textContent = params.isCustomSet
        ? 'Проверьте пары кнопкой 🔊. Если звук не подходит к картинке — переставьте его стрелками.'
        : 'Пары выбранного набора:';
    previewContainer.appendChild(hint);

    sourcePairs.forEach((pair, index) => {
        const row = document.createElement('div');
        row.className = 'pair-row';
        row.dataset.index = index;

        const imageThumb = document.createElement('img');
        imageThumb.className = 'pair-row-image';
        imageThumb.src = pair.imageUrl || pair.image;
        imageThumb.alt = pair.label || `Пара ${index + 1}`;

        // Средняя колонка: подпись + строка звука
        const mainCol = document.createElement('div');
        mainCol.className = 'pair-row-main';

        const labelInput = document.createElement('input');
        labelInput.type = 'text';
        labelInput.className = 'pair-row-label';
        labelInput.value = pair.label || '';
        labelInput.placeholder = 'Подпись';
        labelInput.disabled = !params.isCustomSet;
        labelInput.addEventListener('input', () => {
            pair.label = labelInput.value.trim();
        });

        const audioLine = document.createElement('div');
        audioLine.className = 'pair-row-audio';

        const playBtn = document.createElement('button');
        playBtn.type = 'button';
        playBtn.className = 'pair-row-play';
        playBtn.textContent = '🔊';
        playBtn.title = 'Прослушать звук пары';
        playBtn.addEventListener('click', () => {
            const audioUrl = pair.audioUrl || pair.audio;
            if (!audioUrl) return;
            const previewAudio = new Audio(audioUrl);
            previewAudio.play().catch(error => {
                console.warn('[SoundLoto] Не удалось воспроизвести звук пары:', error);
            });
        });

        const audioName = document.createElement('span');
        audioName.className = 'pair-row-audio-name';
        const audioDisplayName = getAudioDisplayName(pair);
        audioName.textContent = audioDisplayName;
        audioName.title = audioDisplayName;

        audioLine.appendChild(playBtn);
        audioLine.appendChild(audioName);

        mainCol.appendChild(labelInput);
        mainCol.appendChild(audioLine);

        // Правая колонка: стрелки перестановки
        const actionsCol = document.createElement('div');
        actionsCol.className = 'pair-row-actions';

        if (params.isCustomSet) {
            const moveUpBtn = document.createElement('button');
            moveUpBtn.type = 'button';
            moveUpBtn.className = 'pair-row-move';
            moveUpBtn.textContent = '↑';
            moveUpBtn.title = 'Переместить звук вверх';
            moveUpBtn.disabled = index === 0;
            moveUpBtn.addEventListener('click', () => {
                swapPairAudios(params, index, index - 1);
                updatePairPreviewUI(params, settingsContainer);
            });

            const moveDownBtn = document.createElement('button');
            moveDownBtn.type = 'button';
            moveDownBtn.className = 'pair-row-move';
            moveDownBtn.textContent = '↓';
            moveDownBtn.title = 'Переместить звук вниз';
            moveDownBtn.disabled = index === sourcePairs.length - 1;
            moveDownBtn.addEventListener('click', () => {
                swapPairAudios(params, index, index + 1);
                updatePairPreviewUI(params, settingsContainer);
            });

            actionsCol.appendChild(moveUpBtn);
            actionsCol.appendChild(moveDownBtn);
        }

        row.appendChild(imageThumb);
        row.appendChild(mainCol);
        row.appendChild(actionsCol);

        previewContainer.appendChild(row);
    });
}

/**
 * Меняет местами звуки между двумя парами.
 * Картинки и подписи остаются привязанными к своим строкам.
 * Также обновляет карту перестановки для последующего сохранения на сервер.
 * 
 * @param {Object} params - Параметры игры.
 * @param {number} indexA - Индекс первой пары.
 * @param {number} indexB - Индекс второй пары.
 */
function swapPairAudios(params, indexA, indexB) {
    const pairs = params.customPairs;
    if (!pairs || indexA < 0 || indexB < 0 || indexA >= pairs.length || indexB >= pairs.length) return;

    const a = pairs[indexA];
    const b = pairs[indexB];

    [a.audioUrl, b.audioUrl] = [b.audioUrl, a.audioUrl];
    [a.audio, b.audio] = [b.audio, a.audio];
    [a.audioFile, b.audioFile] = [b.audioFile, a.audioFile];

    // Обновляем карту перестановки аудио
    if (!params.audioReorderMap) {
        params.audioReorderMap = pairs.map((_, i) => i);
    }
    [params.audioReorderMap[indexA], params.audioReorderMap[indexB]] =
        [params.audioReorderMap[indexB], params.audioReorderMap[indexA]];
}

// Делаем функцию доступной глобально для вызова из HTML
window.createSoundLotoSeparately = createSoundLotoSeparately;

// Экспорт для использования в whiteboard
export { createSoundLotoOnBoard, setupWhiteboardSoundLoto };