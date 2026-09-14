/**
 * Модуль для сохранения, загрузки и удаления интерактивной доски.
 */
import { getCookie, dataURLtoBlob } from '../common/utils.js';
import { createPuzzleOnBoard } from '../puzzle/index.js';
import { createMemoryGameOnBoard } from '../memory_game/index.js';
import { createSoundLotoOnBoard } from '../sound_loto/index.js';
import { getFullPresetImageUrls } from '../memory_game/logic.js';
import { getFullPresetData } from '../sound_loto/logic.js';

/**
 * Собирает полное текущее состояние доски для отправки на сервер.
 *
 * @param {CanvasDrawing} canvasDrawing - Менеджер рисования.
 * @param {ImageManager} imageManager - Менеджер изображений.
 * @param {GameManager} gameManager - Менеджер игровых элементов.
 * @returns {{strokes: Array, images: Array, games: Array, imageFiles: File[]}}
 */
export function collectBoardState(canvasDrawing, imageManager, gameManager) {
    const strokes = canvasDrawing.getStrokeHistory();

    const images = [];
    const imageFiles = [];

    imageManager.imagesList.forEach((img, index) => {
        images.push({
            id: img.id,
            file_index: index,
            x: img.x,
            y: img.y,
            width: img.width,
            height: img.height
        });

        const blob = dataURLtoBlob(img.dataURL);
        if (blob) {
            const ext = blob.type.split('/')[1] || 'png';
            imageFiles.push(
                new File([blob], `board_image_${index}.${ext}`, { type: blob.type })
            );
        }
    });

    const games = [];

    Object.entries(gameManager.gameElements).forEach(([id, wrapper]) => {
        const gameType = wrapper.dataset.gameName;
        let savedGameId = null;
        let inlineState = null;

        if (gameType === 'puzzles' && wrapper.puzzleGame) {
            const p = wrapper.puzzleGame.params;
            savedGameId = p.id || null;
            if (!savedGameId) {
                inlineState = {
                    name: p.name,
                    gridSize: p.gridSize,
                    selectedImage: p.selectedImage,
                    isPreset: p.isPreset
                };
            }
        } else if (gameType === 'memory-game' && wrapper.memoryGameGame) {
            const p = wrapper.memoryGameGame.params;
            savedGameId = p.id || null;
            if (!savedGameId) {
                inlineState = {
                    name: p.name,
                    pairCount: p.pairCount,
                    selectedImageSet: p.isCustomSet
                        ? (p.customImageObjects || []).map(obj => obj.url)
                        : p.selectedImageSet,
                    isCustomSet: p.isCustomSet
                };
            }
        } else if (gameType === 'sound-loto' && wrapper.soundLotoGame) {
            const p = wrapper.soundLotoGame.params;
            savedGameId = p.id || null;
            if (!savedGameId) {
                inlineState = {
                    name: p.name,
                    roundsCount: p.roundsCount,
                    cardsCount: p.cardsCount,
                    autoplay: p.autoplay,
                    showLabels: p.showLabels,
                    presetName: p.isCustomSet ? null : p.presetName,
                    isCustomSet: p.isCustomSet,
                    customPairs: p.isCustomSet ? p.customPairs : null
                };
            }
        }

        games.push({
            instance_id: id,
            game_type: gameType,
            saved_game_id: savedGameId,
            inline_state: inlineState,
            x: parseFloat(wrapper.style.left) || 0,
            y: parseFloat(wrapper.style.top) || 0,
            width: parseFloat(wrapper.style.width) || 400,
            height: parseFloat(wrapper.style.height) || 300
        });
    });

    return { strokes, images, games, imageFiles };
}

/**
 * Генерирует PNG-превью доски.
 *
 * @returns {Promise<Blob|null>} Blob с превью или null.
 */
export function generateBoardPreview() {
    const imageCanvas = document.getElementById('image-layer');
    const drawCanvas = document.getElementById('draw-layer');

    if (!imageCanvas || !drawCanvas) return Promise.resolve(null);
    if (drawCanvas.width === 0 || drawCanvas.height === 0) return Promise.resolve(null);

    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = drawCanvas.width;
    tempCanvas.height = drawCanvas.height;
    const ctx = tempCanvas.getContext('2d');

    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
    ctx.drawImage(imageCanvas, 0, 0);
    ctx.drawImage(drawCanvas, 0, 0);

    return new Promise(resolve => {
        tempCanvas.toBlob(blob => resolve(blob), 'image/png');
    });
}

/**
 * Отправляет состояние доски на сервер (создание или обновление).
 *
 * @param {string} name - Название сохранения.
 * @param {Object} boardState - Результат collectBoardState().
 * @param {string|null} existingBoardId - ID доски при обновлении, иначе null.
 * @returns {Promise<Object>} Ответ сервера.
 */
export async function saveBoard(name, boardState, existingBoardId = null) {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('canvasStrokes', JSON.stringify(boardState.strokes));
    formData.append('imagesData', JSON.stringify(boardState.images));
    formData.append('gameInstances', JSON.stringify(boardState.games));

    boardState.imageFiles.forEach(file => {
        formData.append('boardImages[]', file, file.name);
    });

    const previewBlob = await generateBoardPreview();
    if (previewBlob) {
        formData.append('canvasPreview', previewBlob, 'preview.png');
    }

    const url = existingBoardId
        ? `/games/api/update-whiteboard/${existingBoardId}/`
        : '/games/api/save-whiteboard/';
    const method = existingBoardId ? 'PUT' : 'POST';

    const response = await fetch(url, {
        method,
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    });

    return response.json();
}

/**
 * Загружает список сохранённых досок пользователя.
 *
 * @returns {Promise<Object>} Ответ сервера с массивом досок.
 */
export async function loadBoardsList() {
    const response = await fetch('/games/api/load-whiteboards/');
    return response.json();
}

/**
 * Загружает полные данные конкретной доски.
 *
 * @param {string} boardId - ID доски.
 * @returns {Promise<Object>} Ответ сервера с полными данными доски.
 */
export async function loadBoardDetail(boardId) {
    const response = await fetch(`/games/api/load-whiteboard/${boardId}/`);
    return response.json();
}

/**
 * Удаляет сохранение доски.
 * Используется в личной библиотеке.
 *
 * @param {string} boardId - ID доски.
 * @returns {Promise<Object>} Ответ сервера.
 */
export async function deleteBoard(boardId) {
    const response = await fetch(`/games/api/delete-whiteboard/${boardId}/`, {
        method: 'DELETE',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    });
    return response.json();
}

/**
 * Закрывает WebSocket-соединения всех игровых экземпляров на доске.
 * Вызывается перед очисткой доски.
 *
 * @param {GameManager} gameManager - Менеджер игровых элементов.
 */
export function closeAllGameWebSockets(gameManager) {
    Object.values(gameManager.gameElements).forEach(wrapper => {
        ['puzzleGame', 'memoryGameGame', 'soundLotoGame'].forEach(key => {
            const game = wrapper[key];
            if (game && typeof game.closeWebSocket === 'function') {
                game.closeWebSocket();
            }
        });
    });
}

/**
 * Восстанавливает доску из загруженных данных.
 * Очищает текущее состояние и последовательно восстанавливает штрихи, картинки, игры.
 *
 * @param {Object} boardData - Данные доски из ответа сервера.
 * @param {Object} whiteboard - Экземпляр класса Whiteboard.
 */
export async function restoreBoard(boardData, whiteboard) {
    const { canvasDrawing, imageManager, gameManager, ui } = whiteboard;

    canvasDrawing.clear();
    canvasDrawing.clearStrokeHistory();
    imageManager.clear();
    closeAllGameWebSockets(gameManager);
    gameManager.clear();
    ui.clearDynamicSettings();

    if (boardData.canvas_strokes && boardData.canvas_strokes.length > 0) {
        canvasDrawing.replayStrokes(boardData.canvas_strokes);
    }
    
    if (boardData.images_data) {
        for (const img of boardData.images_data) {
            if (img.file_url) {
                imageManager.addImage(
                    img.file_url, img.x, img.y, img.width, img.height, img.id, true
                );
            }
        }
    }

    // пакетная загрузка данных сохранённых игр
    if (!boardData.game_instances || boardData.game_instances.length === 0) return;

    const savedGameIdsByType = { 'puzzles': [], 'memory-game': [], 'sound-loto': [] };

    for (const g of boardData.game_instances) {
        if (g.removed) continue;
        if (g.saved_game_id) {
            const arr = savedGameIdsByType[g.game_type];
            if (arr) arr.push(g.saved_game_id);
        }
    }

    // Параллельная загрузка списков игр нужных типов
    const loadedGamesMap = {};
    const loadPromises = [];

    const fetchGames = (url, gamesKey) =>
        fetch(url).then(r => r.json()).then(data => {
            if (data.status === 'success' && data[gamesKey]) {
                data[gamesKey].forEach(item => { loadedGamesMap[item.id] = item; });
            }
        }).catch(err => console.warn(`Не удалось загрузить список игр: ${err}`));

    if (savedGameIdsByType['puzzles'].length > 0) {
        const url = typeof loadPuzzlesUrl !== 'undefined' ? loadPuzzlesUrl : '/games/api/load-puzzles/';
        loadPromises.push(fetchGames(url, 'puzzles'));
    }
    if (savedGameIdsByType['memory-game'].length > 0) {
        const url = typeof loadMemoryGamesUrl !== 'undefined' ? loadMemoryGamesUrl : '/games/api/load-memory-games/';
        loadPromises.push(fetchGames(url, 'games'));
    }
    if (savedGameIdsByType['sound-loto'].length > 0) {
        const url = typeof loadSoundLotosUrl !== 'undefined' ? loadSoundLotosUrl : '/games/api/load-sound-lotos/';
        loadPromises.push(fetchGames(url, 'games'));
    }

    if (loadPromises.length > 0) {
        await Promise.all(loadPromises);
    }

    const videosElement = document.getElementById('videos');
    const roomName = videosElement ? videosElement.dataset.roomName : null;

    for (const gameInst of boardData.game_instances) {
        if (gameInst.removed) continue;

        whiteboard.addGameElement(
            gameInst.instance_id, gameInst.game_type,
            gameInst.x, gameInst.y, gameInst.width, gameInst.height
        );
        gameManager.updateNextGameId(gameInst.instance_id);

        const gameWrapper = gameManager.gameElements[gameInst.instance_id];
        if (!gameWrapper) continue;

        if (gameInst.saved_game_id && loadedGamesMap[gameInst.saved_game_id]) {
            applySavedGameState(gameWrapper, gameInst.game_type, loadedGamesMap[gameInst.saved_game_id]);
        } else if (gameInst.inline_state) {
            applyInlineGameState(gameWrapper, gameInst.game_type, gameInst.inline_state);
        }
    }
}

/**
 * Применяет данные сохранённой игры из библиотеки к игре на доске.
 * Игра восстанавливается в состоянии «настроена, готова к запуску».
 */
function applySavedGameState(gameWrapper, gameType, gameData) {
    if (gameType === 'puzzles' && gameWrapper.puzzleGame) {
        const g = gameWrapper.puzzleGame;
        g.params.id = gameData.id;
        g.params.name = gameData.name;
        g.params.gridSize = gameData.grid_size;
        g.params.selectedImage = gameData.image_url;
        g.params.isPreset = !!gameData.preset_path;
        g.params.piecePositions = [];
        g.puzzleContainer.innerHTML =
            '<p class="initial-message">Пазл загружен. Активируйте и нажмите «Начать игру».</p>';

    } else if (gameType === 'memory-game' && gameWrapper.memoryGameGame) {
        const g = gameWrapper.memoryGameGame;
        g.params.id = gameData.id;
        g.params.name = gameData.name;
        g.params.pairCount = gameData.pair_count;
        g.params.isCustomSet = !!gameData.custom_image_urls;

        if (g.params.isCustomSet) {
            g.params.selectedImageSet = gameData.custom_image_urls;
            g.params.customImageObjects = gameData.custom_image_urls.map(url => ({ url, file: null }));
        } else if (gameData.preset_name) {
            g.params.selectedImageSet = getFullPresetImageUrls(gameData.preset_name);
            g.params.customImageObjects = [];
        }

        g.params.card_layout = [];
        g.params.attempts = 0;
        g.gameContainer.innerHTML =
            '<p class="initial-message">Игра загружена. Нажмите «Перемешать» для запуска.</p>';

    } else if (gameType === 'sound-loto' && gameWrapper.soundLotoGame) {
        const g = gameWrapper.soundLotoGame;
        g.params.id = gameData.id;
        g.params.name = gameData.name;
        g.params.roundsCount = gameData.rounds_count;
        g.params.cardsCount = gameData.cards_count;
        g.params.autoplay = gameData.autoplay;
        g.params.showLabels = gameData.show_labels;
        g.params.isCustomSet = !!gameData.custom_pairs;

        if (g.params.isCustomSet) {
            g.params.presetName = null;
            g.params.customPairs = gameData.custom_pairs.map(pair => ({
                image: pair.image_url,
                audio: pair.audio_url,
                imageUrl: pair.image_url,
                audioUrl: pair.audio_url,
                label: pair.label
            }));
        } else {
            g.params.presetName = gameData.preset_name;
            g.params.customPairs = [];
            g.params.pairs = getFullPresetData(gameData.preset_name);
        }

        g.params.currentRound = 0;
        g.params.roundPairs = [];
        g.params.correctPairIndex = null;
        g.params.usedPairIndices = [];
        g.params.correctClicks = 0;
        g.params.totalClicks = 0;
        g.params.secondsElapsed = 0;
        g.gameContainer.innerHTML =
            '<p class="initial-message">Игра загружена. Нажмите «Начать игру» для запуска.</p>';
    }
}

/**
 * Применяет конфигурацию несохранённой игры (inline_state) к игре на доске.
 */
function applyInlineGameState(gameWrapper, gameType, state) {
    if (gameType === 'puzzles' && gameWrapper.puzzleGame) {
        const g = gameWrapper.puzzleGame;
        g.params.name = state.name;
        g.params.gridSize = state.gridSize;
        g.params.selectedImage = state.selectedImage;
        g.params.isPreset = state.isPreset;
        g.params.piecePositions = [];
        g.puzzleContainer.innerHTML =
            '<p class="initial-message">Пазл настроен. Нажмите «Начать игру».</p>';

    } else if (gameType === 'memory-game' && gameWrapper.memoryGameGame) {
        const g = gameWrapper.memoryGameGame;
        g.params.name = state.name;
        g.params.pairCount = state.pairCount;
        g.params.isCustomSet = state.isCustomSet;

        if (state.isCustomSet) {
            g.params.selectedImageSet = state.selectedImageSet || [];
            g.params.customImageObjects = (state.selectedImageSet || []).map(url => ({ url, file: null }));
        } else {
            g.params.selectedImageSet = state.selectedImageSet || [];
            g.params.customImageObjects = [];
        }

        g.params.card_layout = [];
        g.params.attempts = 0;
        g.gameContainer.innerHTML =
            '<p class="initial-message">Игра настроена. Нажмите «Перемешать» для запуска.</p>';

    } else if (gameType === 'sound-loto' && gameWrapper.soundLotoGame) {
        const g = gameWrapper.soundLotoGame;
        g.params.name = state.name;
        g.params.roundsCount = state.roundsCount;
        g.params.cardsCount = state.cardsCount;
        g.params.autoplay = state.autoplay;
        g.params.showLabels = state.showLabels;
        g.params.isCustomSet = state.isCustomSet;

        if (state.isCustomSet) {
            g.params.presetName = null;
            g.params.customPairs = state.customPairs || [];
        } else {
            g.params.presetName = state.presetName;
            g.params.customPairs = [];
            g.params.pairs = getFullPresetData(state.presetName);
        }

        g.params.currentRound = 0;
        g.params.roundPairs = [];
        g.params.correctPairIndex = null;
        g.params.usedPairIndices = [];
        g.params.correctClicks = 0;
        g.params.totalClicks = 0;
        g.params.secondsElapsed = 0;
        g.gameContainer.innerHTML =
            '<p class="initial-message">Игра настроена. Нажмите «Начать игру» для запуска.</p>';
    }
}