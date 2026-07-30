/**
 * Базовый абстрактный класс для всех игр.
 * Определяет общий интерфейс и предоставляет базовую функциональность.
 */

import { WebSocketManager } from './websocket.js';

/**
 * Абстрактный базовый класс для игр.
 */
export class GameBase {
    /**
     * Создает экземпляр игры.
     * 
     * @param {Object} config - Конфигурация игры
     * @param {string} config.name - Название игры
     * @param {string} config.type - Тип игры (например, 'puzzle', 'memory_game')
     * @param {boolean} config.onWhiteboard - Флаг, находится ли игра на доске
     * @param {string} config.gameId - Уникальный ID экземпляра игры на доске
     * @param {string} config.boardRoomName - Имя комнаты доски
     */
    constructor(config = {}) {
        if (new.target === GameBase) {
            throw new Error("GameBase - абстрактный класс и не может быть инстанциирован напрямую");
        }
        
        this.id = config.id || null;
        this.name = config.name || '';
        this.type = config.type || 'game';
        this.onWhiteboard = config.onWhiteboard || false;
        this.gameId = config.gameId || null;
        this.boardRoomName = config.boardRoomName || null;
        
        this.ws = null;
        this.wsManager = null;
        
        this.container = null;
        this.messageElement = null;
        
        // Ссылка на объект параметров (будет установлена в наследниках)
        this.params = null;
    }
    
    /**
     * Инициализирует WebSocket соединение для синхронизации на доске.
     * Должен быть переопределен в наследниках для специфичной логики.
     */
    initWebSocket() {
        if (!this.onWhiteboard || !this.boardRoomName || !this.gameId) {
            console.log(`[${this.type}] Работа в локальном режиме (без WebSocket)`);
            return;
        }
        
        const wsUrl = `ws://${window.location.host}/ws/${this.type}_on_board/${this.boardRoomName}/${this.gameId}/`;
        
        this.wsManager = new WebSocketManager(wsUrl, {
            onOpen: () => {
                console.log(`[${this.type}] WebSocket подключен для игры ${this.gameId}`);
                
                if (this.params) {
                    this.params.ws = this.wsManager.ws;
                }
                
                this.onWebSocketOpen();
            },
            onMessage: (data) => {
                this.onWebSocketMessage(data);
            },
            onClose: (e) => {
                console.log(`[${this.type}] WebSocket отключен для игры ${this.gameId}`, e.reason);
            },
            onError: (error) => {
                console.error(`[${this.type}] WebSocket ошибка для игры ${this.gameId}:`, error);
            }
        });
        
        this.wsManager.connect();
        this.ws = this.wsManager.ws;
    }
    
    /**
     * Отправляет сообщение через WebSocket.
     * 
     * @param {Object} data - Данные для отправки
     */
    sendWebSocketMessage(data) {
        if (this.wsManager && this.wsManager.isConnected()) {
            this.wsManager.send(data);
        }
    }
    
    /**
     * Закрывает WebSocket соединение.
     */
    closeWebSocket() {
        if (this.wsManager) {
            this.wsManager.close();
            this.wsManager = null;
            this.ws = null;
            if (this.params) this.params.ws = null;
        }
    }
    
    /**
     * Обработчик открытия WebSocket соединения.
     * Должен быть переопределен в наследниках.
     */
    onWebSocketOpen() {
        throw new Error("Метод onWebSocketOpen() должен быть переопределен в наследнике");
    }
    
    /**
     * Обработчик входящих WebSocket сообщений.
     * Должен быть переопределен в наследниках.
     * 
     * @param {Object} data - Полученные данные
     */
    onWebSocketMessage(data) {
        throw new Error("Метод onWebSocketMessage() должен быть переопределен в наследнике");
    }
    
    /**
     * Инициализирует игровое поле.
     * Должен быть переопределен в наследниках.
     * 
     * @param {HTMLElement} container - Контейнер для игры
     * @param {boolean} useExistingState - Использовать ли существующее состояние
     */
    initializeBoard(container, useExistingState = false) {
        throw new Error("Метод initializeBoard() должен быть переопределен в наследнике");
    }
    
    /**
     * Получает текущее состояние игры для сохранения.
     * Должен быть переопределен в наследниках.
     * 
     * @returns {Object} - Объект с состоянием игры
     */
    getState() {
        throw new Error("Метод getState() должен быть переопределен в наследнике");
    }
    
    /**
     * Применяет загруженное состояние игры.
     * Должен быть переопределен в наследниках.
     * 
     * @param {Object} state - Загруженное состояние
     */
    applyState(state) {
        throw new Error("Метод applyState() должен быть переопределен в наследнике");
    }
    
    /**
     * Очищает ресурсы игры.
     */
    destroy() {
        this.closeWebSocket();
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}