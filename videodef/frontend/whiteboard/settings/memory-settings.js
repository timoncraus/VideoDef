/**
 * Модуль для генерации HTML-настроек игры "Поиск пар" на интерактивной доске.
 */

/**
 * Генерирует HTML для панели настроек "Поиска пар".
 * 
 * @returns {string} HTML-строка с настройками "Поиска пар"
 */
export function getMemoryGameSettingsHTML() {
    return `
        <div class="memory-game-settings-container">
            <h2>Настройки "Поиск пар"</h2>
            <label for="game-name">Название игры:</label>
            <input type="text" id="game-name" placeholder="Моя игра в пары">
            <h3>Выберите набор карточек:</h3>
            <div class="presets-container">
                <div class="preset-set" data-set-name="fruits">Фрукты 🍓</div>
                <div class="preset-set" data-set-name="animals">Животные 🐼</div>
            </div>
            <label for="custom-images-input" class="upload-label">ИЛИ Загрузите свои изображения:</label>
            <input type="file" id="custom-images-input" accept="image/*" multiple>
            <div id="custom-images-preview" class="image-preview-container" style="display: none;">
                <p id="custom-images-info-text">Загружено изображений: <span id="custom-images-count">0</span></p>
                <div class="preview-grid"></div>
            </div>
            <label for="pair-count-select">Количество пар:</label>
            <select id="pair-count-select">
                <option value="2">2 пары</option>
                <option value="3">3 пары</option>
                <option value="4" selected>4 пары</option>
                <option value="5">5 пар</option>
                <option value="6">6 пар</option>
            </select>
            <div class="settings-buttons">
                <button id="start-memory-game">Перемешать</button>
                <button id="save-memory-game-btn">Сохранить</button>
                <button id="load-memory-game-btn">Загрузить</button>
            </div>
        </div>
    `;
}