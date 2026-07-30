/**
 * Модуль логики игры "Пазл".
 * Содержит функции для создания, управления и взаимодействия с пазлом.
 */

/**
 * Генерирует базовые компоненты для пазла.
 * 
 * @returns {Array} [params, container, message] - Параметры, контейнер и сообщение
 */
export function getPuzzleParts() {
    const puzzleParams = {
        gridSize: 2,
        piecePositions: [],
        selectedImage: typeof images !== 'undefined' ? images + '/british-cat.jpg' : null,
        selectedPiece: null,
        remoteSelectedPiece: null,
        onWhiteboard: false,
        gameId: null,
        boardRoomName: null,
        ws: null,
        name: "Пазл",
        id: null,
        isPreset: false,
        imageFile: null
    };
    
    const puzzleContainer = createPuzzleContainer();
    const message = createGameMessage();
    
    return [puzzleParams, puzzleContainer, message];
}

/**
 * Создает пазл в указанном контейнере.
 * 
 * @param {HTMLElement} puzzleContainer - Контейнер для элементов
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} message - Элемент для отображения сообщений
 * @param {boolean} useExistingPositions - Если true, использует puzzleParams.piecePositions
 */
export function createPuzzle(puzzleContainer, puzzleParams, message, useExistingPositions = false) {
    if (useExistingPositions && puzzleContainer.querySelectorAll('.puzzle-piece').length > 0) {
        const currentPiecesCount = puzzleContainer.querySelectorAll('.puzzle-piece').length;
        if (currentPiecesCount === puzzleParams.gridSize * puzzleParams.gridSize) {
            placePieces(puzzleContainer, puzzleParams);
            checkVictory(puzzleParams, message);
            return;
        }
    }

    puzzleContainer.innerHTML = '';
    message.style.display = 'none';
    
    if (!puzzleParams.selectedImage) {
        puzzleContainer.innerHTML = '<p style="text-align: center; padding: 10px;">Выберите изображение в настройках.</p>';
        return;
    }
    
    if (!useExistingPositions || !puzzleParams.piecePositions || puzzleParams.piecePositions.length !== puzzleParams.gridSize * puzzleParams.gridSize) {
        console.log(`Генерация новых позиций для пазла ${puzzleParams.gameId || '(отдельный)'}`);
        puzzleParams.piecePositions = shuffle([...Array(puzzleParams.gridSize * puzzleParams.gridSize).keys()]);
    }
    
    for (let i = 0; i < puzzleParams.gridSize * puzzleParams.gridSize; i++) {
        const piece = document.createElement('div');
        piece.classList.add('puzzle-piece');
        piece.setAttribute('data-index', i);
        
        const percent = 100 / puzzleParams.gridSize;
        piece.style.width = `${percent}%`;
        piece.style.height = `${percent}%`;
        piece.style.backgroundSize = `${puzzleParams.gridSize * 100}% ${puzzleParams.gridSize * 100}%`;
        
        piece.addEventListener('click', () => handlePieceClick(puzzleContainer, puzzleParams, piece, message));
        puzzleContainer.appendChild(piece);
    }
    
    updatePuzzleImage(puzzleContainer, puzzleParams);
    
    if (puzzleParams.onWhiteboard && puzzleParams.ws && puzzleParams.ws.readyState === WebSocket.OPEN && !useExistingPositions) {
        puzzleParams.ws.send(JSON.stringify({
            type: 'puzzle_state_change',
            puzzleState: {
                gridSize: puzzleParams.gridSize,
                piecePositions: puzzleParams.piecePositions,
                selectedImage: puzzleParams.selectedImage,
                isPreset: puzzleParams.isPreset,
                name: puzzleParams.name,
                id: puzzleParams.id
            }
        }));
    }
}

/**
 * Обновляет фоновое изображение и расставляет элементы пазла.
 * 
 * @param {HTMLElement} puzzleContainer - Контейнер с элементами пазла
 * @param {Object} puzzleParams - Параметры пазла
 */
export function updatePuzzleImage(puzzleContainer, puzzleParams) {
    if (!puzzleParams.selectedImage) return;
    
    const pieces = puzzleContainer.querySelectorAll('.puzzle-piece');
    pieces.forEach((piece) => {
        const originalIndex = parseInt(piece.dataset.index, 10);
        piece.style.backgroundImage = `url("${puzzleParams.selectedImage}")`;
        
        const row = Math.floor(originalIndex / puzzleParams.gridSize);
        const col = originalIndex % puzzleParams.gridSize;
        piece.style.backgroundPosition = `${(col * -100)}% ${(row * -100)}%`;
    });
    
    placePieces(puzzleContainer, puzzleParams);
}

/**
 * Располагает элементы пазла в соответствии с текущими позициями.
 * 
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 */
export function placePieces(puzzleContainer, puzzleParams) {
    const pieces = Array.from(puzzleContainer.querySelectorAll('.puzzle-piece'));
    const gridPositions = [];
    const percent = 100 / puzzleParams.gridSize;
    
    for (let row = 0; row < puzzleParams.gridSize; row++) {
        for (let col = 0; col < puzzleParams.gridSize; col++) {
            gridPositions.push([col * percent, row * percent]);
        }
    }
    
    pieces.forEach((piece, domOrderIndex) => {
        const targetGridCellIndex = puzzleParams.piecePositions[domOrderIndex];
        if (targetGridCellIndex !== undefined && gridPositions[targetGridCellIndex]) {
            const [x, y] = gridPositions[targetGridCellIndex];
            piece.style.left = `${x}%`;
            piece.style.top = `${y}%`;
        }
    });
}

/**
 * Перемешивает элементы массива (алгоритм Фишера-Йетса).
 * 
 * @param {Array} array - Исходный массив
 * @returns {Array} Перемешанный массив
 */
export function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

/**
 * Обрабатывает клик на элементе пазла.
 * 
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} pieceDomElement - Кликнутый DOM-элемент куска
 * @param {HTMLElement} message - Элемент сообщения
 */
export function handlePieceClick(puzzleContainer, puzzleParams, pieceDomElement, message) {
    const clickedPieceDataIndex = parseInt(pieceDomElement.dataset.index, 10);
    
    // Сначала шлем в сокет
    if (puzzleParams.onWhiteboard && puzzleParams.ws && puzzleParams.ws.readyState === WebSocket.OPEN) {
        puzzleParams.ws.send(JSON.stringify({
            type: 'puzzle_piece_click',
            pieceIndex: clickedPieceDataIndex
        }));
    }
    
    // Выполняем локальное действие (Optimistic UI)
    if (!puzzleParams.selectedPiece) {
        puzzleParams.selectedPiece = pieceDomElement;
        pieceDomElement.style.outline = '2px solid red';
    } else if (puzzleParams.selectedPiece === pieceDomElement) {
        pieceDomElement.style.outline = '';
        puzzleParams.selectedPiece = null;
    } else {
        swapPiecesAndUpdate(puzzleContainer, puzzleParams, puzzleParams.selectedPiece, pieceDomElement);
        checkVictory(puzzleParams, message);
        
        if (puzzleParams.selectedPiece) {
            puzzleParams.selectedPiece.style.outline = '';
        }
        puzzleParams.selectedPiece = null;
    }
}

/**
 * Обменивает куски местами и обновляет отображение.
 * 
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} p1Dom - Первый DOM-элемент
 * @param {HTMLElement} p2Dom - Второй DOM-элемент
 */
function swapPiecesAndUpdate(puzzleContainer, puzzleParams, p1Dom, p2Dom) {
    const pieces = Array.from(puzzleContainer.querySelectorAll('.puzzle-piece'));
    const domIndex1 = pieces.indexOf(p1Dom);
    const domIndex2 = pieces.indexOf(p2Dom);
    
    if (domIndex1 === -1 || domIndex2 === -1) {
        console.error("Один из элементов для обмена не найден.");
        return;
    }
    
    [puzzleParams.piecePositions[domIndex1], puzzleParams.piecePositions[domIndex2]] =
        [puzzleParams.piecePositions[domIndex2], puzzleParams.piecePositions[domIndex1]];
    
    placePieces(puzzleContainer, puzzleParams);
}

/**
 * Применяет удаленное взаимодействие с куском.
 * 
 * @param {HTMLElement} puzzleContainer - Контейнер пазла
 * @param {Object} puzzleParams - Параметры пазла
 * @param {number} pieceDataIndexToInteract - data-index куска
 * @param {HTMLElement} message - Элемент для сообщений
 */
export function applyRemotePieceInteraction(puzzleContainer, puzzleParams, pieceDataIndexToInteract, message) {
    const pieces = Array.from(puzzleContainer.querySelectorAll('.puzzle-piece'));
    const targetPieceDom = pieces.find(p => parseInt(p.dataset.index, 10) === pieceDataIndexToInteract);
    
    if (!targetPieceDom) {
        console.warn(`[REMOTE] Кусок с data-index ${pieceDataIndexToInteract} не найден.`);
        return;
    }
    
    if (!puzzleParams.remoteSelectedPiece) {
        puzzleParams.remoteSelectedPiece = targetPieceDom;
        targetPieceDom.style.outline = '2px solid blue';
    } else if (puzzleParams.remoteSelectedPiece === targetPieceDom) {
        targetPieceDom.style.outline = '';
        puzzleParams.remoteSelectedPiece = null;
    } else {
        if (puzzleParams.remoteSelectedPiece) {
            puzzleParams.remoteSelectedPiece.style.outline = '';
        }
        swapPiecesAndUpdate(puzzleContainer, puzzleParams, puzzleParams.remoteSelectedPiece, targetPieceDom);
        puzzleParams.remoteSelectedPiece = null;
        checkVictory(puzzleParams, message);
    }
}

/**
 * Проверяет победу в пазле.
 * 
 * @param {Object} puzzleParams - Параметры пазла
 * @param {HTMLElement} message - Элемент сообщения
 */
export function checkVictory(puzzleParams, message) {
    if (!puzzleParams || !puzzleParams.piecePositions) return;
    
    const isVictory = puzzleParams.piecePositions.every((val, idx) => val === idx);
    
    if (isVictory) {
        if (message) message.style.display = 'block';
        console.log(`Пазл ${puzzleParams.gameId || '(отдельный)'} собран!`);
    } else {
        if (message) message.style.display = 'none';
    }
}

/**
 * Создает контейнер для пазлов.
 * 
 * @returns {HTMLDivElement} Контейнер
 */
function createPuzzleContainer() {
    const container = document.createElement('div');
    container.classList.add('puzzle-container');
    return container;
}

/**
 * Создает сообщение о победе.
 * 
 * @returns {HTMLDivElement} Элемент сообщения
 */
function createGameMessage() {
    const message = document.createElement('div');
    message.id = 'game-message';
    message.style.display = 'none';
    message.textContent = 'Поздравляем! Вы собрали пазл!';
    return message;
}