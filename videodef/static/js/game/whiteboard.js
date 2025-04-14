const imageCanvas = document.getElementById('image-layer'); 
const drawCanvas = document.getElementById('draw-layer');

// Контексты рисования для изображений и рисования
const imageCtx = imageCanvas.getContext('2d');
const drawCtx = drawCanvas.getContext('2d');

let drawing = false; // Флаг, указывающий, рисуем ли мы
let prev = {}; // Координаты предыдущей точки для рисования
let images = []; // Массив всех изображений
let activeImage = null; // Текущее изображение, которое редактируется
let dragOffset = { x: 0, y: 0 }; // Смещение для перетаскивания изображений
let isDragging = false; // Флаг перетаскивания изображения
let isResizing = false; // Флаг изменения размера изображения

let currentTool = 'pen'; // Текущий инструмент (кисть или ластик)
let currentLineWidth = 2; // Толщина линии
let currentColor = '#000000'; // Цвет линии

// WebSocket-соединение для синхронизации
const ws = new WebSocket(`ws://${window.location.host}/ws/whiteboard/`);
// Обработка сообщений от сервера
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.type === "draw") {
        const { x0, y0, x1, y1, color, lineWidth } = data;
        drawLine(drawCtx, x0, y0, x1, y1, color, lineWidth); // Рисуем линию
    }

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
            images.push(imageObj); // Добавляем изображение
            redrawImages(); // Перерисовываем изображения
        };
        img.src = data.dataURL; // Загружаем изображение
    }

    if (data.type === 'clear') {
        drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        images = []; // Очищаем все изображения
    }
};

// Настройка инструментов рисования
document.getElementById('pen_btn').addEventListener('click', () => {
    currentTool = 'pen'; // Выбор инструмента - кисть
    toggleToolButtons('pen_btn'); // Подсвечиваем активную кнопку
});
document.getElementById('eraser_btn').addEventListener('click', () => {
    currentTool = 'eraser'; // Выбор инструмента - ластик
    toggleToolButtons('eraser_btn'); // Подсвечиваем активную кнопку
});
document.getElementById('colorPicker').addEventListener('input', (e) => {
    currentColor = e.target.value; // Изменяем цвет кисти
});
document.getElementById('thickness').addEventListener('input', (e) => {
    currentLineWidth = parseInt(e.target.value); // Изменяем толщину линии
});

function toggleToolButtons(activeId) {
    document.querySelectorAll('.tool').forEach(btn => btn.classList.remove('active'));
    document.getElementById(activeId).classList.add('active');
}

// События для рисования (только на верхнем холсте)
drawCanvas.addEventListener('mousedown', (e) => {
    const { offsetX: x, offsetY: y } = e;
    activeImage = getImageAt(x, y); // Проверяем, не кликнули ли на изображение
    if (activeImage) {
        if (overResizeHandle(x, y, activeImage)) {
            isResizing = true; // Начали изменение размера изображения
        } else {
            isDragging = true; // Начали перетаскивание изображения
            dragOffset.x = x - activeImage.x;
            dragOffset.y = y - activeImage.y;
        }
    } else {
        drawing = true; // Начали рисовать
        prev = { x, y }; // Устанавливаем начальную точку для рисования
    }
});

drawCanvas.addEventListener('mouseup', () => {
    drawing = false; // Завершаем рисование
    isDragging = false; // Завершаем перетаскивание
    isResizing = false; // Завершаем изменение размера
    activeImage = null;
});

drawCanvas.addEventListener('mousemove', (e) => {
    const { offsetX: x, offsetY: y } = e;

    if (drawing) { // Если рисуем
        const current = { x, y };
        const color = currentTool === 'pen' ? currentColor : '#ffffff'; // Выбираем цвет для рисования или ластика
        const message = {
            type: 'draw',
            x0: prev.x, y0: prev.y,
            x1: current.x, y1: current.y,
            color,
            lineWidth: currentLineWidth
        };
        ws.send(JSON.stringify(message)); // Отправляем данные на сервер

        drawLine(drawCtx, prev.x, prev.y, current.x, current.y, color, currentLineWidth); // Рисуем на канвасе
        prev = current;
    } else if (isDragging && activeImage) { // Если перетаскиваем изображение
        activeImage.x = x - dragOffset.x;
        activeImage.y = y - dragOffset.y;
        redrawImages(); // Перерисовываем изображения
    } else if (isResizing && activeImage) { // Если изменяем размер изображения
        activeImage.width = x - activeImage.x;
        activeImage.height = y - activeImage.y;
        redrawImages(); // Перерисовываем изображения
    }
});

function drawLine(ctx, x0, y0, x1, y1, color, lineWidth) {
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.lineCap = 'round'; // Округлые концы линии
    ctx.lineJoin = 'round'; // Округление углов
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke(); // Применяем рисование
}

// Загрузка изображения
document.getElementById('img-upload').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        const dataURL = reader.result;
        ws.send(JSON.stringify({ type: 'image', dataURL })); // Отправляем изображение на сервер
    };
    reader.readAsDataURL(file); // Читаем файл как DataURL
});

function clearBoard() {
    ws.send(JSON.stringify({ type: 'clear' })); // Отправляем сообщение на сервер для очистки
    document.getElementById('img-upload').value = ''; // Очищаем поле загрузки изображения
}

function redrawImages() {
    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height); // Очищаем холст
    images.forEach(imgObj => {
        imageCtx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height); // Отображаем изображения
        drawResizeHandle(imageCtx, imgObj); // Рисуем ручку для изменения размера
    });
}

function getImageAt(x, y) {
    for (let i = images.length - 1; i >= 0; i--) {
        const img = images[i];
        if (x >= img.x && x <= img.x + img.width &&
            y >= img.y && y <= img.y + img.height) {
            return img;
        }
    }
    return null;
}

function drawResizeHandle(ctx, imgObj) {
    const size = 10;
    ctx.fillStyle = '#00f'; // Синий цвет для ручки
    ctx.fillRect(imgObj.x + imgObj.width - size, imgObj.y + imgObj.height - size, size, size); // Рисуем ручку
}

function overResizeHandle(x, y, imgObj) {
    const size = 10;
    return x >= imgObj.x + imgObj.width - size &&
           x <= imgObj.x + imgObj.width &&
           y >= imgObj.y + imgObj.height - size &&
           y <= imgObj.y + imgObj.height;
}

function resizeCanvasToDisplaySize() {
    const wrapper = imageCanvas.parentElement;
    const width = wrapper.clientWidth;
    const height = wrapper.clientHeight;

    imageCanvas.width = width; // Устанавливаем ширину и высоту холста
    imageCanvas.height = height;
    drawCanvas.width = width; // Устанавливаем ширину и высоту рисующего холста
    drawCanvas.height = height;

    redrawImages(); // Перерисовываем изображения
}

window.addEventListener('load', resizeCanvasToDisplaySize); // Изменяем размер холста при загрузке страницы
window.addEventListener('resize', resizeCanvasToDisplaySize); // Изменяем размер холста при изменении окна

// ---------------- Добавление игр на холст ----------------
const dropdown = document.getElementById("game-menu");
const gamesBtn = document.getElementById("games_btn");

gamesBtn.addEventListener("click", () => {
    dropdown.classList.toggle("show");
});

window.addEventListener("click", (e) => {
    if (!gamesBtn.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove("show");
    }
});

document.querySelectorAll(".game-option").forEach(option => {
    option.addEventListener("click", () => {
        const gameName = option.dataset.name;
        addGameIframe(gameName);
        dropdown.classList.remove("show");
    });
});

function addGameIframe(name) {
    const iframeWrapper = document.createElement('div');
    iframeWrapper.className = 'iframe-wrapper';
    iframeWrapper.style.left = '100px';
    iframeWrapper.style.top = '100px';
    iframeWrapper.style.width = '400px';
    iframeWrapper.style.height = '300px';
    iframeWrapper.style.aspectRatio = '4 / 3';

    const iframe = document.createElement('iframe');
    
    iframe.src = `http://127.0.0.1:8000/games/${name}/`;

    iframe.setAttribute("sandbox", "allow-scripts allow-same-origin allow-forms");

    const closeBtn = document.createElement('button');
    closeBtn.className = 'iframe-close';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => iframeWrapper.remove();

    iframeWrapper.appendChild(closeBtn);
    iframeWrapper.appendChild(iframe);
    document.querySelector('.canvas-wrapper').appendChild(iframeWrapper);
}