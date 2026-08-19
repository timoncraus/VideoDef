/**
 * Модуль для общей логики сохранения и загрузки игр.
 * Предоставляет унифицированный интерфейс для работы с API.
 */

import { isAuthenticated, redirectToLogin, getCookie } from './utils.js';

/**
 * Класс для управления сохранением и загрузкой игр.
 */
export class SaveLoadManager {
    /**
     * Создает экземпляр SaveLoadManager.
     * 
     * @param {Object} config - Конфигурация
     * @param {string} config.saveUrl - URL для сохранения
     * @param {string} config.loadUrl - URL для загрузки списка
     * @param {string} config.updateUrlTemplate - Шаблон URL для обновления (с placeholder {gameId})
     * @param {Function} config.getState - Функция получения состояния игры
     * @param {Function} config.applyState - Функция применения загруженного состояния
     * @param {Object} config.controls - DOM-элементы управления
     * @param {HTMLElement} config.controls.saveButton - Кнопка сохранения
     * @param {HTMLElement} config.controls.loadButton - Кнопка загрузки
     * @param {HTMLElement} config.controls.loadModal - Модальное окно загрузки
     * @param {HTMLElement} config.controls.loadListContainer - Контейнер списка игр
     * @param {HTMLElement} config.controls.loadConfirmBtn - Кнопка подтверждения загрузки
     * @param {HTMLElement} config.controls.loadCancelBtn - Кнопка отмены загрузки
     */
    constructor(config) {
        this.saveUrl = config.saveUrl;
        this.loadUrl = config.loadUrl;
        this.updateUrlTemplate = config.updateUrlTemplate;
        this.getState = config.getState;
        this.applyState = config.applyState;
        this.controls = config.controls;
        
        this.selectedGameToLoad = null;
        
        this.initControls();
    }
    
    /**
     * Инициализирует обработчики событий для элементов управления.
     */
    initControls() {
        const { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn } = this.controls;
        
        if (!saveButton || !loadButton || !loadModal || !loadListContainer || !loadConfirmBtn || !loadCancelBtn) {
            console.warn("Не все элементы управления найдены. Save/Load функциональность может быть ограничена.");
            return;
        }
        
        // Сохранение
        saveButton.addEventListener('click', () => this.handleSave());
        
        // Загрузка
        loadButton.addEventListener('click', () => this.handleLoad());
        loadConfirmBtn.addEventListener('click', () => this.handleConfirmLoad());
        loadCancelBtn.addEventListener('click', () => this.hideLoadModal());
        
        // Клик по элементу списка
        loadListContainer.addEventListener('click', (e) => {
            const target = e.target.closest('li');
            if (target) {
                loadListContainer.querySelectorAll('li').forEach(item => item.classList.remove('selected'));
                target.classList.add('selected');
                this.selectedGameToLoad = JSON.parse(target.dataset.gameData);
                loadConfirmBtn.disabled = false;
            }
        });
    }
    
    /**
     * Обрабатывает нажатие кнопки сохранения.
     */
    async handleSave() {
        // Проверка аутентификации через глобальную переменную или cookie
        const isAuth = (typeof window.isAuthenticated !== 'undefined') ? window.isAuthenticated : false;

        if (!isAuth) {
            alert("Для сохранения игры необходимо войти в аккаунт.");
            if (typeof window.loginUrl !== 'undefined') {
                window.location.href = window.loginUrl;
            }
            return;
        }
        
        const gameState = this.getState();
        if (!gameState) return;
        
        const formData = this.prepareFormData(gameState);
        const gameId = gameState.id;
        const url = gameId ? this.updateUrlTemplate.replace('{gameId}', gameId) : this.saveUrl;
        const method = gameId ? 'PUT' : 'POST';
        
        const { saveButton } = this.controls;
        const originalText = saveButton.textContent;
        saveButton.textContent = 'Сохранение...';
        saveButton.disabled = true;
        
        try {
            const csrfToken = typeof csrfToken !== 'undefined' ? csrfToken : getCookie('csrftoken');
            
            const response = await fetch(url, {
                method: method,
                headers: { 
                    'X-CSRFToken': csrfToken,
                    // Не устанавливаем Content-Type для FormData, браузер сделает это сам с boundary
                },
                body: formData
            });
            
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.message || `Ошибка сервера: ${response.status}`);
            }
            
            alert(result.message || 'Успех!');
            
            if (response.ok && result.id) {
                this.applyState({ id: result.id }, false);
            }
        } catch (error) {
            console.error("Ошибка при сохранении:", error);
            alert(`Ошибка при сохранении: ${error.message}`);
        } finally {
            saveButton.textContent = originalText;
            saveButton.disabled = false;
        }
    }
    
    /**
     * Подготавливает FormData для отправки на сервер.
     * 
     * @param {Object} gameState - Состояние игры
     * @returns {FormData} - Объект FormData
     */
    prepareFormData(gameState) {
        const formData = new FormData();
        
        for (const key in gameState) {
            if (gameState.hasOwnProperty(key)) {
                if (key === 'customImages' || key === 'files') {
                    // Обработка массива файлов
                    gameState[key].forEach(file => {
                        formData.append(`${key}[]`, file, file.name);
                    });
                } else if (gameState[key] !== null && gameState[key] !== undefined) {
                    const value = typeof gameState[key] === 'object' ? JSON.stringify(gameState[key]) : gameState[key];
                    formData.append(key, value);
                }
            }
        }
        
        return formData;
    }
    
    /**
     * Обрабатывает нажатие кнопки загрузки.
     */
    async handleLoad() {
        const isAuth = (typeof window.isAuthenticated !== 'undefined') ? window.isAuthenticated : false;
        
        if (!isAuth) {
            alert("Для загрузки игры необходимо войти в аккаунт.");
            if (typeof window.loginUrl !== 'undefined') {
                window.location.href = window.loginUrl;
            }
            return;
        }
        
        const { loadListContainer, loadConfirmBtn } = this.controls;
        
        loadListContainer.innerHTML = '<p>Загрузка...</p>';
        loadConfirmBtn.disabled = true;
        this.selectedGameToLoad = null;
        this.showLoadModal();
        
        try {
            const response = await fetch(this.loadUrl);
            const result = await response.json();
            
            if (result.status === 'success') {
                this.displayGameList(result.games || result.puzzles || []);
            } else {
                loadListContainer.innerHTML = `<p>Ошибка: ${result.message || 'Не удалось загрузить.'}</p>`;
            }
        } catch (error) {
            console.error("Сетевая ошибка при загрузке:", error);
            loadListContainer.innerHTML = '<p>Сетевая ошибка.</p>';
        }
    }
    
    /**
     * Отображает список игр в модальном окне.
     * Должен быть переопределен в наследниках для специфичного отображения.
     * 
     * @param {Array} games - Массив игр
     */
    displayGameList(games) {
        const { loadListContainer } = this.controls;
        
        if (!games || games.length === 0) {
            loadListContainer.innerHTML = '<p>У вас пока нет сохраненных игр этого типа.</p>';
            return;
        }
        
        const ul = document.createElement('ul');
        games.forEach(game => {
            const li = document.createElement('li');
            li.textContent = this.formatGameListItem(game);
            li.dataset.gameData = JSON.stringify(game);
            li.dataset.id = game.id;
            ul.appendChild(li);
        });
        
        loadListContainer.innerHTML = '';
        loadListContainer.appendChild(ul);
    }
    
    /**
     * Форматирует текст для элемента списка игр.
     * Должен быть переопределен в наследниках.
     * 
     * @param {Object} game - Объект игры
     * @returns {string} - Отформатированный текст
     */
    formatGameListItem(game) {
        return `${game.name} (ID: ${game.id})`;
    }
    
    /**
     * Обрабатывает подтверждение загрузки выбранной игры.
     */
    handleConfirmLoad() {
        if (this.selectedGameToLoad) {
            this.applyState(this.selectedGameToLoad, true);
            this.hideLoadModal();
        }
    }
    
    /**
     * Показывает модальное окно загрузки.
     */
    showLoadModal() {
        const { loadModal } = this.controls;
        if (loadModal) {
            loadModal.style.display = 'flex';
        }
    }
    
    /**
     * Скрывает модальное окно загрузки.
     */
    hideLoadModal() {
        const { loadModal } = this.controls;
        if (loadModal) {
            loadModal.style.display = 'none';
        }
    }
}