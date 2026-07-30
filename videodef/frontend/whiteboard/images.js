/**
 * Модуль для управления изображениями на canvas.
 * Управляет загрузкой, перемещением, изменением размера и удалением изображений.
 */

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
        this.dragOffset = { x: 0, y: 0 };
        
        // Флаг для синхронизации отправки с частотой кадров браузера (requestAnimationFrame).
        // Предотвращает спам сети сообщениями при движении мыши (60+ раз в секунду), 
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
                return 'nwse-resize';
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
     * Проверяет, находится ли курсор над маркером изменения размера.
     */
    overResizeHandle(x, y, imgObj) {
        const size = 10;
        const handleX = imgObj.x + imgObj.width - size / 2;
        const handleY = imgObj.y + imgObj.height - size / 2;
        return x >= handleX && x <= handleX + size &&
               y >= handleY && y <= handleY + size;
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
        
        if (this.overResizeHandle(x, y, this.activeImage)) {
            this.isResizing = true;
            this.dragOffset = {
                startX: x,
                startY: y,
                startImageX: this.activeImage.x,
                startImageY: this.activeImage.y,
                startWidth: this.activeImage.width,
                startHeight: this.activeImage.height
            };
            return 'resize';
        } else {
            this.isDragging = true;
            this.dragOffset = {
                x: x - this.activeImage.x,
                y: y - this.activeImage.y
            };
            return 'drag';
        }
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
            let newWidth = this.dragOffset.startWidth + (x - this.dragOffset.startX);
            let newHeight = this.dragOffset.startHeight + (y - this.dragOffset.startY);
            this.activeImage.width = Math.max(20, newWidth);
            this.activeImage.height = Math.max(20, newHeight);
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
        }
        
        this.imageUpdateScheduled = false;
        return result;
    }
    
    /**
     * Получает курсор для текущей позиции.
     */
    getCursorForPosition(x, y, currentTool) {
        const hoveredImage = this.getImageAt(x, y);
        
        if (hoveredImage && currentTool !== 'pen' && currentTool !== 'eraser') {
            if (this.overResizeHandle(x, y, hoveredImage)) {
                return 'nwse-resize';
            }
            return 'move';
        }
        
        return (currentTool === 'pen' || currentTool === 'eraser') ? 'crosshair' : 'default';
    }
    
    /**
     * Перерисовывает все изображения.
     */
    redraw() {
        this.imageCtx.clearRect(0, 0, this.imageCanvas.width, this.imageCanvas.height);
        
        const prevOp = this.imageCtx.globalCompositeOperation;
        this.imageCtx.globalCompositeOperation = 'source-over';
        
        this.imagesList.forEach(imgObj => {
            this.imageCtx.drawImage(imgObj.img, imgObj.x, imgObj.y, imgObj.width, imgObj.height);
            
            if (this.activeImage && this.activeImage.id === imgObj.id) {
                this.imageCtx.strokeStyle = 'blue';
                this.imageCtx.lineWidth = 2;
                this.imageCtx.strokeRect(imgObj.x - 1, imgObj.y - 1, imgObj.width + 2, imgObj.height + 2);
                this.drawResizeHandle(imgObj);
            }
        });
        
        this.imageCtx.globalCompositeOperation = prevOp;
    }
    
    /**
     * Рисует маркер изменения размера.
     */
    drawResizeHandle(imgObj) {
        const size = 10;
        this.imageCtx.fillStyle = '#007bff';
        this.imageCtx.strokeStyle = 'white';
        this.imageCtx.lineWidth = 1;
        this.imageCtx.fillRect(imgObj.x + imgObj.width - size / 2, imgObj.y + imgObj.height - size / 2, size, size);
        this.imageCtx.strokeRect(imgObj.x + imgObj.width - size / 2, imgObj.y + imgObj.height - size / 2, size, size);
    }
    
    /**
     * Очищает все изображения.
     */
    clear() {
        this.imageCtx.clearRect(0, 0, this.imageCanvas.width, this.imageCanvas.height);
        this.imagesList = [];
        this.activeImage = null;
        this.nextImageId = 0;
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