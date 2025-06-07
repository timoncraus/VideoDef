const PRESET_IMAGE_SETS_CONFIG = {
    fruits: [
        'fruits/apple.png', 'fruits/banana.png', 'fruits/cherry.png', 'fruits/grapes.png', 
        'fruits/lemon.png', 'fruits/orange.png', 'fruits/strawberry.png', 'fruits/pineapple.png',
        'fruits/kiwi.png', 'fruits/watermelon.png', 'fruits/mango.png', 'fruits/coconut.png'
    ],
    animals: [
        'animals/panda.png', 'animals/fox.png', 'animals/bear.png', 'animals/koala.png',
        'animals/tiger.png', 'animals/lion.png', 'animals/cow.png', 'animals/pig.png',
        'animals/frog.png', 'animals/monkey.png', 'animals/chicken.png', 'animals/penguin.png'
    ]
};

/**
 * Генерирует полные URL-адреса для изображений из предустановленного набора.
 * Использует глобальную переменную `presetImagesBasePath`, определенную в HTML.
 * @param {string} setName - Имя набора из PRESET_IMAGE_SETS_CONFIG.
 * @returns {string[]} Массив полных URL-адресов изображений или пустой массив в случае ошибки.
 */
export function getFullPresetImageUrls(setName) {
    if (PRESET_IMAGE_SETS_CONFIG[setName] && typeof presetImagesBasePath !== 'undefined') {
        return PRESET_IMAGE_SETS_CONFIG[setName].map(relativePath => presetImagesBasePath + relativePath);
    }
    console.warn(`Набор изображений "${setName}" не найден или переменная presetImagesBasePath не определена.`);
    return [];
}

// Имя предустановленного набора по умолчанию
const DEFAULT_PRESET_NAME = 'fruits';

/**
 * Рассчитывает оптимальное количество строк и столбцов для сетки карточек.
 * Стремится сделать поле как можно более квадратным.
 * @param {number} totalCards - Общее количество карточек.
 * @returns {{rows: number, cols: number}} Объект с количеством строк и столбцов.
 */
function calculateGridDimensions(totalCards) {
    let bestRows = 1;
    let bestCols = totalCards;
    let minDiff = totalCards - 1;

    // Ищем делители числа totalCards, чтобы найти возможные конфигурации сетки
    for (let rows = 1; rows * rows <= totalCards; rows++) {
        if (totalCards % rows === 0) {
            const cols = totalCards / rows;
            // Если текущая разница меньше предыдущей минимальной, обновляем лучшие значения
            if (Math.abs(rows - cols) < minDiff) {
                minDiff = Math.abs(rows - cols);
                bestRows = rows;
                bestCols = cols;
            } else if (Math.abs(rows - cols) === minDiff) {
                // Если разница та же, предпочитаем вариант, где строк меньше или равно столбцам
                if (rows < bestRows) { 
                    bestRows = rows; 
                    bestCols = cols; 
                }
            }
        }
    }
    return bestRows > bestCols ? { rows: bestCols, cols: bestRows } : { rows: bestRows, cols: bestCols };
}

/**
 * Создает и возвращает объект с начальными параметрами игры.
 * @returns {object} Объект с параметрами игры.
 */
export function getGameParts() {
    return {
        // Параметры по умолчанию
        name: "Моя игра в пары",
        pairCount: 4,
        selectedImageSet: getFullPresetImageUrls(DEFAULT_PRESET_NAME),
        isCustomSet: false,
        customImageObjects: [],
        
        gridSize: { rows: 0, cols: 0 },
        cardContentSet: [],
        
        firstSelectedCard: null,
        secondSelectedCard: null,
        matchesFound: 0,
        totalMatches: 0,
        attempts: 0,
        lockBoard: false,
        
        timerInterval: null,
        secondsElapsed: 0,
        
        // Ссылки на DOM-элементы для обновления UI (инициализируются в initializeBoard)
        uiTimeEl: null,
        uiAttemptsEl: null,
        uiCompletionMessageEl: null,
        uiCompletionTextEl: null
    };
}

/**
 * Перемешивает элементы массива случайным образом (алгоритм Фишера-Йетса).
 * @param {Array<any>} array - Массив для перемешивания.
 * @returns {Array<any>} Новый массив с перемешанными элементами.
 */
export function shuffle(array) {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
}

/**
 * Инициализирует и создает игровое поле.
 * @param {HTMLElement} boardWrapper - DOM-элемент, в который будет встроено игровое поле (`.memory-game-wrapper`).
 * @param {object} gameParams - Объект с текущими параметрами игры.
 * @returns {boolean} `true` если инициализация прошла успешно, `false` в случае ошибки (например, нехватка изображений).
 */
export function initializeBoard(boardWrapper, gameParams) {
    // Сбрасываем ссылки на DOM-элементы
    gameParams.uiTimeEl = null;
    gameParams.uiAttemptsEl = null;
    gameParams.uiCompletionMessageEl = null;
    gameParams.uiCompletionTextEl = null;

    // Очищаем обертку от предыдущего содержимого
    boardWrapper.innerHTML = ''; 
    
    // Создаем главный контейнер для игровой доски=
    const gameBoard = document.createElement('div');
    gameBoard.className = 'memory-game-board';
    boardWrapper.appendChild(gameBoard); 

    // Создаем панель с информацией о ходе игры
    const gameDetailsBar = document.createElement('div');
    gameDetailsBar.className = 'game-details-bar';
    gameDetailsBar.innerHTML = `
        <p class="time">Время: <b data-role="time">0</b>с</p>
        <p class="moves">Ходы: <b data-role="attempts">0</b></p>
    `;
    gameBoard.appendChild(gameDetailsBar);
    gameParams.uiTimeEl = gameDetailsBar.querySelector('b[data-role="time"]');
    gameParams.uiAttemptsEl = gameDetailsBar.querySelector('b[data-role="attempts"]');

    // Создаем контейнер для сетки карточек
    const cardsGridContainer = document.createElement('div');
    cardsGridContainer.className = 'cards-grid-container';
    gameBoard.appendChild(cardsGridContainer);

    // Создаем DOM-элемент для сообщения о завершении игры, если он еще не был создан.
    if (!gameParams.uiCompletionMessageEl) { 
        const completionMessageDiv = document.createElement('div');
        completionMessageDiv.id = 'game-completion-message';
        completionMessageDiv.style.display = 'none';
        const completionTextP = document.createElement('p');
        completionMessageDiv.appendChild(completionTextP);
        boardWrapper.appendChild(completionMessageDiv); 
        gameParams.uiCompletionMessageEl = completionMessageDiv;
        gameParams.uiCompletionTextEl = completionTextP;
    } else {
        gameParams.uiCompletionMessageEl.style.display = 'none';
    }

    // Обновляем/сбрасываем игровые параметры
    gameParams.totalMatches = gameParams.pairCount;
    const totalCards = gameParams.pairCount * 2;
    gameParams.gridSize = calculateGridDimensions(totalCards);
    
    gameParams.matchesFound = 0;
    gameParams.attempts = 0;
    gameParams.firstSelectedCard = null;
    gameParams.secondSelectedCard = null;
    gameParams.lockBoard = false;
    gameParams.secondsElapsed = 0;

    // Подготовка набора изображений для игры
    let imagesForGame; 
    if (gameParams.isCustomSet) { // Если используется пользовательский набор
        // Проверяем, достаточно ли загружено уникальных изображений для выбранного количества пар
        if (gameParams.customImageObjects.length < gameParams.pairCount) {
            boardWrapper.innerHTML = `<p class="initial-message">Ошибка: Загружено ${gameParams.customImageObjects.length} уникальных изображений, а нужно ${gameParams.pairCount} для пар. Пожалуйста, загрузите больше изображений или выберите меньшую сложность.</p>`;
            if(gameParams.uiCompletionMessageEl) gameParams.uiCompletionMessageEl.style.display = 'none';
            updateUIDetails(gameParams);
            return false;
        }
        const uniqueCustomUrls = gameParams.customImageObjects.slice(0, gameParams.pairCount).map(obj => obj.url);
        imagesForGame = shuffle([...uniqueCustomUrls, ...uniqueCustomUrls]);
    } else { // Если используется предустановленный набор
        // Проверяем, достаточно ли изображений в выбранном пресете
        if (gameParams.selectedImageSet.length < gameParams.pairCount) {
            boardWrapper.innerHTML = `<p class="initial-message">Ошибка: В выбранном наборе ${gameParams.selectedImageSet.length} изображений, а нужно ${gameParams.pairCount} для пар. Выберите другой набор или сложность.</p>`;
            if(gameParams.uiCompletionMessageEl) gameParams.uiCompletionMessageEl.style.display = 'none';
            updateUIDetails(gameParams);
            return false;
        }
        const neededImageUrls = gameParams.selectedImageSet.slice(0, gameParams.pairCount);
        imagesForGame = shuffle([...neededImageUrls, ...neededImageUrls]);
    }
    gameParams.cardContentSet = imagesForGame; // Сохраняем подготовленный набор URL-ов

    // Настраиваем CSS Grid для контейнера карточек
    cardsGridContainer.style.gridTemplateColumns = `repeat(${gameParams.gridSize.cols}, 1fr)`;
    cardsGridContainer.style.gridTemplateRows = `repeat(${gameParams.gridSize.rows}, 1fr)`;

    // Создаем и добавляем карточки на поле
    gameParams.cardContentSet.forEach((imageUrl, index) => {
        const cardItem = document.createElement('div');
        cardItem.classList.add('memory-card');
        cardItem.dataset.imageUrl = imageUrl;
        cardItem.dataset.id = index;

        // Создаем лицевую сторону карточки
        const frontFace = document.createElement('div');
        frontFace.classList.add('card-face', 'front');
        const img = document.createElement('img');
        img.src = imageUrl;
        img.alt = "Изображение карточки";
        img.classList.add('card-face-image');
        frontFace.appendChild(img);

        // Создаем оборотную сторону (рубашку)
        const backFace = document.createElement('div');
        backFace.classList.add('card-face', 'back');

        // Добавляем лицевую и оборотную стороны в контейнер карточки
        cardItem.appendChild(frontFace);
        cardItem.appendChild(backFace);
        
        // Назначаем обработчик клика
        cardItem.addEventListener('click', () => handleCardClick(cardItem, gameParams));
        cardsGridContainer.appendChild(cardItem);
    });

    updateUIDetails(gameParams);
    startTimer(gameParams);
    return true;
}

/**
 * Обновляет отображение времени и количества ходов в UI.
 * @param {object} gameParams - Объект с параметрами игры.
 */
function updateUIDetails(gameParams) {
    if (gameParams.uiTimeEl) gameParams.uiTimeEl.textContent = gameParams.secondsElapsed;
    if (gameParams.uiAttemptsEl) gameParams.uiAttemptsEl.textContent = gameParams.attempts;
}

/**
 * Обрабатывает клик по карточке.
 * @param {HTMLElement} clickedCard - DOM-элемент карточки, по которой кликнули.
 * @param {object} gameParams - Объект с параметрами игры.
 */
function handleCardClick(clickedCard, gameParams) {
    if (gameParams.lockBoard || 
        clickedCard === gameParams.firstSelectedCard || 
        clickedCard.classList.contains('flipped') || 
        clickedCard.classList.contains('matched') || 
        gameParams.matchesFound === gameParams.totalMatches) {
        return;
    }

    clickedCard.classList.add('flipped');

    if (!gameParams.firstSelectedCard) { // Если это первая выбранная карточка
        gameParams.firstSelectedCard = clickedCard;
        return;
    }
    // Если это вторая выбранная карточка
    gameParams.secondSelectedCard = clickedCard;
    gameParams.lockBoard = true;
    gameParams.attempts++;
    updateUIDetails(gameParams);
    checkForMatch(gameParams);
}

/**
 * Проверяет, совпадают ли две выбранные карточки.
 * @param {object} gameParams - Объект с параметрами игры.
 */
function checkForMatch(gameParams) {
    const isMatch = gameParams.firstSelectedCard.dataset.imageUrl === gameParams.secondSelectedCard.dataset.imageUrl;

    if (isMatch) {
        gameParams.matchesFound++;
        gameParams.firstSelectedCard.classList.add('matched');
        gameParams.secondSelectedCard.classList.add('matched');
        resetTurn(gameParams);
        checkVictory(gameParams);
    } else {
        // Устанавливаем таймаут, чтобы игрок успел увидеть вторую карточку перед тем, как они перевернутся обратно
        setTimeout(() => {
            if(gameParams.firstSelectedCard) gameParams.firstSelectedCard.classList.remove('flipped');
            if(gameParams.secondSelectedCard) gameParams.secondSelectedCard.classList.remove('flipped');
            resetTurn(gameParams);
        }, 1000);
    }
}

/**
 * Сбрасывает состояние выбора карт (firstSelectedCard, secondSelectedCard) и разблокирует доску.
 * @param {object} gameParams - Объект с параметрами игры.
 */
function resetTurn(gameParams) {
    gameParams.firstSelectedCard = null;
    gameParams.secondSelectedCard = null;
    gameParams.lockBoard = false;
}

/**
 * Проверяет, найдены ли все пары, и отображает сообщение о победе.
 * @param {object} gameParams - Объект с параметрами игры.
 */
function checkVictory(gameParams) {
    if (gameParams.matchesFound === gameParams.totalMatches && gameParams.totalMatches > 0) {
        stopTimer(gameParams);
        
        if (gameParams.uiCompletionMessageEl && gameParams.uiCompletionTextEl) {
            gameParams.uiCompletionTextEl.textContent = `Поздравляем! Вы нашли все ${gameParams.totalMatches} пары за ${gameParams.attempts} ходов и ${gameParams.secondsElapsed}с!`;
            gameParams.uiCompletionMessageEl.style.display = 'block';
        } else {
            console.error("Элементы сообщения о победе не найдены в gameParams при проверке победы.");
        }
    }
}

/**
 * Запускает игровой таймер.
 * @param {object} gameParams - Объект с параметрами игры.
 */
function startTimer(gameParams) {
    stopTimer(gameParams);
    gameParams.secondsElapsed = 0;
    updateUIDetails(gameParams);
    gameParams.timerInterval = setInterval(() => {
        gameParams.secondsElapsed++;
        updateUIDetails(gameParams);
    }, 1000);
}

/**
 * Останавливает игровой таймер.
 * @param {object} gameParams - Объект с параметрами игры.
 */
export function stopTimer(gameParams) {
    if (gameParams.timerInterval) {
        clearInterval(gameParams.timerInterval);
        gameParams.timerInterval = null;
    }
}