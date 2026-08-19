/**
 * Модуль логики игры "Звуковое лото".
 * Содержит функции для создания, управления и взаимодействия с игровым полем.
 */
import { shuffle } from '../common/utils.js';

/**
 * Конфигурация предустановленных наборов пар (изображение + аудио + подпись).
 */
export const SOUND_LOTO_PRESETS_CONFIG = {
    animals: [
        { image: 'animals/dog.jpg', audio: 'animals/dog_bark.mp3', label: 'Собака' },
        { image: 'animals/cat.jpg', audio: 'animals/cat_meow.mp3', label: 'Кошка' },
        { image: 'animals/cow.jpg', audio: 'animals/cow_moo.mp3', label: 'Корова' },
        { image: 'animals/frog.jpg', audio: 'animals/frog_croak.mp3', label: 'Лягушка' },
        { image: 'animals/rooster.jpg', audio: 'animals/rooster_crow.mp3', label: 'Петух' },
        { image: 'animals/duck.jpg', audio: 'animals/duck_quack.mp3', label: 'Утка' },
    ],
    transport: [
        { image: 'transport/train.jpg', audio: 'transport/train_horn.mp3', label: 'Поезд' },
        { image: 'transport/car.jpg', audio: 'transport/car_honk.mp3', label: 'Машина' },
        { image: 'transport/plane.jpg', audio: 'transport/plane_engine.mp3', label: 'Самолёт' },
        { image: 'transport/helicopter.jpg', audio: 'transport/helicopter_blades.mp3', label: 'Вертолёт' },
        { image: 'transport/bicycle.jpg', audio: 'transport/bicycle_bell.mp3', label: 'Велосипед' },
        { image: 'transport/ship.jpg', audio: 'transport/ship_horn.mp3', label: 'Корабль' },
    ]
};

/**
 * Имя предустановленного набора по умолчанию.
 */
const DEFAULT_PRESET_NAME = 'animals';

/**
 * Генерирует полные URL-адреса для пар (изображение + аудио) из предустановленного набора.
 * 
 * @param {string} setName - Имя набора из SOUND_LOTO_PRESETS_CONFIG.
 * @returns {Array<{image: string, audio: string, label: string}>} Массив объектов с полными URL.
 */
export function getFullPresetData(setName) {
    if (SOUND_LOTO_PRESETS_CONFIG[setName] && typeof soundLotoImagesBasePath !== 'undefined' && typeof soundLotoAudioBasePath !== 'undefined') {
        return SOUND_LOTO_PRESETS_CONFIG[setName].map(item => ({
            image: soundLotoImagesBasePath + item.image,
            audio: soundLotoAudioBasePath + item.audio,
            label: item.label
        }));
    }
    console.warn(`Набор "${setName}" не найден или переменные путей не определены.`);
    return [];
}

/**
 * Определяет имя пресета по URL первого изображения.
 * 
 * @param {string} imageUrl - URL изображения.
 * @returns {string|null} Имя пресета или null.
 */
export function findPresetNameByImageUrl(imageUrl) {
    if (!imageUrl || typeof soundLotoImagesBasePath === 'undefined') return null;
    const pathWithoutBase = imageUrl.replace(soundLotoImagesBasePath, '');
    const setName = pathWithoutBase.split('/')[0];
    return SOUND_LOTO_PRESETS_CONFIG.hasOwnProperty(setName) ? setName : null;
}

/**
 * Возвращает URL изображения пары с учётом обоих вариантов ключей.
 * 
 * @param {Object} pair - Объект пары.
 * @returns {string|null} URL изображения.
 */
export function getPairImage(pair) {
    return pair.image || pair.imageUrl || null;
}

/**
 * Возвращает URL аудио пары с учётом обоих вариантов ключей.
 * 
 * @param {Object} pair - Объект пары.
 * @returns {string|null} URL аудио.
 */
export function getPairAudio(pair) {
    return pair.audio || pair.audioUrl || null;
}

/**
 * Создает и возвращает объект с начальными параметрами игры.
 * 
 * @returns {Object} Объект с параметрами игры.
 */
export function getGameParts() {
    return {
        id: null,
        name: "Моё звуковое лото",
        roundsCount: 4,
        cardsCount: 4,
        autoplay: true,
        showLabels: true,
        presetName: DEFAULT_PRESET_NAME,
        isCustomSet: false,
        pairs: getFullPresetData(DEFAULT_PRESET_NAME),
        customPairs: [],

        // Состояние игры
        currentRound: 0,
        roundPairs: [],
        correctPairIndex: null,
        correctClicks: 0,
        totalClicks: 0,
        lockBoard: false,
        usedPairIndices: [],

        // UI элементы
        uiRoundEl: null,
        uiCorrectEl: null,
        uiTimeEl: null,
        uiPlayButton: null,
        uiCompletionMessageEl: null,
        uiCompletionTextEl: null,

        // Таймер
        timerInterval: null,
        secondsElapsed: 0,

        // Аудио
        currentAudio: null,

        // WebSocket
        onWhiteboard: false,
        gameId: null,
        boardRoomName: null,
        ws: null,

        // Для перестановки звуков у пользовательских пар
        audioReorderMap: null
    };
}

/**
 * Инициализирует и создает игровое поле.
 * 
 * @param {HTMLElement} boardWrapper - DOM-элемент, в который будет встроено игровое поле.
 * @param {Object} params - Объект с текущими параметрами игры.
 * @param {boolean} autoStart - Если true, сбрасывает состояние и запускает первый раунд.
 *                              Если false, восстанавливает UI из текущего состояния без генерации раунда.
 * @returns {boolean} true, если инициализация успешна.
 */
export function initializeBoard(boardWrapper, params, autoStart = true) {
    boardWrapper.innerHTML = '';

    // Проверка достаточности пар
    const availablePairs = params.isCustomSet ? params.customPairs : params.pairs;
    const requiredPairs = Math.max(params.roundsCount, params.cardsCount);

    if (!availablePairs || availablePairs.length < requiredPairs) {
        boardWrapper.innerHTML = `<p class="initial-message">Ошибка: Недостаточно пар для игры. Требуется минимум ${requiredPairs}, доступно ${(availablePairs || []).length}.</p>`;
        return false;
    }

    // Панель информации
    const infoPanel = document.createElement('div');
    infoPanel.className = 'sound-loto-info-panel';
    infoPanel.innerHTML = `
        <span class="sound-loto-info-item">Раунд: <b data-role="round">0</b> / ${params.roundsCount}</span>
        <span class="sound-loto-info-item">Верно: <b data-role="correct">0</b></span>
        <span class="sound-loto-info-item">Время: <b data-role="time">0</b>с</span>
    `;
    boardWrapper.appendChild(infoPanel);

    params.uiRoundEl = infoPanel.querySelector('b[data-role="round"]');
    params.uiCorrectEl = infoPanel.querySelector('b[data-role="correct"]');
    params.uiTimeEl = infoPanel.querySelector('b[data-role="time"]');

    // Кнопка воспроизведения звука
    const playButtonWrapper = document.createElement('div');
    playButtonWrapper.className = 'sound-loto-play-wrapper';

    const playButton = document.createElement('button');
    playButton.className = 'sound-loto-play-btn';
    playButton.innerHTML = '<span class="play-icon">&#9654;</span><span class="play-waves"></span>';
    playButton.title = 'Воспроизвести звук';
    playButton.addEventListener('click', () => {
        if (params.correctPairIndex !== null && params.roundPairs[params.correctPairIndex]) {
            const audioUrl = getPairAudio(params.roundPairs[params.correctPairIndex]);
            playSound(audioUrl, params);
            sendWebSocketEvent(params, { type: 'play_sound', audioUrl: audioUrl });
        }
    });


    playButtonWrapper.appendChild(playButton);
    boardWrapper.appendChild(playButtonWrapper);
    params.uiPlayButton = playButton;

    // Сетка карточек
    const cardsGrid = document.createElement('div');
    cardsGrid.className = 'sound-loto-cards-grid';
    cardsGrid.style.gridTemplateColumns = `repeat(${Math.min(params.cardsCount, 3)}, 1fr)`;
    boardWrapper.appendChild(cardsGrid);

    // Сообщение о завершении
    const completionMessageDiv = document.createElement('div');
    completionMessageDiv.id = 'sound-loto-completion-message';
    completionMessageDiv.className = 'sound-loto-completion-message';
    completionMessageDiv.style.display = 'none';
    const completionTextP = document.createElement('p');
    completionMessageDiv.appendChild(completionTextP);
    boardWrapper.appendChild(completionMessageDiv);

    params.uiCompletionMessageEl = completionMessageDiv;
    params.uiCompletionTextEl = completionTextP;

    if (autoStart) {
        // Полный сброс и запуск первого раунда
        params.currentRound = 0;
        params.correctClicks = 0;
        params.totalClicks = 0;
        params.lockBoard = false;
        params.usedPairIndices = [];
        params.correctPairIndex = null;
        params.roundPairs = [];
        params.secondsElapsed = 0;

        updateUIDetails(params);
        startTimer(params);
        startRound(params);
    } else {
        // Восстановление существующего состояния без генерации нового раунда.
        // Используется при синхронизации через WebSocket.
        updateUIDetails(params);

        if (params.roundPairs && params.roundPairs.length > 0 && params.currentRound > 0) {
            renderCards(params);
        }

        // Таймер без сброса секунд, если ещё не запущен
        if (!params.timerInterval && params.currentRound > 0) {
            params.timerInterval = setInterval(() => {
                params.secondsElapsed++;
                updateUIDetails(params);
            }, 1000);
        }
    }

    return true;
}

/**
 * Запускает новый раунд игры.
 * 
 * @param {Object} params - Объект с параметрами игры.
 */
export function startRound(params) {
    params.currentRound++;
    params.lockBoard = false;

    const availablePairs = params.isCustomSet ? params.customPairs : params.pairs;

    if (params.currentRound > params.roundsCount) {
        finishGame(params);
        return;
    }

    const remainingIndices = [];
    for (let i = 0; i < availablePairs.length; i++) {
        if (!params.usedPairIndices.includes(i)) {
            remainingIndices.push(i);
        }
    }

    if (remainingIndices.length === 0) {
        // Если все пары использованы, начинаем заново
        params.usedPairIndices = [];
        for (let i = 0; i < availablePairs.length; i++) {
            remainingIndices.push(i);
        }
    }

    // Выбираем правильную пару
    const correctPairPoolIndex = Math.floor(Math.random() * remainingIndices.length);
    const correctPairIndex = remainingIndices[correctPairPoolIndex];
    params.usedPairIndices.push(correctPairIndex);

    // Выбираем дистракторы
    const distractorIndices = remainingIndices.filter((_, idx) => idx !== correctPairPoolIndex);
    const shuffledDistractors = shuffle(distractorIndices);
    const selectedDistractors = shuffledDistractors.slice(0, params.cardsCount - 1);

    // Формируем набор пар для раунда (правильная + дистракторы)
    const roundIndices = shuffle([correctPairIndex, ...selectedDistractors]);
    params.roundPairs = roundIndices.map(idx => availablePairs[idx]);
    params.correctPairIndex = roundIndices.indexOf(correctPairIndex);

    renderCards(params);
    updateUIDetails(params);

    // Автовоспроизведение звука
    if (params.autoplay) {
        const audioUrl = getPairAudio(params.roundPairs[params.correctPairIndex]);
        playSound(audioUrl, params);
    }

    // Отправка WS события
    sendWebSocketEvent(params, {
        type: 'round_start',
        round: params.currentRound,
        totalRounds: params.roundsCount,
        pairs: params.roundPairs,
        correctIndex: params.correctPairIndex,
        autoplay: params.autoplay
    });
}

/**
 * Отрисовывает карточки на игровом поле.
 * 
 * @param {Object} params - Объект с параметрами игры.
 */
export function renderCards(params) {
    const boardWrapper = params.uiRoundEl?.closest('.sound-loto-game-wrapper') || document.querySelector('.sound-loto-game-wrapper');
    if (!boardWrapper) return;

    const cardsGrid = boardWrapper.querySelector('.sound-loto-cards-grid');
    if (!cardsGrid) return;

    cardsGrid.innerHTML = '';
    cardsGrid.style.gridTemplateColumns = `repeat(${Math.min(params.cardsCount, 3)}, 1fr)`;

    params.roundPairs.forEach((pair, index) => {
        const card = document.createElement('div');
        card.className = 'sound-loto-card';
        card.dataset.index = index;

        const img = document.createElement('img');
        img.src = getPairImage(pair);
        img.alt = pair.label || `Карточка ${index + 1}`;
        img.className = 'sound-loto-card-image';
        card.appendChild(img);

        if (params.showLabels && pair.label) {
            const label = document.createElement('span');
            label.className = 'sound-loto-card-label';
            label.textContent = pair.label;
            card.appendChild(label);
        }

        card.addEventListener('click', () => handleCardClick(card, params));
        cardsGrid.appendChild(card);
    });
}

/**
 * Обрабатывает клик по карточке (локальный пользователь).
 * Важно: следующий раунд генерирует именно тот клиент, который сделал клик.
 * 
 * @param {HTMLElement} card - DOM-элемент карточки.
 * @param {Object} params - Объект с параметрами игры.
 */
export function handleCardClick(card, params) {
    if (params.lockBoard) return;

    const cardIndex = parseInt(card.dataset.index, 10);
    const isCorrect = cardIndex === params.correctPairIndex;

    params.totalClicks++;

    if (isCorrect) {
        params.correctClicks++;
        params.lockBoard = true;
        card.classList.add('sound-loto-card-correct');

        updateUIDetails(params);

        stopSound(params);

        // Переход к следующему раунду через задержку.
        setTimeout(() => {
            startRound(params);
        }, 1200);
    } else {
        card.classList.add('sound-loto-card-wrong');
        setTimeout(() => {
            card.classList.remove('sound-loto-card-wrong');
        }, 600);
    }

    // Отправка WS события
    sendWebSocketEvent(params, {
        type: 'card_click',
        cardIndex: cardIndex,
        isCorrect: isCorrect
    });
}

/**
 * Применяет удаленный клик по карточке, полученный через WebSocket.
 * 
 * @param {HTMLElement} boardWrapper - Контейнер игры.
 * @param {Object} params - Параметры игры.
 * @param {number} cardIndex - Индекс карточки.
 * @param {boolean} isCorrect - Был ли клик верным.
 */
export function applyRemoteCardClick(boardWrapper, params, cardIndex, isCorrect) {
    const cardsGrid = boardWrapper.querySelector('.sound-loto-cards-grid');
    if (!cardsGrid) return;

    const card = cardsGrid.querySelector(`.sound-loto-card[data-index="${cardIndex}"]`);
    if (!card) return;

    if (isCorrect) {
        params.lockBoard = true;
        params.correctClicks++;
        card.classList.add('sound-loto-card-correct');
        updateUIDetails(params);
        stopSound(params);
    } else {
        card.classList.add('sound-loto-card-wrong');
        setTimeout(() => {
            card.classList.remove('sound-loto-card-wrong');
        }, 600);
    }
}

/**
 * Применяет удаленное начало раунда, полученное через WebSocket.
 * 
 * @param {HTMLElement} boardWrapper - Контейнер игры.
 * @param {Object} params - Параметры игры.
 * @param {Object} data - Данные раунда.
 */
export function applyRemoteRoundStart(boardWrapper, params, data) {
    params.currentRound = data.round;
    params.roundPairs = data.pairs;
    params.correctPairIndex = data.correctIndex;
    params.lockBoard = false;

    renderCards(params);
    updateUIDetails(params);

    // Запускаем таймер, если ещё не запущен (без сброса секунд)
    if (!params.timerInterval) {
        params.timerInterval = setInterval(() => {
            params.secondsElapsed++;
            updateUIDetails(params);
        }, 1000);
    }

    if (data.autoplay) {
        const audioUrl = getPairAudio(params.roundPairs[params.correctPairIndex]);
        playSound(audioUrl, params);
    }
}

/**
 * Завершает игру и показывает результаты.
 * 
 * @param {Object} params - Объект с параметрами игры.
 */
export function finishGame(params) {
    stopTimer(params);
    stopSound(params);

    const accuracy = params.totalClicks > 0 ? Math.round((params.correctClicks / params.totalClicks) * 100) : 100;

    if (params.uiCompletionMessageEl && params.uiCompletionTextEl) {
        params.uiCompletionTextEl.textContent = `Игра завершена! Верных: ${params.correctClicks}/${params.roundsCount} за ${params.secondsElapsed}с. Точность: ${accuracy}%`;
        params.uiCompletionMessageEl.style.display = 'block';
    }

    // Отправка WS события
    sendWebSocketEvent(params, {
        type: 'game_finish',
        correctClicks: params.correctClicks,
        totalRounds: params.roundsCount,
        totalClicks: params.totalClicks,
        timeElapsed: params.secondsElapsed
    });
}

/**
 * Применяет удаленное завершение игры, полученное через WebSocket.
 * 
 * @param {HTMLElement} boardWrapper - Контейнер игры.
 * @param {Object} params - Параметры игры.
 * @param {Object} data - Данные завершения.
 */
export function applyRemoteGameFinish(boardWrapper, params, data) {
    stopTimer(params);
    stopSound(params);

    const accuracy = data.totalClicks > 0 ? Math.round((data.correctClicks / data.totalClicks) * 100) : 100;

    if (params.uiCompletionMessageEl && params.uiCompletionTextEl) {
        params.uiCompletionTextEl.textContent = `Игра завершена! Верных: ${data.correctClicks}/${data.totalRounds} за ${data.timeElapsed}с. Точность: ${accuracy}%`;
        params.uiCompletionMessageEl.style.display = 'block';
    }
}

/**
 * Проигрывает аудиофайл.
 * 
 * @param {string} audioUrl - URL аудиофайла.
 * @param {Object} params - Параметры игры.
 */
export function playSound(audioUrl, params) {
    stopSound(params);

    try {
        const audio = new Audio(audioUrl);
        params.currentAudio = audio;

        const playPromise = audio.play();
        if (playPromise !== undefined) {
            playPromise.then(() => {
                // Успешное воспроизведение — снимаем оранжевую подсветку
                if (params.uiPlayButton) {
                    params.uiPlayButton.classList.remove('sound-loto-play-btn-blocked');
                    params.uiPlayButton.title = 'Воспроизвести звук';
                }
            }).catch(error => {
                console.warn(`[SoundLoto] Автовоспроизведение заблокировано браузером:`, error);
                if (params.uiPlayButton) {
                    params.uiPlayButton.classList.add('sound-loto-play-btn-blocked');
                    params.uiPlayButton.title = 'Нажмите для воспроизведения звука';
                }
            });
        }

        audio.onended = () => {
            if (params.uiPlayButton) {
                params.uiPlayButton.classList.remove('sound-loto-play-btn-blocked');
            }
        };
    } catch (error) {
        console.error(`[SoundLoto] Ошибка воспроизведения аудио:`, error);
    }
}

/**
 * Останавливает текущее воспроизведение аудио.
 * 
 * @param {Object} params - Параметры игры.
 */
export function stopSound(params) {
    if (params.currentAudio) {
        params.currentAudio.pause();
        params.currentAudio.currentTime = 0;
        params.currentAudio = null;
    }
}

/**
 * Обновляет отображение раунда, верных ответов и времени в UI.
 * 
 * @param {Object} params - Объект с параметрами игры.
 */
export function updateUIDetails(params) {
    if (params.uiRoundEl) params.uiRoundEl.textContent = Math.min(params.currentRound, params.roundsCount);
    if (params.uiCorrectEl) params.uiCorrectEl.textContent = params.correctClicks;
    if (params.uiTimeEl) params.uiTimeEl.textContent = params.secondsElapsed;
}

/**
 * Запускает игровой таймер.
 * 
 * @param {Object} params - Объект с параметрами игры.
 */
export function startTimer(params) {
    stopTimer(params);
    params.secondsElapsed = 0;
    updateUIDetails(params);
    params.timerInterval = setInterval(() => {
        params.secondsElapsed++;
        updateUIDetails(params);
    }, 1000);
}

/**
 * Останавливает игровой таймер.
 * 
 * @param {Object} params - Объект с параметрами игры.
 */
export function stopTimer(params) {
    if (params.timerInterval) {
        clearInterval(params.timerInterval);
        params.timerInterval = null;
    }
}

/**
 * Отправляет событие через WebSocket, если игра на доске.
 * 
 * @param {Object} params - Параметры игры.
 * @param {Object} data - Данные для отправки.
 */
function sendWebSocketEvent(params, data) {
    if (params.onWhiteboard && params.ws && params.ws.readyState === WebSocket.OPEN) {
        params.ws.send(JSON.stringify(data));
    }
}