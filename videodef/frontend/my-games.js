document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('deleteConfirmationModal');
    const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
    const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
    const closeBtn = modal.querySelector('.modal-close-btn');
    const gameNameElement = document.getElementById('gameNameToDelete');
    const noGamesMessage = document.getElementById('no-games-message');
    const gamesGrid = document.querySelector('.my-saved-games-grid');

    let gameIdToDelete = null;
    let gameCardElementToDelete = null;

    // Функция для получения CSRF-токена
    function getCookie(name) {
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
    const csrftoken = getCookie('csrftoken');

    // Открытие модального окна
    document.querySelectorAll('.delete-game-btn').forEach(button => {
        button.addEventListener('click', function (event) {
            event.preventDefault();
            event.stopPropagation();

            gameIdToDelete = this.dataset.gameId;
            gameCardElementToDelete = this.closest('.saved-game-item-wrapper');

            const titleElement = gameCardElementToDelete.querySelector('.saved-game-card__title');
            gameNameElement.textContent = titleElement ? titleElement.textContent.trim() : 'эту игру';
            
            modal.style.display = 'flex';
        });
    });

    // Закрытие модального окна
    function closeModal() {
        modal.style.display = 'none';
        gameIdToDelete = null;
        gameCardElementToDelete = null;
    }

    if (cancelDeleteBtn) cancelDeleteBtn.addEventListener('click', closeModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    // Подтверждение удаления
    if (confirmDeleteBtn) {
        confirmDeleteBtn.addEventListener('click', function () {
            if (!gameIdToDelete || !gameCardElementToDelete) return;

            const deleteUrl = `/games/delete/${gameIdToDelete}/`; 

            fetch(deleteUrl, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrftoken
                },
            })
            .then(response => {
                if (response.ok) {
                    if (response.status === 204) {
                        return Promise.resolve({ status: 'success', message: 'Игра успешно удалена (204).' });
                    }
                    return response.json();
                }
                return response.json().then(err => { throw new Error(err.message || 'Не удалось удалить игру.') });
            })
            .then(data => {
                if (data.status === 'success') {
                    gameCardElementToDelete.remove();
                    checkIfGamesExist();
                    console.log(data.message || 'Игра успешно удалена.');
                    closeModal();
                } else {
                    throw new Error(data.message || 'Ошибка при удалении игры на сервере.');
                }
            })
            .catch(error => {
                console.error('Ошибка при удалении игры:', error);
                alert(`Ошибка: ${error.message}`);
                closeModal();
            });
        });
    }

    function checkIfGamesExist() {
        if (gamesGrid && noGamesMessage) {
            const remainingGames = gamesGrid.querySelectorAll('.saved-game-item-wrapper').length;
            if (remainingGames === 0) {
                noGamesMessage.style.display = 'block';
            } else {
                noGamesMessage.style.display = 'none';
            }
        }
    }
    checkIfGamesExist();
});