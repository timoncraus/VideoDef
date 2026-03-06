import { createPuzzleOnBoard, setupWhiteboardPuzzleSaveLoad } from './puzzle/index.js';
import { createMemoryGameOnBoard, setupWhiteboardMemoryGame } from './memory_game/index.js';

// Получение элементов в случае если мы на странице видеозвонка
const videosElement = document.getElementById('videos');
const roomName = videosElement ? videosElement.dataset.roomName : null;

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
let imageUpdateScheduled = false;

let nextGameElementId = 0; // Счетчик для ID игровых элементов
let gameElements = {}; // Карта для хранения ссылок на DOM элементы игр: { id: element }
let gameElementUpdateScheduled = false;

let dragOffset = { x: 0, y: 0 }; // Смещение при перетаскивании
let isResizing = false; // Флаг изменения размера (для изображений на canvas)
let isDragging = false; // Флаг перетаскивания (для изображений на canvas)

let currentTool = 'pen'; // Текущий инструмент
let currentLineWidth = 2; // Толщина линии
let currentColor = '#000000'; // Цвет по умолчанию

// Функция для получения координат мыши на канвасе
function getMousePos(canvas, evt) {
    const rect = canvas.getBoundingClientRect();
    return {
        x: evt.clientX - rect.left,
        y: evt.clientY - rect.top
    };
}

// Инициализация WebSocket соединения
let ws;
const isWebSocketActive = !!roomName;

if (isWebSocketActive) {
    console.log(`Доска подключается к комнате: ${roomName}`);
    ws = new WebSocket(`ws://${window.location.host}/ws/whiteboard/${roomName}/`);

    // Обработчик входящих сообщений
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data);

        // Рисование
        if (data.type === "draw") {
            const { x0, y0, x1, y1, color, lineWidth, tool} = data;
            drawLine(drawCtx, x0, y0, x1, y1, color, lineWidth, tool);
        } else if (data.type === 'image') { // Работа с изображениями
            const img = new Image();
            img.onload = () => {
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
                if (!imagesList.find(item => item.id === imageObj.id)) {
                    imagesList.push(imageObj);
                     // Убедимся, что nextImageId всегда больше существующих ID, если ID пришел от сервера
                    if (data.id !== undefined && data.id >= nextImageId) {
                        nextImageId = data.id + 1;
                    }
                } else {
                    const existingImgIndex = imagesList.findIndex(item => item.id === imageObj.id);
                    if (existingImgIndex !== -1) {
                        imagesList[existingImgIndex] = {...imagesList[existingImgIndex], ...imageObj};
                    }
                }
                redrawImages();
            };
            img.src = data.dataURL;
        } else if (data.type === 'clear') { // Очистка доски
            drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
            imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
            imagesList = [];
            activeImage = null;
            nextImageId = 0;

            for (const id in gameElements) {
                if (gameElements.hasOwnProperty(id)) {
                    gameElements[id].remove();
                }
            }
            gameElements = {};
            nextGameElementId = 0;
            clearDynamicSettings();

        } else if (data.type === 'delete_image') { // Удаление изображения
            imagesList = imagesList.filter(imgObj => imgObj.id !== data.id);
            if (activeImage && activeImage.id === data.id) {
                activeImage = null;
            }
            redrawImages();
        } else if (data.type === 'move_image' || data.type === 'resize_image') { // Перемещение и/или изменение размера изображения
            const imgIndex = imagesList.findIndex(img => img.id === data.id);
            if (imgIndex !== -1) {
                imagesList[imgIndex].x = data.x;
                imagesList[imgIndex].y = data.y;
                if (data.type === 'resize_image') {
                    imagesList[imgIndex].width = data.width;
                    imagesList[imgIndex].height = data.height;
                }
                if (!imagesList[imgIndex].img.src && data.dataURL) {
                    const newImg = new Image();
                    newImg.onload = () => {
                        imagesList[imgIndex].img = newImg;
                        redrawImages();
                    }
                    newImg.src = data.dataURL;
                } else {
                    redrawImages();
                }
            } else if (data.dataURL) { // Если изображения нет, создаем его
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
                    if (data.id !== undefined && data.id >= nextImageId) {
                        nextImageId = data.id + 1;
                    }
                    redrawImages();
                };
                img.src = data.dataURL;
            }
        } else if (data.type === 'image_drag_update') {
            const imgIndex = imagesList.findIndex(img => img.id === data.id);
            if (imgIndex !== -1) {
                imagesList[imgIndex].x = data.x;
                imagesList[imgIndex].y = data.y;
                redrawImages();
            }
        } else if (data.type === 'image_resize_update') {
            const imgIndex = imagesList.findIndex(img => img.id === data.id);
            if (imgIndex !== -1) {
                imagesList[imgIndex].x = data.x;
                imagesList[imgIndex].y = data.y;
                imagesList[imgIndex].width = data.width;
                imagesList[imgIndex].height = data.height;
                redrawImages();
            }
        }
        else if (data.type === 'add_game_element') { // Добавление игры на доску
            if (!gameElements[data.id]) {
                const gameWrapper = createGameElementLocally(data.id, data.gameName, data.x, data.y, data.width, data.height);
                if (gameWrapper) {
                    if (data.gameName === "puzzles" && !gameWrapper.dataset.puzzleInitialized) {
                        createPuzzleOnBoard(gameWrapper, roomName, data.id);
                        gameWrapper.dataset.puzzleInitialized = "true";
                    } else if (data.gameName === "memory-game" && !gameWrapper.dataset.memoryGameInitialized) {
                        createMemoryGameOnBoard(gameWrapper, roomName, data.id);
                        gameWrapper.dataset.memoryGameInitialized = "true";
                    }
                }
            }
             // Обновляем nextGameElementId, чтобы избежать коллизий, если ID пришел от другого клиента
            const numericId = parseInt(data.id.split('-')[1]);
            if (!isNaN(numericId) && numericId >= nextGameElementId) {
                nextGameElementId = numericId + 1;
            }
        } else if (data.type === 'delete_game_element') { // Удаление игры с доски
            const gameWrapper = gameElements[data.id];
            if (gameWrapper) {
                if (gameWrapper.puzzleWebSocket && gameWrapper.puzzleWebSocket.readyState === WebSocket.OPEN) {
                    gameWrapper.puzzleWebSocket.close();
                    console.log(`Вебсокет для пазла ${gameWrapper.dataset.id} закрыт.`);
                }
                if (gameWrapper.classList.contains('active-game')) {
                    clearDynamicSettings();
                }
                gameWrapper.remove();
                delete gameElements[data.id];
            }
        } else if (data.type === 'move_game_element' || data.type === 'game_element_drag_update') { // Перемещение и/или изменение размера gameWrapper
            const gameWrapper = gameElements[data.id];
            if (gameWrapper) {
                gameWrapper.style.left = data.x + 'px';
                gameWrapper.style.top = data.y + 'px';
            }
        } else if (data.type === 'resize_game_element' || data.type === 'game_element_resize_update') {
            const gameWrapper = gameElements[data.id];
            if (gameWrapper) {
                gameWrapper.style.left = data.x + 'px';
                gameWrapper.style.top = data.y + 'px';
                gameWrapper.style.width = data.width + 'px';
                gameWrapper.style.height = data.height + 'px';
            }
        } else if (data.type === 'game_element_focus') { // Выделение активной игры
            const gameWrapper = gameElements[data.id];
            if (gameWrapper) {
                document.querySelectorAll('.paste-game-wrapper.active-game').forEach(activeWrapper => {
                    if (activeWrapper !== gameWrapper) {
                        activeWrapper.classList.remove('active-game');
                        activeWrapper.dataset.settingsUpdated = 'false';
                        activeWrapper.style.borderColor = '';
                        activeWrapper.style.zIndex = '';
                    }
                });
                gameWrapper.classList.add('active-game');
                gameWrapper.style.borderColor = 'blue';
                gameWrapper.style.zIndex = '100';
                updateGameSettings(gameWrapper.dataset.gameName);
                gameWrapper.dataset.settingsUpdated = 'true';

                if (gameWrapper.dataset.gameName === "puzzles") {
                    setupWhiteboardPuzzleSaveLoad(gameWrapper);
                } else if (gameWrapper.dataset.gameName === "memory-game") {
                    setupWhiteboardMemoryGame(gameWrapper);
                }
            }
        } else if (data.type === 'game_element_blur') { // Удаление выделения
             const gameWrapper = gameElements[data.id];
             if (gameWrapper) {
                gameWrapper.classList.remove('active-game');
                gameWrapper.dataset.settingsUpdated = 'false';
                gameWrapper.style.borderColor = '';
                gameWrapper.style.zIndex = '';
                if (!document.querySelector('.paste-game-wrapper.active-game')) {
                    clearDynamicSettings();
                }
             }
        } 
    };

    ws.onopen = () => {
        console.log(`Вебсокет доски подключен к комнате: ${roomName}`);
    };

    ws.onclose = () => {
        console.log(`Вебсокет доски отключен от комнаты: ${roomName}`);
    };

    ws.onerror = (error) => {
        console.error(`Ошибка вебсокета доски для комнаты ${roomName}:`, error);
    };

} else {
    console.warn("roomName для доски не найден. Синхронизация будет отключена. Работа в локальном режиме.");
    ws = {
        send: (message) => {
            const data = JSON.parse(message);
            if (data.type === 'add_game_element') {
                if (!gameElements[data.id]) {
                    const gameWrapper = createGameElementLocally(data.id, data.gameName, data.x, data.y, data.width, data.height);
                    if (gameWrapper) {
                        if (data.gameName === "puzzles" && !gameWrapper.dataset.puzzleInitialized) {
                            createPuzzleOnBoard(gameWrapper, roomName, data.id);
                            gameWrapper.dataset.puzzleInitialized = "true";
                        } else if (data.gameName === "memory-game" && !gameWrapper.dataset.memoryGameInitialized) {
                            createMemoryGameOnBoard(gameWrapper, roomName, data.id);
                            gameWrapper.dataset.memoryGameInitialized = "true";
                        }
                    }
                }
                // Обновляем nextGameElementId
                const numericId = parseInt(data.id.split('-')[1]);
                if (!isNaN(numericId) && numericId >= nextGameElementId) {
                    nextGameElementId = numericId + 1;
                }
            } else if (data.type === 'delete_game_element') {
                const gameWrapper = gameElements[data.id];
                if (gameWrapper) {
                    if (gameWrapper.classList.contains('active-game')) {
                        clearDynamicSettings();
                    }
                    gameWrapper.remove();
                    delete gameElements[data.id];
                }
            } else if (data.type === 'game_element_focus') {
                 const gameWrapper = gameElements[data.id];
                 if (gameWrapper) {
                    document.querySelectorAll('.paste-game-wrapper.active-game').forEach(activeWrapper => {
                        if (activeWrapper !== gameWrapper) {
                            activeWrapper.classList.remove('active-game');
                            activeWrapper.dataset.settingsUpdated = 'false';
                            activeWrapper.style.borderColor = '';
                            activeWrapper.style.zIndex = '';
                        }
                    });
                    gameWrapper.classList.add('active-game');
                    gameWrapper.style.borderColor = 'blue';
                    gameWrapper.style.zIndex = '100';
                    updateGameSettings(gameWrapper.dataset.gameName);
                    gameWrapper.dataset.settingsUpdated = 'true';
                    if (gameWrapper.dataset.gameName === "puzzles") {
                        setupWhiteboardPuzzleSaveLoad(gameWrapper);
                    } else if (gameWrapper.dataset.gameName === "memory-game") {
                        setupWhiteboardMemoryGame(gameWrapper);
                    }
                 }
            } else if (data.type === 'game_element_blur') {
                const gameWrapper = gameElements[data.id];
                if (gameWrapper) {
                   gameWrapper.classList.remove('active-game');
                   gameWrapper.dataset.settingsUpdated = 'false';
                   gameWrapper.style.borderColor = '';
                   gameWrapper.style.zIndex = '';
                   if (!document.querySelector('.paste-game-wrapper.active-game')) {
                       clearDynamicSettings();
                   }
                }
            }
        },
        readyState: WebSocket.CLOSED
    };
}

// Инициализация инструментов
document.getElementById('pen_btn').addEventListener('click', () => {
    currentTool = 'pen';
    toggleToolButtons('pen_btn');
    drawCanvas.style.cursor = 'crosshair';
    clearSelection();

    const activeGameObject = document.querySelector('.paste-game-wrapper.active-game');
    if (activeGameObject && activeGameObject.dataset.id && ws.readyState === WebSocket.OPEN) {
        activeGameObject.classList.remove('active-game');
        activeGameObject.dataset.settingsUpdated = 'false';
        activeGameObject.style.borderColor = '';
        activeGameObject.style.zIndex = '';
        clearDynamicSettings();
    }
});
document.getElementById('eraser_btn').addEventListener('click', () => {
    currentTool = 'eraser';
    toggleToolButtons('eraser_btn');
    drawCanvas.style.cursor = 'crosshair';
    clearSelection();
    const activeGameObject = document.querySelector('.paste-game-wrapper.active-game');
    if (activeGameObject && activeGameObject.dataset.id && ws.readyState === WebSocket.OPEN) {
        activeGameObject.classList.remove('active-game');
        activeGameObject.dataset.settingsUpdated = 'false';
        activeGameObject.style.borderColor = '';
        activeGameObject.style.zIndex = '';
        clearDynamicSettings();
    }
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
    if (activeId && document.getElementById(activeId)) { // Проверка существования элемента
        document.getElementById(activeId).classList.add('active');
    }
}

// Обработчики событий мыши для Canvas
drawCanvas.addEventListener('mousedown', (e) => {
    const { x, y } = getMousePos(drawCanvas, e);

    const clickedImage = getImageAt(x, y);

    if (!e.target.closest('.paste-game-wrapper')) {
        const activeGameObject = document.querySelector('.paste-game-wrapper.active-game');
        if (activeGameObject) {
            // Если есть активная игра и клик мимо нее, снимаем фокус
            if (isWebSocketActive && ws.readyState === WebSocket.OPEN) {
                 ws.send(JSON.stringify({ type: 'game_element_blur', id: activeGameObject.dataset.id }));
            } else if (!isWebSocketActive) { // Локальный режим
                activeGameObject.classList.remove('active-game');
                activeGameObject.dataset.settingsUpdated = 'false';
                activeGameObject.style.borderColor = '';
                activeGameObject.style.zIndex = '';
                clearDynamicSettings();
            }
        }
    }


    if (clickedImage) { // Взаимодействие с изображением на canvas
        activeImage = clickedImage;
        redrawImages();

        if (overResizeHandle(x, y, activeImage)) {
            isResizing = true;
            dragOffset.startX = x;
            dragOffset.startY = y;
            dragOffset.startImageX = activeImage.x;
            dragOffset.startImageY = activeImage.y;
            dragOffset.startWidth = activeImage.width;
            dragOffset.startHeight = activeImage.height;
            drawCanvas.style.cursor = 'nwse-resize';
        } else {
            isDragging = true;
            dragOffset.x = x - activeImage.x;
            dragOffset.y = y - activeImage.y;
            drawCanvas.style.cursor = 'move';
        }
    } else { // Клик на пустом месте canvas
        if (currentTool === 'pen' || currentTool === 'eraser') {
            drawing = true;
            prev = { x, y };
            clearSelection();
            drawCanvas.style.cursor = 'crosshair';
        } else {
            clearSelection();
            drawCanvas.style.cursor = 'default';
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
    imageUpdateScheduled = false;
});

drawCanvas.addEventListener('mousemove', (e) => {
    const { x, y } = getMousePos(drawCanvas, e);
    const someonesDraggingDOM = Object.values(gameElements).some(el => el.isDragging || el.isResizing); // Проверка, не тащится ли DOM элемент

    if (drawing && !someonesDraggingDOM) {
        const current = { x, y };
        if (prev.x === current.x && prev.y === current.y) return;
        const colorForDraw = currentTool === 'pen' ? currentColor : '#000000';

        const message = {
            type: 'draw',
            x0: prev.x, y0: prev.y, x1: current.x, y1: current.y,
            color: colorForDraw, lineWidth: currentLineWidth, tool: currentTool
        };
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
        }

        drawLine(drawCtx, prev.x, prev.y, current.x, current.y, colorForDraw, currentLineWidth, currentTool);
        prev = current;
    } else if (isDragging && activeImage && !someonesDraggingDOM) {
        activeImage.x = x - dragOffset.x;
        activeImage.y = y - dragOffset.y;
        redrawImages();
        drawCanvas.style.cursor = 'grabbing';
        if (!imageUpdateScheduled && ws.readyState === WebSocket.OPEN) {
            imageUpdateScheduled = true;
            requestAnimationFrame(() => {
                if (isDragging && activeImage) {
                    ws.send(JSON.stringify({
                        type: 'image_drag_update', id: activeImage.id,
                        x: activeImage.x, y: activeImage.y
                    }));
                }
                imageUpdateScheduled = false;
            });
        }
    } else if (isResizing && activeImage && !someonesDraggingDOM) {
        let newWidth = dragOffset.startWidth + (x - dragOffset.startX);
        let newHeight = dragOffset.startHeight + (y - dragOffset.startY);
        activeImage.width = Math.max(20, newWidth);
        activeImage.height = Math.max(20, newHeight);
        redrawImages();
        drawCanvas.style.cursor = 'nwse-resize';
        if (!imageUpdateScheduled && ws.readyState === WebSocket.OPEN) {
            imageUpdateScheduled = true;
            requestAnimationFrame(() => {
                if (isResizing && activeImage) {
                    ws.send(JSON.stringify({
                        type: 'image_resize_update', id: activeImage.id,
                        x: activeImage.x, y: activeImage.y,
                        width: activeImage.width, height: activeImage.height
                    }));
                }
                imageUpdateScheduled = false;
            });
        }
    } else if (!drawing && !isDragging && !isResizing && !someonesDraggingDOM) {
        const hoveredImage = getImageAt(x, y);
        if (hoveredImage && currentTool !== 'pen' && currentTool !== 'eraser') { // Не менять курсор если рисуем
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

// Обработчик нажатия клавиш для удаления изображения на canvas
window.addEventListener('keydown', (e) => {
    if (e.key === 'Delete' || e.key === 'Backspace') {
        if (activeImage && !isInputActive()) { // Удаление изображения на canvas
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

// Удаления изображения с canvas
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

// Снятие выделения с изображения на canvas
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
        const imageId = nextImageId++;

        const img = new Image();
        img.onload = () => {
            const imageObj = {
                id: imageId,
                img,
                x: 50,
                y: 50,
                width: img.naturalWidth > 400 ? 400 : img.naturalWidth,
                height: img.naturalHeight > 300 ? (img.naturalHeight * (400/img.naturalWidth)) : img.naturalHeight,
                dataURL
            };
            if (imageObj.width > 400 || imageObj.height > 300) {
                const aspectRatio = imageObj.width / imageObj.height;
                if (imageObj.width > imageObj.height) {
                    imageObj.width = 400;
                    imageObj.height = 400 / aspectRatio;
                } else {
                    imageObj.height = 300;
                    imageObj.width = 300 * aspectRatio;
                }
            }
            imagesList.push(imageObj);
            redrawImages();

            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'image',
                    id: imageId, dataURL,
                    x: imageObj.x, y: imageObj.y,
                    width: imageObj.width, height: imageObj.height
                }));
            }
        };
        img.onerror = () => console.error("Ошибка загрузки изображения для dataURL");
        img.src = dataURL;
    };
    reader.readAsDataURL(file);
    this.value = '';
});


/**
 * Очищает доску и сбрасывает загруженные изображения.
 */
function clearBoard() {
    if (isWebSocketActive && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'clear' }));
    } else if (!isWebSocketActive) { // Локальный режим: очищаем сразу
        drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        imagesList = [];
        activeImage = null;
        nextImageId = 0;
        document.getElementById('img-upload').value = ''; // Сбрасываем input

        for (const id in gameElements) {
            if (gameElements.hasOwnProperty(id)) {
                gameElements[id].remove();
            }
        }
        gameElements = {};
        nextGameElementId = 0;
        clearDynamicSettings();
        console.log("Доска очищена локально.");
    }
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

// Вспомогательные функции для изображений на canvas
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
    if (document.getElementById('pen_btn')) {
        toggleToolButtons('pen_btn');
        currentTool = 'pen'; // Убедимся, что currentTool соответствует
        drawCanvas.style.cursor = 'crosshair';
    } else {
        currentTool = 'select'; // или другое значение по умолчанию, если кнопки pen нет
        drawCanvas.style.cursor = 'default';
    }
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

/**
 * Создает DOM-элемент игры локально на основе данных.
 * Не отправляет WebSocket сообщение о создании.
 * @param {string} id - Уникальный ID элемента игры
 * @param {string} gameName - Название игры
 * @param {number} x - Координата X
 * @param {number} y - Координата Y
 * @param {number} width - Ширина
 * @param {number} height - Высота
 * @returns {HTMLDivElement | null} - Созданный элемент или null, если ошибка
 */
function createGameElementLocally(id, gameName, x, y, width, height) {
    if (gameElements[id]) {
        console.warn(`Game element with id ${id} already exists locally.`);
        return gameElements[id];
    }

    const gameWrapper = document.createElement('div');
    gameWrapper.className = 'paste-game-wrapper';
    gameWrapper.style.left = x + 'px';
    gameWrapper.style.top = y + 'px';
    gameWrapper.style.width = width + 'px';
    gameWrapper.style.height = height + 'px';
    gameWrapper.dataset.gameName = gameName;
    gameWrapper.dataset.id = id; // Сохраняем ID

    const closeBtn = document.createElement('button');
    closeBtn.className = 'paste-game-close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => {
        if (isWebSocketActive && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'delete_game_element',
                id: gameWrapper.dataset.id
            }));
        } else if (!isWebSocketActive) { // Локальный режим: удаляем сразу
            if (gameWrapper.classList.contains('active-game')) {
                clearDynamicSettings();
            }
            gameWrapper.remove();
            delete gameElements[gameWrapper.dataset.id];
        }
    };

    gameWrapper.appendChild(closeBtn);
    document.querySelector('.canvas-wrapper').appendChild(gameWrapper);
    
    makeDraggable(gameWrapper, id);
    makeResizable(gameWrapper, id);

    // Флаги для отслеживания состояния перетаскивания/изменения размера для этого конкретного элемента
    gameWrapper.isDragging = false;
    gameWrapper.isResizing = false;


    gameWrapper.addEventListener('mousedown', (e) => {
        // Игнорируем клики на кнопку закрытия и маркер изменения размера, они обрабатываются отдельно
        if (e.target.closest('.paste-game-close') || e.target.classList.contains('resize-handle')) {
            return;
        }

        // Если кликнули на игровой элемент, он должен стать активным
        if (!gameWrapper.classList.contains('active-game')) {
            if (isWebSocketActive && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'game_element_focus', id: gameWrapper.dataset.id }));
            } else if (!isWebSocketActive) { // Локальный режим: фокусируем сразу
                document.querySelectorAll('.paste-game-wrapper.active-game').forEach(activeWrapper => {
                    if (activeWrapper !== gameWrapper) {
                        activeWrapper.classList.remove('active-game');
                        activeWrapper.dataset.settingsUpdated = 'false';
                        activeWrapper.style.borderColor = '';
                        activeWrapper.style.zIndex = '';
                    }
                });
                gameWrapper.classList.add('active-game');
                gameWrapper.style.borderColor = 'blue';
                gameWrapper.style.zIndex = '100';
                updateGameSettings(gameWrapper.dataset.gameName);
                gameWrapper.dataset.settingsUpdated = 'true';
                if (gameWrapper.dataset.gameName === "puzzles") {
                    setupWhiteboardPuzzleSaveLoad();
                } else if (gameWrapper.dataset.gameName === "memory-game") {
                    setupWhiteboardMemoryGame(gameWrapper);
                }
            }
        } else {
             gameWrapper.style.zIndex = (parseInt(window.getComputedStyle(gameWrapper).zIndex) || 0) + 1;
        }
        clearSelection(); // Снять выделение с картинки на canvas
        e.stopPropagation();
    });

    gameElements[id] = gameWrapper;
    return gameWrapper;
}


// Обработка добавления игры на доску
document.querySelectorAll(".game-option").forEach(option => {
    if (option.dataset.listenerAttached === 'true') {
        return;
    }

    option.addEventListener("click", () => {
        const gameName = option.dataset.name;
        const gameId = `game-${nextGameElementId++}`;
        const initialX = 100;
        const initialY = 100;
        const initialWidth = 400;
        const initialHeight = 300;

        // Сообщение для отправки или локальной обработки
        const gameData = {
            type: 'add_game_element',
            id: gameId,
            gameName: gameName,
            x: initialX,
            y: initialY,
            width: initialWidth,
            height: initialHeight
        };

        if (isWebSocketActive && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(gameData));
        } else if (!isWebSocketActive) { // Локальный режим для доски
            const localGameWrapper = createGameElementLocally(gameId, gameName, initialX, initialY, initialWidth, initialHeight);
            if (localGameWrapper) {
                if (gameName === "puzzles" && !localGameWrapper.dataset.puzzleInitialized) {
                    createPuzzleOnBoard(localGameWrapper, null, gameId);
                    localGameWrapper.dataset.puzzleInitialized = "true";
                } else if (gameName === "memory-game" && !localGameWrapper.dataset.memoryGameInitialized) {
                    createMemoryGameOnBoard(localGameWrapper, null, gameId);
                    localGameWrapper.dataset.memoryGameInitialized = "true";
                }
            }
            if (ws.send && typeof ws.send === 'function') {
                ws.send(JSON.stringify({ type: 'game_element_focus', id: gameId }));
            }
        }
        dropdown.classList.remove("show");
    });
    option.dataset.listenerAttached = 'true';
});

/**
 * Делает контейнер игры перетаскиваемым.
 * @param {HTMLDivElement} gameWrapper - Контейнер игры
 * @param {string} gameId - Уникальный ID этого игрового элемента
 */
function makeDraggable(gameWrapper, gameId) {
    let dragStartX, dragStartY, initialLeft, initialTop; // Локальные переменные для перетаскивания

    const onElementMouseDown = (e) => {
        // Игнорируем клики на кнопку закрытия и маркер изменения размера
        if (e.target.closest('.paste-game-close') || e.target.classList.contains('resize-handle')) {
            return;
        }
        // Игнорируем, если клик не левой кнопкой мыши
        if (e.button !== 0) {
            return;
        }
        // Блокировка перетаскивания только что добавленной игры
        if (gameWrapper._blockImmediateDrag === true) {
            return;
        }

        gameWrapper.isDragging = true;

        dragStartX = e.clientX;
        dragStartY = e.clientY;
        initialLeft = parseFloat(gameWrapper.style.left) || 0;
        initialTop = parseFloat(gameWrapper.style.top) || 0;

        gameWrapper.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none'; // Предотвращаем выделение текста при перетаскивании

        document.addEventListener('mousemove', onDocumentMouseMoveDrag);
        document.addEventListener('mouseup', onDocumentMouseUpDrag);
        
        e.stopPropagation();
    };

    const onDocumentMouseMoveDrag = (e) => {
        if (!gameWrapper.isDragging) return;

        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        const newLeft = initialLeft + dx;
        const newTop = initialTop + dy;

        gameWrapper.style.left = `${newLeft}px`;
        gameWrapper.style.top = `${newTop}px`;

        // Плавная синхронизация
        if (!gameElementUpdateScheduled && ws.readyState === WebSocket.OPEN) {
            gameElementUpdateScheduled = true;
            requestAnimationFrame(() => {
                if (gameWrapper.isDragging) { // Проверяем, что все еще тащим
                    ws.send(JSON.stringify({
                        type: 'game_element_drag_update',
                        id: gameId,
                        x: parseFloat(gameWrapper.style.left),
                        y: parseFloat(gameWrapper.style.top)
                    }));
                }
                gameElementUpdateScheduled = false;
            });
        }
    };

    const onDocumentMouseUpDrag = () => {
        if (!gameWrapper.isDragging) return;

        gameWrapper.isDragging = false;

        gameWrapper.style.cursor = 'grab';
        document.body.style.userSelect = '';

        document.removeEventListener('mousemove', onDocumentMouseMoveDrag);
        document.removeEventListener('mouseup', onDocumentMouseUpDrag);

        // Отправка финального состояния
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'move_game_element',
                id: gameId,
                x: parseFloat(gameWrapper.style.left),
                y: parseFloat(gameWrapper.style.top)
            }));
        }
        gameElementUpdateScheduled = false;
    };

    gameWrapper.addEventListener('mousedown', onElementMouseDown);
    gameWrapper.style.cursor = 'grab';
}

/**
 * Делает контейнер игры изменяемым по размеру.
 * @param {HTMLDivElement} gameWrapper - Контейнер игры
 * @param {string} gameId - Уникальный ID этого игрового элемента
 */
function makeResizable(gameWrapper, gameId) {
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    gameWrapper.appendChild(resizeHandle);

    let resizeStartX, resizeStartY, initialWidth, initialHeight, initialElementX, initialElementY;

    resizeHandle.addEventListener('mousedown', (e) => {
        e.stopPropagation(); // чтобы drag и resize не конфликтовали
        gameWrapper.isResizing = true;

        const rect = gameWrapper.getBoundingClientRect(); // Получаем размеры относительно viewport
        resizeStartX = e.clientX;
        resizeStartY = e.clientY;
        initialWidth = rect.width;
        initialHeight = rect.height;
        initialElementX = parseFloat(gameWrapper.style.left) || 0;
        initialElementY = parseFloat(gameWrapper.style.top) || 0;

        document.body.style.userSelect = 'none';
        // Используем слушатели на document для отслеживания мыши за пределами элемента
        document.addEventListener('mousemove', onDocumentMouseMoveResize);
        document.addEventListener('mouseup', onDocumentMouseUpResize);
    });

    const onDocumentMouseMoveResize = (e) => {
        if (!gameWrapper.isResizing) return;

        const dx = e.clientX - resizeStartX;
        const dy = e.clientY - resizeStartY;

        const newWidth = Math.max(200, initialWidth + dx);
        const newHeight = Math.max(150, initialHeight + dy);

        gameWrapper.style.width = `${newWidth}px`;
        gameWrapper.style.height = `${newHeight}px`;

        // Плавная синхронизация
        if (!gameElementUpdateScheduled && ws.readyState === WebSocket.OPEN) {
            gameElementUpdateScheduled = true;
            requestAnimationFrame(() => {
                if (gameWrapper.isResizing) {
                    ws.send(JSON.stringify({
                        type: 'game_element_resize_update',
                        id: gameId,
                        x: parseFloat(gameWrapper.style.left),
                        y: parseFloat(gameWrapper.style.top),
                        width: parseFloat(gameWrapper.style.width),
                        height: parseFloat(gameWrapper.style.height)
                    }));
                }
                gameElementUpdateScheduled = false;
            });
        }
    };

    const onDocumentMouseUpResize = () => {
        if (gameWrapper.isResizing) {
            gameWrapper.isResizing = false;
            document.body.style.userSelect = '';
            document.removeEventListener('mousemove', onDocumentMouseMoveResize);
            document.removeEventListener('mouseup', onDocumentMouseUpResize);

            // Отправка финального состояния
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'resize_game_element',
                    id: gameId,
                    x: parseFloat(gameWrapper.style.left),
                    y: parseFloat(gameWrapper.style.top),
                    width: parseFloat(gameWrapper.style.width),
                    height: parseFloat(gameWrapper.style.height)
                }));
            }
            gameElementUpdateScheduled = false;
        }
    };
}

// Панель настроек
const toggleButton = document.getElementById('toggle-settings-btn');
const settingsPanel = document.querySelector('.settings-panel');

// Открытие/Скрытие настроек
toggleButton.addEventListener('click', () => {
    settingsPanel.classList.toggle('hidden');
    toggleButton.textContent = settingsPanel.classList.contains('hidden') ? 'Открыть настройки' : 'Закрыть настройки';
});

/**
 * Удаляет все динамически созданные элементы настроек игр.
 */
function clearDynamicSettings() {
    const settingsPanel = document.querySelector('.settings-panel');
    if (!settingsPanel) return;
    const dynamicElements = settingsPanel.querySelectorAll('.dynamic-setting');
    dynamicElements.forEach(el => el.remove());
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
        settingsContainer.className = "dynamic-setting puzzle-settings-container";

        // Проверяем наличие переменной 'images' перед использованием
        const imagesPath = typeof images !== 'undefined' ? images : '/static/images/default_path';

        // Содержимое настроек
        const content = `
            <div class="modal-content">
                <h2>Настройки пазла</h2>
                <!-- Имя для сохранения -->
                <label for="puzzle-name">Название для сохранения:</label>
                <input type="text" id="puzzle-name" placeholder="Название пазла">

                <h3>Выберите изображение для пазла</h3>

                <div class="presets-container">
                    <img src="${imagesPath}/british-cat.jpg" class="preset" data-src="${imagesPath}/british-cat.jpg" alt="Британский кот">
                    <img src="${imagesPath}/tree.png" class="preset" data-src="${imagesPath}/tree.png" alt="Дерево">
                </div>

                <!-- Загрузка пользовательского изображения -->
                <label class="upload-label">
                    Загрузить своё:
                </label>
                <input type="file" id="custom-image" accept="image/*">
                
                <div id="image-preview-container" class="image-preview-container" style="display: none;">
                    <img id="image-preview" src="#" alt="Предпросмотр">
                    <p id="image-preview-text">Используется загруженное изображение.</p>
                </div>

                <!-- Выбор сложности пазла -->
                <label for="difficulty">Выберите сложность:</label>
                <select id="difficulty">
                    <option value="2" selected>2x2</option>
                    <option value="3">3x3</option>
                    <option value="4">4x4</option>
                </select>

                <!-- Кнопки управления -->
                <div class="settings-buttons">
                    <button id="start-game">Начать игру</button>
                    <button id="save-puzzle-btn">Сохранить</button>
                    <button id="load-puzzle-btn">Загрузить</button>
            </div>
            </div>
        `;

        // Вставляем содержимое в контейнер
        settingsContainer.innerHTML = content;

        // Добавляем в панель настроек
        settingsPanel.appendChild(settingsContainer);
    } else if (gameName === "memory-game") {
        const settingsContainer = document.createElement('div');
        settingsContainer.className = "dynamic-setting memory-game-settings-container";
        
        const content = `
            <div class="settings-content-inner">
                <h2>Настройки "Поиск пар"</h2>
                <label for="game-name">Название игры:</label>
                <input type="text" id="game-name" placeholder="Моя игра в пары">

                <h3>Выберите набор карточек:</h3>
                <div class="presets-container">
                    <div class="preset-set" data-set-name="fruits">Фрукты 🍓</div>
                    <div class="preset-set" data-set-name="animals">Животные 🐼</div>
                </div>

                <label for="custom-images-input" class="upload-label">
                    ИЛИ Загрузите свои изображения:
                </label>
                <input type="file" id="custom-images-input" accept="image/*" multiple>
                
                <div id="custom-images-preview" class="image-preview-container" style="display: none;">
                    <p id="custom-images-info-text">Загружено изображений: <span id="custom-images-count">0</span></p>
                    <div class="preview-grid"></div>
                </div>

                <label for="pair-count-select">Количество пар:</label>
                <select id="pair-count-select">
                    <option value="2">2 пары</option>
                    <option value="3">3 пары</option>
                    <option value="4" selected>4 пары</option>
                    <option value="5">5 пары</option>
                    <option value="6">6 пар</option> 
                </select>
                
                <div class="settings-buttons">
                    <button id="start-memory-game">Перемешать</button> <!-- На доске кнопка может выполнять роль "перемешать" -->
                    <button id="save-memory-game-btn">Сохранить</button>
                    <button id="load-memory-game-btn">Загрузить</button>
                </div>
            </div>
        `;

        settingsContainer.innerHTML = content;
        
        settingsPanel.appendChild(settingsContainer);   
    }
}