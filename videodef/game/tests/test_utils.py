import json
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from game.utils import (
    parse_and_validate_puzzle_data,
    parse_and_validate_memory_game_data,
    handle_db_integrity_error,
    cleanup_uploaded_files,
    save_memory_game_custom_images
)
from django.db import InternalError


class ParseAndValidatePuzzleDataTests(TestCase):
    """Тесты для функции parse_and_validate_puzzle_data."""
    
    def test_valid_data_with_preset(self):
        """Тест проверяет корректный парсинг данных с пресетом."""
        post_data = {
            'name': 'Test Puzzle',
            'gridSize': '3',
            'piecePositions': json.dumps([0, 1, 2, 3, 4, 5, 6, 7, 8]),
            'preset_image_path': 'preset.png'
        }
        
        result = parse_and_validate_puzzle_data(post_data)
        
        self.assertEqual(result['name'], 'Test Puzzle')
        self.assertEqual(result['grid_size'], 3)
        self.assertEqual(result['piece_positions'], [0, 1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(result['preset_path'], 'preset.png')
        self.assertIsNone(result['uploaded_image_file'])

    def test_valid_data_with_uploaded_image(self):
        """Тест проверяет корректный парсинг данных с загруженным изображением."""
        post_data = {
            'name': 'Test Puzzle',
            'gridSize': '2',
            'piecePositions': json.dumps([0, 1, 2, 3])
        }
        test_file = SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        files_data = {'user_image_file': test_file}
        
        result = parse_and_validate_puzzle_data(post_data, files_data)
        
        self.assertEqual(result['name'], 'Test Puzzle')
        self.assertEqual(result['grid_size'], 2)
        self.assertIsNotNone(result['uploaded_image_file'])
        self.assertIsNone(result['preset_path'])

    def test_empty_name_raises_error(self):
        """Тест проверяет, что пустое название вызывает ValueError."""
        post_data = {
            'name': '',
            'gridSize': '3',
            'piecePositions': json.dumps([0, 1, 2, 3, 4, 5, 6, 7, 8])
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_puzzle_data(post_data)
        
        self.assertIn("Название не может быть пустым", str(cm.exception))

    def test_invalid_grid_size_raises_error(self):
        """Тест проверяет, что некорректный размер сетки вызывает ValueError."""
        post_data = {
            'name': 'Test',
            'gridSize': '1',
            'piecePositions': json.dumps([0])
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_puzzle_data(post_data)
        
        self.assertIn("Размер сетки слишком мал", str(cm.exception))

    def test_piece_positions_length_mismatch_raises_error(self):
        """Тест проверяет, что несоответствие длины позиций размеру сетки вызывает ValueError."""
        post_data = {
            'name': 'Test',
            'gridSize': '3',
            'piecePositions': json.dumps([0, 1])  # Должно быть 9
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_puzzle_data(post_data)
        
        self.assertIn("Количество позиций", str(cm.exception))
        self.assertIn("не соответствует размеру сетки", str(cm.exception))

    def test_invalid_json_in_positions_raises_error(self):
        """Тест проверяет, что некорректный JSON в позициях вызывает ValueError."""
        post_data = {
            'name': 'Test',
            'gridSize': '2',
            'piecePositions': 'invalid json'
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_puzzle_data(post_data)
        
        self.assertIn("Неверный формат JSON", str(cm.exception))


class ParseAndValidateMemoryGameDataTests(TestCase):
    """Тесты для функции parse_and_validate_memory_game_data."""
    
    def test_valid_data_with_preset(self):
        """Тест проверяет корректный парсинг данных с пресетом."""
        post_data = {
            'name': 'Test Memory Game',
            'pairCount': '4',
            'cardLayout': json.dumps([0, 1, 2, 3, 0, 1, 2, 3]),
            'presetName': 'fruits'
        }
        
        result = parse_and_validate_memory_game_data(post_data)
        
        self.assertEqual(result['name'], 'Test Memory Game')
        self.assertEqual(result['pair_count'], 4)
        self.assertEqual(result['card_layout'], [0, 1, 2, 3, 0, 1, 2, 3])
        self.assertEqual(result['preset_name'], 'fruits')
        self.assertEqual(result['custom_images'], [])

    def test_valid_data_with_custom_images(self):
        """Тест проверяет корректный парсинг данных с пользовательскими изображениями."""
        post_data = {
            'name': 'Test Memory Game',
            'pairCount': '2',
            'cardLayout': json.dumps([0, 1, 0, 1])
        }
        test_file1 = SimpleUploadedFile("test1.jpg", b"file_content1", content_type="image/jpeg")
        test_file2 = SimpleUploadedFile("test2.jpg", b"file_content2", content_type="image/jpeg")
        files_data = {'customImages[]': [test_file1, test_file2]}
        
        result = parse_and_validate_memory_game_data(post_data, files_data)
        
        self.assertEqual(result['name'], 'Test Memory Game')
        self.assertEqual(result['pair_count'], 2)
        self.assertEqual(len(result['custom_images']), 2)
        self.assertIsNone(result['preset_name'])

    def test_empty_name_raises_error(self):
        """Тест проверяет, что пустое название вызывает ValueError."""
        post_data = {
            'name': '',
            'pairCount': '4',
            'cardLayout': json.dumps([0, 1, 2, 3, 0, 1, 2, 3])
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_memory_game_data(post_data)
        
        self.assertIn("Название не может быть пустым", str(cm.exception))

    def test_invalid_pair_count_raises_error(self):
        """Тест проверяет, что некорректное количество пар вызывает ValueError."""
        post_data = {
            'name': 'Test',
            'pairCount': '1',  # Минимум 2
            'cardLayout': json.dumps([0, 1])
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_memory_game_data(post_data)
        
        self.assertIn("Неверное количество пар", str(cm.exception))

    def test_card_layout_length_mismatch_raises_error(self):
        """Тест проверяет, что несоответствие длины cardLayout вызывает ValueError."""
        post_data = {
            'name': 'Test',
            'pairCount': '4',
            'cardLayout': json.dumps([0, 1, 2])  # Должно быть 8
        }
        
        with self.assertRaises(ValueError) as cm:
            parse_and_validate_memory_game_data(post_data)
        
        self.assertIn("Некорректные данные о расположении карточек", str(cm.exception))


class HandleDbIntegrityErrorTests(TestCase):
    """Тесты для функции handle_db_integrity_error."""
    
    def test_puzzle_duplicate_error(self):
        """Тест проверяет обработку ошибки дубликата пазла."""
        error = InternalError('пазл с названием "Test" уже существует')
        
        response = handle_db_integrity_error(error, 'puzzle', 'Test', 'и размером сетки 3x3')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('уже существует', json.loads(response.content)['message'])

    def test_memory_game_duplicate_error(self):
        """Тест проверяет обработку ошибки дубликата "Поиска пар"."""
        error = InternalError('игра "поиск пар" с названием "Test" уже существует')
        
        response = handle_db_integrity_error(error, 'memory_game', 'Test', 'и количеством пар 4')
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('уже существует', json.loads(response.content)['message'])

    def test_unexpected_db_error(self):
        """Тест проверяет обработку непредвиденной ошибки БД."""
        error = InternalError('unexpected database error')
        
        response = handle_db_integrity_error(error, 'puzzle', 'Test')
        
        self.assertEqual(response.status_code, 500)
        self.assertIn('ошибка базы данных', json.loads(response.content)['message'])


class CleanupUploadedFilesTests(TestCase):
    """Тесты для функции cleanup_uploaded_files."""
    
    def test_cleanup_existing_files(self):
        """Тест проверяет удаление существующих файлов."""
        from django.core.files.storage import default_storage
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        # Создаем тестовый файл
        test_file = SimpleUploadedFile("test_cleanup.jpg", b"file_content", content_type="image/jpeg")
        saved_path = default_storage.save("test_cleanup/test.jpg", test_file)
        
        # Проверяем, что файл существует
        self.assertTrue(default_storage.exists(saved_path))
        
        # Вызываем функцию очистки
        cleanup_uploaded_files([saved_path])
        
        # Проверяем, что файл удален
        self.assertFalse(default_storage.exists(saved_path))

    def test_cleanup_nonexistent_files(self):
        """Тест проверяет, что функция не падает на несуществующих файлах."""
        # Вызываем функцию с несуществующим путем
        cleanup_uploaded_files(["nonexistent/path/file.jpg"])
        
        # Функция должна завершиться без исключений


class SaveMemoryGameCustomImagesTests(TestCase):
    """Тесты для функции save_memory_game_custom_images."""
    
    def test_save_custom_images_success(self):
        """Тест проверяет успешное сохранение пользовательских изображений."""
        test_file1 = SimpleUploadedFile("test1.jpg", b"file_content1", content_type="image/jpeg")
        test_file2 = SimpleUploadedFile("test2.jpg", b"file_content2", content_type="image/jpeg")
        custom_images = [test_file1, test_file2]
        
        saved_paths = save_memory_game_custom_images(custom_images, pair_count=2)
        
        self.assertEqual(len(saved_paths), 2)
        self.assertTrue(all(path.startswith('memory_game_images/') for path in saved_paths))
        
        # Очищаем созданные файлы
        cleanup_uploaded_files(saved_paths)

    def test_save_insufficient_images_raises_error(self):
        """Тест проверяет, что недостаточное количество изображений вызывает ValueError."""
        test_file1 = SimpleUploadedFile("test1.jpg", b"file_content1", content_type="image/jpeg")
        custom_images = [test_file1]
        
        with self.assertRaises(ValueError) as cm:
            save_memory_game_custom_images(custom_images, pair_count=2)
        
        self.assertIn("Недостаточно пользовательских изображений", str(cm.exception))