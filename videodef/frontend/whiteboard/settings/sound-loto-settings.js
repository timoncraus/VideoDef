/**
 * Модуль для генерации HTML-настроек игры "Звуковое лото" на интерактивной доске.
 */

/**
 * Генерирует HTML для панели настроек "Звукового лото".
 * 
 * @returns {string} HTML-строка с настройками "Звукового лото"
 */
export function getSoundLotoSettingsHTML() {
    return `
        <div class="sound-loto-settings-container">
            <h2>Настройки "Звуковое лото"</h2>
            <label for="game-name">Название игры:</label>
            <input type="text" id="game-name" placeholder="Моё звуковое лото">
            
            <label>Выберите набор пар:</label>
            <div class="presets-container">
                <div class="preset-set" data-set-name="animals">Животные 🐶</div>
                <div class="preset-set" data-set-name="transport">Транспорт 🚂</div>
            </div>
            
            <label class="upload-label" style="font-weight: 600; color: #555; margin-bottom: 0.4rem; display: block;">
                Или загрузите свои пары:
            </label>
            <label style="font-weight: 500; color: #666; margin-bottom: 0.2rem;">Изображения:</label>
            <input type="file" id="custom-images-input" accept="image/*" multiple>
            <label style="font-weight: 500; color: #666; margin-bottom: 0.2rem;">Аудиофайлы:</label>
            <input type="file" id="custom-audios-input" accept="audio/*" multiple>
            
            <div id="pair-preview-container" class="pair-preview-container" style="display: none;">
            </div>
            
            <label for="rounds-count-select">Количество раундов:</label>
            <select id="rounds-count-select">
                <option value="2">2 раунда</option>
                <option value="3">3 раунда</option>
                <option value="4" selected>4 раунда</option>
                <option value="5">5 раундов</option>
                <option value="6">6 раундов</option>
            </select>
            
            <label for="cards-count-select">Карточек на экране:</label>
            <select id="cards-count-select">
                <option value="2">2 карточки</option>
                <option value="3">3 карточки</option>
                <option value="4" selected>4 карточки</option>
                <option value="6">6 карточек</option>
            </select>
            
            <div class="checkbox-group">
                <label class="checkbox-label">
                    <input type="checkbox" id="autoplay-checkbox" checked>
                    Автовоспроизведение звука
                </label>
                <label class="checkbox-label">
                    <input type="checkbox" id="show-labels-checkbox" checked>
                    Показывать подписи
                </label>
            </div>
            
            <div class="settings-buttons">
                <button id="start-sound-loto" class="game-btn game-btn-success">Начать игру</button>
                <button id="save-sound-loto-btn" class="game-btn game-btn-primary">Сохранить</button>
                <button id="load-sound-loto-btn" class="game-btn game-btn-secondary">Загрузить</button>
            </div>
        </div>
    `;
}