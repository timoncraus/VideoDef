const canvas = document.getElementById('board');
const ctx = canvas.getContext('2d');

let drawing = false; // Флаг рисования
let prev = {}; // Предыдущие координаты

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
        img.onload = () => ctx.drawImage(img, 0, 0);
        img.src = data.dataURL;
    }

    if (data.type === 'clear') {
        // Очищаем холст
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
};

// Начало рисования
canvas.addEventListener('mousedown', (e) => {
    drawing = true;
    prev = { x: e.offsetX, y: e.offsetY };
});

// Конец рисования
canvas.addEventListener('mouseup', () => drawing = false);

// Рисуем линию при перемещении мыши
canvas.addEventListener('mousemove', (e) => {
    if (!drawing) return;

    const current = { x: e.offsetX, y: e.offsetY };
    const message = {
        type: 'draw',
        x0: prev.x, y0: prev.y,
        x1: current.x, y1: current.y,
        color: '#000',       // Цвет линии
        lineWidth: 2         // Толщина
    };
    ws.send(JSON.stringify(message));
    prev = current;
});

// Функция рисования на canvas
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

// Очистка доски
function clearBoard() {
    ws.send(JSON.stringify({ type: 'clear' }));
}