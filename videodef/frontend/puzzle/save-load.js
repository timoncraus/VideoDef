/**
 * Модуль сохранения и загрузки для игры "Пазл".
 */

import { dataURLtoBlob } from '../common/utils.js';

/**
 * Отображает список сохраненных пазлов.
 * 
 * @param {HTMLElement} container - DOM-элемент для списка
 * @param {Array<object>} puzzles - Массив объектов пазлов
 */
export function displayPuzzleList(container, puzzles) {
    if (!puzzles || puzzles.length === 0) {
        container.innerHTML = '<p>У вас пока нет сохраненных пазлов.</p>';
        return;
    }
    
    const ul = document.createElement('ul');
    puzzles.forEach(puzzle => {
        const li = document.createElement('li');
        let imageInfo = puzzle.has_user_image ? "(свое фото)" : "(пресет)";
        li.textContent = `${puzzle.name} (${puzzle.grid_size}x${puzzle.grid_size}) ${imageInfo}`;
        
        li.dataset.gameData = JSON.stringify(puzzle);
        li.dataset.id = puzzle.id;
        ul.appendChild(li);
    });
    
    container.innerHTML = '';
    container.appendChild(ul);
}

/**
 * Подготавливает данные пазла для сохранения.
 * 
 * @param {Object} puzzleParams - Параметры пазла
 * @param {Array<HTMLElement>} presetElements - Элементы пресетов
 * @param {HTMLInputElement} customImageInputEl - Input для пользовательского изображения
 * @param {boolean} skipAlerts - Пропускать ли алерты
 * @returns {Object|null} Объект с данными для сохранения или null
 */
export function preparePuzzleSaveData(puzzleParams, presetElements, customImageInputEl, skipAlerts = false) {
    if (!puzzleParams.name) {
        if (!skipAlerts) alert("Пожалуйста, введите название для сохранения.");
        return null;
    }
    
    if (!puzzleParams.selectedImage) {
        if (!skipAlerts) alert("Пожалуйста, выберите или загрузите изображение.");
        return null;
    }
    
    if (!puzzleParams.piecePositions || puzzleParams.piecePositions.length !== puzzleParams.gridSize * puzzleParams.gridSize) {
        if (!skipAlerts) alert("Ошибка: Некорректные данные о позициях элементов.");
        return null;
    }
    
    const saveData = {
        id: puzzleParams.id,
        name: puzzleParams.name,
        gridSize: puzzleParams.gridSize,
        piecePositions: puzzleParams.piecePositions,
        selectedImage: puzzleParams.selectedImage,
        presetElements: presetElements,
        customImageInputEl: customImageInputEl
    };
    
    return saveData;
}

/**
 * Формирует FormData для отправки пазла на сервер.
 * 
 * @param {Object} saveData - Данные для сохранения
 * @returns {FormData} Объект FormData
 */
export function createPuzzleFormData(saveData) {
    const { name, gridSize, piecePositions, selectedImage, presetElements, customImageInputEl } = saveData;
    
    const formData = new FormData();
    formData.append('name', name);
    formData.append('gridSize', gridSize);
    formData.append('piecePositions', JSON.stringify(piecePositions));
    
    let isPreset = false;
    if (presetElements && presetElements.length > 0) {
        presetElements.forEach(preset => {
            const presetSrc = preset.dataset.src || preset.src;
            if (presetSrc === selectedImage) {
                isPreset = true;
                let presetPath = selectedImage.replace(window.location.origin, '');
                if (presetPath.startsWith('/static/')) {
                    presetPath = presetPath.substring('/static/'.length);
                }
                formData.append('preset_image_path', presetPath);
            }
        });
    }
    
    if (!isPreset && selectedImage.startsWith('data:image')) {
        const imageBlob = dataURLtoBlob(selectedImage);
        if (imageBlob) {
            const filename = (customImageInputEl && customImageInputEl.files.length > 0)
                ? customImageInputEl.files[0].name
                : `upload.${imageBlob.type.split('/')[1] || 'png'}`;
            formData.append('user_image_file', imageBlob, filename);
        } else {
            alert("Ошибка конвертации пользовательского изображения.");
            return null;
        }
    }
    
    return formData;
}