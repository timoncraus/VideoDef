/**
 * Модуль для управления UI элементами доски.
 * Управляет панелью инструментов, меню игр и панелью настроек.
 */

/**
 * Класс для управления UI доски.
 */
export class WhiteboardUI {
    /**
     * Создает экземпляр WhiteboardUI.
     * 
     * @param {Object} options - Опции
     * @param {Function} options.onToolChange - Callback при смене инструмента
     * @param {Function} options.onGameSelect - Callback при выборе игры
     * @param {Function} options.onClear - Callback при очистке доски
     * @param {Function} options.onSettingsToggle - Callback при переключении панели настроек
     */
    constructor(options = {}) {
        this.onToolChange = options.onToolChange || null;
        this.onGameSelect = options.onGameSelect || null;
        this.onClear = options.onClear || null;
        this.onSettingsToggle = options.onSettingsToggle || null;
        
        this.initToolbar();
        this.initGameMenu();
        this.initSettingsPanel();
    }
    
    /**
     * Инициализирует панель инструментов.
     */
    initToolbar() {
        const penBtn = document.getElementById('pen_btn');
        const eraserBtn = document.getElementById('eraser_btn');
        const colorPicker = document.getElementById('colorPicker');
        const thickness = document.getElementById('thickness');
        const clearBtn = document.getElementById('clear_btn');
        
        if (penBtn) {
            penBtn.addEventListener('click', () => {
                this.setActiveTool('pen_btn');
                if (this.onToolChange) this.onToolChange('pen');
            });
        }
        
        if (eraserBtn) {
            eraserBtn.addEventListener('click', () => {
                this.setActiveTool('eraser_btn');
                if (this.onToolChange) this.onToolChange('eraser');
            });
        }
        
        if (colorPicker) {
            colorPicker.addEventListener('input', (e) => {
                if (this.onToolChange) this.onToolChange('color', e.target.value);
            });
        }
        
        if (thickness) {
            thickness.addEventListener('input', (e) => {
                if (this.onToolChange) this.onToolChange('thickness', e.target.value);
            });
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                if (this.onClear) this.onClear();
            });
        }
    }
    
    /**
     * Устанавливает активный инструмент.
     * 
     * @param {string} activeId - ID активной кнопки
     */
    setActiveTool(activeId) {
        document.querySelectorAll('.tool').forEach(btn => btn.classList.remove('active'));
        if (activeId) {
            const btn = document.getElementById(activeId);
            if (btn) btn.classList.add('active');
        }
    }
    
    /**
     * Инициализирует меню игр.
     */
    initGameMenu() {
        const gamesBtn = document.getElementById('games_btn');
        const dropdown = document.getElementById('game-menu');
        
        if (gamesBtn && dropdown) {
            gamesBtn.addEventListener('click', () => {
                this.updateGameMenuPos();
                dropdown.classList.toggle('show');
            });
            
            window.addEventListener('resize', () => {
                if (dropdown.classList.contains('show')) {
                    this.updateGameMenuPos();
                }
            });
            
            window.addEventListener('click', (e) => {
                if (!gamesBtn.contains(e.target) && !dropdown.contains(e.target)) {
                    dropdown.classList.remove('show');
                }
            });
            
            document.querySelectorAll('.game-option').forEach(option => {
                option.addEventListener('click', () => {
                    const gameName = option.dataset.name;
                    if (this.onGameSelect) this.onGameSelect(gameName);
                    dropdown.classList.remove('show');
                });
            });
        }
    }
    
    /**
     * Обновляет позицию меню игр.
     */
    updateGameMenuPos() {
        const gamesBtn = document.getElementById('games_btn');
        const gameMenu = document.getElementById('game-menu');
        
        if (gamesBtn && gameMenu) {
            const rect = gamesBtn.getBoundingClientRect();
            gameMenu.style.top = `${rect.bottom + window.scrollY}px`;
            gameMenu.style.left = `${rect.left + window.scrollX}px`;
        }
    }
    
    /**
     * Инициализирует панель настроек.
     */
    initSettingsPanel() {
        const toggleButton = document.getElementById('toggle-settings-btn');
        const settingsPanel = document.querySelector('.settings-panel');
        
        if (toggleButton && settingsPanel) {
            toggleButton.addEventListener('click', () => {
                settingsPanel.classList.toggle('hidden');
                toggleButton.textContent = settingsPanel.classList.contains('hidden') 
                    ? 'Открыть настройки' 
                    : 'Закрыть настройки';
                
                if (this.onSettingsToggle) {
                    setTimeout(() => this.onSettingsToggle(), 0);
                }
            });
        }
    }
    
    /**
     * Очищает динамические настройки и слушатели на общих элементах модального окна.
     */
    clearDynamicSettings() {
        const settingsPanel = document.querySelector('.settings-panel');
        if (!settingsPanel) return;
        
        const dynamicElements = settingsPanel.querySelectorAll('.dynamic-setting');
        dynamicElements.forEach(el => el.remove());

        const loadConfirmBtn = document.getElementById('load-confirm-btn');
        if (loadConfirmBtn) {
            const newBtn = loadConfirmBtn.cloneNode(true);
            loadConfirmBtn.parentNode.replaceChild(newBtn, loadConfirmBtn);
            newBtn.disabled = true; // Сбрасываем состояние кнопки
        }
    }
}