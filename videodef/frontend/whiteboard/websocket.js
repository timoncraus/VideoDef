/**
 * Модуль для работы с WebSocket соединениями доски.
 */

import { WebSocketManager } from '../common/websocket.js';

/**
 * Класс для управления WebSocket доски.
 */
export class WhiteboardWebSocket {
    /**
     * Создает экземпляр WhiteboardWebSocket.
     * 
     * @param {string} roomName - Имя комнаты
     * @param {Object} handlers - Обработчики событий
     */
    constructor(roomName, handlers = {}) {
        this.roomName = roomName;
        this.handlers = handlers;
        this.wsManager = null;
        this.isLocalMode = !roomName;
        
        if (roomName) {
            this.connect();
        } else {
            console.warn("roomName для доски не найден. Синхронизация будет отключена. Работа в локальном режиме.");
            this.setupLocalModeStub();
        }
    }
    
    /**
     * Устанавливает WebSocket соединение.
     */
    connect() {
        const wsUrl = `ws://${window.location.host}/ws/whiteboard/${this.roomName}/`;
        console.log(`Доска подключается к комнате: ${this.roomName}`);
        
        this.wsManager = new WebSocketManager(wsUrl, {
            onOpen: () => {
                console.log(`Вебсокет доски подключен к комнате: ${this.roomName}`);
                if (this.handlers.onOpen) this.handlers.onOpen();
            },
            onMessage: (data) => {
                if (this.handlers.onMessage) this.handlers.onMessage(data);
            },
            onClose: () => {
                console.log(`Вебсокет доски отключен от комнаты: ${this.roomName}`);
                if (this.handlers.onClose) this.handlers.onClose();
            },
            onError: (error) => {
                console.error(`Ошибка вебсокета доски для комнаты ${this.roomName}:`, error);
                if (this.handlers.onError) this.handlers.onError(error);
            }
        });

        this.wsManager.connect();
    }
    
    /**
     * Настраивает заглушку для локального режима.
     */
    setupLocalModeStub() {
        this.wsManager = {
            send: (data) => {
                // В локальном режиме обрабатываем сообщения локально
                if (this.handlers.onLocalMessage) {
                    this.handlers.onLocalMessage(data);
                }
            },
            readyState: WebSocket.CLOSED,
            close: () => {},
            isConnected: () => false
        };
    }
    
    /**
     * Отправляет сообщение через WebSocket.
     */
    send(data) {
        if (this.wsManager) {
            if (this.isLocalMode) {
                this.wsManager.send(data);
            } else {
                this.wsManager.send(data);
            }
        }
    }
    
    /**
     * Закрывает WebSocket соединение.
     */
    close() {
        if (this.wsManager && this.wsManager.close) {
            this.wsManager.close();
        }
    }
    
    /**
     * Проверяет, активно ли соединение.
     */
    isConnected() {
        return this.wsManager && (
            typeof this.wsManager.isConnected === 'function' 
                ? this.wsManager.isConnected()
                : this.wsManager.readyState === WebSocket.OPEN
        );
    }
    
    /**
     * Проверяет, работает ли в локальном режиме.
     */
    isLocalModeActive() {
        return this.isLocalMode;
    }
}