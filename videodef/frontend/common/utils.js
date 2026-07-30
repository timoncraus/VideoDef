/**
 * Общие утилиты для всех модулей игр.
 * Содержит вспомогательные функции, используемые в различных частях приложения.
 */

/**
 * Конвертирует строку Data URL в объект Blob.
 * Необходимо для отправки пользовательских изображений на сервер через FormData.
 * 
 * @param {string} dataURL - Строка Data URL (например, "data:image/png;base64,...")
 * @returns {Blob|null} - Объект Blob или null в случае ошибки
 */
export function dataURLtoBlob(dataURL) {
    try {
        // Разделяем строку на метаданные (MIME-тип) и данные Base64
        const parts = dataURL.split(';base64,');
        const contentType = parts[0].split(':')[1];
        
        // Декодируем Base64 строку в бинарную строку
        const raw = window.atob(parts[1]);
        const rawLength = raw.length;
        
        // Создаем массив 8-битных беззнаковых целых чисел
        const uInt8Array = new Uint8Array(rawLength);
        for (let i = 0; i < rawLength; ++i) {
            uInt8Array[i] = raw.charCodeAt(i);
        }
        
        // Создаем и возвращаем Blob с указанным MIME-типом
        return new Blob([uInt8Array], { type: contentType });
    } catch (error) {
        console.error("Ошибка конвертации Data URL в Blob:", error);
        return null;
    }
}

/**
 * Перемешивает элементы массива случайным образом (алгоритм Фишера-Йетса).
 * 
 * @param {Array<any>} array - Массив для перемешивания
 * @returns {Array<any>} - Новый массив с перемешанными элементами
 */
export function shuffle(array) {
    const newArray = [...array];
    for (let i = newArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
    }
    return newArray;
}

/**
 * Получает CSRF-токен из cookies.
 * 
 * @param {string} name - Имя cookie (обычно 'csrftoken')
 * @returns {string|null} - Значение CSRF-токена или null
 */
export function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Проверяет, аутентифицирован ли пользователь.
 * 
 * @returns {boolean} - true, если пользователь аутентифицирован
 */
export function isAuthenticated() {
    return typeof window.isAuthenticated !== 'undefined' && window.isAuthenticated;
}

/**
 * Перенаправляет на страницу входа.
 */
export function redirectToLogin() {
    if (typeof window.loginUrl !== 'undefined') {
        window.location.href = window.loginUrl;
    } else {
        console.error("URL для входа не определен");
    }
}

/**
 * Генерирует уникальный ID для элемента.
 * 
 * @param {string} prefix - Префикс для ID (например, 'game', 'image')
 * @param {number} counter - Счетчик для уникальности
 * @returns {string} - Уникальный ID (например, 'game-1', 'image-2')
 */
export function generateUniqueId(prefix, counter) {
    return `${prefix}-${counter}`;
}

/**
 * Безопасно парсит JSON строку.
 * 
 * @param {string} jsonString - JSON строка для парсинга
 * @param {any} defaultValue - Значение по умолчанию в случае ошибки
 * @returns {any} - Распарсенный объект или defaultValue
 */
export function safeJsonParse(jsonString, defaultValue = null) {
    try {
        return JSON.parse(jsonString);
    } catch (error) {
        console.error("Ошибка парсинга JSON:", error);
        return defaultValue;
    }
}

/**
 * Делает DOM-элемент перетаскиваемым.
 * 
 * @param {HTMLElement} element - Элемент для перетаскивания
 * @param {Function} onDrag - Callback при перетаскивании (x, y)
 * @param {Function} onDragEnd - Callback при завершении перетаскивания (x, y)
 */
export function makeDraggable(element, onDrag, onDragEnd) {
    let dragStartX, dragStartY, initialLeft, initialTop;
    
    const onMouseDown = (e) => {
        if (e.button !== 0) return; // Только левая кнопка мыши
        
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        initialLeft = parseFloat(element.style.left) || 0;
        initialTop = parseFloat(element.style.top) || 0;
        
        element.style.cursor = 'grabbing';
        document.body.style.userSelect = 'none';
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
        
        e.stopPropagation();
    };
    
    const onMouseMove = (e) => {
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        const newLeft = initialLeft + dx;
        const newTop = initialTop + dy;
        
        element.style.left = `${newLeft}px`;
        element.style.top = `${newTop}px`;
        
        if (onDrag) {
            onDrag(newLeft, newTop);
        }
    };
    
    const onMouseUp = () => {
        element.style.cursor = 'grab';
        document.body.style.userSelect = '';
        
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        
        if (onDragEnd) {
            const finalLeft = parseFloat(element.style.left) || 0;
            const finalTop = parseFloat(element.style.top) || 0;
            onDragEnd(finalLeft, finalTop);
        }
    };
    
    element.addEventListener('mousedown', onMouseDown);
    element.style.cursor = 'grab';
}

/**
 * Делает DOM-элемент изменяемым по размеру.
 * 
 * @param {HTMLElement} element - Элемент для изменения размера
 * @param {Function} onResize - Callback при изменении размера (width, height)
 * @param {Function} onResizeEnd - Callback при завершении изменения (width, height)
 */
export function makeResizable(element, onResize, onResizeEnd) {
    const resizeHandle = document.createElement('div');
    resizeHandle.className = 'resize-handle';
    element.appendChild(resizeHandle);
    
    let resizeStartX, resizeStartY, initialWidth, initialHeight;
    
    resizeHandle.addEventListener('mousedown', (e) => {
        e.stopPropagation();
        
        const rect = element.getBoundingClientRect();
        resizeStartX = e.clientX;
        resizeStartY = e.clientY;
        initialWidth = rect.width;
        initialHeight = rect.height;
        
        document.body.style.userSelect = 'none';
        
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
    
    const onMouseMove = (e) => {
        const dx = e.clientX - resizeStartX;
        const dy = e.clientY - resizeStartY;
        const newWidth = Math.max(200, initialWidth + dx);
        const newHeight = Math.max(150, initialHeight + dy);
        
        element.style.width = `${newWidth}px`;
        element.style.height = `${newHeight}px`;
        
        if (onResize) {
            onResize(newWidth, newHeight);
        }
    };
    
    const onMouseUp = () => {
        document.body.style.userSelect = '';
        
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
        
        if (onResizeEnd) {
            const finalWidth = parseFloat(element.style.width) || 0;
            const finalHeight = parseFloat(element.style.height) || 0;
            onResizeEnd(finalWidth, finalHeight);
        }
    };
}