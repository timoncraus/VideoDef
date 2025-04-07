const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d');

let drawing = false; // Флаг рисования
let prev = {}; // Предыдущие координаты
let images = []; // Массив всех добавленных изображений
let activeImage = null; // Текущее редактируемое изображение
let dragOffset = { x: 0, y: 0 }; // Смещение для перетаскивания
let isDragging = false; // Флаг перетаскивания
let isResizing = false; // Флаг изменения размера
let activeResizeHandle = null; // Текущая ручка изменения размера

// Устанавливаем WebSocket-соединение
const ws = new WebSocket(`ws://${window.location.host}/ws/whiteboard/`);

// При получении сообщения — обрабатываем его
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.type === "draw") {
        // Рисуем линию
        const { x0, y0, x1, y1, color, lineWidth } = data;
        drawLine(x0, y0, x1, y1, color, lineWidth);
    }

    if (data.type === 'image') {
        // Отображаем прикреплённое изображение
        const img = new Image();
        img.onload = () => {
            const imageObj = {
                img: img,
                x: 50,
                y: 50,
                width: 200,
                height: 200
            };
            images.push(imageObj);
            redrawCanvas();
        };
        img.src = data.dataURL;
    }

    if (data.type === 'clear') {
        // Очищаем холст
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        images = [];
    }
};

// Начало рисования
canvas.addEventListener('mousedown', (e) => {
    const { offsetX: x, offsetY: y } = e;

    // Проверка на перетаскивание или изменение размера изображения
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

// Конец рисования или перетаскивания
canvas.addEventListener('mouseup', () => {
    drawing = false;
    isDragging = false;
    isResizing = false;
    activeImage = null;
});

// Рисуем линии при перемещении мыши
canvas.addEventListener('mousemove', (e) => {
    const { offsetX: x, offsetY: y } = e;

    if (drawing) {
        const current = { x, y };
        const message = {
            type: 'draw',
            x0: prev.x, y0: prev.y,
            x1: current.x, y1: current.y,
            color: '#000',       // Цвет линии
            lineWidth: 2         // Толщина
        };
        ws.send(JSON.stringify(message));
        prev = current;
    } else if (isDragging && activeImage) {
        activeImage.x = x - dragOffset.x;
        activeImage.y = y - dragOffset.y;
        redrawCanvas();
    } else if (isResizing && activeImage) {
        activeImage.width = x - activeImage.x;
        activeImage.height = y - activeImage.y;
        redrawCanvas();
    }
});

// Функция рисования линии
function drawLine(x0, y0, x1, y1, color, lineWidth) {
    ctx.strokeStyle = color;
    ctx.lineWidth = lineWidth;
    ctx.beginPath();
    ctx.moveTo(x0, y0);
    ctx.lineTo(x1, y1);
    ctx.stroke();
}

// Загрузка изображения
document.getElementById('img-upload').addEventListener('change', function () {
    const file = this.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
        const dataURL = reader.result;
        ws.send(JSON.stringify({ type: 'image', dataURL }));
    };
    reader.readAsDataURL(file);
});

// Очистка доски и сброс поля загрузки изображения
function clearBoard() {
    ws.send(JSON.stringify({ type: 'clear' }));
    // Сбросим массив с изображениями
    images = [];
    // Очистим поле загрузки изображения
    document.getElementById('img-upload').value = ''; // сбрасываем выбранный файл
    redrawCanvas(); // Перерисовываем холст (поскольку мы очистили изображения)
}

// Перерисовка холста
function redrawCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    images.forEach(imgObj => {
        ctx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height);
        drawResizeHandle(imgObj); // Рисуем ручку для изменения размера
    });
}

// Функция получения изображения по координатам
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

// Функция рисования ручки изменения размера
function drawResizeHandle(imgObj) {
    const size = 10;
    ctx.fillStyle = '#00f';
    ctx.fillRect(imgObj.x + imgObj.width - size, imgObj.y + imgObj.height - size, size, size);
}

// Проверка, находится ли курсор на ручке изменения размера
function overResizeHandle(x, y, imgObj) {
    const size = 10;
    return x >= imgObj.x + imgObj.width - size &&
           x <= imgObj.x + imgObj.width &&
           y >= imgObj.y + imgObj.height - size &&
           y <= imgObj.y + imgObj.height;
}
