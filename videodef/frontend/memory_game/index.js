import { getGameParts, initializeBoard, stopTimer, getFullPresetImageUrls } from './memory-game-logic.js'; 

/**
 * Инициализирует интерфейс и логику для отдельной страницы игры "Поиск пар".
 * Находит все необходимые DOM-элементы и назначает им обработчики событий.
 */
function createMemoryGameSeparately() {
    // Получаем ссылки на основные DOM-элементы
    const gameWrapper = document.getElementById('memory-game-wrapper');     
    const pairCountSelect = document.getElementById('pair-count-select');   
    const startButton = document.getElementById('start-memory-game');       
    
    // Элементы панели настроек
    const gameNameInput = document.getElementById('game-name');                   
    const presetSetElements = document.querySelectorAll('.preset-set');           
    const customImagesInput = document.getElementById('custom-images-input');     
    const customImagesPreviewContainer = document.getElementById('custom-images-preview'); 
    const previewGrid = customImagesPreviewContainer.querySelector('.preview-grid'); 
    const customImagesInfoText = document.getElementById('custom-images-info-text'); 


    if (!gameWrapper || !pairCountSelect || !startButton || !gameNameInput || !presetSetElements.length || 
        !customImagesInput || !customImagesPreviewContainer || !previewGrid || !customImagesInfoText) {
        console.error("Критическая ошибка: Не найдены все необходимые DOM-элементы для инициализации игры. Проверьте HTML-разметку и ID элементов.");
        return;
    }

    let localGameParams = getGameParts(); 

    // --- Обработчики событий для элементов UI настроек ---
    gameNameInput.addEventListener('input', (e) => {
        localGameParams.name = e.target.value.trim(); 
    });
    gameNameInput.value = localGameParams.name; 

    presetSetElements.forEach(presetEl => {
        presetEl.addEventListener('click', () => {
            presetSetElements.forEach(el => el.classList.remove('selected'));
            presetEl.classList.add('selected');
            
            const setName = presetEl.dataset.setName; 
            
            localGameParams.selectedImageSet = getFullPresetImageUrls(setName); 
            localGameParams.isCustomSet = false; 
            
            customImagesInput.value = ''; 
            previewGrid.innerHTML = ''; 
            customImagesInfoText.innerHTML = 'Загружено изображений: <span id="custom-images-count">0</span>'; 
            customImagesPreviewContainer.style.display = 'none';
        });
    });
    
    if (presetSetElements.length > 0) {
        presetSetElements[0].click(); 
    }

    customImagesInput.addEventListener('change', (event) => {
        const files = event.target.files; 
        previewGrid.innerHTML = ''; 
        localGameParams.customImageObjects = []; 

        if (files.length > 0) { 
            localGameParams.isCustomSet = true; 
            presetSetElements.forEach(el => el.classList.remove('selected')); 
            
            let loadedCount = 0; 
            Array.from(files).forEach(file => {
                if (!file.type.startsWith('image/')) {
                    console.warn(`Файл ${file.name} не является изображением и будет пропущен.`);
                    if (++loadedCount === files.length) updateCustomImagePreview(); 
                    return;
                }
                
                const reader = new FileReader(); 
                reader.onload = (e) => { 
                    localGameParams.customImageObjects.push({ url: e.target.result, file: file });
                    
                    const imgPreview = document.createElement('img');
                    imgPreview.src = e.target.result;
                    imgPreview.alt = file.name;
                    imgPreview.classList.add('preview-thumb');
                    previewGrid.appendChild(imgPreview);

                    if (++loadedCount === files.length) updateCustomImagePreview(); 
                };
                reader.onerror = () => { 
                    console.error(`Ошибка чтения файла ${file.name}`);
                    if (++loadedCount === files.length) updateCustomImagePreview();
                };
                reader.readAsDataURL(file); 
            });
        } else { 
            localGameParams.isCustomSet = false; 
            const currentlySelectedPreset = document.querySelector('.preset-set.selected') || presetSetElements[0];
            if (currentlySelectedPreset) {
                currentlySelectedPreset.click();
            } else {
                updateCustomImagePreview(); 
            }
        }
    });

    /**
     * Обновляет отображение предпросмотра пользовательских изображений.
     */
    function updateCustomImagePreview() {
        if (localGameParams.isCustomSet && localGameParams.customImageObjects.length > 0) {
            customImagesInfoText.innerHTML = `Загружено изображений: <span id="custom-images-count">${localGameParams.customImageObjects.length}</span>`;
            customImagesPreviewContainer.style.display = 'block'; 
        } else {
            customImagesInfoText.innerHTML = 'Загружено изображений: <span id="custom-images-count">0</span>';
            customImagesPreviewContainer.style.display = 'none'; 
        }
    }

    // --- Логика старта и управления игрой ---
    /**
     * Запускает или перезапускает игру с текущими настройками.
     */
    const startGame = () => {
        localGameParams.pairCount = parseInt(pairCountSelect.value, 10);
        stopTimer(localGameParams); 
        
        const success = initializeBoard(gameWrapper, localGameParams); 
    };

    pairCountSelect.addEventListener('change', () => {
        localGameParams.pairCount = parseInt(pairCountSelect.value, 10);
        gameWrapper.innerHTML = '<p class="initial-message">Настройки изменены. Нажмите "Начать игру", чтобы применить.</p>';
        if (localGameParams.uiCompletionMessageEl) { 
            localGameParams.uiCompletionMessageEl.style.display = 'none';
        }
        stopTimer(localGameParams); 
    });

    startButton.addEventListener('click', startGame);

    console.log("Страница игры 'Поиск пар' инициализирована.");
}

window.MemoryGameModule = window.MemoryGameModule || {};
window.MemoryGameModule.createMemoryGameSeparately = createMemoryGameSeparately;