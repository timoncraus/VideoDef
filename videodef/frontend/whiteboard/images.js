/**
 * Модуль для управления изображениями на canvas.
 * Управляет загрузкой, перемещением, изменением размера и удалением изображений.
 */

const COLORS = {
    primary: '#4D8CF2',
    accent: '#00bfff',
    selectionStroke: '#4D8CF2',
    handleFill: '#4D8CF2',
    handleStroke: '#ffffff',
    shadowColor: 'rgba(77, 140, 242, 0.35)'
};

// Размеры элементов выделения
const SELECTION_LINE_WIDTH = 1.5;
const HANDLE_RADIUS = 5;
const CORNER_RADIUS = 6;

/**
 * Класс для управления изображениями на canvas.
 */
export class ImageManager {
    /**
     * Создает экземпляр ImageManager.
     * 
     * @param {HTMLCanvasElement} imageCanvas - Canvas для изображений
     * @param {Object} options - Опции
     * @param {Function} options.onImageChange - Callback при изменении изображения (action, data)
     * @param {Function} options.onImageDragUpdate - Callback при перетаскивании (id, x, y)
     * @param {Function} options.onImageResizeUpdate - Callback при изменении размера (id, x, y, width, height)
     */
    constructor(imageCanvas, options = {}) {
        this.imageCanvas = imageCanvas;
        this.imageCtx = imageCanvas.getContext('2d');
        this.onImageChange = options.onImageChange || null;
        this.onImageDragUpdate = options.onImageDragUpdate || null;
        this.onImageResizeUpdate = options.onImageResizeUpdate || null;
        
        this.imagesList = [];
        this.activeImage = null;
        this.nextImageId = 0;
        
        this.isDragging = false;
        this.isResizing = false;
        this.activeHandle = null; // 'tl' | 'tr' | 'bl' | 'br' — какой угол тянем
        this.dragOffset = { x: 0, y: 0 };
        
        // Флаг для синхронизации отправки с частотой кадров браузера (requestAnimationFrame).
        // Предотвращает спам сети сообщениями при движении мыши (60+ раз в секунду)
        this.imageUpdateScheduled = false;
        
        // Слушатели добавляются в Whiteboard.setupCanvasEventListeners для избежания конфликтов
    }
    
    /**
     * Обработчик нажатия мыши на canvas.
     * Вызывается из Whiteboard.handleCanvasMouseDown
     */
    handleMouseDown(x, y) {
        const clickedImage = this.getImageAt(x, y);
        
        if (clickedImage) {
            this.setActiveImage(clickedImage);
            const dragType = this.startDrag(x, y);
            return dragType;
        } else {
            this.clearSelection();
            return false;
        }
    }
    
    /**
     * Обработчик движения мыши на canvas.
     * Вызывается из Whiteboard.handleCanvasMouseMove
     */
    handleMouseMove(x, y) {
        if (this.isDragging || this.isResizing) {
            this.handleDrag(x, y);
            
            if (this.isDragging) {
                return 'grabbing';
            } else if (this.isResizing) {
                return this.getResizeCursorForHandle(this.activeHandle);
            }
        } 
        
        // Обновление курсора при наведении
        const cursor = this.getCursorForPosition(x, y, 'default');
        return cursor;
    }
    
    /**
     * Обработчик отпускания мыши на canvas.
     * Вызывается из Whiteboard.handleCanvasMouseUp
     */
    handleMouseUp() {
        const dragResult = this.endDrag();
        return dragResult;
    }
    
    /**
     * Добавляет изображение на canvas.
     * 
     * @param {string} dataURL - Данные изображения
     * @param {number} x - Координата X
     * @param {number} y - Координата Y
     * @param {number} width - Ширина
     * @param {number} height - Высота
     * @param {number|null} id - ID изображения
     * @param {boolean} isFromServer - Если true, не отправлять событие onImageChange (защита от эхо-петли)
     */
    addImage(dataURL, x, y, width, height, id = null, isFromServer = false) {
        const img = new Image();
        img.onload = () => {
            const imageId = id !== null ? id : this.nextImageId++;
            
            const imageObj = {
                id: imageId,
                img,
                x,
                y,
                width,
                height,
                dataURL
            };
            
            const existingIndex = this.imagesList.findIndex(item => item.id === imageId);
            if (existingIndex !== -1) {
                this.imagesList[existingIndex] = { ...this.imagesList[existingIndex], ...imageObj };
            } else {
                this.imagesList.push(imageObj);
                if (id !== null && id >= this.nextImageId) {
                    this.nextImageId = id + 1;
                }
            }
            
            this.redraw();
            
            // Отправляем событие только если изображение добавлено локально
            if (!isFromServer && this.onImageChange) {
                this.onImageChange('add', imageObj);
            }
        };
        img.src = dataURL;
        return img;
    }
    
    /**
     * Обновляет позицию изображения (вызывается при получении сообщения от сервера).
     */
    updateImagePosition(id, x, y) {
        const imgIndex = this.imagesList.findIndex(img => img.id === id);
        if (imgIndex !== -1) {
            this.imagesList[imgIndex].x = x;
            this.imagesList[imgIndex].y = y;
            this.redraw();
        }
    }
    
    /**
     * Обновляет размер изображения (вызывается при получении сообщения от сервера).
     */
    updateImageSize(id, x, y, width, height) {
        const imgIndex = this.imagesList.findIndex(img => img.id === id);
        if (imgIndex !== -1) {
            this.imagesList[imgIndex].x = x;
            this.imagesList[imgIndex].y = y;
            this.imagesList[imgIndex].width = width;
            this.imagesList[imgIndex].height = height;
            this.redraw();
        }
    }
    
    /**
     * Удаляет изображение.
     */
    deleteImage(id) {
        this.imagesList = this.imagesList.filter(imgObj => imgObj.id !== id);
        
        if (this.activeImage && this.activeImage.id === id) {
            this.activeImage = null;
        }
        
        this.redraw();
        
        if (this.onImageChange) {
            this.onImageChange('delete', { id });
        }
    }
    
    /**
     * Получает изображение по координатам.
     */
    getImageAt(x, y) {
        for (let i = this.imagesList.length - 1; i >= 0; i--) {
            const img = this.imagesList[i];
            if (x >= img.x && x <= img.x + img.width &&
                y >= img.y && y <= img.y + img.height) {
                return img;
            }
        }
        return null;
    }
    
    /**
     * Возвращает координаты 4 угловых маркеров для заданного изображения.
     * @param {Object} imgObj - Объект изображения
     * @returns {Object} Координаты центров маркеров { tl, tr, bl, br }
     */
    getHandlePositions(imgObj) {
        return {
            tl: { x: imgObj.x, y: imgObj.y },
            tr: { x: imgObj.x + imgObj.width, y: imgObj.y },
            bl: { x: imgObj.x, y: imgObj.y + imgObj.height },
            br: { x: imgObj.x + imgObj.width, y: imgObj.y + imgObj.height }
        };
    }
    
    /**
     * Определяет, какой угловой маркер находится под курсором.
     * @param {number} x - Координата X курсора
     * @param {number} y - Координата Y курсора
     * @param {Object} imgObj - Объект изображения
     * @returns {string|null} Идентификатор маркера ('tl'|'tr'|'bl'|'br') или null
     */
    getHandleAtPosition(x, y, imgObj) {
        const handles = this.getHandlePositions(imgObj);
        const hitRadius = HANDLE_RADIUS + 4;
        
        for (const [key, pos] of Object.entries(handles)) {
            const dx = x - pos.x;
            const dy = y - pos.y;
            if (dx * dx + dy * dy <= hitRadius * hitRadius) {
                return key;
            }
        }
        return null;
    }
    
    /**
     * Возвращает CSS-курсор в зависимости от угла resize.
     */
    getResizeCursorForHandle(handleKey) {
        if (handleKey === 'tl' || handleKey === 'br') return 'nwse-resize';
        if (handleKey === 'tr' || handleKey === 'bl') return 'nesw-resize';
        return 'nwse-resize';
    }
    
    /**
     * Устанавливает активное изображение.
     */
    setActiveImage(image) {
        this.activeImage = image;
        this.redraw();
    }
    
    /**
     * Очищает выделение.
     */
    clearSelection() {
        if (this.activeImage) {
            this.activeImage = null;
            this.redraw();
        }
    }
    
    /**
     * Обрабатывает начало перетаскивания изображения.
     */
    startDrag(x, y) {
        if (!this.activeImage) return false;
        
        const handleKey = this.getHandleAtPosition(x, y, this.activeImage);
        if (handleKey) {
            this.isResizing = true;
            this.activeHandle = handleKey;
            this.dragOffset = {
                startX: x,
                startY: y,
                startImageX: this.activeImage.x,
                startImageY: this.activeImage.y,
                startWidth: this.activeImage.width,
                startHeight: this.activeImage.height
            };
            return 'resize';
        }

        this.isDragging = true;
        this.activeHandle = null;
        this.dragOffset = {
            x: x - this.activeImage.x,
            y: y - this.activeImage.y
        };
        return 'drag';
    }
    
    /**
     * Обрабатывает процесс перетаскивания.
     */
    handleDrag(x, y) {
        if (this.isDragging && this.activeImage) {
            this.activeImage.x = x - this.dragOffset.x;
            this.activeImage.y = y - this.dragOffset.y;
            this.redraw();
            
            if (this.onImageDragUpdate && !this.imageUpdateScheduled) {
                this.imageUpdateScheduled = true;
                requestAnimationFrame(() => {
                    if (this.isDragging && this.activeImage) {
                        this.onImageDragUpdate(this.activeImage.id, this.activeImage.x, this.activeImage.y);
                    }
                    this.imageUpdateScheduled = false;
                });
            }
            return true;
        }
        
        if (this.isResizing && this.activeImage) {
            const dx = x - this.dragOffset.startX;
            const dy = y - this.dragOffset.startY;
            const MIN_SIZE = 40;
            
            // В зависимости от того, какой угол тянем, пересчитываем x/y/width/height
            switch (this.activeHandle) {
                case 'br': {
                    this.activeImage.width = Math.max(MIN_SIZE, this.dragOffset.startWidth + dx);
                    this.activeImage.height = Math.max(MIN_SIZE, this.dragOffset.startHeight + dy);
                    break;
                }
                case 'bl': {
                    const newWidth = Math.max(MIN_SIZE, this.dragOffset.startWidth - dx);
                    this.activeImage.x = this.dragOffset.startImageX + this.dragOffset.startWidth - newWidth;
                    this.activeImage.width = newWidth;
                    this.activeImage.height = Math.max(MIN_SIZE, this.dragOffset.startHeight + dy);
                    break;
                }
                case 'tr': {
                    this.activeImage.width = Math.max(MIN_SIZE, this.dragOffset.startWidth + dx);
                    const newHeight = Math.max(MIN_SIZE, this.dragOffset.startHeight - dy);
                    this.activeImage.y = this.dragOffset.startImageY + this.dragOffset.startHeight - newHeight;
                    this.activeImage.height = newHeight;
                    break;
                }
                case 'tl': {
                    const newWidth = Math.max(MIN_SIZE, this.dragOffset.startWidth - dx);
                    const newHeight = Math.max(MIN_SIZE, this.dragOffset.startHeight - dy);
                    this.activeImage.x = this.dragOffset.startImageX + this.dragOffset.startWidth - newWidth;
                    this.activeImage.y = this.dragOffset.startImageY + this.dragOffset.startHeight - newHeight;
                    this.activeImage.width = newWidth;
                    this.activeImage.height = newHeight;
                    break;
                }
            }
            
            this.redraw();
            
            if (this.onImageResizeUpdate && !this.imageUpdateScheduled) {
                this.imageUpdateScheduled = true;
                requestAnimationFrame(() => {
                    if (this.isResizing && this.activeImage) {
                        this.onImageResizeUpdate(
                            this.activeImage.id,
                            this.activeImage.x,
                            this.activeImage.y,
                            this.activeImage.width,
                            this.activeImage.height
                        );
                    }
                    this.imageUpdateScheduled = false;
                });
            }
            return true;
        }
        
        return false;
    }
    
    /**
     * Завершает перетаскивание.
     */
    endDrag() {
        let result = null;
        
        if (this.isDragging && this.activeImage) {
            result = {
                type: 'move',
                id: this.activeImage.id,
                x: this.activeImage.x,
                y: this.activeImage.y,
                dataURL: this.activeImage.dataURL
            };
            this.isDragging = false;
        }
        
        if (this.isResizing && this.activeImage) {
            result = {
                type: 'resize',
                id: this.activeImage.id,
                x: this.activeImage.x,
                y: this.activeImage.y,
                width: this.activeImage.width,
                height: this.activeImage.height,
                dataURL: this.activeImage.dataURL
            };
            this.isResizing = false;
            this.activeHandle = null;
        }
        
        this.imageUpdateScheduled = false;
        return result;
    }
    
    /**
     * Получает курсор для текущей позиции.
     */
    getCursorForPosition(x, y, currentTool) {
        const hoveredImage = this.getImageAt(x, y);
        
        if (hoveredImage) {
            const handle = this.getHandleAtPosition(x, y, hoveredImage);
            if (handle) {
                return this.getResizeCursorForHandle(handle);
            }
            return 'move';
        }
        
        return (currentTool === 'pen' || currentTool === 'eraser') ? 'crosshair' : 'default';
    }
    
    /**
     * Рисует скруглённый прямоугольник
     */
    drawRoundedRect(ctx, x, y, w, h, r) {
        ctx.beginPath();
        ctx.moveTo(x + r, y);
        ctx.lineTo(x + w - r, y);
        ctx.quadraticCurveTo(x + w, y, x + w, y + r);
        ctx.lineTo(x + w, y + h - r);
        ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
        ctx.lineTo(x + r, y + h);
        ctx.quadraticCurveTo(x, y + h, x, y + h - r);
        ctx.lineTo(x, y + r);
        ctx.quadraticCurveTo(x, y, x + r, y);
        ctx.closePath();
    }
    
    /**
     * Перерисовывает все изображения и элементы выделения.
     */
    redraw() {
        this.imageCtx.clearRect(0, 0, this.imageCanvas.width, this.imageCanvas.height);
        
        const prevOp = this.imageCtx.globalCompositeOperation;
        this.imageCtx.globalCompositeOperation = 'source-over';
        
        // Рисуем сами изображения
        this.imagesList.forEach(imgObj => {
            this.imageCtx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height);
        });
        
        // Рисуем выделение поверх активного изображения
        if (this.activeImage) {
            const img = this.activeImage;
            const ctx = this.imageCtx;
            
            // Сохраняем состояние, чтобы тень не влияла на другие отрисовки
            ctx.save();
            
            // Рамка выделения
            ctx.shadowColor = COLORS.shadowColor;
            ctx.shadowBlur = 8;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 2;
            
            ctx.strokeStyle = COLORS.selectionStroke;
            ctx.lineWidth = SELECTION_LINE_WIDTH;
            
            const pad = SELECTION_LINE_WIDTH / 2 + 1;
            this.drawRoundedRect(
                ctx,
                img.x - pad,
                img.y - pad,
                img.width + pad * 2,
                img.height + pad * 2,
                CORNER_RADIUS
            );
            ctx.stroke();
            
            ctx.shadowColor = 'transparent';
            ctx.shadowBlur = 0;
            ctx.shadowOffsetX = 0;
            ctx.shadowOffsetY = 0;
            
            // Угловые маркеры
            const handles = this.getHandlePositions(img);
            for (const pos of Object.values(handles)) {
                ctx.beginPath();
                ctx.arc(pos.x, pos.y, HANDLE_RADIUS, 0, Math.PI * 2);
                ctx.fillStyle = COLORS.handleFill;
                ctx.fill();
                ctx.lineWidth = 1.5;
                ctx.strokeStyle = COLORS.handleStroke;
                ctx.stroke();
            }
            
            ctx.restore();
        }
        
        this.imageCtx.globalCompositeOperation = prevOp;
    }
    
    /**
     * Очищает все изображения.
     */
    clear() {
        this.imageCtx.clearRect(0, 0, this.imageCanvas.width, this.imageCanvas.height);
        this.imagesList = [];
        this.activeImage = null;
        this.nextImageId = 0;
        this.activeHandle = null;
    }
    
    /**
     * Адаптирует размер canvas под родительский контейнер.
     */
    resizeToDisplaySize() {
        const wrapper = this.imageCanvas.parentElement;
        if (!wrapper) return;
        
        const width = wrapper.clientWidth;
        const height = wrapper.clientHeight;
        
        this.imageCanvas.width = width;
        this.imageCanvas.height = height;
        
        this.redraw();
    }
}