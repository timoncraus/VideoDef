/**
 * Модуль сохранения и загрузки для игры "Поиск пар".
 */

import { dataURLtoBlob } from '../common/utils.js';

/**
 * Отображает список сохраненных игр "Поиск пар".
 * 
 * @param {HTMLElement} container - DOM-элемент для списка.
 * @param {Array<Object>} games - Массив объектов игр с сервера.
 */
export function displayMemoryGameList(container, games) {
    if (!games || games.length === 0) {
        container.innerHTML = '<p>У вас пока нет сохраненных игр этого типа.</p>';
        return;
    }
    
    const ul = document.createElement('ul');
    games.forEach(game => {
        const li = document.createElement('li');
        let imageInfo = game.preset_name ? `(набор: ${game.preset_name})` : "(свои фото)";
        li.textContent = `${game.name} (${game.pair_count} пар) ${imageInfo}`;
        li.dataset.gameData = JSON.stringify(game);
        li.dataset.id = game.id;
        ul.appendChild(li);
    });
    
    container.innerHTML = '';
    container.appendChild(ul);
}

/**
 * Вспомогательная функция для определения имени пресета по URL первого изображения.
 * 
 * @param {string} imageUrl - URL изображения.
 * @returns {string|null} Имя пресета или null.
 */
export function findPresetNameByUrl(imageUrl) {
    if (!imageUrl || typeof presetImagesBasePath === 'undefined' || typeof PRESET_IMAGE_SETS_CONFIG === 'undefined') return null;
    const pathWithoutBase = imageUrl.replace(presetImagesBasePath, '');
    const setName = pathWithoutBase.split('/')[0];
    return PRESET_IMAGE_SETS_CONFIG.hasOwnProperty(setName) ? setName : null;
}

/**
 * Подготавливает данные игры для сохранения.
 * 
 * @param {Object} gameParams - Параметры игры.
 * @param {boolean} skipAlerts - Пропускать ли алерты.
 * @returns {Object|null} Объект с данными для сохранения или null.
 */
export function prepareMemoryGameSaveData(gameParams, skipAlerts = false) {
    if (!gameParams.name) {
        if (!skipAlerts) alert("Введите название для сохранения.");
        return null;
    }
    
    if (!gameParams.card_layout || gameParams.card_layout.length === 0) {
        if (!skipAlerts) alert("Сначала начните игру.");
        return null;
    }
    
    const gameState = {
        id: gameParams.id,
        name: gameParams.name,
        pairCount: gameParams.pairCount,
        cardLayout: gameParams.card_layout,
    };
    
    if (gameParams.isCustomSet) {
        if (gameParams.customImageObjects?.some(obj => obj.file)) {
            if (!skipAlerts && gameParams.customImageObjects.length < gameParams.pairCount) {
                alert("Недостаточно изображений для сохранения.");
                return null;
            }
            gameState.customImages = gameParams.customImageObjects
                .slice(0, gameParams.pairCount)
                .map(imgObj => imgObj.file)
                .filter(Boolean);
        }
    } else {
        const presetName = findPresetNameByUrl(gameParams.selectedImageSet[0]);
        if (presetName) {
            gameState.presetName = presetName;
        } else if (!skipAlerts) {
            alert("Не удалось определить имя пресета.");
            return null;
        }
    }
    
    return gameState;
}

/**
 * Формирует FormData для отправки игры на сервер.
 * 
 * @param {Object} gameState - Состояние игры.
 * @returns {FormData} Объект FormData.
 */
export function createMemoryGameFormData(gameState) {
    const formData = new FormData();
    
    for (const key in gameState) {
        if (gameState.hasOwnProperty(key)) {
            if (key === 'customImages') {
                gameState[key].forEach(file => formData.append('customImages[]', file, file.name));
            } else if (gameState[key] !== null && gameState[key] !== undefined) {
                const value = typeof gameState[key] === 'object' ? JSON.stringify(gameState[key]) : gameState[key];
                formData.append(key, value);
            }
        }
    }
    
    return formData;
}

/**
 * Подготавливает данные игры для сохранения на доске (с конвертацией dataURL в Blob).
 * 
 * @param {Object} gameParams - Параметры игры.
 * @param {boolean} skipAlerts - Пропускать ли алерты.
 * @returns {Object|null} Объект с данными для сохранения или null.
 */
export function prepareMemoryGameSaveDataForWhiteboard(gameParams, skipAlerts = false) {
    if (!gameParams.name) {
        if (!skipAlerts) alert("Введите название для сохранения.");
        return null;
    }
    
    if (!gameParams.card_layout || gameParams.card_layout.length === 0) {
        return null;
    }
    
    const gameState = {
        id: gameParams.id,
        name: gameParams.name,
        pairCount: gameParams.pairCount,
        cardLayout: gameParams.card_layout,
    };
    
    if (gameParams.isCustomSet) {
        const imageObjects = gameParams.customImageObjects || [];
        if (!skipAlerts && imageObjects.length < gameParams.pairCount) {
            alert(`Недостаточно изображений для сохранения. Требуется ${gameParams.pairCount}, а загружено ${imageObjects.length}.`);
            return null;
        }
        
        const hasNewFiles = imageObjects.some(obj => obj.file);
        
        if (!gameParams.id || hasNewFiles) {
            gameState.customImages = [];
            for (let i = 0; i < gameParams.pairCount; i++) {
                const imgObj = imageObjects[i];
                if (imgObj.file) {
                    gameState.customImages.push(imgObj.file);
                } else if (imgObj.url && imgObj.url.startsWith('data:image')) {
                    const blob = dataURLtoBlob(imgObj.url);
                    if (blob) {
                        const filename = `upload_${i}.${blob.type.split('/')[1] || 'png'}`;
                        gameState.customImages.push(new File([blob], filename, { type: blob.type }));
                    } else {
                        if (!skipAlerts) alert(`Ошибка обработки изображения №${i + 1}. Сохранение прервано.`);
                        return null;
                    }
                }
            }
            
            if (!skipAlerts && gameState.customImages.length < gameParams.pairCount) {
                alert(`Не удалось подготовить все изображения для сохранения. Требуется ${gameParams.pairCount}, готово ${gameState.customImages.length}.`);
                return null;
            }
        }
    } else {
        const presetName = findPresetNameByUrl(gameParams.selectedImageSet[0]);
        if (presetName) {
            gameState.presetName = presetName;
        } else if (!skipAlerts) {
            alert("Не удалось определить имя пресета.");
            return null;
        }
    }
    
    return gameState;
}