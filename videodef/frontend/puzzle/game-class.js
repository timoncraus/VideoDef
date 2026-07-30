/**
 * Класс игры "Пазл", наследующий от базового класса GameBase.
 * Инкапсулирует логику пазла и взаимодействие с WebSocket.
 */

import { GameBase } from '../common/game-base.js';
import { getPuzzleParts, createPuzzle, applyRemotePieceInteraction } from './logic.js';

/**
 * Класс, представляющий экземпляр игры "Пазл".
 * Наследует общую логику WebSocket и управления состоянием от GameBase.
 */
export class PuzzleGame extends GameBase {
    /**
     * Создаёт экземпляр игры "Пазл".
     * 
     * @param {Object} config - Конфигурация
     * @param {HTMLElement} config.container - DOM-контейнер для игры
     * @param {string} config.gameId - Уникальный ID экземпляра игры
     * @param {string} config.boardRoomName - Имя комнаты доски
     * @param {string} config.name - Название пазла
     * @param {number} config.gridSize - Размер сетки (по умолчанию 2)
     */
    constructor(config = {}) {
        super({
            ...config,
            type: 'puzzle'
        });
        
        // Получаем базовые компоненты пазла
        const [puzzleParams, puzzleContainer, message] = getPuzzleParts();
        
        // Сохраняем ссылки на DOM-элементы и параметры
        this.params = puzzleParams;
        this.puzzleContainer = puzzleContainer;
        this.messageElement = message;
        
        // Инициализация параметров пазла
        this.params.onWhiteboard = !!config.boardRoomName;
        this.params.gameId = config.gameId || null;
        this.params.boardRoomName = config.boardRoomName || null;
        this.params.name = config.name || `Пазл ${config.gameId ? config.gameId.split('-')[1] || '' : ''}`;
        this.params.gridSize = config.gridSize || 2;
        this.params.selectedImage = config.selectedImage || null;
        this.params.isPreset = false;
        this.params.piecePositions = [];
        this.params.id = null;
    }
    
    /**
     * Обработчик открытия WebSocket соединения.
     * Переопределяет абстрактный метод GameBase.
     */
    onWebSocketOpen() {
        console.log(`[PuzzleGame:${this.gameId}] WebSocket connected`);
        
        this.broadcastState();
    }
    
    /**
     * Обработчик входящих WebSocket сообщений.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @param {Object} data - Полученные данные
     */
    onWebSocketMessage(data) {
        if (data.type === 'puzzle_piece_click') {
            applyRemotePieceInteraction(
                this.puzzleContainer,
                this.params,
                data.pieceIndex,
                this.messageElement
            );
        } else if (data.type === 'puzzle_state_change') {
            // Применяем полное состояние, полученное от другого клиента
            Object.assign(this.params, data.puzzleState);
            
            // Обновляем UI панели настроек, если этот пазл сейчас активен
            const activeBoardGame = document.querySelector('.paste-game-wrapper.active-game');
            if (activeBoardGame && activeBoardGame.puzzleGame === this) {
                const settingsPanel = document.querySelector('.settings-panel');
                const puzzleNameInput = settingsPanel?.querySelector('#puzzle-name');
                const difficultySelect = settingsPanel?.querySelector('#difficulty');
                if (puzzleNameInput) puzzleNameInput.value = this.params.name || '';
                if (difficultySelect) difficultySelect.value = this.params.gridSize;
            }
            
            // Перерисовываем пазл с новым состоянием
            createPuzzle(this.puzzleContainer, this.params, this.messageElement, true);
        }
    }
    
    /**
     * Инициализирует игровое поле.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @param {HTMLElement} container - Контейнер для игры
     * @param {boolean} useExistingState - Использовать ли существующее состояние
     */
    initializeBoard(container, useExistingState = false) {
        if (container) {
            this.puzzleContainer = container;
        }
        createPuzzle(this.puzzleContainer, this.params, this.messageElement, useExistingState);
    }
    
    /**
     * Получает текущее состояние игры для сохранения или синхронизации.
     * Переопределяет абстрактный метод GameBase.
     * 
     * @returns {Object} Объект с состоянием игры
     */
    getState() {
        return {
            gridSize: this.params.gridSize,
            piecePositions: this.params.piecePositions,
            selectedImage: this.params.selectedImage,
            isPreset: this.params.isPreset,
            name: this.params.name,
            id: this.params.id
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
        createPuzzle(this.puzzleContainer, this.params, this.messageElement, true);
    }
    
    /**
     * Отправляет текущее состояние игры через WebSocket всем подключённым клиентам.
     */
    broadcastState() {
        if (this.params.onWhiteboard && this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.sendWebSocketMessage({
                type: 'puzzle_state_change',
                puzzleState: this.getState()
            });
        }
    }
    
    /**
     * Очищает ресурсы игры.
     * Переопределяет метод GameBase.
     */
    destroy() {
        super.destroy();
        if (this.puzzleContainer) {
            this.puzzleContainer.innerHTML = '';
        }
    }
}