/**
 * Генерирует базовые компоненты для пазла
 * @returns {Array} [params, container, message] - Параметры, контейнер и сообщение
 */
export function getPuzzleParts() {
    // Параметры пазла по умолчанию
    let puzzleParams = {
        gridSize: 2, // Размер сетки (2x2)
        piecePositions: [], // Позиции элементов
        selectedImage: images + "/british-cat.jpg", // Изображение по умолчанию
        selectedPiece: null, // Локально выбранный кусок для текущего пользователя
        remoteSelectedPiece: null, // Кусок, "выбранный" удаленным пользователем (для обмена)
        onWhiteboard: false, // Флаг, что пазл на доске
        gameId: null, // Уникальный ID экземпляра пазла на доске
        boardRoomName: null, // Имя комнаты доски
        ws: null, // WebSocket соединение для этого экземпляра пазла
        name: "Пазл", // Имя пазла (для сохранения)
        id: null, // ID пазла из БД (после сохранения/загрузки)
        isPreset: false, // Является ли изображение пресетом
        imageFile: null, // Для загрузки пользовательских фото
    };

    const puzzleContainer = createPuzzleContainer();
    const message = createGameMessage();

    return [puzzleParams, puzzleContainer, message];
}

/**
 * Создает пазл в указанном контейнере
 * @param {HTMLElement} puzzleContainer - Контейнер для элементов
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} message - Элемент для отображения сообщений
 * @param {boolean} useExistingPositions - Если true, использует puzzleParams.piecePositions, иначе генерирует новые
 */
export function createPuzzle(
    puzzleContainer,
    puzzleParams,
    message,
    useExistingPositions = false
) {
    puzzleContainer.innerHTML = "";
    message.style.display = "none";

    if (!puzzleParams.selectedImage) {
        puzzleContainer.innerHTML =
            '<p style="text-align: center; padding: 10px;">Выберите изображение в настройках.</p>';
        return; // Не создаем пазл без изображения
    }

    // Генерируем новые позиции только если не используем существующие
    if (!useExistingPositions ||
        !puzzleParams.piecePositions ||
        puzzleParams.piecePositions.length !==
        puzzleParams.gridSize * puzzleParams.gridSize
    ) {
        console.log(
            `Генерация новых позиций для пазла ${
        puzzleParams.gameId || "(отдельный)"
      } (размер ${puzzleParams.gridSize}x${puzzleParams.gridSize}).`
        );
        puzzleParams.piecePositions = shuffle([
            ...Array(puzzleParams.gridSize * puzzleParams.gridSize).keys(),
        ]);
    } else {
        console.log(
            `Использование существующих позиций для пазла ${
        puzzleParams.gameId || "(отдельный)"
      }.`
        );
    }

    // Создание элементов пазла
    for (let i = 0; i < puzzleParams.gridSize * puzzleParams.gridSize; i++) {
        const piece = document.createElement("div");
        piece.classList.add("puzzle-piece");
        // data-index всегда соответствует оригинальному индексу куска (0..N-1)
        piece.setAttribute("data-index", i);

        // Расчет размеров элемента
        const percent = 100 / puzzleParams.gridSize;
        piece.style.width = `${percent}%`;
        piece.style.height = `${percent}%`;
        piece.style.backgroundSize = `${puzzleParams.gridSize * 100}% ${
      puzzleParams.gridSize * 100
    }%`;

        // Обработчик клика на элемент
        piece.addEventListener("click", () =>
            handlePieceClick(puzzleContainer, puzzleParams, piece, message)
        );

        puzzleContainer.appendChild(piece);
    }

    // Установка фона и расстановка по местам
    updatePuzzleImage(puzzleContainer, puzzleParams);

    // Отправка состояния, если это пазл на доске, WS есть, и это не обновление от другого клиента
    // (useExistingPositions = true обычно означает, что состояние пришло по WS)
    if (
        puzzleParams.onWhiteboard &&
        puzzleParams.ws &&
        puzzleParams.ws.readyState === WebSocket.OPEN &&
        !useExistingPositions
    ) {
        console.log(
            `[PUZZLE-LOGIC] Отправка состояния пазла ${puzzleParams.gameId} после создания/сброса.`
        );
        puzzleParams.ws.send(
            JSON.stringify({
                type: "puzzle_state_change",
                puzzleState: {
                    gridSize: puzzleParams.gridSize,
                    piecePositions: puzzleParams.piecePositions,
                    selectedImage: puzzleParams.selectedImage,
                    isPreset: puzzleParams.isPreset,
                    name: puzzleParams.name,
                    id: puzzleParams.id,
                },
            })
        );
    }
}

/**
 * Обновляет фоновое изображение и расставляет элементы пазла
 * @param {HTMLElement} puzzleContainer - Контейнер с элементами пазла
 * @param {Object} puzzleParams - Параметры пазла
 */
export function updatePuzzleImage(puzzleContainer, puzzleParams) {
    if (!puzzleParams.selectedImage) return; // Ничего не делаем без изображения

    const pieces = puzzleContainer.querySelectorAll(".puzzle-piece");
    pieces.forEach((piece) => {
        const originalIndex = parseInt(piece.dataset.index, 10);
        piece.style.backgroundImage = `url("${puzzleParams.selectedImage}")`;
        const row = Math.floor(originalIndex / puzzleParams.gridSize);
        const col = originalIndex % puzzleParams.gridSize;
        piece.style.backgroundPosition = `${col * -100}% ${row * -100}%`;
    });
    placePieces(puzzleContainer, puzzleParams);
}

// Создание контейнера для пазлов
function createPuzzleContainer() {
    const container = document.createElement("div");
    container.classList.add("puzzle-container");
    return container;
}

/**
 * Располагает элементы пазла в соответствии с текущими позициями
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 */
export function placePieces(puzzleContainer, puzzleParams) {
    const pieces = Array.from(puzzleContainer.querySelectorAll(".puzzle-piece"));
    const gridPositions = [];
    const percent = 100 / puzzleParams.gridSize;

    // Генерация сетки
    for (let row = 0; row < puzzleParams.gridSize; row++) {
        for (let col = 0; col < puzzleParams.gridSize; col++) {
            gridPositions.push([col * percent, row * percent]);
        }
    }

    // Распределение элементов по позициям
    pieces.forEach((piece, domOrderIndex) => {
        const targetGridCellIndex = puzzleParams.piecePositions[domOrderIndex];
        if (
            targetGridCellIndex !== undefined &&
            gridPositions[targetGridCellIndex]
        ) {
            const [x, y] = gridPositions[targetGridCellIndex];
            piece.style.left = `${x}%`;
            piece.style.top = `${y}%`;
        } else {
            console.error(
                `Ошибка расстановки: для куска ${domOrderIndex} не найдена позиция ${targetGridCellIndex} в piecePositions или gridPositions.`
            );
        }
    });
}

/**
 * Алгоритм Фишера-Йетса для перемешивания массива
 * @param {Array} array - Исходный массив
 * @returns {Array} Перемешанный массив
 */
function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

/**
 * Обрабатывает клик на элементе пазла
 * Для пазлов на доске отправляет событие через WebSocket.
 * Локально обрабатывает UI выделения. Обмен кусками для синхронизируемых пазлов происходит при получении ответа.
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} pieceDomElement - Кликнутый DOM-элемент куска
 * @param {HTMLElement} message - Элемент сообщения
 */
export function handlePieceClick(
    puzzleContainer,
    puzzleParams,
    pieceDomElement,
    message
) {
    const clickedPieceDataIndex = parseInt(pieceDomElement.dataset.index, 10);

    // Отправляем действие по WebSocket этого пазла, если это пазл на доске и WS есть
    if (
        puzzleParams.onWhiteboard &&
        puzzleParams.ws &&
        puzzleParams.ws.readyState === WebSocket.OPEN
    ) {
        puzzleParams.ws.send(
            JSON.stringify({
                type: "puzzle_piece_click",
                pieceIndex: clickedPieceDataIndex, // Отправляем data-index оригинального куска
            })
        );
    }

    // Локальная обработка UI (выделение) и логики (если не пазл на доске или WS нет)
    if (!puzzleParams.selectedPiece) {
        // Первый локальный клик
        puzzleParams.selectedPiece = pieceDomElement;
        pieceDomElement.style.outline = "2px solid red";
    } else if (puzzleParams.selectedPiece === pieceDomElement) {
        // Клик по уже выделенному (отмена)
        pieceDomElement.style.outline = "";
        puzzleParams.selectedPiece = null;
    } else {
        // Второй локальный клик (по другому куску)
        // Если это не пазл на доске с активным WS, то делаем обмен локально.
        // Если это пазл на доске с WS, то обмен произойдет при получении сообщения от puzzleWs.onmessage -> applyRemotePieceInteraction.
        if (!puzzleParams.onWhiteboard ||
            !puzzleParams.ws ||
            puzzleParams.ws.readyState !== WebSocket.OPEN
        ) {
            swapPiecesAndUpdate(
                puzzleContainer,
                puzzleParams,
                puzzleParams.selectedPiece,
                pieceDomElement
            );
            checkVictory(puzzleParams, message); // Проверка победы только для локальных изменений
        }
        // В любом случае снимаем локальное UI выделение после второго клика
        if (puzzleParams.selectedPiece) {
            puzzleParams.selectedPiece.style.outline = "";
        }
        puzzleParams.selectedPiece = null;
    }
}

// Вспомогательная функция для обмена кусками (только меняет piecePositions и вызывает placePieces)
function swapPiecesAndUpdate(puzzleContainer, puzzleParams, p1Dom, p2Dom) {
    const pieces = Array.from(puzzleContainer.querySelectorAll(".puzzle-piece"));
    const domIndex1 = pieces.indexOf(p1Dom);
    const domIndex2 = pieces.indexOf(p2Dom);

    if (domIndex1 === -1 || domIndex2 === -1) {
        console.error(
            "Один из элементов для обмена не найден в DOM-контейнере пазла."
        );
        return;
    }

    // Меняем местами значения в piecePositions, соответствующие этим DOM-элементам
    [
        puzzleParams.piecePositions[domIndex1],
        puzzleParams.piecePositions[domIndex2],
    ] = [
        puzzleParams.piecePositions[domIndex2],
        puzzleParams.piecePositions[domIndex1],
    ];

    placePieces(puzzleContainer, puzzleParams); // Перерисовываем пазл с новыми позициями
}

/**
 * Применяет "удаленное" взаимодействие с куском (клик от другого пользователя).
 * Вызывается из puzzleWs.onmessage в puzzle/index.js.
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 * @param {number} pieceDataIndexToInteract - data-index куска, с которым взаимодействуют
 * @param {HTMLElement} message - Элемент для сообщений
 */
export function applyRemotePieceInteraction(
    puzzleContainer,
    puzzleParams,
    pieceDataIndexToInteract,
    message
) {
    const pieces = Array.from(puzzleContainer.querySelectorAll(".puzzle-piece"));
    const targetPieceDom = pieces.find(
        (p) => parseInt(p.dataset.index, 10) === pieceDataIndexToInteract
    );

    if (!targetPieceDom) {
        console.warn(
            `[REMOTE] Кусок с data-index ${pieceDataIndexToInteract} не найден в пазле ${puzzleParams.gameId}.`
        );
        return;
    }

    // Логика для удаленного взаимодействия:
    // Если еще не было "удаленно выбранного" куска, запоминаем этот.
    // Если кликнули по "удаленно выбранному", сбрасываем выбор.
    // Если кликнули по другому, производим обмен.
    if (!puzzleParams.remoteSelectedPiece) {
        puzzleParams.remoteSelectedPiece = targetPieceDom;
        // Временное UI выделение для "удаленно" выбранного куска
        targetPieceDom.style.outline = "2px solid blue";
    } else if (puzzleParams.remoteSelectedPiece === targetPieceDom) {
        targetPieceDom.style.outline = "";
        puzzleParams.remoteSelectedPiece = null;
    } else {
        // Второй "удаленный" клик - производим обмен
        if (puzzleParams.remoteSelectedPiece) {
            puzzleParams.remoteSelectedPiece.style.outline = "";
        }
        swapPiecesAndUpdate(
            puzzleContainer,
            puzzleParams,
            puzzleParams.remoteSelectedPiece,
            targetPieceDom
        );
        puzzleParams.remoteSelectedPiece = null; // Сброс
        checkVictory(puzzleParams, message); // Проверяем победу после удаленного обмена
    }
}

export function checkVictory(puzzleParams, message) {
    if (!puzzleParams || !puzzleParams.piecePositions) return; // Защита от ошибок
    const isVictory = puzzleParams.piecePositions.every(
        (val, idx) => val === idx
    );
    if (isVictory) {
        if (message) message.style.display = "block";
        console.log(`Пазл ${puzzleParams.gameId || "(отдельный)"} собран!`);
    } else {
        if (message) message.style.display = "none";
    }
}

// Создание сообщение о победе
function createGameMessage() {
    const message = document.createElement("div");
    message.id = "game-message";
    message.style.display = "none";
    message.textContent = "Поздравляем! Вы собрали пазл!";
    return message;
}