document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('start-modal');
    const startBtn = document.getElementById('start-game');
    const customInput = document.getElementById('custom-image');
    const presets = document.querySelectorAll('.preset');
    const piecesContainer = document.querySelector('.puzzle-container');
    const message = document.getElementById('game-message');
    const difficultySelect = document.getElementById('difficulty');
    
    let gridSize = 3; // По умолчанию 3x3
    let piecePositions = [];
    let selectedImage = '';
    
    // Функция для создания пазла
    function createPuzzle() {
        piecesContainer.innerHTML = ''; // Очистим контейнер от старых пазлов
        piecePositions = shuffle([...Array(gridSize * gridSize).keys()]);

        const gridPositions = [];
        for (let row = 0; row < gridSize; row++) {
            for (let col = 0; col < gridSize; col++) {
                gridPositions.push([col * (300 / gridSize), row * (300 / gridSize)]);
            }
        }

        // Создание новых пазлов
        for (let i = 0; i < gridSize * gridSize; i++) {
            const piece = document.createElement('div');
            piece.classList.add('puzzle-piece');
            piece.id = `piece-${i + 1}`;
            piece.setAttribute('data-index', i);
            piece.style.width = `${300 / gridSize}px`;
            piece.style.height = `${300 / gridSize}px`;
            piece.style.backgroundSize = `${300}px ${300}px`; // Размер фона зависит от общего размера

            // Добавляем обработчик событий для кликов на кусочках
            piece.addEventListener('click', () => handlePieceClick(piece));

            piecesContainer.appendChild(piece);
        }

        placePieces(); // Разместить кусочки
    }

    // Размещение кусочков
    function placePieces() {
        const pieces = document.querySelectorAll('.puzzle-piece');
        const gridPositions = [];
        for (let row = 0; row < gridSize; row++) {
            for (let col = 0; col < gridSize; col++) {
                gridPositions.push([col * (300 / gridSize), row * (300 / gridSize)]);
            }
        }

        pieces.forEach((piece, idx) => {
            const [x, y] = gridPositions[piecePositions[idx]];
            piece.style.left = `${x}px`;
            piece.style.top = `${y}px`;

            // Позиционирование фона в зависимости от размера сетки
            const row = Math.floor(idx / gridSize);
            const col = idx % gridSize;
            piece.style.backgroundPosition = `-${col * (300 / gridSize)}px -${row * (300 / gridSize)}px`;
        });
    }

    // Перемешивание элементов
    function shuffle(array) {
        for (let i = array.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    }

    let selectedPiece = null;

    // Обработчик клика по кусочку
    function handlePieceClick(piece) {
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
    }

    // Меняем местами два кусочка
    function swapPieces(p1, p2) {
        const i1 = Array.from(document.querySelectorAll('.puzzle-piece')).indexOf(p1);
        const i2 = Array.from(document.querySelectorAll('.puzzle-piece')).indexOf(p2);
        [piecePositions[i1], piecePositions[i2]] = [piecePositions[i2], piecePositions[i1]];
        placePieces();
    }

    // Проверка на победу
    function checkVictory() {
        const isVictory = piecePositions.every((val, idx) => val === idx);
        if (isVictory) {
            message.style.display = 'block';
        }
    }

    // Обработчик выбора изображения
    presets.forEach(preset => {
        preset.addEventListener('click', () => {
            presets.forEach(p => p.classList.remove('selected'));
            preset.classList.add('selected');
            selectedImage = preset.dataset.src;
        });
    });

    // Обработчик выбора файла
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

    // Обработчик изменения сложности
    difficultySelect.addEventListener('change', (e) => {
        gridSize = parseInt(e.target.value, 10);
        createPuzzle(); // Пересоздаем пазл с новым размером
    });

    // Обработчик начала игры
    startBtn.addEventListener('click', () => {
        if (!selectedImage) {
            alert("Пожалуйста, выберите или загрузите изображение.");
            return;
        }

        document.querySelectorAll('.puzzle-piece').forEach(piece => {
            piece.style.backgroundImage = `url("${selectedImage}")`;
        });

        modal.style.display = 'none';
        placePieces();
    });

    createPuzzle(); // Инициализация игры с дефолтными настройками
});
