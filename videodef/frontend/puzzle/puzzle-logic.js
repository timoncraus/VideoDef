/**
 * Генерирует базовые компоненты для пазла
 * @returns {Array} [params, container, message] - Параметры, контейнер и сообщение
 */
export function getPuzzleParts() {
    // Параметры пазла по умолчанию
    let puzzleParams = {
        gridSize: 2, // Размер сетки (2x2)
        piecePositions: [], // Позиции элементов
        selectedImage: images + '/british-cat.jpg', // Изображение по умолчанию
        selectedPiece: null // Выбранный элемент
    }

    const puzzleContainer = createPuzzleContainer();
    const message = createGameMessage();

    return [puzzleParams, puzzleContainer, message];
}

/**
 * Создает пазл в указанном контейнере
 * @param {HTMLElement} puzzleContainer - Контейнер для элементов
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} message - Элемент для отображения сообщений
 */
export function createPuzzle(puzzleContainer, puzzleParams, message) {
    puzzleContainer.innerHTML = '';
    // Перемешиваем позиции элементов пазла
    puzzleParams.piecePositions = shuffle([...Array(puzzleParams.gridSize * puzzleParams.gridSize).keys()]);

    // Создание элементов пазла
    for (let i = 0; i < puzzleParams.gridSize * puzzleParams.gridSize; i++) {
        const piece = document.createElement('div');
        piece.classList.add('puzzle-piece');
        piece.id = `piece-${i + 1}`;
        piece.setAttribute('data-index', i);

        // Расчет размеров элемента
        const percent = 100 / puzzleParams.gridSize;
        piece.style.width = `${percent}%`;
        piece.style.height = `${percent}%`;
        piece.style.backgroundSize = `${puzzleParams.gridSize * 100}% ${puzzleParams.gridSize * 100}%`;

        // Обработчик клика на элемент
        piece.addEventListener('click', () =>
            handlePieceClick(puzzleContainer, puzzleParams, piece, message)
        );

        puzzleContainer.appendChild(piece);
    }

    placePieces(puzzleContainer, puzzleParams);
}

// Создание контейнера для пазлов
function createPuzzleContainer() {
    const container = document.createElement('div');
    container.classList.add('puzzle-container');

    const ids = '123456789'.split('');

    ids.forEach((id, index) => {
        const piece = document.createElement('div');
        piece.classList.add('puzzle-piece');
        piece.id = `piece-${id}`;
        piece.setAttribute('draggable', 'true');
        piece.setAttribute('data-index', id);
        container.appendChild(piece);
    });

    return container;
}

/**
 * Располагает элементы пазла в соответствии с текущими позициями
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 */
export function placePieces(puzzleContainer, puzzleParams) {
    const pieces = puzzleContainer.querySelectorAll('.puzzle-piece');
    const gridPositions = [];
    const percent = 100 / puzzleParams.gridSize;

    // Генерация сетки
    for (let row = 0; row < puzzleParams.gridSize; row++) {
        for (let col = 0; col < puzzleParams.gridSize; col++) {
            gridPositions.push([col * percent, row * percent]);
        }
    }

    // Распределение элементов по позициям
    pieces.forEach((piece, idx) => {
        const [x, y] = gridPositions[puzzleParams.piecePositions[idx]];
        piece.style.left = `${x}%`;
        piece.style.top = `${y}%`;

        // Расчет позиции фона
        const row = Math.floor(idx / puzzleParams.gridSize);
        const col = idx % puzzleParams.gridSize;
        piece.style.backgroundPosition =
            `${(col * -100)}% ${(row  * -100)}%`;
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
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} piece - Выбранный элемент
 * @param {HTMLElement} message - Элемент сообщения
 */
function handlePieceClick(puzzleContainer, puzzleParams, piece, message) {
    if (!puzzleParams.selectedPiece) {
        puzzleParams.selectedPiece = piece;
        piece.style.outline = '2px solid red';
    } else if (puzzleParams.selectedPiece === piece) {
        piece.style.outline = '';
        puzzleParams.selectedPiece = null;
    } else {
        swapPieces(puzzleContainer, puzzleParams, puzzleParams.selectedPiece, piece);
        puzzleParams.selectedPiece.style.outline = '';
        puzzleParams.selectedPiece = null;
        checkVictory(puzzleParams, message);
    }
}

// Перемещение элементов пазла
function swapPieces(puzzleContainer, puzzleParams, p1, p2) {
    const i1 = Array.from(puzzleContainer.querySelectorAll('.puzzle-piece')).indexOf(p1);
    const i2 = Array.from(puzzleContainer.querySelectorAll('.puzzle-piece')).indexOf(p2);
    [puzzleParams.piecePositions[i1], puzzleParams.piecePositions[i2]] = [puzzleParams.piecePositions[i2], puzzleParams.piecePositions[i1]];
    placePieces(puzzleContainer, puzzleParams);
}

// Проверка условий победы
function checkVictory(puzzleParams, message) {
    const isVictory = puzzleParams.piecePositions.every((val, idx) => val === idx);
    if (isVictory) {
        message.style.display = 'block';
    }
}

// Создание сообщение о победе
function createGameMessage() {
    const message = document.createElement('div');
    message.id = 'game-message';
    message.style.display = 'none';
    message.textContent = 'Поздравляем! Вы собрали пазл!';
    return message;
}