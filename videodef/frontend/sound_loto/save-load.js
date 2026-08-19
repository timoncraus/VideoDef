/**
 * Модуль сохранения и загрузки для игры "Звуковое лото".
 */
import { dataURLtoBlob } from '../common/utils.js';

/**
 * Отображает список сохраненных игр "Звуковое лото".
 * 
 * @param {HTMLElement} container - DOM-элемент для списка.
 * @param {Array<Object>} games - Массив объектов игр с сервера.
 */
export function displaySoundLotoList(container, games) {
    if (!games || games.length === 0) {
        container.innerHTML = '<p>У вас пока нет сохраненных игр этого типа.</p>';
        return;
    }

    const ul = document.createElement('ul');
    games.forEach(game => {
        const li = document.createElement('li');
        const PRESET_DISPLAY_NAMES = { animals: 'Животные', transport: 'Транспорт' };
        let sourceInfo = game.preset_name
            ? `(набор: ${PRESET_DISPLAY_NAMES[game.preset_name] || game.preset_name})`
            : "(свои пары)";
        li.textContent = `${game.name} (${game.rounds_count} раундов, ${game.cards_count} карточек) ${sourceInfo}`;
        li.dataset.gameData = JSON.stringify(game);
        li.dataset.id = game.id;
        ul.appendChild(li);
    });

    container.innerHTML = '';
    container.appendChild(ul);
}

/**
 * Подготавливает данные игры для сохранения.
 * 
 * @param {Object} params - Параметры игры.
 * @param {boolean} skipAlerts - Пропускать ли алерты.
 * @returns {Object|null} Объект с данными для сохранения или null.
 */
export function prepareSoundLotoSaveData(params, skipAlerts = false) {
    if (!params.name) {
        if (!skipAlerts) alert("Введите название для сохранения.");
        return null;
    }

    const gameState = {
        id: params.id,
        name: params.name,
        roundsCount: params.roundsCount,
        cardsCount: params.cardsCount,
        autoplay: params.autoplay,
        showLabels: params.showLabels,
    };

    if (params.isCustomSet) {
        const pairs = params.customPairs || [];
        const requiredCount = Math.max(params.roundsCount, params.cardsCount);

        if (pairs.length < requiredCount) {
            if (!skipAlerts) alert(`Недостаточно пар для сохранения. Требуется минимум ${requiredCount}, загружено ${pairs.length}.`);
            return null;
        }

        const hasNewFiles = pairs.some(pair => pair.imageFile || pair.audioFile);

        if (hasNewFiles) {
            // Пользователь загрузил новые файлы — отправляем их
            gameState.customImages = [];
            gameState.customAudios = [];
            gameState.customLabels = [];

            for (let i = 0; i < pairs.length; i++) {
                const pair = pairs[i];

                // Обработка изображения
                if (pair.imageFile) {
                    gameState.customImages.push(pair.imageFile);
                } else if (pair.imageUrl && pair.imageUrl.startsWith('data:')) {
                    const blob = dataURLtoBlob(pair.imageUrl);
                    if (blob) {
                        const ext = blob.type.split('/')[1] || 'png';
                        gameState.customImages.push(new File([blob], `image_${i}.${ext}`, { type: blob.type }));
                    } else {
                        if (!skipAlerts) alert(`Ошибка обработки изображения №${i + 1}. Сохранение прервано.`);
                        return null;
                    }
                } else {
                    if (!skipAlerts) alert(`Изображение №${i + 1} отсутствует. Сохранение прервано.`);
                    return null;
                }

                // Обработка аудио
                if (pair.audioFile) {
                    gameState.customAudios.push(pair.audioFile);
                } else if (pair.audioUrl && pair.audioUrl.startsWith('data:')) {
                    const blob = dataURLtoBlob(pair.audioUrl);
                    if (blob) {
                        const ext = blob.type.split('/')[1] || 'mp3';
                        gameState.customAudios.push(new File([blob], `audio_${i}.${ext}`, { type: blob.type }));
                    } else {
                        if (!skipAlerts) alert(`Ошибка обработки аудио №${i + 1}. Сохранение прервано.`);
                        return null;
                    }
                } else {
                    if (!skipAlerts) alert(`Аудио №${i + 1} отсутствует. Сохранение прервано.`);
                    return null;
                }

                gameState.customLabels.push(pair.label || '');
            }
        } else {
            // Файлы уже на сервере — отправляем только подписи и порядок аудио
            gameState.customLabels = pairs.map(pair => pair.label || '');

            if (params.audioReorderMap && params.audioReorderMap.some((val, idx) => val !== idx)) {
                gameState.audioOrder = params.audioReorderMap;
            }
        }
    } else {
        if (params.presetName) {
            gameState.presetName = params.presetName;
        } else {
            if (!skipAlerts) alert("Не выбран набор изображений.");
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
export function createSoundLotoFormData(gameState) {
    const formData = new FormData();
    
    formData.append('name', gameState.name);
    formData.append('roundsCount', gameState.roundsCount);
    formData.append('cardsCount', gameState.cardsCount);
    formData.append('autoplay', gameState.autoplay.toString());
    formData.append('showLabels', gameState.showLabels.toString());

    if (gameState.presetName) {
        formData.append('presetName', gameState.presetName);
    }

    if (gameState.customImages) {
        gameState.customImages.forEach(file => {
            formData.append('customImages[]', file, file.name);
        });
    }

    if (gameState.customAudios) {
        gameState.customAudios.forEach(file => {
            formData.append('customAudios[]', file, file.name);
        });
    }

    if (gameState.customLabels) {
        formData.append('customLabels', JSON.stringify(gameState.customLabels));
    }

    if (gameState.audioOrder) {
        formData.append('audioOrder', JSON.stringify(gameState.audioOrder));
    }

    return formData;
}

/**
 * Подготавливает данные игры для сохранения на доске (с конвертацией dataURL в Blob).
 * 
 * @param {Object} params - Параметры игры.
 * @param {boolean} skipAlerts - Пропускать ли алерты.
 * @returns {Object|null} Объект с данными для сохранения или null.
 */
export function prepareSoundLotoSaveDataForWhiteboard(params, skipAlerts = false) {
    // Для доски логика аналогична обычной подготовке
    return prepareSoundLotoSaveData(params, skipAlerts);
}