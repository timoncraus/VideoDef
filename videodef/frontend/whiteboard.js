import { createPuzzleOnBoard, setupWhiteboardPuzzleSaveLoad } from './puzzle/index.js';

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
let activeImage = null; // Активное изображение для перемещения/удаления
let nextImageId = 0;    // Счетчик для уникальных ID изображений
let dragOffset = { x: 0, y: 0 }; // Смещение при перетаскивании
let isResizing = false; // Флаг изменения размера
let isDragging = false; // Флаг перетаскивания
let currentTool = 'pen'; // Текущий инструмент
let currentLineWidth = 2; // Толщина линии
let currentColor = '#000000'; // Цвет по умолчанию

// Инициализация WebSocket соединения
const ws = new WebSocket(`ws://${window.location.host}/ws/whiteboard/`);

// Функция для получения координат мыши на канвасе
function getMousePos(canvas, evt) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}

// Обработчик входящих сообщений
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.type === "draw") {
        const { x0, y0, x1, y1, color, lineWidth, tool} = data;
        drawLine(drawCtx, x0, y0, x1, y1, color, lineWidth, tool);
    } else if (data.type === 'image') {
        const img = new Image();
        img.onload = () => {
            // Если в data есть id, используем его (пришло от другого клиента),
            // иначе генерируем новый (это локальная загрузка)
            const imageId = data.id !== undefined ? data.id : nextImageId++;
            const imageObj = {
                id: imageId,
                img,
                x: data.x !== undefined ? data.x : 50,
                y: data.y !== undefined ? data.y : 50,
                width: data.width !== undefined ? data.width : 200,
                height: data.height !== undefined ? data.height : 200,
                dataURL: data.dataURL
            };
            // Предотвращаем дублирование, если сообщение пришло о уже существующем изображении
            if (!imagesList.find(item => item.id === imageObj.id)) {
                imagesList.push(imageObj);
            } else {
                // Если изображение уже есть, обновляем его (на случай, если это было изменение)
                const existingImgIndex = imagesList.findIndex(item => item.id === imageObj.id);
                if (existingImgIndex !== -1) {
                    imagesList[existingImgIndex] = {...imagesList[existingImgIndex], ...imageObj};
                }
            }
            redrawImages();
        };
        img.src = data.dataURL;
    } else if (data.type === 'clear') {
        drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        imagesList = [];
        activeImage = null;
        nextImageId = 0;
    } else if (data.type === 'delete_image') {
        imagesList = imagesList.filter(imgObj => imgObj.id !== data.id);
        if (activeImage && activeImage.id === data.id) {
            activeImage = null;
        }
        redrawImages();
    } else if (data.type === 'move_image' || data.type === 'resize_image') {
        const imgIndex = imagesList.findIndex(img => img.id === data.id);
        if (imgIndex !== -1) {
            imagesList[imgIndex].x = data.x;
            imagesList[imgIndex].y = data.y;
            if (data.type === 'resize_image') {
                imagesList[imgIndex].width = data.width;
                imagesList[imgIndex].height = data.height;
            }
            redrawImages();
        } else if (data.dataURL) { // Если изображение еще не загружено у этого клиента
            const img = new Image();
            img.onload = () => {
                 const imageObj = {
                    id: data.id,
                    img,
                    x: data.x,
                    y: data.y,
                    width: data.width,
                    height: data.height,
                    dataURL: data.dataURL
                };
                imagesList.push(imageObj);
                redrawImages();
            };
            img.src = data.dataURL;
        }
    }
};

// Инициализация инструментов
document.getElementById('pen_btn').addEventListener('click', () => {
    currentTool = 'pen';
    toggleToolButtons('pen_btn');
    drawCanvas.style.cursor = 'crosshair';
    clearSelection();
});
document.getElementById('eraser_btn').addEventListener('click', () => {
    currentTool = 'eraser';
    toggleToolButtons('eraser_btn');
    drawCanvas.style.cursor = 'crosshair';
    clearSelection();
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
    const { x, y } = getMousePos(drawCanvas, e);

    const clickedImage = getImageAt(x, y);

    if (clickedImage) {
        activeImage = clickedImage; // Делаем изображение активным
        redrawImages();

        if (overResizeHandle(x, y, activeImage)) {
            isResizing = true;
            dragOffset.startX = activeImage.x;
            dragOffset.startY = activeImage.y;
            dragOffset.startWidth = activeImage.width;
            dragOffset.startHeight = activeImage.height;
        } else {
            isDragging = true;
            dragOffset.x = x - activeImage.x;
            dragOffset.y = y - activeImage.y;
        }
        drawCanvas.style.cursor = 'move';
    } else {
        if (currentTool === 'pen' || currentTool === 'eraser') {
            drawing = true;
            prev = { x, y };
            clearSelection();
            drawCanvas.style.cursor = 'crosshair';
        } else {
            clearSelection();
        }
    }
});

drawCanvas.addEventListener('mouseup', () => {
    if (drawing) {
        drawing = false;
        if (currentTool === 'eraser') {
            drawCtx.globalCompositeOperation = 'source-over';
        }
    }
    if (isDragging && activeImage) {
        // Отправляем финальное состояние перемещенного изображения
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'move_image',
                id: activeImage.id,
                x: activeImage.x,
                y: activeImage.y,
                // Передаем dataURL на случай, если у других клиентов этого изображения еще нет
                dataURL: activeImage.dataURL
            }));
        }
        isDragging = false;
    }
    if (isResizing && activeImage) {
        // Отправляем финальное состояние измененного изображения
         if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'resize_image',
                id: activeImage.id,
                x: activeImage.x,
                y: activeImage.y,
                width: activeImage.width,
                height: activeImage.height,
                dataURL: activeImage.dataURL
            }));
        }
        isResizing = false;
    }
});

drawCanvas.addEventListener('mousemove', (e) => {
    const { x, y } = getMousePos(drawCanvas, e);

    if (drawing && !someonesDragging) {
        const current = { x, y };
        const colorForDraw = currentTool === 'pen' ? currentColor : '#000000';

        const message = {
            type: 'draw',
            x0: prev.x,
            y0: prev.y,
            x1: current.x,
            y1: current.y,
            color: colorForDraw,
            lineWidth: currentLineWidth,
            tool: currentTool
        };
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
        }

        drawLine(drawCtx, prev.x, prev.y, current.x, current.y, colorForDraw, currentLineWidth, currentTool);
        prev = current;
        drawCanvas.style.cursor = 'crosshair';
    } else if (isDragging && activeImage && !someonesDragging) {
        activeImage.x = x - dragOffset.x;
        activeImage.y = y - dragOffset.y;
        redrawImages();
        drawCanvas.style.cursor = 'grabbing';
    } else if (isResizing && activeImage && !someonesDragging) {
        const newWidth = Math.abs(x - dragOffset.startX);
        const newHeight = Math.abs(y - dragOffset.startY);

        activeImage.width = Math.max(20, newWidth); // Мин. ширина
        activeImage.height = Math.max(20, newHeight); // Мин. высота

        if (x < dragOffset.startX) {
            activeImage.x = x;
        } else {
            activeImage.x = dragOffset.startX;
        }
        if (y < dragOffset.startY) {
            activeImage.y = y;
        } else {
            activeImage.y = dragOffset.startY;
        }

        redrawImages();
        drawCanvas.style.cursor = 'nwse-resize';
    } else if (!drawing && !isDragging && !isResizing) {
        // Управление курсором при наведении на изображения или маркеры
        const hoveredImage = getImageAt(x, y);
        if (hoveredImage) {
            if (overResizeHandle(x, y, hoveredImage)) {
                drawCanvas.style.cursor = 'nwse-resize';
            } else {
                drawCanvas.style.cursor = 'move';
            }
        } else {
            drawCanvas.style.cursor = (currentTool === 'pen' || currentTool === 'eraser') ? 'crosshair' : 'default';
        }
    }
});

// Обработчик нажатия клавиш для удаления
window.addEventListener('keydown', (e) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (activeImage && !isInputActive()) {
            e.preventDefault();
            deleteImage(activeImage.id);
        }
    }
});

// Проверка: активно ли поле ввода
function isInputActive() {
    const activeEl = document.activeElement;
    return activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable);
}

// Удаления изображения
function deleteImage(imageId) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'delete_image', id: imageId }));
    }
    imagesList = imagesList.filter(imgObj => imgObj.id !== imageId);
    if (activeImage && activeImage.id === imageId) {
        activeImage = null;
    }
    redrawImages();
}

// Снятие выделения с изображения
function clearSelection() {
    if (activeImage) {
        activeImage = null;
        redrawImages();
    }
}

/**
 * Рисует линию на заданном контексте.
 * @param {CanvasRenderingContext2D} ctx - Контекст рисования
 * @param {number} x0 - Начальная координата X
 * @param {number} y0 - Начальная координата Y
 * @param {number} x1 - Конечная координата X
 * @param {number} y1 - Конечная координата Y
 * @param {string} color - Цвет линии
 * @param {number} lineWidth - Толщина линии
 * @param {string} tool - Текущий инструмент ('pen' или 'eraser')
 */
function drawLine(ctx, x0, y0, x1, y1, color, lineWidth, tool = 'pen') {
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    if (tool === 'eraser') {
        ctx.globalCompositeOperation = 'destination-out';
    } else {
        ctx.globalCompositeOperation = 'source-over';
        ctx.strokeStyle = color;
    }
    
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
        const imageId = nextImageId++; // Генерируем ID для нового изображения
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'image',
                id: imageId,
                dataURL,
                x: 50,
                y: 50,
                width: 200,
                height: 200
            }));
        }

        const img = new Image();
        img.onload = () => {
            const imageObj = {
                id: imageId,
                img,
                x: 50,
                y: 50,
                width: 200,
                height: 200,
                dataURL
            };
            imagesList.push(imageObj);
            redrawImages();
        };
        img.src = dataURL;
    };
    reader.readAsDataURL(file);
    this.value = ''; // Сбрасываем input, чтобы можно было загрузить тот же файл снова
});

/**
 * Очищает доску и сбрасывает загруженные изображения.
 */
function clearBoard() {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'clear' }));
    }
    drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
    imagesList = [];
    activeImage = null;
    nextImageId = 0;
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
    const prevOp = imageCtx.globalCompositeOperation;
    imageCtx.globalCompositeOperation = 'source-over';

    imagesList.forEach(imgObj => {
        imageCtx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height);
        
        // Если изображение активно, рисуем рамку выделения и маркеры
        if (activeImage && activeImage.id === imgObj.id) {
            imageCtx.strokeStyle = 'blue';
            imageCtx.lineWidth = 2;
            imageCtx.strokeRect(imgObj.x -1, imgObj.y -1, imgObj.width +2, imgObj.height +2);
            drawResizeHandle(imageCtx, imgObj);
        }
    });
    imageCtx.globalCompositeOperation = prevOp;
}

// Вспомогательные функции
function getImageAt(x, y) {
    // Перебираем в обратном порядке, чтобы выбрать верхнее изображение, если они накладываются
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
    ctx.fillStyle = '#007bff';
    ctx.strokeStyle = 'white';
    ctx.lineWidth = 1;
    ctx.fillRect(imgObj.x + imgObj.width - size / 2, imgObj.y + imgObj.height - size / 2, size, size);
    ctx.strokeRect(imgObj.x + imgObj.width - size / 2, imgObj.y + imgObj.height - size / 2, size, size);
}

function overResizeHandle(x, y, imgObj) {
    const size = 10;
    const handleX = imgObj.x + imgObj.width - size / 2;
    const handleY = imgObj.y + imgObj.height - size / 2;
    return x >= handleX && x <= handleX + size &&
           y >= handleY && y <= handleY + size;
}

/**
 * Адаптирует размер холста (canvas) под размеры родительского контейнера.
 */
function resizeCanvasToDisplaySize() {
    const wrapper = imageCanvas.parentElement;
    if (!wrapper) {
        console.warn("Холст не найден");
        return;
    }
    const width = wrapper.clientWidth;
    const height = wrapper.clientHeight;

    // Сохраняем текущее содержимое drawCanvas
    const tempDrawCanvas = document.createElement('canvas');
    tempDrawCanvas.width = drawCanvas.width;
    tempDrawCanvas.height = drawCanvas.height;
    const tempDrawCtx = tempDrawCanvas.getContext('2d');
    if (drawCanvas.width > 0 && drawCanvas.height > 0) {
        tempDrawCtx.drawImage(drawCanvas, 0, 0);
    }

    imageCanvas.width = width;
    imageCanvas.height = height;
    drawCanvas.width = width;
    drawCanvas.height = height;

    // Восстанавливаем содержимое drawCanvas
    if (tempDrawCanvas.width > 0 && tempDrawCanvas.height > 0) {
         // Убедимся, что настройки рисования (цвет, толщина, compositeOperation) не сбились
        drawCtx.strokeStyle = currentColor;
        drawCtx.lineWidth = currentLineWidth;
        drawCtx.lineCap = 'round';
        drawCtx.lineJoin = 'round';
        if (currentTool === 'eraser') {
            drawCtx.globalCompositeOperation = 'destination-out';
        } else {
            drawCtx.globalCompositeOperation = 'source-over';
        }
        drawCtx.drawImage(tempDrawCanvas, 0, 0);
    }

    redrawImages();
}

window.addEventListener('load', () => {
    resizeCanvasToDisplaySize();
    toggleToolButtons('pen_btn');
});
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
    if (dropdown.classList.contains("show")) {
        updategameMenuPos();
    }
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

// Обработка добавления игры на доску
document.querySelectorAll(".game-option").forEach(option => {
    if (option.dataset.listenerAttached === 'true') {
        return;
    }

    option.addEventListener("click", () => {
        const gameName = option.dataset.name;
        const gameWrapper = addGamePasteGame();
        gameWrapper.dataset.gameName = gameName;

        updateGameSettings(gameName);

        if (gameName === "puzzles") {
            createPuzzleOnBoard(gameWrapper);
        }
        dropdown.classList.remove("show");

        setTimeout(() => {
            if (document.body.contains(gameWrapper)) {
                gameWrapper.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
            }
        }, 0);
    });
    option.dataset.listenerAttached = 'true';
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

    gameWrapper._blockImmediateDrag = true; // блокировка перемещения только что добавленной игры

    const closeBtn = document.createElement('button');
    closeBtn.className = 'paste-game-close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => {
        // Если удаляем активный элемент, очищаем настройки
        if (gameWrapper.classList.contains('active-game')) {
            clearDynamicSettings();
        }
        gameWrapper.remove();
    };

    gameWrapper.appendChild(closeBtn);
    document.querySelector('.canvas-wrapper').appendChild(gameWrapper);
    makeDraggable(gameWrapper);
    makeResizable(gameWrapper);

    // сброс блокировки перемещения только что добавленной игры
    setTimeout(() => {
        if (gameWrapper) { // Проверяем, что элемент все еще существует
           delete gameWrapper._blockImmediateDrag;
        }
    }, 1);

    gameWrapper.addEventListener('mousedown', (e) => {
        // Игнорируем клики на кнопку закрытия и кружок изменения размера
        if (e.target.closest('.paste-game-close') || e.target.classList.contains('resize-handle')) {
            return;
        }

        // Проверяем, стал ли wrapper активным
        if (!gameWrapper.classList.contains('active-game')) {
            const gameName = gameWrapper.dataset.gameName;

            // Снимаем активность и флаг 'settingsUpdated' со всех остальных
            document.querySelectorAll('.paste-game-wrapper.active-game').forEach(activeWrapper => {
                activeWrapper.classList.remove('active-game');
                activeWrapper.dataset.settingsUpdated = 'false';
                activeWrapper.style.borderColor = '';
                 activeWrapper.style.zIndex = '';
            });

            // Делаем текущий активным
            gameWrapper.classList.add('active-game');
            gameWrapper.style.borderColor = 'blue';
            gameWrapper.style.zIndex = '100';

            // Обновляем панель настроек, если нужно
            if (gameName && gameWrapper.dataset.settingsUpdated !== 'true') {
                updateGameSettings(gameName);
                gameWrapper.dataset.settingsUpdated = 'true';

                // Вызываем настройку обработчиков
                if (gameName === "puzzles") {
                    setupWhiteboardPuzzleSaveLoad();
                }
            } else if (!gameName) {
                 clearDynamicSettings();
            }
        } else {
             gameWrapper.style.zIndex = '100';
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
    let startX, startY, initialLeft, initialTop;

    // Обработка начала перетаскивания
    const onMouseDown = (e) => {
        if (gameWrapper._blockImmediateDrag === true) {
            return;
        }

        // Игнорируем клики на кнопку закрытия и маркер изменения размера
        if (e.target.closest('.paste-game-close') || e.target.classList.contains('resize-handle')) {
            return;
        }
        // Игнорируем, если клик не левой кнопкой мыши
        if (e.button !== 0) {
            return;
        }

        gameWrapper.isDragging = true;
        someonesDragging = true;

        // Координаты мыши относительно viewport
        startX = e.clientX;
        startY = e.clientY;

        // Текущие координаты элемента
        initialLeft = parseFloat(gameWrapper.style.left) || 0;
        initialTop = parseFloat(gameWrapper.style.top) || 0;

        gameWrapper.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    };

    // Обработка движения мыши во время перетаскивания
    const onMouseMove = (e) => {
        if (!gameWrapper.isDragging) return;

        // Рассчитываем смещение мыши от начальной точки
        const dx = e.clientX - startX;
        const dy = e.clientY - startY;

        // Рассчитываем новые координаты top/left
        const newLeft = initialLeft + dx;
        const newTop = initialTop + dy;

        gameWrapper.style.left = `${newLeft}px`;
        gameWrapper.style.top = `${newTop}px`;
    };

    // Обработка отпускания кнопки мыши
    const onMouseUp = () => {
        if (!gameWrapper.isDragging) return;

        gameWrapper.isDragging = false;
        someonesDragging = false;

        gameWrapper.style.cursor = 'grab';
        document.body.style.userSelect = '';

        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    };

    gameWrapper.addEventListener('mousedown', onMouseDown);

    gameWrapper.style.cursor = 'grab';
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

        const newWidth = Math.max(200, startWidth + dx);
        const newHeight = Math.max(150, startHeight + dy);

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
    const settingsPanel = document.querySelector('.settings-panel');
    if (!settingsPanel) return;
    const dynamicElements = settingsPanel.querySelectorAll('.dynamic-setting');
    dynamicElements.forEach(el => el.remove());
    const puzzleSettingsContainer = settingsPanel.querySelector('.puzzle-settings-container');
    if (puzzleSettingsContainer) {
        puzzleSettingsContainer.remove();
    }
}

/**
 * Обновляет панель настроек в зависимости от выбранной игры.
 * @param {string} gameName - Название выбранной игры
 */
function updateGameSettings(gameName) {
    const settingsPanel = document.querySelector('.settings-panel');
    if (!settingsPanel) {
        console.error("Не найдена панель настроек для обновления настроек игры");
        return;
    }
    if (typeof images === 'undefined') {
         console.error("'переменная images (путь к статическим изображениям) не определена.");
         return;
    }

    clearDynamicSettings();

    if (gameName === "puzzles") {
        // Очищаем существующие настройки для пазлов, если они были добавлены ранее
        const existingSettings = document.querySelector('.puzzle-settings-container');
        if (existingSettings) {
            existingSettings.remove();
        }

        const settingsContainer = document.createElement('div');
        settingsContainer.className = "dynamic-setting puzzle-settings-container"; // Контейнер для настроек пазлов

        // Содержимое настроек
        const content = `
            <div class="modal-content">
                <h2>Настройки пазла</h2>
                <label for="puzzle-name">Название для сохранения:</label>
                <input type="text" id="puzzle-name" placeholder="Название пазла" style="width: 80%; padding: 8px; margin-bottom: 15px;">

                <h2>Выберите изображение для пазла</h2>

                <div class="preset-images">
                    <img src="${images}/british-cat.jpg" class="preset" data-src="${images}/british-cat.jpg">
                    <img src="${images}/tree.png" class="preset" data-src="${images}/tree.png">
                </div>

                <label class="upload-label">
                    Загрузить своё:
                    <input type="file" id="custom-image" accept="image/*">
                </label>

                <div id="image-preview-container" class="image-preview-container" style="display: none; margin-top: 10px; text-align: center;">
                    <img id="image-preview" src="#" alt="Предпросмотр" style="max-width: 100px; max-height: 100px; border: 1px solid #ccc; margin-bottom: 5px;">
                    <p id="image-preview-text" style="font-size: 0.9em; color: #555;">Используется загруженное изображение.</p>
                </div>

                <label for="difficulty">Выберите сложность:</label>
                <select id="difficulty">
                    <option value="2" selected>2x2</option>
                    <option value="3">3x3</option>
                    <option value="4">4x4</option>
                </select>

                <div class="settings-buttons">
                    <button id="start-game">Начать игру</button> <!-- Эта кнопка будет скрыта JS -->
                    <button id="save-puzzle-btn">Сохранить</button>
                    <button id="load-puzzle-btn">Загрузить</button>
                </div>
            </div>
        `;

        // Вставляем содержимое в контейнер
        settingsContainer.innerHTML = content;

        // Добавляем в панель настроек
        settingsPanel.appendChild(settingsContainer);
    } else if (gameName === "another-game") {}
}