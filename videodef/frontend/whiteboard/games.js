/**
 * Модуль для управления игровыми элементами на доске.
 * Управляет созданием, перемещением, изменением размера и удалением игр.
 */

import { makeDraggable, makeResizable } from '../common/utils.js';

/**
 * Класс для управления игровыми элементами.
 */
export class GameManager {
    /**
     * Создает экземпляр GameManager.
     * 
     * @param {Object} options - Опции
     * @param {Function} options.onGameChange - Callback при изменении игры
     */
    constructor(options = {}) {
        this.onGameChange = options.onGameChange || null;
        
        this.gameElements = {};
        this.nextGameElementId = 0;
        this.activeGameId = null; // Отслеживаем активную игру
    }
    
    /**
     * Создает игровой элемент локально.
     * 
     * @param {string} id - Уникальный ID элемента
     * @param {string} gameName - Название игры
     * @param {number} x - Координата X
     * @param {number} y - Координата Y
     * @param {number} width - Ширина
     * @param {number} height - Высота
     * @returns {HTMLDivElement} - Созданный элемент
     */
    createGameElement(id, gameName, x, y, width, height) {
        if (this.gameElements[id]) {
            console.warn(`Game element with id ${id} already exists.`);
            return this.gameElements[id];
        }
        
        const gameWrapper = document.createElement('div');
        gameWrapper.className = 'paste-game-wrapper';
        gameWrapper.style.left = x + 'px';
        gameWrapper.style.top = y + 'px';
        gameWrapper.style.width = width + 'px';
        gameWrapper.style.height = height + 'px';
        gameWrapper.dataset.gameName = gameName;
        gameWrapper.dataset.id = id;
        
        // Флаги для отслеживания состояния перетаскивания/изменения размера
        gameWrapper.isDragging = false;
        gameWrapper.isResizing = false;
        
        const closeBtn = document.createElement('button');
        closeBtn.className = 'paste-game-close';
        closeBtn.textContent = '×';
        closeBtn.onclick = () => this.deleteGameElement(id);
        
        gameWrapper.appendChild(closeBtn);
        document.querySelector('.canvas-wrapper').appendChild(gameWrapper);
        
        // Делаем элемент перетаскиваемым и изменяемым по размеру
        makeDraggable(gameWrapper, 
            (newX, newY) => {
                gameWrapper.isDragging = true;
                if (this.onGameChange) {
                    this.onGameChange('drag_update', { id, x: newX, y: newY });
                }
            },
            (finalX, finalY) => {
                gameWrapper.isDragging = false;
                if (this.onGameChange) {
                    this.onGameChange('move', { id, x: finalX, y: finalY });
                }
            }
        );
        
        makeResizable(gameWrapper,
            (newWidth, newHeight) => {
                gameWrapper.isResizing = true;
                if (this.onGameChange) {
                    this.onGameChange('resize_update', { 
                        id, 
                        x: parseFloat(gameWrapper.style.left),
                        y: parseFloat(gameWrapper.style.top),
                        width: newWidth, 
                        height: newHeight 
                    });
                }
            },
            (finalWidth, finalHeight) => {
                gameWrapper.isResizing = false;
                if (this.onGameChange) {
                    this.onGameChange('resize', { 
                        id, 
                        x: parseFloat(gameWrapper.style.left),
                        y: parseFloat(gameWrapper.style.top),
                        width: finalWidth, 
                        height: finalHeight 
                    });
                }
            }
        );
        
        gameWrapper.addEventListener('mousedown', (e) => {
            if (e.target.closest('.paste-game-close') || e.target.classList.contains('resize-handle')) {
                return;
            }
            
            // Если эта игра уже активна, просто поднимаем z-index
            if (this.activeGameId === id) {
                gameWrapper.style.zIndex = (parseInt(window.getComputedStyle(gameWrapper).zIndex) || 0) + 1;
            } else {
                // Если другая игра была активна, снимаем с нее фокус
                if (this.activeGameId && this.gameElements[this.activeGameId]) {
                    this.blurGame(this.activeGameId);
                }
                
                // Фокусируем новую игру
                this.setActiveGame(id);
            }
            
            e.stopPropagation();
        });
        
        this.gameElements[id] = gameWrapper;
        
        return gameWrapper;
    }
    
    /**
     * Удаляет игровой элемент.
     * 
     * @param {string} id - ID элемента
     */
    deleteGameElement(id) {
        const gameWrapper = this.gameElements[id];
        if (gameWrapper) {
            if (this.activeGameId === id) {
                this.activeGameId = null;
                if (this.onGameChange) {
                    this.onGameChange('blur', { id });
                }
            }
            
            gameWrapper.remove();
            delete this.gameElements[id];
            
            if (this.onGameChange) {
                this.onGameChange('delete', { id });
            }
        }
    }
    
    /**
     * Обновляет позицию игрового элемента.
     * 
     * @param {string} id - ID элемента
     * @param {number} x - Координата X
     * @param {number} y - Координата Y
     */
    updateGamePosition(id, x, y) {
        const gameWrapper = this.gameElements[id];
        if (gameWrapper) {
            gameWrapper.style.left = x + 'px';
            gameWrapper.style.top = y + 'px';
        }
    }
    
    /**
     * Обновляет размер игрового элемента.
     * 
     * @param {string} id - ID элемента
     * @param {number} x - Координата X
     * @param {number} y - Координата Y
     * @param {number} width - Ширина
     * @param {number} height - Высота
     */
    updateGameSize(id, x, y, width, height) {
        const gameWrapper = this.gameElements[id];
        if (gameWrapper) {
            gameWrapper.style.left = x + 'px';
            gameWrapper.style.top = y + 'px';
            gameWrapper.style.width = width + 'px';
            gameWrapper.style.height = height + 'px';
        }
    }
    
    /**
     * Устанавливает активный игровой элемент.
     * 
     * @param {string} id - ID элемента
     */
    setActiveGame(id) {
        // Снимаем активность со всех остальных
        Object.values(this.gameElements).forEach(wrapper => {
            if (wrapper.dataset.id !== id) {
                wrapper.classList.remove('active-game');
                wrapper.style.borderColor = '';
                wrapper.style.zIndex = '';
            }
        });
        
        const gameWrapper = this.gameElements[id];
        if (gameWrapper) {
            this.activeGameId = id;
            gameWrapper.classList.add('active-game');
            gameWrapper.style.borderColor = 'blue';
            gameWrapper.style.zIndex = '100';
            
            if (this.onGameChange) {
                this.onGameChange('focus', { id });
            }
        }
    }
    
    /**
     * Снимает выделение с игрового элемента.
     * 
     * @param {string} id - ID элемента
     */
    blurGame(id) {
        const gameWrapper = this.gameElements[id];
        if (gameWrapper) {
            gameWrapper.classList.remove('active-game');
            gameWrapper.style.borderColor = '';
            gameWrapper.style.zIndex = '';
            
            if (this.activeGameId === id) {
                this.activeGameId = null;
            }
            
            if (this.onGameChange) {
                this.onGameChange('blur', { id });
            }
        }
    }
    
    /**
     * Получает активный игровой элемент.
     * 
     * @returns {HTMLDivElement|null} - Активный элемент или null
     */
    getActiveGame() {
        if (this.activeGameId && this.gameElements[this.activeGameId]) {
            return this.gameElements[this.activeGameId];
        }
        return null;
    }
    
    /**
     * Очищает все игровые элементы.
     */
    clear() {
        for (const id in this.gameElements) {
            if (this.gameElements.hasOwnProperty(id)) {
                this.gameElements[id].remove();
            }
        }
        this.gameElements = {};
        this.nextGameElementId = 0;
        this.activeGameId = null;
    }
    
    /**
     * Получает следующий ID для игрового элемента.
     * 
     * @returns {string} - Уникальный ID
     */
    getNextGameId() {
        return `game-${this.nextGameElementId++}`;
    }
    
    /**
     * Обновляет счетчик ID, чтобы избежать коллизий.
     * 
     * @param {number} id - ID от другого клиента
     */
    updateNextGameId(id) {
        const numericId = parseInt(id.split('-')[1]);
        if (!isNaN(numericId) && numericId >= this.nextGameElementId) {
            this.nextGameElementId = numericId + 1;
        }
    }
}