import { getPuzzleParts, placePieces, createPuzzle, updatePuzzleImage } from './puzzle-logic.js';

window.createPuzzleSeparately = createPuzzleSeparately;

/**
 * Конвертирует строку Data URL в объект Blob.
 * Необходимо для отправки пользовательских изображений на сервер через FormData.
 * @param {string} dataURL - Строка Data URL
 * @returns {Blob|null} - Объект Blob или null в случае ошибки.
 */
function dataURLtoBlob(dataURL) {
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
 * Отображает список сохраненных пазлов в указанном контейнере.
 * @param {HTMLElement} container - DOM-элемент (например, div), куда будет добавлен список.
 * @param {Array<object>} puzzles - Массив объектов, каждый из которых представляет сохраненный пазл.
 */
function displayPuzzleList(container, puzzles) {
    if (puzzles.length === 0) {
        container.innerHTML = '<p>У вас пока нет сохраненных пазлов.</p>';
        return;
    }

    const ul = document.createElement('ul');
    // Проходим по каждому объекту пазла в массиве
    puzzles.forEach(puzzle => {
        const li = document.createElement('li');
        let imageInfo = puzzle.has_user_image ? "(свое фото)" : "(пресет)";
        li.textContent = `${puzzle.name} (${puzzle.grid_size}x${puzzle.grid_size}) ${imageInfo}`;
        // Сохраняем полные данные пазла в data-атрибут 'puzzleData' в виде JSON строки.
        li.dataset.puzzleData = JSON.stringify(puzzle);
        li.dataset.id = puzzle.id;
        ul.appendChild(li);
    });
    container.innerHTML = '';
    container.appendChild(ul);
}

/**
 * Инициализирует общую логику сохранения и загрузки пазлов.
 * @param {function} getPuzzleState - Функция, возвращающая объект с текущим состоянием пазла для сохранения
 * @param {function} applyLoadedState - Функция, принимающая загруженные данные пазла и применяющая их к текущему экземпляру.
 * @param {object} controls - Объект с DOM-элементами управления { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn }
 */
function initSaveLoadFeatures(getPuzzleState, applyLoadedState, controls) {
    const { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn } = controls;

    // Проверка наличия всех необходимых элементов управления для сохранения и загрузки
    if (!saveButton || !loadButton || !loadModal || !loadListContainer || !loadConfirmBtn || !loadCancelBtn) {
        console.error("Ошибка сохранения/загрузки: отсутствует один или несколько элементов управления.");
        if (loadModal) {
             console.error("Отсутствуют элементы:", { saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn });
        } else {
            console.warn("Модальное окно загрузки не найдено, загрузка может быть ограничена");
            if (!saveButton) {
                 console.error("Кнопка сохранения также отсутствует.");
                 return;
            }
        }
    }

    let selectedPuzzleToLoad = null;

    // --- Обработчик нажатия кнопки "Сохранить" ---
    const saveHandler = async () => {
        if (typeof isAuthenticated === 'undefined' || typeof loginUrl === 'undefined') {
            console.error("Ошибка: Переменные isAuthenticated или loginUrl не определены. Проверьте HTML-шаблон.");
            alert("Произошла ошибка конфигурации. Невозможно проверить статус пользователя.");
            return;
        }
        if (!isAuthenticated) {
            alert("Чтобы сохранить игру, пожалуйста, войдите в свой аккаунт.");
            window.location.href = loginUrl; // Перенаправляем на страницу входа
            return;
        }

        const currentState = getPuzzleState();
        if (!currentState) return;

        // Извлекаем необходимые данные из полученного состояния
        const { name, gridSize, piecePositions, selectedImage, presetElements, customImageInputEl } = currentState;

        // --- Валидация данных перед сохранением ---
        if (!name) {
            alert("Пожалуйста, введите название для сохранения.");
            return;
        }
        if (!selectedImage) {
            alert("Пожалуйста, выберите или загрузите изображение.");
            return;
        }
        if (!piecePositions || piecePositions.length !== gridSize * gridSize) {
            alert("Ошибка: Некорректные данные о позициях элементов.");
            console.error("Недопустимые позиции элементов для сохранения", piecePositions, "Grid size:", gridSize);
            return;
        }

        // --- Формирование данных для отправки на сервер с использованием FormData ---
        const formData = new FormData();
        formData.append('name', name);
        formData.append('gridSize', gridSize);
        formData.append('piecePositions', JSON.stringify(piecePositions));

        // Определяем, используется ли изображение-пресет или пользовательское изображение
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
                alert("Ошибка конвертации пользовательского изображения для сохранения."); return;
            }
        } else if (!isPreset) {
             if (selectedImage && (selectedImage.includes('/media/puzzle_images/') || selectedImage.includes('/static/'))) {
                  alert("Невозможно сохранить: выбранное изображение было загружено ранее. Пожалуйста, выберите пресет или загрузите изображение заново, чтобы сохранить текущее состояние.");
                  console.warn("Не удается сохранить существующее пользовательское изображение по URL-адресу:", selectedImage);
                  return;
             } else {
                 alert("Не удалось определить источник изображения для сохранения.");
                 console.warn("Невозможно сохранить источник изображения:", selectedImage);
                 return;
             }
        }

        // --- Отправка запроса на сервер для сохранения пазла ---
        saveButton.textContent = 'Сохранение...'; saveButton.disabled = true;
        try {
            const response = await fetch(savePuzzleUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': csrfToken, 'Accept': 'application/json' },
                body: formData,
            });
            const result = await response.json();
            if (response.ok && result.status === 'success') {
                alert(result.message || 'Пазл сохранен!');
            } else {
                alert(`Ошибка сохранения: ${result.message || response.statusText}`);
            }
        } catch (error) {
            alert("Сетевая ошибка при сохранении.");
            console.error("Ошибка сохранения:", error);
        } finally {
            saveButton.textContent = saveButton.dataset.originalText || 'Сохранить';
            saveButton.disabled = false;
        }
    };

    // --- Назначение обработчика на кнопку "Сохранить" ---
    if (saveButton) {
        saveButton.dataset.originalText = saveButton.textContent;
        saveButton.removeEventListener('click', saveButton.clickHandler);
        saveButton.addEventListener('click', saveHandler);
        saveButton.clickHandler = saveHandler;
    }


    // --- Логика Загрузки ---
    if (loadButton && loadModal && loadListContainer && loadConfirmBtn && loadCancelBtn) {
        // --- Обработчик нажатия кнопки "Загрузить" ---
        const loadHandler = async () => {
            if (typeof isAuthenticated === 'undefined' || typeof loginUrl === 'undefined') {
                console.error("Ошибка: Переменные isAuthenticated или loginUrl не определены. Проверьте HTML-шаблон.");
                alert("Произошла ошибка конфигурации. Невозможно проверить статус пользователя.");
                return;
            }
            if (!isAuthenticated) {
                alert("Чтобы загрузить сохраненные игры, пожалуйста, войдите в свой аккаунт.");
                window.location.href = loginUrl; // Перенаправляем на страницу входа
                return;
            }

             loadListContainer.innerHTML = '<p>Загрузка...</p>';
             loadConfirmBtn.disabled = true;
             selectedPuzzleToLoad = null;
             loadModal.style.display = 'flex';

             try {
                 const response = await fetch(loadPuzzlesUrl, {
                     method: 'GET', headers: { 'Accept': 'application/json' }
                 });
                 const result = await response.json();
                 if (response.ok && result.status === 'success') {
                     displayPuzzleList(loadListContainer, result.puzzles);
                 } else {
                     loadListContainer.innerHTML = `<p>Ошибка: ${result.message || 'Не удалось загрузить.'}</p>`;
                 }
             } catch (error) {
                 loadListContainer.innerHTML = '<p>Сетевая ошибка при загрузке.</p>';
                 console.error("Ошибка в списке загрузки:", error);
             }
        };
        loadButton.removeEventListener('click', loadButton.clickHandler);
        loadButton.addEventListener('click', loadHandler);
        loadButton.clickHandler = loadHandler;

        // --- Обработчики Модального окна ---
        const cancelHandler = () => { loadModal.style.display = 'none'; };
        loadCancelBtn.removeEventListener('click', loadCancelBtn.clickHandler);
        loadCancelBtn.addEventListener('click', cancelHandler);
        loadCancelBtn.clickHandler = cancelHandler;

        const listClickHandler = (event) => {
            const target = event.target;
            if (target.tagName === 'LI') {
                 loadListContainer.querySelectorAll('li').forEach(item => item.classList.remove('selected'));
                 target.classList.add('selected');
                 try {
                     selectedPuzzleToLoad = JSON.parse(target.dataset.puzzleData);
                     loadConfirmBtn.disabled = false;
                 } catch (e) {
                     console.error("Ошибка парсинга данных пазла:", e);
                     selectedPuzzleToLoad = null;
                     loadConfirmBtn.disabled = true;
                 }
            }
        };
        loadListContainer.removeEventListener('click', loadListContainer.clickHandler);
        loadListContainer.addEventListener('click', listClickHandler);
        loadListContainer.clickHandler = listClickHandler;

        const confirmHandler = () => {
             if (!selectedPuzzleToLoad) return;
             applyLoadedState(selectedPuzzleToLoad);
             loadModal.style.display = 'none';
        };
        loadConfirmBtn.removeEventListener('click', loadConfirmBtn.clickHandler);
        loadConfirmBtn.addEventListener('click', confirmHandler);
        loadConfirmBtn.clickHandler = confirmHandler;

    } else if (loadButton) {
        loadButton.disabled = true;
        loadButton.title = "Модальное окно для загрузки не найдено";
        console.warn("Кнопка загрузки найдена, но отсутствуют элементы модального окна.");
    }

    console.log("Функции сохранения/загрузки инициализированны");
}

/**
 * Назначает обработчики для пользовательского изображения, пресетов и сложности.
 * @param {object} options - Объект с параметрами настройки.
 * @param {HTMLInputElement} options.customInput - Поле для загрузки пользовательского фото.
 * @param {Array<HTMLElement>} options.presets - Массив HTML-элементов, представляющих пресеты изображений.
 * @param {HTMLSelectElement} options.difficultySelect - Выпадающий список для выбора сложности (размера сетки).
 * @param {HTMLButtonElement} [options.startBtn] - Кнопка "Начать игру"
 * @param {object} options.puzzleParams - Объект параметров текущего пазла
 * @param {HTMLElement} options.puzzleContainer - Контейнер для кусочков пазла
 * @param {HTMLElement} options.message - Элемент для сообщений
 * @param {boolean} [options.instantUpdate=false] - Обновлять ли пазл сразу
 * @param {function} [options.onStateChange] - Колбэк при изменении состояния
 */
function setupPuzzleControls({
    customInput,
    presets,
    difficultySelect,
    startBtn,
    puzzleParams,
    puzzleContainer,
    message,
    instantUpdate = false,
    onStateChange
}) {
    // Проверка наличия обязательных элементов и параметров
    if (!customInput || !presets || !difficultySelect || !puzzleParams || !puzzleContainer || !message) {
        console.error("настройка элементов управления пазлом: отсутствуют необходимые элементы или параметры.");
        return;
    }

    // Пользовательское изображение
    const customImageHandler = (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => {
                puzzleParams.selectedImage = reader.result;
                puzzleParams.isPreset = false;
                puzzleParams.imageFile = file;
                presets.forEach(p => p.classList.remove('selected'));
                const previewContainer = document.getElementById('image-preview-container');
                const previewImg = document.getElementById('image-preview');
                const previewText = document.getElementById('image-preview-text');
                 if(previewContainer && previewImg && previewText) {
                      previewImg.src = reader.result;
                      previewText.textContent = `Используется: ${file.name}`;
                      previewContainer.style.display = 'block';
                 }

                if (instantUpdate) {
                    createPuzzle(puzzleContainer, puzzleParams, message, false);
                }
                if (onStateChange) onStateChange(puzzleParams);
            };
            reader.readAsDataURL(file);
        } else {
             if (puzzleParams.selectedImage && puzzleParams.selectedImage.startsWith('data:image')) {
                 puzzleParams.selectedImage = null;
                 puzzleParams.imageFile = null;
                 const previewContainer = document.getElementById('image-preview-container');
                 if(previewContainer) previewContainer.style.display = 'none';
                 if (instantUpdate) puzzleContainer.innerHTML = '<p>Выберите изображение</p>';
             }
             if (onStateChange) onStateChange(puzzleParams);
        }
    };
    customInput.removeEventListener('change', customInput.changeHandler);
    customInput.addEventListener('change', customImageHandler);
    customInput.changeHandler = customImageHandler;

    // Пресеты
    presets.forEach(preset => {
        const presetClickHandler = () => {
            presets.forEach(p => p.classList.remove('selected'));
            preset.classList.add('selected');
            puzzleParams.selectedImage = preset.dataset.src;
            puzzleParams.isPreset = true;
            puzzleParams.imageFile = null;
            customInput.value = '';
            const previewContainer = document.getElementById('image-preview-container');
            if(previewContainer) previewContainer.style.display = 'none';

            if (instantUpdate) {
                createPuzzle(puzzleContainer, puzzleParams, message, false);
            }
            if (onStateChange) onStateChange(puzzleParams);
        };
        preset.removeEventListener('click', preset.clickHandler);
        preset.addEventListener('click', presetClickHandler);
        preset.clickHandler = presetClickHandler;
    });

    // Сложность (размер сетки)
    const difficultyHandler = (e) => {
        const newSize = parseInt(e.target.value, 10);
        if (newSize !== puzzleParams.gridSize) {
            puzzleParams.gridSize = newSize;
            puzzleParams.piecePositions = [];
            console.log(`Размер сетки изменен на ${newSize}, позиции очищены.`);
            if (instantUpdate) {
                 createPuzzle(puzzleContainer, puzzleParams, message, false);
            }
            if (onStateChange) onStateChange(puzzleParams);
        }
    };
    difficultySelect.removeEventListener('change', difficultySelect.changeHandler);
    difficultySelect.addEventListener('change', difficultyHandler);
    difficultySelect.changeHandler = difficultyHandler;

    // Кнопка "Начать игру"
    if (startBtn) {
        const startHandler = () => {
            if (!puzzleParams.selectedImage) {
                alert("Пожалуйста, выберите или загрузите изображение.");
                return;
            }
            const useLoadedPositions = puzzleParams.piecePositions && puzzleParams.piecePositions.length === puzzleParams.gridSize * puzzleParams.gridSize;
            createPuzzle(puzzleContainer, puzzleParams, message, useLoadedPositions);
        };
        startBtn.removeEventListener('click', startBtn.clickHandler);
        startBtn.addEventListener('click', startHandler);
        startBtn.clickHandler = startHandler;
    }

    console.log("Настройка элементов управления пазлом завершена.");
}

/**
 * Инициализирует интерфейс и логику для отдельной страницы пазла.
 * Эта функция находит все необходимые элементы управления на странице, настраивает их
 * с помощью `setupPuzzleControls` и инициализирует функции сохранения/загрузки
 * с помощью `initSaveLoadFeatures`. Пазл создается по нажатию кнопки "Начать игру".
 */
function createPuzzleSeparately() {
    const [localPuzzleParams, puzzleContainer, message] = getPuzzleParts();
    localPuzzleParams.onWhiteboard = false;
    localPuzzleParams.name = "";

    const wrapper = document.getElementById('puzzle-wrapper');
    if (!wrapper) { console.error("#puzzle-wrapper not found!"); return; }
    wrapper.innerHTML = '';
    wrapper.appendChild(puzzleContainer);
    wrapper.appendChild(message);

    // Находим контролы на странице игры
    const customInput = document.getElementById('custom-image');
    const difficultySelect = document.getElementById('difficulty');
    const presetsNodeList = document.querySelectorAll('.preset');
    const startBtn = document.getElementById('start-game');
    const puzzleNameInput = document.getElementById('puzzle-name');
    const saveButton = document.getElementById('save-puzzle-btn');
    const loadButton = document.getElementById('load-puzzle-btn');
    const loadModal = document.getElementById('load-puzzle-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');

    if (!customInput || !difficultySelect || !presetsNodeList?.length || !startBtn || !puzzleNameInput || !saveButton || !loadButton || !loadModal) {
        console.error("Элементы управления на странице пазлов не найдены!"); return;
    }
    const presets = Array.from(presetsNodeList);

    // Настройка обработчиков
    setupPuzzleControls({
        customInput, presets, difficultySelect, startBtn,
        puzzleParams: localPuzzleParams,
        puzzleContainer, message,
        instantUpdate: false,
        onStateChange: (params) => {
             if (params && typeof params.name !== 'undefined') {
                 puzzleNameInput.value = params.name;
             }
        }
    });

    // Собираем текущее состояние пазла данной страницы для сохранения
    const getPuzzleStateForSeparatePage = () => {
        localPuzzleParams.name = puzzleNameInput.value.trim();
        return {
            name: localPuzzleParams.name,
            gridSize: localPuzzleParams.gridSize,
            piecePositions: localPuzzleParams.piecePositions,
            selectedImage: localPuzzleParams.selectedImage,
            presetElements: presets,
            customImageInputEl: customInput
        };
    };

    // Применяем загруженное состояние пазла к странице
    const applyLoadedStateForSeparatePage = (puzzleData) => {
        console.log("Применение загруженного состояния к отдельной странице:", puzzleData);
        localPuzzleParams.gridSize = puzzleData.grid_size;
        localPuzzleParams.piecePositions = puzzleData.piece_positions || [];
        localPuzzleParams.name = puzzleData.name;
        localPuzzleParams.selectedImage = puzzleData.image_url;
        localPuzzleParams.isPreset = !!puzzleData.preset_path;
        localPuzzleParams.imageFile = null;

        difficultySelect.value = puzzleData.grid_size;
        puzzleNameInput.value = puzzleData.name;
        customInput.value = '';
         const previewContainer = document.getElementById('image-preview-container');
         if(previewContainer) previewContainer.style.display = 'none';

        presets.forEach(p => p.classList.remove('selected'));
        if (localPuzzleParams.isPreset) {
            let found = false;
            presets.forEach(preset => {
                 const presetSrcRelative = (preset.dataset.src || preset.src).replace(window.location.origin, '');
                 const loadedUrlRelative = puzzleData.image_url.replace(window.location.origin, '');
                 if (presetSrcRelative === loadedUrlRelative) {
                     preset.classList.add('selected');
                     found = true;
                 }
            });
            if (!found) console.warn("Загруженное предустановленное изображение не найдено:", puzzleData.image_url);
        } else {
            // Показываем превью для загруженного пользовательского фото
             const previewImg = document.getElementById('image-preview');
             const previewText = document.getElementById('image-preview-text');
             if(previewContainer && previewImg && previewText && puzzleData.image_url) {
                 previewImg.src = puzzleData.image_url;
                 previewText.textContent = `Загружено: ${puzzleData.name}`;
                 previewContainer.style.display = 'block';
             } else {
                 console.log("Загруженное пользовательское изображение:", puzzleData.image_url);
             }
        }

        alert(`Пазл "${puzzleData.name}" (${puzzleData.grid_size}x${puzzleData.grid_size}) загружен. Нажмите "Начать игру", чтобы собрать его.`);
        puzzleContainer.innerHTML = '<p>Пазл загружен. Нажмите "Начать игру".</p>';
        message.style.display = 'none';
    };

    // Инициализируем Save/Load
    initSaveLoadFeatures(getPuzzleStateForSeparatePage, applyLoadedStateForSeparatePage, {
        saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn
    });

    if (presets.length > 0 && !localPuzzleParams.selectedImage) {
        presets[0].click();
    }
    puzzleContainer.innerHTML = '<p>Выберите настройки и нажмите "Начать игру"</p>';
    message.style.display = 'none';

    console.log("Страница пазла инициализирована");
}

/**
 * Создает интерактивный пазл внутри игрового контейнера на доске.
 * @param {HTMLElement} gameWrapper - Родительский контейнер для пазла
 */
export function createPuzzleOnBoard(gameWrapper) {
    const [localPuzzleParams, puzzleContainer, message] = getPuzzleParts();
    
    // Устанавливаем параметры по умолчанию для нового пазла на доске
    localPuzzleParams.onWhiteboard = true;
    localPuzzleParams.name = "Новый пазл";
    localPuzzleParams.gridSize = 2;
    localPuzzleParams.selectedImage = null;
    localPuzzleParams.isPreset = false;
    localPuzzleParams.imageFile = null;
    localPuzzleParams.piecePositions = [];

    gameWrapper.puzzleParams = localPuzzleParams;
    gameWrapper.puzzleContainer = puzzleContainer;
    gameWrapper.puzzleMessage = message;

    const closeButton = gameWrapper.querySelector('.paste-game-close');
    const resizeHandle = gameWrapper.querySelector('.resize-handle');
    gameWrapper.innerHTML = '';
    if (closeButton) gameWrapper.appendChild(closeButton);
    if (resizeHandle) gameWrapper.appendChild(resizeHandle);

    gameWrapper.appendChild(puzzleContainer);
    gameWrapper.appendChild(message);
    puzzleContainer.innerHTML = '<p style="text-align: center; padding: 20px;">Активируйте пазл и выберите настройки в панели справа.</p>';
    message.style.display = 'none';

    console.log("Экземпляр пазла создан на доске и ожидает активации");
}

/**
 * Настраивает контролы и Save/Load для активного пазла на доске.
 */
export function setupWhiteboardPuzzleSaveLoad() {
    console.log("Пытаюсь настроить сохранение/загрузку для активного пазла на доске...");

    // Проверяем, найден ли активный пазл и содержит ли он необходимые данные
    const activeGameWrapper = document.querySelector('.paste-game-wrapper.active-game');
    if (!activeGameWrapper || !activeGameWrapper.puzzleParams || !activeGameWrapper.puzzleContainer || !activeGameWrapper.puzzleMessage) {
        console.warn("На доске не найден активный пазл или в нём отсутствуют необходимые данные. Настройка пропущена.");
        return;
    }

    const activePuzzleParams = activeGameWrapper.puzzleParams;
    const activePuzzleContainer = activeGameWrapper.puzzleContainer;
    const activePuzzleMessage = activeGameWrapper.puzzleMessage;

    const settingsPanel = document.querySelector('.settings-panel');
    if (!settingsPanel) {
        console.error("Панель настроек не найдена. Не удается настроить элементы управления пазлом на доске");
        return;
    }

    const puzzleNameInput = settingsPanel.querySelector('#puzzle-name');
    const customInput = settingsPanel.querySelector('#custom-image');
    const difficultySelect = settingsPanel.querySelector('#difficulty');
    const presetsNodeList = settingsPanel.querySelectorAll('.preset');
    const saveButton = settingsPanel.querySelector('#save-puzzle-btn');
    const loadButton = settingsPanel.querySelector('#load-puzzle-btn');
    const startBtn = settingsPanel.querySelector('#start-game');

    const loadModal = document.getElementById('load-puzzle-modal');
    const loadListContainer = document.getElementById('load-list-container');
    const loadConfirmBtn = document.getElementById('load-confirm-btn');
    const loadCancelBtn = document.getElementById('load-cancel-btn');

    if (!puzzleNameInput || !customInput || !difficultySelect || !presetsNodeList?.length || !saveButton || !loadButton) {
        console.error("Основные элементы управления пазлом  (#puzzle-name, #custom-image, #difficulty, .preset, #save-puzzle-btn, #load-puzzle-btn) отсутствуют на панели настроек доски!");
        return;
    }
    const presets = Array.from(presetsNodeList);

    if (startBtn) {
        startBtn.style.display = 'none';
    }

    // Настраиваем обработчика
    setupPuzzleControls({
        customInput, presets, difficultySelect, startBtn: null,
        puzzleParams: activePuzzleParams,
        puzzleContainer: activePuzzleContainer,
        message: activePuzzleMessage,
        instantUpdate: true,
        onStateChange: (params) => {
             if (params && typeof params.name !== 'undefined') {
                 puzzleNameInput.value = params.name;
             }
            console.log("Изменено состояние активного пазла на доске:", params);
        }
    });

    puzzleNameInput.value = activePuzzleParams.name || '';
    difficultySelect.value = activePuzzleParams.gridSize;

    // Сбрасываем выделение пресетов и состояние превью в панели настроек
    presets.forEach(p => p.classList.remove('selected'));
    const previewContainer = settingsPanel.querySelector('#image-preview-container');
    const previewImg = settingsPanel.querySelector('#image-preview');
    const previewText = settingsPanel.querySelector('#image-preview-text');
    if(previewContainer) previewContainer.style.display = 'none';

    // Устанавливаем правильный пресет или показываем превью пользовательского фото в панели настроек
    if (activePuzzleParams.isPreset && activePuzzleParams.selectedImage) {
        let found = false;
        presets.forEach(preset => {
            if ((preset.dataset.src || preset.src) === activePuzzleParams.selectedImage) {
                preset.classList.add('selected');
                found = true;
            }
        });
         if (!found) console.warn("Предустановленное изображение активного пазла не найдено в панели настроек", activePuzzleParams.selectedImage);
    } else if (!activePuzzleParams.isPreset && activePuzzleParams.selectedImage) {
         if(previewContainer && previewImg && previewText) {
             previewImg.src = activePuzzleParams.selectedImage;
             previewText.textContent = activePuzzleParams.imageFile ? `Загружено: ${activePuzzleParams.imageFile.name}` : 'Загруженное изображение';
             previewContainer.style.display = 'block';
         }
    }
     customInput.value = '';


    // Получаем состояние активного пазла для сохранения
    const getPuzzleStateForWhiteboard = () => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');
        if (!currentActiveWrapper || currentActiveWrapper !== activeGameWrapper || !currentActiveWrapper.puzzleParams) {
            alert("Активный пазл изменился или не найден. Сохранение отменено.");
            return null;
        }
        const params = currentActiveWrapper.puzzleParams;
        params.name = puzzleNameInput.value.trim();
        if (!params.name) {
             alert("Введите название для сохранения.");
             puzzleNameInput.focus();
             return null;
        }
         if (!params.piecePositions || params.piecePositions.length !== params.gridSize * params.gridSize) {
             alert("Ошибка: Пазл не инициализирован или данные о позициях некорректны. Перемешайте элементы или измените настройки перед сохранением.");
             console.error("Невозможно сохранить: недопустимые позиции элементов", params.piecePositions, "for grid size", params.gridSize);
             return null;
         }

        return {
            name: params.name,
            gridSize: params.gridSize,
            piecePositions: params.piecePositions,
            selectedImage: params.selectedImage,
            presetElements: presets,
            customImageInputEl: customInput
        };
    };

    // Применяем загруженное состояние к активному пазлу
    const applyLoadedStateForWhiteboard = (puzzleData) => {
        const currentActiveWrapper = document.querySelector('.paste-game-wrapper.active-game');
         if (!currentActiveWrapper || currentActiveWrapper !== activeGameWrapper || !currentActiveWrapper.puzzleParams) {
            alert("Активный пазл изменился или не найден. Загрузка отменена.");
            return;
        }
        const targetParams = currentActiveWrapper.puzzleParams;
        const targetContainer = currentActiveWrapper.puzzleContainer;
        const targetMessage = currentActiveWrapper.puzzleMessage;

        console.log("Применение загруженного состояния к пазлу на доске:", puzzleData);

        targetParams.gridSize = puzzleData.grid_size;
        targetParams.piecePositions = puzzleData.piece_positions || [];
        targetParams.name = puzzleData.name;
        targetParams.selectedImage = puzzleData.image_url;
        targetParams.isPreset = !!puzzleData.preset_path;
        targetParams.imageFile = null;

        puzzleNameInput.value = targetParams.name;
        difficultySelect.value = targetParams.gridSize;
        customInput.value = '';
        if(previewContainer) previewContainer.style.display = 'none';

        presets.forEach(p => p.classList.remove('selected'));
        if (targetParams.isPreset) {
            let found = false;
            presets.forEach(preset => {
                 const presetSrcRelative = (preset.dataset.src || preset.src).replace(window.location.origin, '');
                 const loadedUrlRelative = puzzleData.image_url.replace(window.location.origin, '');
                 if (presetSrcRelative === loadedUrlRelative) {
                     preset.classList.add('selected');
                     found = true;
                 }
            });
             if (!found) console.warn("Загруженное предустановленное изображение не найдено:", puzzleData.image_url);
        } else {
            // Показываем превью для загруженного пользовательского фото
             if(previewContainer && previewImg && previewText && puzzleData.image_url) {
                 previewImg.src = puzzleData.image_url;
                 previewText.textContent = `Загружено: ${puzzleData.name}`;
                 previewContainer.style.display = 'block';
             } else {
                 console.log("Загруженное изображение пользователя:", puzzleData.image_url);
             }
        }

        createPuzzle(targetContainer, targetParams, targetMessage, true);

        alert(`Пазл "${puzzleData.name}" загружен в активный контейнер.`);
    };

    // Инициализируем функции Сохранения и Загрузки
    initSaveLoadFeatures(getPuzzleStateForWhiteboard, applyLoadedStateForWhiteboard, {
        saveButton, loadButton, loadModal, loadListContainer, loadConfirmBtn, loadCancelBtn
    });

    console.log("Настройка сохранения / загрузки завершена для активного пазла на доске.");
}