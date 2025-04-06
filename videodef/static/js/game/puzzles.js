document.addEventListener('DOMContentLoaded', () => {
    const container = document.querySelector('.puzzle-container');
    const pieces = Array.from(document.querySelectorAll('.puzzle-piece'));
    const message = document.getElementById('game-message');

    // Сетка 3x3
    const gridPositions = [
        [0, 0], [100, 0], [200, 0],
        [0, 100], [100, 100], [200, 100],
        [0, 200], [100, 200], [200, 200],
    ];

    // Случайная расстановка индексов
    let piecePositions = shuffle([...Array(9).keys()]);  // [0...8]

    function placePieces() {
        pieces.forEach((piece, idx) => {
            const [x, y] = gridPositions[piecePositions[idx]];
            piece.style.left = `${x}px`;
            piece.style.top = `${y}px`;
        });
    }

    // Перестановка по клику (двойной клик)
    let selectedPiece = null;

    pieces.forEach(piece => {
        piece.addEventListener('click', () => {
            if (!selectedPiece) {
                selectedPiece = piece;
                piece.style.outline = '2px solid red';
            } else if (selectedPiece === piece) {
                selectedPiece.style.outline = '';
                selectedPiece = null;
            } else {
                // Обмен позиций
                swapPieces(selectedPiece, piece);
                selectedPiece.style.outline = '';
                selectedPiece = null;
                checkVictory();
            }
        });
    });

    function swapPieces(p1, p2) {
        const i1 = pieces.indexOf(p1);
        const i2 = pieces.indexOf(p2);
        [piecePositions[i1], piecePositions[i2]] = [piecePositions[i2], piecePositions[i1]];
        placePieces();
    }

    function checkVictory() {
        const isVictory = piecePositions.every((val, idx) => val === idx);
        if (isVictory) {
            message.style.display = 'block';
        }
    }

    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    placePieces();
});
