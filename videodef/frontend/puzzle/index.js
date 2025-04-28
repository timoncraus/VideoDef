import { getPuzzleParts, placePieces, createPuzzle } from './puzzle-logic.js';

export const puzzleParams = {
    onWhiteboard: false, // Флаг для проверки: создан ли пазл на доске
}
window.createPuzzleSeparately = createPuzzleSeparately;

/**
 * Назначает обработчики для пользовательского изображения, пресетов и сложности
 * @param {Object} options
 * @param {HTMLInputElement} options.customInput - Элемент загрузки изображения
 * @param {NodeList} options.presets - Коллекция элементов пресетов
 * @param {HTMLSelectElement} options.difficultySelect - Выпадающий список сложности
 * @param {HTMLButtonElement} startBtn - Кнопка "Начать игру"
 * @param {Object} options.puzzleParams - Параметры пазла
 * @param {HTMLElement} [options.puzzleContainer] - Контейнер пазла (опционально для моментального обновления фона)
 * @param {HTMLElement} [options.message] - Сообщение о состоянии (опционально для пересоздания пазла)
 * @param {boolean} [options.instantUpdate] - Нужно ли сразу обновлять пазл (по умолчанию true)
 */
function setupPuzzleControls({ customInput, presets, difficultySelect, startBtn, puzzleParams, puzzleContainer, message, instantUpdate = true }) {
    // Обработчик загрузки пользовательского изображения
    customInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                puzzleParams.selectedImage = reader.result;
                if (instantUpdate && puzzleContainer) {
                    updatePuzzleImage(puzzleContainer, puzzleParams);
                }
            };
            reader.readAsDataURL(file);
        }
    });

    // Обработчики выбора пресетных изображений
    presets.forEach(preset => {
        preset.addEventListener('click', () => {
            presets.forEach(p => p.classList.remove('selected'));
            preset.classList.add('selected');
            puzzleParams.selectedImage = preset.dataset.src;
            if (instantUpdate && puzzleContainer) {
                updatePuzzleImage(puzzleContainer, puzzleParams);
            }
        });
    });

    // Обработчик для изменения сложности (размерность сетки)
    difficultySelect.addEventListener('change', (e) => {
        puzzleParams.gridSize = parseInt(e.target.value, 10);
        if (instantUpdate && puzzleContainer && message) {
            createPuzzle(puzzleContainer, puzzleParams, message);
        }
    });

    // Обработчик начала игры
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            if (!puzzleParams.selectedImage) {
                alert("Пожалуйста, выберите или загрузите изображение.");
                return;
            }

            createPuzzle(puzzleContainer, puzzleParams, message);

            puzzleContainer.querySelectorAll('.puzzle-piece').forEach(piece => {
                piece.style.backgroundImage = `url("${puzzleParams.selectedImage}")`;
            });

            placePieces(puzzleContainer, puzzleParams);

            if (message) {
                message.style.display = 'none';
            }
        });
    }
}

/**
 * Создает интерактивный пазл внутри игрового контейнера на доске
 * @param {HTMLElement} gameWrapper - Родительский контейнер для пазла
 */
export function createPuzzleOnBoard(gameWrapper) {
    // Получаем компоненты пазла: параметры, контейнер и сообщение
    const [puzzleParams, puzzleContainer, message] = getPuzzleParts();
    
    // Получаем элементы управления из панели настроек на доске
    const customInput = document.getElementById('custom-image'); // Элемент для загрузки изображения
    const difficultySelect = document.getElementById('difficulty'); // Выпадающий список сложности
    const presets = document.querySelectorAll('.preset'); // Пресеты изображений
    const startBtn = document.getElementById('start-game') // Кнопка "Начать игру"

    // Назначаем обработчики
    setupPuzzleControls({ 
        customInput, 
        presets, 
        difficultySelect,
        startBtn, 
        puzzleParams, 
        puzzleContainer, 
        message,
        instantUpdate: true
    });

    createPuzzle(puzzleContainer, puzzleParams, message);

    // Устанавливаем начальное изображение для пазла
    updatePuzzleImage(puzzleContainer, puzzleParams);

    // Добавляем элементы на доску
    gameWrapper.appendChild(puzzleContainer);
    gameWrapper.appendChild(message);
}

/**
 * Обновляет фоновое изображение для всех элементов пазла
 * @param {HTMLElement} puzzleContainer - Контейнер с элементами пазла
 * @param {Object} puzzleParams - Параметры пазла
 */
function updatePuzzleImage(puzzleContainer, puzzleParams) {
    puzzleContainer.querySelectorAll('.puzzle-piece').forEach(piece => {
        piece.style.backgroundImage = `url("${puzzleParams.selectedImage}")`;
    });
    placePieces(puzzleContainer, puzzleParams);
}

/**
 * Создает независимый пазл вне основной доски
 */
function createPuzzleSeparately() {
    const [puzzleParams, puzzleContainer, message] = getPuzzleParts();
    // Создание основного контейнера для пазла
    const wrapper = document.getElementById('puzzle-wrapper');
    wrapper.appendChild(puzzleContainer);
    wrapper.appendChild(message);

    const customInput = document.getElementById('custom-image');
    const difficultySelect = document.getElementById('difficulty');
    const presets = document.querySelectorAll('.preset');
    const startBtn = document.getElementById('start-game');

    setupPuzzleControls({
        customInput,
        presets,
        difficultySelect,
        startBtn,
        puzzleParams,
        puzzleContainer,
        message,
        instantUpdate: false
    });

}