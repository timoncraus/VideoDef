/**
 * Класс игры "Поиск пар", наследующий от базового класса GameBase.
 * Инкапсулирует логику игры и взаимодействие с WebSocket.
 */
import { GameBase } from '../common/game-base.js';
import { getGameParts, initializeBoard, applyRemoteCardClick, stopTimer } from './logic.js';

/**
 * Класс, представляющий экземпляр игры "Поиск пар".
 * Наследует общую логику WebSocket и управления состоянием от GameBase.
 */
export class MemoryGameGame extends GameBase {
    /**
     * Создаёт экземпляр игры "Поиск пар".
     * 
     * @param {Object} config - Конфигурация
     * @param {HTMLElement} config.container - DOM-контейнер для игры
     * @param {string} config.gameId - Уникальный ID экземпляра игры
     * @param {string} config.boardRoomName - Имя комнаты доски
     * @param {string} config.name - Название игры
     */
    constructor(config = {}) {
        super({
            ...config,
            type: 'memory_game'
        });
        
        // Получаем базовые параметры игры
        this.params = getGameParts();
        
        // Создаём контейнер для игры
        this.gameContainer = config.container || document.createElement('div');
        this.gameContainer.className = 'memory-game-wrapper';
        
        // Инициализация параметров игры
        this.params.onWhiteboard = !!config.boardRoomName;
        this.params.gameId = config.gameId || null;
        this.params.boardRoomName = config.boardRoomName || null;
        this.params.name = config.name || `Поиск пар ${config.gameId ? config.gameId.split('-')[1] || '' : ''}`;
    }
    
    /**
     * Обработчик открытия WebSocket соединения.
     * Переопределяет абстрактный метод GameBase.
     * Транслирует состояние только если игра уже запущена (есть layout),
     * иначе запрашивает состояние у других клиентов (позднее подключение).
     */
    onWebSocketOpen() {
        console.log(`[MemoryGameGame:${this.gameId}] WebSocket connected`);
        
        if (this.params.card_layout && this.params.card_layout.length > 0) {
            this.broadcastState();
        } else {
            this.sendWebSocketMessage({ type: 'request_state' });
        }
    }
    
    /**
     * Обработчик входящих WebSocket сообщений.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @param {Object} data - Полученные данные
     */
    onWebSocketMessage(data) {
        if (data.type === 'request_state') {
            // Ответ только если есть реальное состояние
            if (this.params.card_layout && this.params.card_layout.length > 0) {
                this.broadcastState();
            }
            return;
        }
        
        if (data.type === 'game_state_change') {
            const receivedState = data.gameState;
            Object.assign(this.params, receivedState);
            
            // Если используются пользовательские изображения, создаём объекты
            if (receivedState.isCustomSet) {
                this.params.customImageObjects = (receivedState.selectedImageSet || []).map(url => ({ url, file: null }));
            }
            
            const receivedHasLayout = receivedState.card_layout && receivedState.card_layout.length > 0;
            
            if (receivedHasLayout) {
                // Игра запущена — применяем существующий layout
                initializeBoard(this.gameContainer, this.params, true);
            } else {
                stopTimer(this.params);
                this.gameContainer.innerHTML = '<p class="initial-message">Ожидание начала игры. Нажмите "Перемешать".</p>';
            }
            
            // Если эта игра активна, настраиваем UI
            const activeGameWrapper = document.querySelector('.paste-game-wrapper.active-game');
            if (activeGameWrapper && activeGameWrapper.memoryGameGame === this) {
                if (typeof window.setupWhiteboardMemoryGame === 'function') {
                    window.setupWhiteboardMemoryGame(activeGameWrapper);
                }
            }
        } else if (data.type === 'card_click') {
            applyRemoteCardClick(this.gameContainer, this.params, data.cardDomIndex);
        }
    }
    
    /**
     * Инициализирует игровое поле.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @param {HTMLElement} container - Контейнер для игры
     * @param {boolean} useExistingState - Использовать ли существующее состояние
     * @returns {boolean} true, если инициализация успешна
     */
    initializeBoard(container, useExistingState = false) {
        if (container) {
            this.gameContainer = container;
        }
        return initializeBoard(this.gameContainer, this.params, useExistingState);
    }
    
    /**
     * Получает текущее состояние игры для сохранения или синхронизации.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @returns {Object} Объект с состоянием игры
     */
    getState() {
        const imageSetToSend = this.params.isCustomSet 
            ? this.params.customImageObjects.map(obj => obj.url) 
            : this.params.selectedImageSet;
        
        return {
            id: this.params.id,
            name: this.params.name,
            pairCount: this.params.pairCount,
            selectedImageSet: imageSetToSend,
            isCustomSet: this.params.isCustomSet,
            card_layout: this.params.card_layout,
            attempts: this.params.attempts
        };
    }
    
    /**
     * Применяет загруженное состояние игры.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @param {Object} state - Загруженное состояние
     */
    applyState(state) {
        Object.assign(this.params, state);
        const useExistingLayout = state.card_layout && state.card_layout.length > 0;
        initializeBoard(this.gameContainer, this.params, useExistingLayout);
    }
    
    /**
     * Отправляет текущее состояние игры через WebSocket всем подключённым клиентам.
     */
    broadcastState() {
        if (this.params.onWhiteboard && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.sendWebSocketMessage({ 
                type: 'game_state_change', 
                gameState: this.getState() 
            });
        }
    }
    
    /**
     * Очищает ресурсы игры.
     * Переопределяет метод GameBase.
     */
    destroy() {
        super.destroy();
        if (this.gameContainer) {
            this.gameContainer.innerHTML = '';
        }
    }
}