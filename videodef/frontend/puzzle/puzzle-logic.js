export function getPuzzleParts() {
    let puzzleParams = {
        gridSize: 2,
        piecePositions: [],
        selectedImage: images + '/puzzle_test.png',
        selectedPiece: null
    }

    const puzzleContainer = createPuzzleContainer();
    const message = createGameMessage();

    return [puzzleParams, puzzleContainer, message];
}

export function createPuzzle(puzzleContainer, puzzleParams, message) {
    puzzleContainer.innerHTML = '';
    puzzleParams.piecePositions = shuffle([...Array(puzzleParams.gridSize * puzzleParams.gridSize).keys()]);

    for (let i = 0; i < puzzleParams.gridSize * puzzleParams.gridSize; i++) {
        const piece = document.createElement('div');
        piece.classList.add('puzzle-piece');
        piece.id = `piece-${i + 1}`;
        piece.setAttribute('data-index', i);
        const percent = 100 / puzzleParams.gridSize;
        piece.style.width = `${percent}%`;
        piece.style.height = `${percent}%`;
        piece.style.backgroundSize = `${puzzleParams.gridSize * 100}% ${puzzleParams.gridSize * 100}%`;
        piece.addEventListener('click', () => handlePieceClick(puzzleContainer, puzzleParams, piece, message));

        puzzleContainer.appendChild(piece);
    }



    placePieces(puzzleContainer, puzzleParams);
}

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

export function placePieces(puzzleContainer, puzzleParams) {
    const pieces = puzzleContainer.querySelectorAll('.puzzle-piece');
    const gridPositions = [];
    const percent = 100 / puzzleParams.gridSize;
    for (let row = 0; row < puzzleParams.gridSize; row++) {
        for (let col = 0; col < puzzleParams.gridSize; col++) {
            gridPositions.push([col * percent, row * percent]);
        }
    }

    pieces.forEach((piece, idx) => {
        const [x, y] = gridPositions[puzzleParams.piecePositions[idx]];
        piece.style.left = `${x}%`;
        piece.style.top = `${y}%`;

        const row = Math.floor(idx / puzzleParams.gridSize);
        const col = idx % puzzleParams.gridSize;
        piece.style.backgroundPosition =
            `${(col * -100)}% ${(row  * -100)}%`;
    });
}

function shuffle(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}

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

function swapPieces(puzzleContainer, puzzleParams, p1, p2) {
    const i1 = Array.from(document.querySelectorAll('.puzzle-piece')).indexOf(p1);
    const i2 = Array.from(document.querySelectorAll('.puzzle-piece')).indexOf(p2);
    [puzzleParams.piecePositions[i1], puzzleParams.piecePositions[i2]] = [puzzleParams.piecePositions[i2], puzzleParams.piecePositions[i1]];
    placePieces(puzzleContainer, puzzleParams);
}

function checkVictory(puzzleParams, message) {
    const isVictory = puzzleParams.piecePositions.every((val, idx) => val === idx);
    if (isVictory) {
        message.style.display = 'block';
    }
}

function createGameMessage() {
    const message = document.createElement('div');
    message.id = 'game-message';
    message.style.display = 'none';
    message.style.textAlign = 'center';
    message.style.fontSize = '1.5em';
    message.style.marginTop = '20px';
    message.textContent = 'Поздравляем! Вы собрали пазл!';
    return message;
}