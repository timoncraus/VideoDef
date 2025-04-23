import { getPuzzleParts, placePieces, createPuzzle } from './puzzle-logic.js';

export const puzzleParams = {
    onWhiteboard: false,
}
window.createPuzzleSeparately = createPuzzleSeparately;


export function createPuzzleOnBoard(gameWrapper) {
    const [puzzleParams, puzzleContainer, message] = getPuzzleParts();
    createPuzzle(puzzleContainer, puzzleParams, message);
    puzzleContainer.querySelectorAll('.puzzle-piece').forEach(piece => {
        piece.style.backgroundImage = `url("${puzzleParams.selectedImage}")`;
    });
    gameWrapper.appendChild(puzzleContainer);
    gameWrapper.appendChild(message);
}

function createPuzzleSeparately() {
    const [puzzleParams, puzzleContainer, message] = getPuzzleParts();
    document.body.appendChild(puzzleContainer);
    document.body.appendChild(message);

    const modal = document.getElementById('start-modal');
    const startBtn = document.getElementById('start-game');
    startBtn.addEventListener('click', () => {
        if (!puzzleParams.selectedImage) {
            alert("Пожалуйста, выберите или загрузите изображение.");
            return;
        }

        document.querySelectorAll('.puzzle-piece').forEach(piece => {
            piece.style.backgroundImage = `url("${puzzleParams.selectedImage}")`;
        });
        placePieces(puzzleContainer, puzzleParams);
        modal.style.display = 'none';
    });

    const customInput = document.getElementById('custom-image');
    customInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                puzzleParams.selectedImage = reader.result;
            };
            reader.readAsDataURL(file);
        }
    });

    const presets = document.querySelectorAll('.preset');
    presets.forEach(preset => {
        preset.addEventListener('click', () => {
            presets.forEach(p => p.classList.remove('selected'));
            preset.classList.add('selected');
            puzzleParams.selectedImage = preset.dataset.src;
        });
    });

    createPuzzle(puzzleContainer, puzzleParams, message);

    const difficultySelect = document.getElementById('difficulty');
    difficultySelect.addEventListener('change', (e) => {
        puzzleParams.gridSize = parseInt(e.target.value, 10);
        createPuzzle(puzzleContainer, puzzleParams, message);
    });
}