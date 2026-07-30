/**
 * Модуль для работы с canvas (рисование).
 */

export class CanvasDrawing {
    constructor(drawCanvas, options = {}) {
        this.drawCanvas = drawCanvas;
        this.drawCtx = drawCanvas.getContext('2d');
        this.onDraw = options.onDraw || null;
        
        this.drawing = false;
        this.prev = {};
        this.currentTool = 'pen';
        this.currentLineWidth = 2;
        this.currentColor = '#000000';
    }
    
    initEventListeners() {
        this.drawCanvas.addEventListener('mousedown', this.onMouseDown.bind(this));
        this.drawCanvas.addEventListener('mouseup', this.onMouseUp.bind(this));
        this.drawCanvas.addEventListener('mousemove', this.onMouseMove.bind(this));
    }
    
    /**
     * Получает координаты мыши относительно canvas.
     */
    getMousePos(evt) {
        const rect = this.drawCanvas.getBoundingClientRect();
        return {
            x: evt.clientX - rect.left,
            y: evt.clientY - rect.top
        };
    }
    
    onMouseDown(e) {
        if (e.button !== 0) return;
        
        const { x, y } = this.getMousePos(e);
        
        if (this.currentTool === 'pen' || this.currentTool === 'eraser') {
            this.drawing = true;
            this.prev = { x, y };
            this.drawCanvas.style.cursor = 'crosshair';
        }
    }
    
    onMouseUp() {
        if (this.drawing) {
            this.drawing = false;
            if (this.currentTool === 'eraser') {
                this.drawCtx.globalCompositeOperation = 'source-over';
            }
        }
    }
    
    onMouseMove(e) {
        if (!this.drawing) return;
        
        const { x, y } = this.getMousePos(e);
        
        if (this.prev.x === x && this.prev.y === y) return;
        
        const current = { x, y };
        const colorForDraw = this.currentTool === 'pen' ? this.currentColor : '#000000';
        
        this.drawLine(this.prev.x, this.prev.y, current.x, current.y, colorForDraw, this.currentLineWidth, this.currentTool);
        
        if (this.onDraw) {
            this.onDraw(this.prev.x, this.prev.y, current.x, current.y, colorForDraw, this.currentLineWidth, this.currentTool);
        }
        
        this.prev = current;
    }
    
    drawLine(x0, y0, x1, y1, color, lineWidth, tool = 'pen') {
        this.drawCtx.lineWidth = lineWidth;
        this.drawCtx.lineCap = 'round';
        this.drawCtx.lineJoin = 'round';
        
        if (tool === 'eraser') {
            this.drawCtx.globalCompositeOperation = 'destination-out';
        } else {
            this.drawCtx.globalCompositeOperation = 'source-over';
            this.drawCtx.strokeStyle = color;
        }
        
        this.drawCtx.beginPath();
        this.drawCtx.moveTo(x0, y0);
        this.drawCtx.lineTo(x1, y1);
        this.drawCtx.stroke();
    }
    
    setTool(tool) {
        this.currentTool = tool;
        this.drawCanvas.style.cursor = tool === 'pen' || tool === 'eraser' ? 'crosshair' : 'default';
    }
    
    setColor(color) {
        this.currentColor = color;
    }
    
    setLineWidth(width) {
        this.currentLineWidth = parseInt(width);
    }
    
    clear() {
        this.drawCtx.clearRect(0, 0, this.drawCanvas.width, this.drawCanvas.height);
    }
    
    resizeToDisplaySize() {
        const wrapper = this.drawCanvas.parentElement;
        if (!wrapper) return;
        
        const width = wrapper.clientWidth;
        const height = wrapper.clientHeight;
        
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.drawCanvas.width;
        tempCanvas.height = this.drawCanvas.height;
        const tempCtx = tempCanvas.getContext('2d');
        
        if (this.drawCanvas.width > 0 && this.drawCanvas.height > 0) {
            tempCtx.drawImage(this.drawCanvas, 0, 0);
        }
        
        this.drawCanvas.width = width;
        this.drawCanvas.height = height;
        
        if (tempCanvas.width > 0 && tempCanvas.height > 0) {
            this.drawCtx.drawImage(tempCanvas, 0, 0);
        }
        
        this.drawCtx.strokeStyle = this.currentColor;
        this.drawCtx.lineWidth = this.currentLineWidth;
        this.drawCtx.lineCap = 'round';
        this.drawCtx.lineJoin = 'round';
        
        if (this.currentTool === 'eraser') {
            this.drawCtx.globalCompositeOperation = 'destination-out';
        } else {
            this.drawCtx.globalCompositeOperation = 'source-over';
        }
    }
}