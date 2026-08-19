/**
 * Класс игры "Звуковое лото", наследующий от базового класса GameBase.
 * Инкапсулирует логику игры и взаимодействие с WebSocket.
 */
import { GameBase } from '../common/game-base.js';
import {
    getGameParts,
    initializeBoard,
    applyRemoteCardClick,
    applyRemoteRoundStart,
    applyRemoteGameFinish,
    playSound,
    stopSound,
    stopTimer
} from './logic.js';

/**
 * Класс, представляющий экземпляр игры "Звуковое лото".
 * Наследует общую логику WebSocket и управления состоянием от GameBase.
 */
export class SoundLotoGame extends GameBase {
    /**
     * Создаёт экземпляр игры "Звуковое лото".
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
            type: 'sound_loto'
        });

        // Получаем базовые параметры игры
        this.params = getGameParts();

        // Создаём контейнер для игры
        this.gameContainer = config.container || document.createElement('div');
        this.gameContainer.className = 'sound-loto-game-wrapper';

        // Инициализация параметров игры
        this.params.onWhiteboard = !!config.boardRoomName;
        this.params.gameId = config.gameId || null;
        this.params.boardRoomName = config.boardRoomName || null;
        this.params.name = config.name || `Звуковое лото ${config.gameId ? config.gameId.split('-')[1] || '' : ''}`;
    }

    /**
     * Обработчик открытия WebSocket соединения.
     * Переопределяет абстрактный метод GameBase.
     * Транслирует состояние только если игра уже идёт,
     * иначе запрашивает состояние у других клиентов (позднее подключение).
     */
    onWebSocketOpen() {
        console.log(`[SoundLotoGame:${this.gameId}] WebSocket connected`);

        if (this.params.currentRound > 0) {
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
        switch (data.type) {
            case 'request_state': {
                // Ответ только если есть реальное состояние
                if (this.params.currentRound > 0) {
                    this.broadcastState();
                }
                break;
            }

            case 'game_state_change': {
                const receivedState = data.gameState;

                Object.assign(this.params, receivedState);

                if (receivedState.isCustomSet && receivedState.customPairs) {
                    this.params.customPairs = receivedState.customPairs;
                }

                const receivedIsActive = (receivedState.currentRound || 0) > 0;

                if (receivedIsActive && receivedState.roundPairs && receivedState.roundPairs.length > 0) {
                    // Игра идёт — восстанавливаем состояние без генерации нового раунда
                    initializeBoard(this.gameContainer, this.params, false);
                } else {
                    stopTimer(this.params);
                    stopSound(this.params);
                    this.gameContainer.innerHTML = '<p class="initial-message">Ожидание начала игры. Нажмите "Начать игру".</p>';
                }
                break;
            }

            case 'round_start': {
                applyRemoteRoundStart(this.gameContainer, this.params, data);
                break;
            }

            case 'play_sound': {
                playSound(data.audioUrl, this.params);
                break;
            }

            case 'stop_sound': {
                stopSound(this.params);
                break;
            }

            case 'card_click': {
                applyRemoteCardClick(this.gameContainer, this.params, data.cardIndex, data.isCorrect);
                break;
            }

            case 'game_finish': {
                applyRemoteGameFinish(this.gameContainer, this.params, data);
                break;
            }
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
        return {
            id: this.params.id,
            name: this.params.name,
            roundsCount: this.params.roundsCount,
            cardsCount: this.params.cardsCount,
            autoplay: this.params.autoplay,
            showLabels: this.params.showLabels,
            presetName: this.params.isCustomSet ? null : this.params.presetName,
            isCustomSet: this.params.isCustomSet,
            customPairs: this.params.isCustomSet ? this.params.customPairs : null,
            // Состояние текущей игры для синхронизации
            currentRound: this.params.currentRound,
            roundPairs: this.params.roundPairs,
            correctPairIndex: this.params.correctPairIndex,
            usedPairIndices: this.params.usedPairIndices,
            correctClicks: this.params.correctClicks,
            totalClicks: this.params.totalClicks,
            secondsElapsed: this.params.secondsElapsed,
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
        initializeBoard(this.gameContainer, this.params, false);
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
        stopSound(this.params);
        super.destroy();
        if (this.gameContainer) {
            this.gameContainer.innerHTML = '';
        }
    }
}