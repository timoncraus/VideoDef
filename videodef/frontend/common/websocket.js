/**
 * Модуль для работы с WebSocket соединениями.
 * Предоставляет унифицированный интерфейс для подключения и обмена сообщениями.
 */

/**
 * Класс для управления WebSocket соединением.
 */
export class WebSocketManager {
    /**
     * Создает экземпляр WebSocketManager.
     * 
     * @param {string} url - URL WebSocket сервера
     * @param {Object} handlers - Обработчики событий
     * @param {Function} handlers.onOpen - Обработчик подключения
     * @param {Function} handlers.onMessage - Обработчик входящих сообщений
     * @param {Function} handlers.onClose - Обработчик отключения
     * @param {Function} handlers.onError - Обработчик ошибок
     */
    constructor(url, handlers = {}) {
        this.url = url;
        this.handlers = handlers;
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 3;
        this.reconnectDelay = 1000;
        
        // Очередь сообщений для отправки после подключения
        this.messageQueue = [];
    }
    
    /**
     * Устанавливает WebSocket соединение.
     */
    connect() {
        try {
            this.ws = new WebSocket(this.url);
            
            this.ws.onopen = () => {
                console.log(`WebSocket подключен к ${this.url}`);
                this.reconnectAttempts = 0;
                
                // Отправляем все накопленные сообщения из очереди
                if (this.messageQueue.length > 0) {
                    console.log(`Отправка ${this.messageQueue.length} накопленных сообщений`);
                    this.messageQueue.forEach(msg => {
                        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                            this.ws.send(JSON.stringify(msg));
                        }
                    });
                    this.messageQueue = [];
                }
                
                if (this.handlers.onOpen) {
                    this.handlers.onOpen();
                }
            };
            
            this.ws.onmessage = (e) => {
                if (this.handlers.onMessage) {
                    try {
                        const data = JSON.parse(e.data);
                        this.handlers.onMessage(data);
                    } catch (error) {
                        console.error("Ошибка парсинга WebSocket сообщения:", error);
                    }
                }
            };
            
            this.ws.onclose = (e) => {
                console.log(`WebSocket отключен от ${this.url}`, e.reason);
                if (this.handlers.onClose) {
                    this.handlers.onClose(e);
                }
                
                // Попытка переподключения
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnectAttempts++;
                    setTimeout(() => {
                        console.log(`Попытка переподключения ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
                        this.connect();
                    }, this.reconnectDelay * this.reconnectAttempts);
                }
            };
            
            this.ws.onerror = (error) => {
                console.error(`WebSocket ошибка для ${this.url}:`, error);
                if (this.handlers.onError) {
                    this.handlers.onError(error);
                }
            };
        } catch (error) {
            console.error("Ошибка создания WebSocket:", error);
        }
    }
    
    /**
     * Отправляет сообщение через WebSocket.
     * Если соединение ещё устанавливается (CONNECTING), сообщение добавляется в очередь.
     * 
     * @param {Object} data - Данные для отправки (будут сериализованы в JSON)
     */
    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        } else if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
            // Добавляем сообщение в очередь, пока соединение устанавливается
            this.messageQueue.push(data);
            console.log(`Сообщение добавлено в очередь. Всего в очереди: ${this.messageQueue.length}`);
        } else {
            console.warn("WebSocket не подключен. Сообщение не отправлено.");
        }
    }
    
    /**
     * Закрывает WebSocket соединение.
     */
    close() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
        this.messageQueue = [];
    }
    
    /**
     * Проверяет, активно ли соединение.
     * 
     * @returns {boolean} - true, если соединение активно
     */
    isConnected() {
        return this.ws && this.ws.readyState === WebSocket.OPEN;
    }
}

/**
 * Создает локальную WebSocket-заглушку для работы в режиме без сервера.
 * 
 * @param {Function} messageHandler - Обработчик "отправленных" сообщений
 * @returns {Object} - Объект с интерфейсом WebSocket
 */
export function createLocalWebSocketStub(messageHandler) {
    return {
        send: (message) => {
            const data = JSON.parse(message);
            if (messageHandler) {
                messageHandler(data);
            }
        },
        readyState: WebSocket.CLOSED,
        close: () => {}
    };
}