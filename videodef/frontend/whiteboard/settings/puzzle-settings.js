/**
 * Модуль для генерации HTML-настроек игры "Пазл" на интерактивной доске.
 */

/**
 * Генерирует HTML для панели настроек пазла.
 * 
 * @param {string} imagesPath - Путь к статическим изображениям (по умолчанию '/static/images')
 * @returns {string} HTML-строка с настройками пазла
 */
export function getPuzzleSettingsHTML(imagesPath = '/static/images') {
    return `
        <div class="puzzle-settings-container">
            <h2>Настройки пазла</h2>
            <label for="puzzle-name">Название для сохранения:</label>
            <input type="text" id="puzzle-name" placeholder="Название пазла">
            <h3>Выберите изображение для пазла</h3>
            <div class="presets-container">
                <img src="${imagesPath}/british-cat.jpg" class="preset" data-src="${imagesPath}/british-cat.jpg" alt="Британский кот">
                <img src="${imagesPath}/tree.png" class="preset" data-src="${imagesPath}/tree.png" alt="Дерево">
            </div>
            <label class="upload-label">Загрузить своё:</label>
            <input type="file" id="custom-image" accept="image/*">
            <div id="image-preview-container" class="image-preview-container" style="display: none;">
                <img id="image-preview" src="#" alt="Предпросмотр">
                <p id="image-preview-text">Используется загруженное изображение.</p>
            </div>
            <label for="difficulty">Выберите сложность:</label>
            <select id="difficulty">
                <option value="2" selected>2x2</option>
                <option value="3">3x3</option>
                <option value="4">4x4</option>
            </select>
            <div class="settings-buttons">
                <button id="start-game">Начать игру</button>
                <button id="save-puzzle-btn">Сохранить</button>
                <button id="load-puzzle-btn">Загрузить</button>
            </div>
        </div>
    `;
}