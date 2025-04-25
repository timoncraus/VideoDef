import { createPuzzleOnBoard, puzzleParams } from './puzzle/index.js';

puzzleParams.onWhiteboard = true;

const imageCanvas = document.getElementById('image-layer');
const drawCanvas = document.getElementById('draw-layer');

const imageCtx = imageCanvas.getContext('2d');
const drawCtx = drawCanvas.getContext('2d');

let drawing = false;
let prev = {};
let images = [];
let activeImage = null;
let dragOffset = { x: 0, y: 0 };
let isResizing = false;
let isDragging = false;
let currentTool = 'pen';
let currentLineWidth = 2;
let currentColor = '#000000';

const ws = new WebSocket(`ws://${window.location.host}/ws/whiteboard/`);
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);

    if (data.type === "draw") {
        const { x0, y0, x1, y1, color, lineWidth } = data;
        drawLine(drawCtx, x0, y0, x1, y1, color, lineWidth);
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
            images.push(imageObj);
            redrawImages();
        };
        img.src = data.dataURL;
    }

    if (data.type === 'clear') {
        drawCtx.clearRect(0, 0, drawCanvas.width, drawCanvas.height);
        imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
        images = [];
    }
};


document.getElementById('pen_btn').addEventListener('click', () => {
    currentTool = 'pen';
    toggleToolButtons('pen_btn');
});
document.getElementById('eraser_btn').addEventListener('click', () => {
    currentTool = 'eraser';
    toggleToolButtons('eraser_btn');
});
document.getElementById('colorPicker').addEventListener('input', (e) => {
    currentColor = e.target.value;
});
document.getElementById('thickness').addEventListener('input', (e) => {
    currentLineWidth = parseInt(e.target.value);
});

function toggleToolButtons(activeId) {
    document.querySelectorAll('.tool').forEach(btn => btn.classList.remove('active'));
    document.getElementById(activeId).classList.add('active');
}

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

function clearBoard() {
    ws.send(JSON.stringify({ type: 'clear' }));
    document.getElementById('img-upload').value = '';
}

document.querySelector("#clear_btn").addEventListener("click", () => {
    clearBoard();
});

function redrawImages() {
    imageCtx.clearRect(0, 0, imageCanvas.width, imageCanvas.height);
    images.forEach(imgObj => {
        imageCtx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height);
        drawResizeHandle(imageCtx, imgObj);
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
        if (gameName === "puzzles") {
            createPuzzleOnBoard(gameWrapper);
        }
        dropdown.classList.remove("show");
    });
});

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
    closeBtn.onclick = () => gameWrapper.remove();

    gameWrapper.appendChild(closeBtn);
    document.querySelector('.canvas-wrapper').appendChild(gameWrapper);
    makeDraggable(gameWrapper);
    makeResizable(gameWrapper);
    return gameWrapper;
}

let someonesDragging = false;

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