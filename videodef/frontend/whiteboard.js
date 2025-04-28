import { createPuzzleOnBoard, puzzleParams } from './puzzle/index.js';

// Активация режима работы на интерактивной доске
puzzleParams.onWhiteboard = true;

// Получение ссылок на элементы canvas
const imageCanvas = document.getElementById('image-layer');
const drawCanvas = document.getElementById('draw-layer');

// Контексты рисования
const imageCtx = imageCanvas.getContext('2d');
const drawCtx = drawCanvas.getContext('2d');

// Состояние приложения
let drawing = false; // Флаг процесса рисования
let prev = {}; // Предыдущие координаты курсора
let imagesList = []; // Список загруженных изображений
let activeImage = null; // Активное изображение для перемещения
let dragOffset = { x: 0, y: 0 }; // Смещение при перетаскивании
let isResizing = false; // Флаг изменения размера
let isDragging = false; // Флаг перетаскивания
let currentTool = 'pen'; // Текущий инструмент
let currentLineWidth = 2; // Толщина линии
let currentColor = '#000000'; // Цвет по умолчанию

// Инициализация WebSocket соединения
const ws = new WebSocket(`ws://${window.location.host}/ws/whiteboard/`);

// Обработчик входящих сообщений
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);

    // Обработка рисования
    if (data.type === "draw") {
        const { x0, y0, x1, y1, color, lineWidth } = data;
        drawLine(drawCtx, x0, y0, x1, y1, color, lineWidth);
    }

    // Обработка загрузки изображений
    if (data.type === 'image') {
        const img = new Image();
        img.onload = () => {
            const imageObj = {
                img,
                x: 50,
                y: 50,
                width: 200,
                height: 200
            };
            imagesList.push(imageObj);
            redrawImages();
        };
        img.src = data.dataURL;
    }

    // Обработка очистки доски
    if (data.type === 'clear') {
        drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        imagesList = [];
    }
};

// Инициализация инструментов
document.getElementById('pen_btn').addEventListener('click', () => {
    currentTool = 'pen';
    toggleToolButtons('pen_btn');
});
document.getElementById('eraser_btn').addEventListener('click', () => {
    currentTool = 'eraser';
    toggleToolButtons('eraser_btn');
});

// Обработчики параметров рисования
document.getElementById('colorPicker').addEventListener('input', (e) => {
    currentColor = e.target.value;
});
document.getElementById('thickness').addEventListener('input', (e) => {
    currentLineWidth = parseInt(e.target.value);
});

/**
 * Управляет визуальной активностью кнопок инструментов.
 * Убирает класс 'active' со всех кнопок и добавляет его выбранной кнопке.
 * @param {string} activeId - ID активной кнопки инструмента
 */
function toggleToolButtons(activeId) {
    document.querySelectorAll('.tool').forEach(btn => btn.classList.remove('active'));
    document.getElementById(activeId).classList.add('active');
}

// Обработчики событий мыши
drawCanvas.addEventListener('mousedown', (e) => {
    const { offsetX: x, offsetY: y } = e;
    activeImage = getImageAt(x, y);
    if (activeImage) {
        if (overResizeHandle(x, y, activeImage)) {
            isResizing = true;
        } else {
            isDragging = true;
            dragOffset.x = x - activeImage.x;
            dragOffset.y = y - activeImage.y;
        }
    } else {
        drawing = true;
        prev = { x, y };
    }
});

drawCanvas.addEventListener('mouseup', () => {
    drawing = false;
    isDragging = false;
    isResizing = false;
    activeImage = null;
});

drawCanvas.addEventListener('mousemove', (e) => {
    const { offsetX: x, offsetY: y } = e;

    if (drawing && !someonesDragging) {
        const current = { x, y };
        const color = currentTool === 'pen' ? currentColor : '#ffffff';
        const message = {
            type: 'draw',
            x0: prev.x,
            y0: prev.y,
            x1: current.x,
            y1: current.y,
            color,
            lineWidth: currentLineWidth
        };
        ws.send(JSON.stringify(message));

        drawLine(drawCtx, prev.x, prev.y, current.x, current.y, color, currentLineWidth);
        prev = current;
    } else if (isDragging && activeImage) {
        activeImage.x = x - dragOffset.x;
        activeImage.y = y - dragOffset.y;
        redrawImages();
    } else if (isResizing && activeImage) {
        activeImage.width = x - activeImage.x;
        activeImage.height = y - activeImage.y;
        redrawImages();
    }
});


/**
 * Рисует линию на заданном контексте.
 * @param {CanvasRenderingContext2D} ctx - Контекст рисования
 * @param {number} x0 - Начальная координата X
 * @param {number} y0 - Начальная координата Y
 * @param {number} x1 - Конечная координата X
 * @param {number} y1 - Конечная координата Y
 * @param {string} color - Цвет линии
 * @param {number} lineWidth - Толщина линии
 */
function drawLine(ctx, x0, y0, x1, y1, color, lineWidth) {
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
}

// Загрузка пользовательских изображений
document.getElementById('img-upload').addEventListener('change', function() {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        const dataURL = reader.result;
        ws.send(JSON.stringify({ type: 'image', dataURL }));
    };
    reader.readAsDataURL(file);
});

/**
 * Очищает доску и сбрасывает загруженные изображения.
 */
function clearBoard() {
    ws.send(JSON.stringify({ type: 'clear' }));
    document.getElementById('img-upload').value = '';
}

document.querySelector("#clear_btn").addEventListener("click", () => {
    clearBoard();
});

/**
 * Перерисовывает все изображения на слое изображений и отображает маркеры изменения размера.
 */
function redrawImages() {
    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
    imagesList.forEach(imgObj => {
        imageCtx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height);
        drawResizeHandle(imageCtx, imgObj);
    });
}

// Вспомогательные функции
function getImageAt(x, y) {
    for (let i = imagesList.length - 1; i >= 0; i--) {
        const img = imagesList[i];
        if (x >= img.x && x <= img.x + img.width &&
            y >= img.y && y <= img.y + img.height) {
            return img;
        }
    }
    return null;
}

function drawResizeHandle(ctx, imgObj) {
    const size = 10;
    ctx.fillStyle = '#00f';
    ctx.fillRect(imgObj.x + imgObj.width - size, imgObj.y + imgObj.height - size, size, size);
}

function overResizeHandle(x, y, imgObj) {
    const size = 10;
    return x >= imgObj.x + imgObj.width - size &&
        x <= imgObj.x + imgObj.width &&
        y >= imgObj.y + imgObj.height - size &&
        y <= imgObj.y + imgObj.height;
}

/**
 * Адаптирует размер холста (canvas) под размеры родительского контейнера.
 */
function resizeCanvasToDisplaySize() {
    const wrapper = imageCanvas.parentElement;
    const width = wrapper.clientWidth;
    const height = wrapper.clientHeight;

    imageCanvas.width = width;
    imageCanvas.height = height;
    drawCanvas.width = width;
    drawCanvas.height = height;

    redrawImages();
}

window.addEventListener('load', resizeCanvasToDisplaySize);
window.addEventListener('resize', resizeCanvasToDisplaySize);


// Инициализация меню игр
const dropdown = document.getElementById("game-menu");
const gamesBtn = document.getElementById("games_btn");
const gameMenu = document.getElementById("game-menu");

gamesBtn.addEventListener("click", () => {
    updategameMenuPos();
    dropdown.classList.toggle("show");
});

window.addEventListener("resize", () => {
    updategameMenuPos();
})

/**
 * Обновляет позицию выпадающего меню игр относительно кнопки.
 */
function updategameMenuPos() {
    const rect = gamesBtn.getBoundingClientRect();
    gameMenu.style.top = `${rect.bottom + window.scrollY}px`;
    gameMenu.style.left = `${rect.left + window.scrollX}px`;
}

window.addEventListener("click", (e) => {
    if (!gamesBtn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
    }
});

document.querySelectorAll(".game-option").forEach(option => {
    option.addEventListener("click", () => {
        const gameName = option.dataset.name;
        const gameWrapper = addGamePasteGame();
        gameWrapper.dataset.gameName = gameName;

        updateGameSettings(gameName);

        if (gameName === "puzzles") {
            createPuzzleOnBoard(gameWrapper);
        }
        dropdown.classList.remove("show");

    });
});

/**
 * Создает и добавляет контейнер для вставляемой игры на доску.
 * @returns {HTMLDivElement} gameWrapper - созданный контейнер игры
 */
function addGamePasteGame() {
    const gameWrapper = document.createElement('div');
    gameWrapper.className = 'paste-game-wrapper';
    gameWrapper.style.left = '100px';
    gameWrapper.style.top = '100px';
    gameWrapper.style.width = '400px';
    gameWrapper.style.height = '300px';
    gameWrapper.style.aspectRatio = '4 / 3';

    const closeBtn = document.createElement('button');
    closeBtn.className = 'paste-game-close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => {
        clearDynamicSettings()
        gameWrapper.remove()
    };

    gameWrapper.appendChild(closeBtn);
    document.querySelector('.canvas-wrapper').appendChild(gameWrapper);
    makeDraggable(gameWrapper);
    makeResizable(gameWrapper);

    gameWrapper.addEventListener('click', (e) => {
        if (!e.target.closest('.paste-game-close') && !e.target.classList.contains('resize-handle')) {
            const gameName = gameWrapper.dataset.gameName;
    
            // Сбрасываем флаг для всех остальных gameWrapper
            document.querySelectorAll('.paste-game-wrapper').forEach(wrapper => {
                if (wrapper !== gameWrapper) {
                    wrapper.dataset.settingsUpdated = 'false';  // Сбрасываем флаг для других игр
                }
            });
    
            // Проверка, был ли уже обновлен набор настроек для этой игры
            if (gameName && gameWrapper.dataset.settingsUpdated !== 'true') {
                updateGameSettings(gameName);
                gameWrapper.dataset.settingsUpdated = 'true';  // Устанавливаем флаг, что настройки обновлены
            }
    
            document.querySelectorAll('.paste-game-wrapper').forEach(wrapper => {
                wrapper.classList.remove('active-game');
            });
    
            gameWrapper.classList.add('active-game');
        }
    });

    return gameWrapper;
}

let someonesDragging = false;

/**
 * Делает контейнер игры перетаскиваемым.
 * @param {HTMLDivElement} gameWrapper - Контейнер игры
 */
function makeDraggable(gameWrapper) {
    gameWrapper.isDragging = false;
    gameWrapper.offsetX = 0;
    gameWrapper.offsetY = 0;

    gameWrapper.addEventListener('mousedown', (e) => {
        if (e.target.closest('.paste-game-close')) return;

        gameWrapper.isDragging = true;
        someonesDragging = true;

        const rect = gameWrapper.getBoundingClientRect();
        const { x: x, y: y } = e;
        console.log(rect.left, rect.top)
        gameWrapper.offsetX = x - rect.left;
        gameWrapper.offsetY = y - rect.top;

        gameWrapper.style.zIndex = 999;
        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!gameWrapper.isDragging) return;

        gameWrapper.style.left = `${e.clientX - gameWrapper.offsetX - 100}px`;
        gameWrapper.style.top = `${e.clientY - gameWrapper.offsetY - 180}px`;
    });

    document.addEventListener('mouseup', () => {
        if (gameWrapper.isDragging) {
            gameWrapper.isDragging = false;
            someonesDragging = false;
            document.body.style.userSelect = '';
        }
    });
}

/**
 * Делает контейнер игры изменяемым по размеру.
 * @param {HTMLDivElement} gameWrapper - Контейнер игры
 */
function makeResizable(gameWrapper) {
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    gameWrapper.appendChild(resizeHandle);

    gameWrapper.isResizing = false;
    let startX, startY, startWidth, startHeight;

    resizeHandle.addEventListener('mousedown', (e) => {
        e.stopPropagation(); // чтобы drag и resize не конфликтовали
        gameWrapper.isResizing = true;
        someonesDragging = true;

        const rect = gameWrapper.getBoundingClientRect();
        startX = e.clientX;
        startY = e.clientY;
        startWidth = rect.width;
        startHeight = rect.height;

        document.body.style.userSelect = 'none';
    });

    document.addEventListener('mousemove', (e) => {
        if (!gameWrapper.isResizing) return;

        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        const newWidth = Math.max(400, startWidth + dx);
        const newHeight = Math.max(300, startHeight + dy);

        gameWrapper.style.width = `${newWidth}px`;
        gameWrapper.style.height = `${newHeight}px`;
    });

    document.addEventListener('mouseup', () => {
        if (gameWrapper.isResizing) {
            gameWrapper.isResizing = false;
            someonesDragging = false;
            document.body.style.userSelect = '';
        }
    });
}

// Панель настроек
const toggleButton = document.getElementById('toggle-settings-btn');
const settingsPanel = document.querySelector('.settings-panel');

// Открытие/Скрытие настроек
toggleButton.addEventListener('click', () => {
    settingsPanel.classList.toggle('hidden');
    
    if (settingsPanel.classList.contains('hidden')) {
        toggleButton.textContent = 'Открыть настройки';
    } else {
        toggleButton.textContent = 'Закрыть настройки';
    }
});

/**
 * Удаляет все динамически созданные элементы настроек игр.
 */
function clearDynamicSettings() {
    const dynamicElements = settingsPanel.querySelectorAll('.dynamic-setting');
    dynamicElements.forEach(el => el.remove());
}

/**
 * Обновляет панель настроек в зависимости от выбранной игры.
 * @param {string} gameName - Название выбранной игры
 */
function updateGameSettings(gameName) {
    clearDynamicSettings();

    if (gameName === "puzzles") {
        // Очищаем существующие настройки для пазлов, если они были добавлены ранее
        const existingSettings = document.querySelector('.puzzle-settings-container');
        if (existingSettings) {
            existingSettings.remove();
        }

        const settingsContainer = document.createElement('div');
        settingsContainer.className = "dynamic-setting puzzle-settings-container"; // Контейнер для настроек пазлов

        // Содержимое для выбора изображения и сложности
        const content = `
            <div class="modal-content">
                <h2>Выберите изображение для пазла</h2>

                <div class="preset-images">
                    <img src="${images}/puzzle_test.png" class="preset" data-src="${images}/puzzle_test.png">
                    <img src="${images}/masha-i-medvedi.png" class="preset" data-src="${images}/masha-i-medvedi.png">
                </div>

                <label class="upload-label">
                    Загрузить своё:
                    <input type="file" id="custom-image" accept="image/*">
                </label>

                <label for="difficulty">Выберите сложность:</label>
                <select id="difficulty">
                    <option value="2" selected>2x2</option>
                    <option value="3">3x3</option>
                    <option value="4">4x4</option>
                </select>

                <button id="start-game">Начать игру</button>
            </div>
        `;

        // Вставляем содержимое в контейнер
        settingsContainer.innerHTML = content;

        // Добавляем в панель настроек
        settingsPanel.appendChild(settingsContainer);
    }

    else if (gameName === "another-game") {
    }
}