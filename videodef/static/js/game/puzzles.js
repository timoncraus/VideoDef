document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('start-modal');
    const startBtn = document.getElementById('start-game');
    const customInput = document.getElementById('custom-image');
    const presets = document.querySelectorAll('.preset');
    const pieces = Array.from(document.querySelectorAll('.puzzle-piece'));
    const message = document.getElementById('game-message');
    const gridPositions = [
        [0, 0], [100, 0], [200, 0],
        [0, 100], [100, 100], [200, 100],
        [0, 200], [100, 200], [200, 200],
    ];
    let piecePositions = shuffle([...Array(9).keys()]);
    let selectedImage = '';

    function placePieces() {
        pieces.forEach((piece, idx) => {
            const [x, y] = gridPositions[piecePositions[idx]];
            piece.style.left = `${x}px`;
            piece.style.top = `${y}px`;
        });
    }

    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    let selectedPiece = null;

    pieces.forEach(piece => {
        piece.addEventListener('click', () => {
            if (!selectedPiece) {
                selectedPiece = piece;
                piece.style.outline = '2px solid red';
            } else if (selectedPiece === piece) {
                piece.style.outline = '';
                selectedPiece = null;
            } else {
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

    // Обработка выбора изображения
    presets.forEach(preset => {
        preset.addEventListener('click', () => {
            presets.forEach(p => p.classList.remove('selected'));
            preset.classList.add('selected');
            selectedImage = preset.dataset.src;
        });
    });

    customInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                selectedImage = reader.result;
            };
            reader.readAsDataURL(file);
        }
    });

    startBtn.addEventListener('click', () => {
        if (!selectedImage) {
            alert("Пожалуйста, выберите или загрузите изображение.");
            return;
        }

        pieces.forEach(piece => {
            piece.style.backgroundImage = `url("${selectedImage}")`;
        });

        modal.style.display = 'none';
        placePieces();
    });
});
