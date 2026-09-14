/**
 * Главный модуль интерактивной доски.
 * Интегрирует все компоненты (canvas, images, games, ui, websocket).
 */

import { CanvasDrawing } from './canvas.js';
import { ImageManager } from './images.js';
import { GameManager } from './games.js';
import { WhiteboardUI } from './ui.js';
import { WhiteboardWebSocket } from './websocket.js';
import { getPuzzleSettingsHTML } from './settings/puzzle-settings.js';
import { getMemoryGameSettingsHTML } from './settings/memory-settings.js';
import { getSoundLotoSettingsHTML } from './settings/sound-loto-settings.js';
import { createPuzzleOnBoard, setupWhiteboardPuzzleSaveLoad } from '../puzzle/index.js';
import { createMemoryGameOnBoard, setupWhiteboardMemoryGame } from '../memory_game/index.js';
import { createSoundLotoOnBoard, setupWhiteboardSoundLoto } from '../sound_loto/index.js';
import {
    collectBoardState, saveBoard,
    loadBoardsList, loadBoardDetail,
    restoreBoard, closeAllGameWebSockets
} from './board-save-load.js';

/**
 * Класс интерактивной доски.
 */
class Whiteboard {
    constructor() {
        // Флаг для предотвращения бесконечных петель сообщений в локальном режиме
        this.isProcessingRemoteMessage = false;
        this.currentBoardId = null;
        this.currentBoardName = null;
        this.init();
    }
    
    /**
     * Инициализирует все компоненты доски.
     */
    init() {
        // Получаем элементы canvas
        const imageCanvas = document.getElementById('image-layer');
        const drawCanvas = document.getElementById('draw-layer');
        
        if (!imageCanvas || !drawCanvas) {
            console.error('Canvas элементы не найдены');
            return;
        }
        
        // Получаем имя комнаты для WebSocket
        const videosElement = document.getElementById('videos');
        const roomName = videosElement ? videosElement.dataset.roomName : null;
        
        // Инициализируем компоненты
        this.canvasDrawing = new CanvasDrawing(drawCanvas, {
            onDraw: (x0, y0, x1, y1, color, lineWidth, tool) => {
                this.canvasDrawing.addToStrokeHistory({ x0, y0, x1, y1, color, lineWidth, tool });
                if (this.ws && this.ws.isConnected()) {
                    this.ws.send({ type: 'draw', x0, y0, x1, y1, color, lineWidth, tool });
                }
            }
        });
        
        this.imageManager = new ImageManager(imageCanvas, {
            onImageChange: (action, data) => {
                if (this.ws && this.ws.isConnected()) {
                    if (action === 'add') {
                        this.ws.send({
                            type: 'image',
                            id: data.id, dataURL: data.dataURL,
                            x: data.x, y: data.y, width: data.width, height: data.height
                        });
                    } else if (action === 'delete') {
                        this.ws.send({ type: 'delete_image', id: data.id });
                    }
                }
            },
            onImageDragUpdate: (id, x, y) => {
                if (this.ws && this.ws.isConnected()) {
                    this.ws.send({ type: 'image_drag_update', id, x, y });
                }
            },
            onImageResizeUpdate: (id, x, y, width, height) => {
                if (this.ws && this.ws.isConnected()) {
                    this.ws.send({ type: 'image_resize_update', id, x, y, width, height });
                }
            }
        });
        
        this.gameManager = new GameManager({
            onGameChange: (action, data) => {
                if (this.isProcessingRemoteMessage) return;

                // Локальное обновление UI при фокусе/блюре
                if (action === 'focus') {
                    this.handleGameFocusUI(data.id);
                } else if (action === 'blur') {
                    if (!this.gameManager.getActiveGame()) {
                        this.ui.clearDynamicSettings();
                    }
                }

                if (this.ws && (this.ws.isConnected() || this.ws.isLocalModeActive())) {
                    const messageType = {
                        'drag_update': 'game_element_drag_update',
                        'move': 'move_game_element',
                        'resize_update': 'game_element_resize_update',
                        'resize': 'resize_game_element',
                        'focus': 'game_element_focus',
                        'blur': 'game_element_blur',
                        'delete': 'delete_game_element'
                    }[action] || action;
                    this.ws.send({ type: messageType, ...data });
                }
            }
        });
        
        this.ui = new WhiteboardUI({
            onSettingsToggle: () => {
                this.canvasDrawing.resizeToDisplaySize();
                this.imageManager.resizeToDisplaySize();
            },
            onToolChange: (tool, value) => {
                if (tool === 'pen' || tool === 'eraser') {
                    this.canvasDrawing.setTool(tool);
                    this.imageManager.clearSelection();
                    this.blurActiveGame();
                } else if (tool === 'color') {
                    this.canvasDrawing.setColor(value);
                } else if (tool === 'thickness') {
                    this.canvasDrawing.setLineWidth(value);
                }
            },
            onGameSelect: (gameName) => this.addGame(gameName),
            onClear: () => this.clearBoard(),
            onSaveBoard: () => this.openSaveBoardModal(),
            onLoadBoard: () => this.openLoadBoardModal()
        });
        // Инициализируем WebSocket
        this.ws = new WhiteboardWebSocket(roomName, {
            onMessage: (data) => this.handleIncomingData(data),
            onLocalMessage: (data) => this.handleIncomingData(data)
        });
        
        // Загрузка изображений
        const imgUpload = document.getElementById('img-upload');
        if (imgUpload) {
            imgUpload.addEventListener('change', (e) => this.handleImageUpload(e));
        }
        
        // Обработка событий canvas
        this.setupCanvasEventListeners(drawCanvas);
        
        // Обработка клавиш
        window.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Адаптация размера canvas
        window.addEventListener('load', () => {
            this.canvasDrawing.resizeToDisplaySize();
            this.imageManager.resizeToDisplaySize();
            
            if (document.getElementById('pen_btn')) {
                this.ui.setActiveTool('pen_btn');
                this.canvasDrawing.setTool('pen');
            }
        });
        
        window.addEventListener('resize', () => {
            this.canvasDrawing.resizeToDisplaySize();
            this.imageManager.resizeToDisplaySize();
        });
        
        console.log('Интерактивная доска инициализирована');
    }
    
    /**
     * Настраивает обработчики событий для canvas.
     */
    setupCanvasEventListeners(drawCanvas) {
        drawCanvas.addEventListener('mousedown', (e) => this.handleCanvasMouseDown(e));
        drawCanvas.addEventListener('mouseup', (e) => this.handleCanvasMouseUp(e));
        drawCanvas.addEventListener('mousemove', (e) => this.handleCanvasMouseMove(e));
    }
    
    /**
     * Обрабатывает нажатие кнопки мыши на canvas.
     */
    handleCanvasMouseDown(e) {
        const { x, y } = this.canvasDrawing.getMousePos(e);
        
        // Проверка: клик не на игровом элементе
        if (!e.target.closest('.paste-game-wrapper')) {
            this.blurActiveGame();
        }
        
        // Проверка клика на изображении перед началом рисования
        const dragType = this.imageManager.handleMouseDown(x, y);
        
        if (dragType) {
            this.canvasDrawing.drawCanvas.style.cursor = dragType === 'resize' ? 'nwse-resize' : 'grabbing';
        } else {
            // Клик на пустом месте canvas - разрешаем рисование
            if (this.canvasDrawing.currentTool === 'pen' || this.canvasDrawing.currentTool === 'eraser') {
                this.canvasDrawing.onMouseDown(e);
            } else {
                this.canvasDrawing.drawCanvas.style.cursor = 'default';
            }
        }
    }
    
    /**
     * Обрабатывает отпускание кнопки мыши на canvas.
     */
    handleCanvasMouseUp(e) {
        // Завершение рисования
        this.canvasDrawing.onMouseUp();
        
        // Завершение перетаскивания/изменения размера изображения
        const dragResult = this.imageManager.handleMouseUp();
        if (dragResult && this.ws && this.ws.isConnected()) {
            this.ws.send({
                type: dragResult.type === 'move' ? 'move_image' : 'resize_image',
                ...dragResult
            });
        }
        this.canvasDrawing.drawCanvas.style.cursor = 
            (this.canvasDrawing.currentTool === 'pen' || this.canvasDrawing.currentTool === 'eraser') 
                ? 'crosshair' : 'default';
    }
    
    /**
     * Обрабатывает движение мыши на canvas.
     */
    handleCanvasMouseMove(e) {
        const { x, y } = this.canvasDrawing.getMousePos(e);
        
        // Проверка: не тащится ли DOM-элемент игры
        const someonesDraggingDOM = Object.values(this.gameManager.gameElements).some(
            el => el.isDragging || el.isResizing
        );
        
        if (someonesDraggingDOM) return;
        
        // Рисование
        if (this.canvasDrawing.drawing) {
            this.canvasDrawing.onMouseMove(e);
        } else if (this.imageManager.isDragging || this.imageManager.isResizing) {
            const cursor = this.imageManager.handleMouseMove(x, y);
            if (cursor) this.canvasDrawing.drawCanvas.style.cursor = cursor;
        } else {
            this.canvasDrawing.drawCanvas.style.cursor = this.imageManager.getCursorForPosition(x, y, this.canvasDrawing.currentTool);
        }
    }

    /**
     * Унифицированный обработчик входящих данных (WS и Локальных).
     */
    async handleIncomingData(data) {
        if (this.isProcessingRemoteMessage) return;
        this.isProcessingRemoteMessage = true;
        try {
            await this.handleWebSocketMessage(data);
        } finally {
            this.isProcessingRemoteMessage = false;
        }
    }
    
    /**
     * Снимает фокус с активной игры.
     */
    blurActiveGame() {
        const activeGame = this.gameManager.getActiveGame();
        if (activeGame) {
            const gameId = activeGame.dataset.id;
            if (this.ws && (this.ws.isConnected() || this.ws.isLocalModeActive())) {
                this.ws.send({ type: 'game_element_blur', id: gameId });
            } else {
                this.gameManager.blurGame(gameId);
                this.ui.clearDynamicSettings();
            }
        }
    }
    
    /**
     * Обрабатывает входящие WebSocket сообщения.
     */
    async handleWebSocketMessage(data) {
        switch (data.type) {
            case 'draw':
                this.canvasDrawing.drawLine(data.x0, data.y0, data.x1, data.y1, data.color, data.lineWidth, data.tool);
                this.canvasDrawing.addToStrokeHistory({
                    x0: data.x0, y0: data.y0, x1: data.x1, y1: data.y1,
                    color: data.color, lineWidth: data.lineWidth, tool: data.tool
                });
                break;
            case 'image':
                this.imageManager.addImage(data.dataURL, data.x, data.y, data.width, data.height, data.id, true);
                break;
            case 'clear':
                this.canvasDrawing.clear();
                this.canvasDrawing.clearStrokeHistory();
                this.imageManager.clear();
                closeAllGameWebSockets(this.gameManager);
                this.gameManager.clear();
                this.ui.clearDynamicSettings();
                break;
            case 'delete_image':
                this.imageManager.deleteImage(data.id);
                break;
            case 'move_image':
            case 'image_drag_update':
                this.imageManager.updateImagePosition(data.id, data.x, data.y);
                break;
            case 'resize_image':
            case 'image_resize_update':
                this.imageManager.updateImageSize(data.id, data.x, data.y, data.width, data.height);
                break;
            case 'add_game_element':
                this.addGameElement(data.id, data.gameName, data.x, data.y, data.width, data.height);
                this.gameManager.setActiveGame(data.id);
                this.handleGameFocusUI(data.id);
                break;
            case 'delete_game_element': {
                const gameWrapper = this.gameManager.gameElements[data.id];
                if (gameWrapper) {
                    if (gameWrapper.puzzleWebSocket?.readyState === WebSocket.OPEN) {
                        gameWrapper.puzzleWebSocket.close();
                    }
                    if (gameWrapper.classList.contains('active-game')) {
                        this.ui.clearDynamicSettings();
                    }
                    this.gameManager.deleteGameElement(data.id);
                }
                break;
            }
            case 'move_game_element':
            case 'game_element_drag_update':
                this.gameManager.updateGamePosition(data.id, data.x, data.y);
                break;
            case 'resize_game_element':
            case 'game_element_resize_update':
                this.gameManager.updateGameSize(data.id, data.x, data.y, data.width, data.height);
                break;
            case 'game_element_focus':
                this.gameManager.setActiveGame(data.id);
                this.handleGameFocusUI(data.id);
                break;
            case 'game_element_blur':
                this.gameManager.blurGame(data.id);
                if (!this.gameManager.getActiveGame()) {
                    this.ui.clearDynamicSettings();
                }
                break;
            case 'board_restore':
                await restoreBoard(data.boardData, this);
                this.currentBoardId = data.boardId || null;
                this.currentBoardName = data/boardData?.name || null;
                break;
        }
    }

    /**
     * Вспомогательный метод для обновления UI настроек при фокусе игры.
     */
    handleGameFocusUI(gameId) {
        const focusedWrapper = this.gameManager.gameElements[gameId];
        if (focusedWrapper) {
            this.updateGameSettings(focusedWrapper.dataset.gameName);

            // Инициализируем логику игры (сохранение/загрузка)
            if (focusedWrapper.dataset.gameName === 'puzzles') {
                setupWhiteboardPuzzleSaveLoad(focusedWrapper);
            } else if (focusedWrapper.dataset.gameName === 'memory-game') {
                setupWhiteboardMemoryGame(focusedWrapper);
            } else if (focusedWrapper.dataset.gameName === 'sound-loto') {
                setupWhiteboardSoundLoto(focusedWrapper);
            }
        }
    }
    
    /**
     * Добавляет игру на доску.
     */
    addGame(gameName) {
        const gameId = this.gameManager.getNextGameId();
        const initialX = 100, initialY = 100, initialWidth = 400, initialHeight = 300;
        
        this.addGameElement(gameId, gameName, initialX, initialY, initialWidth, initialHeight);
        this.gameManager.setActiveGame(gameId);
        this.handleGameFocusUI(gameId);
        
        // Отправляем сообщение другим клиентам
        if (this.ws && (this.ws.isConnected() || this.ws.isLocalModeActive())) {
            this.ws.send({
                type: 'add_game_element',
                id: gameId, gameName,
                x: initialX, y: initialY, width: initialWidth, height: initialHeight
            });
            
            // Фокусируем на новой игре
            this.ws.send({ type: 'game_element_focus', id: gameId });
        }
    }
    
    /**
     * Добавляет игровой элемент локально.
     */
    addGameElement(id, gameName, x, y, width, height) {
        const gameWrapper = this.gameManager.createGameElement(id, gameName, x, y, width, height);
        
        if (gameWrapper) {
            const videosElement = document.getElementById('videos');
            const roomName = videosElement ? videosElement.dataset.roomName : null;
            
            if (gameName === 'puzzles' && !gameWrapper.dataset.puzzleInitialized) {
                createPuzzleOnBoard(gameWrapper, roomName, id);
                gameWrapper.dataset.puzzleInitialized = 'true';
            } else if (gameName === 'memory-game' && !gameWrapper.dataset.memoryGameInitialized) {
                createMemoryGameOnBoard(gameWrapper, roomName, id);
                gameWrapper.dataset.memoryGameInitialized = 'true';
            } else if (gameName === 'sound-loto' && !gameWrapper.dataset.soundLotoInitialized) {
                createSoundLotoOnBoard(gameWrapper, roomName, id);
                gameWrapper.dataset.soundLotoInitialized = 'true';
            }
        }
    }
    
    /**
     * Обрабатывает загрузку изображения.
     */
    handleImageUpload(e) {
        const file = e.target.files[0];
        if (!file) return;
        
        const reader = new FileReader();
        reader.onload = () => {
            const dataURL = reader.result;
            const img = new Image();
            img.onload = () => {
                let width = img.naturalWidth > 400 ? 400 : img.naturalWidth;
                let height = img.naturalHeight > 300 ? (img.naturalHeight * (400 / img.naturalWidth)) : img.naturalHeight;
                
                if (width > 400 || height > 300) {
                    const aspectRatio = width / height;
                    if (width > height) {
                        width = 400;
                        height = 400 / aspectRatio;
                    } else {
                        height = 300;
                        width = 300 * aspectRatio;
                    }
                }
                
                this.imageManager.addImage(dataURL, 50, 50, width, height);
            };
            img.src = dataURL;
        };
        reader.readAsDataURL(file);
        e.target.value = '';
    }
    
    /**
     * Обрабатывает нажатие клавиш.
     */
    handleKeyDown(e) {
        if (e.key === 'Delete' || e.key === 'Backspace') {
            if (this.imageManager.activeImage && !this.isInputActive()) {
                e.preventDefault();
                this.imageManager.deleteImage(this.imageManager.activeImage.id);
            }
        }
    }
    
    /**
     * Проверяет, активно ли поле ввода.
     */
    isInputActive() {
        const activeEl = document.activeElement;
        return activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable);
    }
    
    /**
     * Очищает доску.
     */
    clearBoard() {
        this.canvasDrawing.clear();
        this.canvasDrawing.clearStrokeHistory();
        this.imageManager.clear();
        closeAllGameWebSockets(this.gameManager);
        this.gameManager.clear();
        this.ui.clearDynamicSettings();
        
        const imgUpload = document.getElementById('img-upload');
        if (imgUpload) imgUpload.value = '';
        
        // Отправляем сообщение другим клиентам
        if (this.ws && (this.ws.isConnected() || this.ws.isLocalModeActive())) {
            this.ws.send({ type: 'clear' });
        }
        
        console.log("Доска очищена.");
    }
    
    /**
     * Обновляет панель настроек для выбранной игры.
     */
    updateGameSettings(gameName) {
        this.ui.clearDynamicSettings();
        
        const settingsPanel = document.querySelector('.settings-panel');
        if (!settingsPanel) return;
        
        const settingsContainer = document.createElement('div');
        settingsContainer.className = 'dynamic-setting';
        
        if (gameName === 'puzzles') {
            const imagesPath = typeof images !== 'undefined' ? images : '/static/images';
            settingsContainer.innerHTML = getPuzzleSettingsHTML(imagesPath);
        } else if (gameName === 'memory-game') {
            settingsContainer.innerHTML = getMemoryGameSettingsHTML();
        } else if (gameName === 'sound-loto') {
            settingsContainer.innerHTML = getSoundLotoSettingsHTML();
        }
        settingsPanel.appendChild(settingsContainer);
    }
    
    openSaveBoardModal() {
        const modal = document.getElementById('save-board-modal');
        const nameInput = document.getElementById('board-save-name-input');
        const confirmBtn = document.getElementById('save-board-confirm-btn');
        const cancelBtn = document.getElementById('save-board-cancel-btn');
        const closeBtn = modal.querySelector('.modal-close-btn');
        const titleEl = modal.querySelector('h2');

        const isUpdate = !!this.currentBoardId;
        if (titleEl) titleEl.textContent = isUpdate ? 'Обновить доску' : 'Сохранить доску';
        confirmBtn.textContent = isUpdate ? 'Обновить' : 'Сохранить';
        nameInput.value = this.currentBoardName || '';
        confirmBtn.disabled = nameInput.value.trim().length === 0;
        this.ui.showModal('save-board-modal');
        
        const onInput = () => {
            confirmBtn.disabled = nameInput.value.trim().length === 0;
        };
        nameInput.removeEventListener('input', nameInput._handler);
        nameInput._handler = onInput;
        nameInput.addEventListener('input', onInput);
        nameInput.focus();
        
        const closeModal = () => {
            this.ui.hideModal('save-board-modal');
            confirmBtn.removeEventListener('click', onConfirm);
            cancelBtn.removeEventListener('click', closeModal);
            closeBtn.removeEventListener('click', closeModal);
        };
        
        const onConfirm = async () => {
            const name = nameInput.value.trim();
            if (!name) return;
            
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Сохранение...';
            
            try {
                const boardState = collectBoardState(this.canvasDrawing, this.imageManager, this.gameManager);
                const result = await saveBoard(name, boardState, this.currentBoardId || null);
                
                if (result.status === 'success') {
                    if (result.board_id) {
                        this.currentBoardId = result.board_id;
                    }
                    this.currentBoardName = name;
                    alert(result.message);
                } else {
                    alert(`Ошибка: ${result.message}`);
                }
            } catch (error) {
                console.error('Ошибка сохранения доски:', error);
                alert('Произошла ошибка при сохранении доски.');
            } finally {
                confirmBtn.textContent = isUpdate ? 'Обновить' : 'Сохранить';
                confirmBtn.disabled = false;
                closeModal();
            }
        };
        
        confirmBtn.addEventListener('click', onConfirm);
        cancelBtn.addEventListener('click', closeModal);
        closeBtn.addEventListener('click', closeModal);
    }
    
    async openLoadBoardModal() {
        const modal = document.getElementById('load-board-modal');
        const listContainer = document.getElementById('load-board-list-container');
        const confirmBtn = document.getElementById('load-board-confirm-btn');
        const cancelBtn = document.getElementById('load-board-cancel-btn');
        const closeBtn = modal?.querySelector('.modal-close-btn');

        if (!modal || !listContainer || !confirmBtn || !cancelBtn) {
            console.error('Не найдены элементы модального окна загрузки доски.');
            return;
        }

        let selectedBoardId = null;
        listContainer.innerHTML = '<p class="text-center text-muted">Загрузка списка досок…</p>';
        confirmBtn.disabled = true;

        const closeModal = () => this.ui.hideModal('load-board-modal');

        const confirmHandler = async () => {
            if (!selectedBoardId) return;
            confirmBtn.disabled = true;
            confirmBtn.textContent = 'Загрузка…';

            try {
                const result = await loadBoardDetail(selectedBoardId);
                if (result.status === 'success') {
                    await restoreBoard(result.board, this);
                    this.currentBoardId = selectedBoardId;
                    this.currentBoardName = result.board.name;
                    if (this.ws && this.ws.isConnected()) {
                        this.ws.send({
                            type: 'board_restore',
                            boardData: result.board,
                            boardId: selectedBoardId
                        });
                    }
                    closeModal();
                } else {
                    alert(result.message || 'Не удалось загрузить доску.');
                }
            } catch (error) {
                console.error('Ошибка загрузки доски:', error);
                alert('Сетевая ошибка при загрузке доски.');
            } finally {
                confirmBtn.textContent = 'Загрузить';
                confirmBtn.disabled = !selectedBoardId;
            }
        };

        const newConfirm = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirm, confirmBtn);
        newConfirm.addEventListener('click', confirmHandler);

        const newCancel = cancelBtn.cloneNode(true);
        cancelBtn.parentNode.replaceChild(newCancel, cancelBtn);
        newCancel.addEventListener('click', closeModal);

        if (closeBtn) {
            const newClose = closeBtn.cloneNode(true);
            closeBtn.parentNode.replaceChild(newClose, closeBtn);
            newClose.addEventListener('click', closeModal);
        }

        modal.onclick = (e) => { if (e.target === modal) closeModal(); };
        this.ui.showModal('load-board-modal');

        try {
            const result = await loadBoardsList();
            if (result.status !== 'success') {
                listContainer.innerHTML = `<p class="text-danger">${result.message || 'Ошибка загрузки.'}</p>`;
                return;
            }

            if (!result.boards || result.boards.length === 0) {
                listContainer.innerHTML = '<p class="text-center text-muted">У вас пока нет сохранённых досок.</p>';
                return;
            }

            const ul = document.createElement('ul');
            result.boards.forEach(board => {
                const li = document.createElement('li');
                const date = new Date(board.updated_at).toLocaleDateString('ru-RU', {
                    day: '2-digit', month: '2-digit', year: 'numeric',
                    hour: '2-digit', minute: '2-digit'
                });
                li.textContent = `${board.name} — ${date}`;
                li.dataset.boardId = board.id;

                li.addEventListener('click', () => {
                    ul.querySelectorAll('li').forEach(item => item.classList.remove('selected'));
                    li.classList.add('selected');
                    selectedBoardId = board.id;
                    document.getElementById('load-board-confirm-btn').disabled = false;
                });
                ul.appendChild(li);
            });

            listContainer.innerHTML = '';
            listContainer.appendChild(ul);
        } catch (error) {
            console.error('Ошибка получения списка досок:', error);
            listContainer.innerHTML = '<p class="text-danger">Сетевая ошибка.</p>';
        }
    }
}

// Инициализация доски при загрузке DOM
document.addEventListener('DOMContentLoaded', () => {
    new Whiteboard();
});