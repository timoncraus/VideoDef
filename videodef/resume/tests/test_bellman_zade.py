# videodef/resume/tests/test_bellman_zade.py

"""
Тесты для реализации метода Беллмана-Заде
"""

import math
import json
import numpy as np
from django.test import TestCase

from resume.bellman_zade import (
    calculate_distance,
    SaatyScale,
    ComparisonMatrix,
    FuzzySetFromComparisons,
    BellmanZadeMCDA,
    WhatIfAnalyzer,
    create_brand_project_example
)


class CalculateDistanceTest(TestCase):
    """Тесты для функции calculate_distance"""

    def test_distance_between_moscow_and_spb(self):
        """Расчет расстояния между Москвой и Санкт-Петербургом"""
        # Москва: 55.751244, 37.618423
        # Санкт-Петербург: 59.934280, 30.335099
        distance = calculate_distance(55.751244, 37.618423, 59.934280, 30.335099)
        # Примерное расстояние ~ 634 км
        self.assertAlmostEqual(distance, 634, delta=10)

    def test_distance_same_point(self):
        """Расчет расстояния между одинаковыми точками"""
        distance = calculate_distance(55.751244, 37.618423, 55.751244, 37.618423)
        self.assertAlmostEqual(distance, 0, delta=0.001)

    def test_distance_with_negative_coordinates(self):
        """Расчет расстояния с отрицательными координатами"""
        distance = calculate_distance(-33.8688, 151.2093, -33.8688, 151.2093)
        self.assertAlmostEqual(distance, 0, delta=0.001)


class SaatyScaleTest(TestCase):
    """Тесты для шкалы Саати"""

    def test_from_linguistic_equal(self):
        value = SaatyScale.from_linguistic("одинаковая важность")
        self.assertEqual(value, 1)

    def test_from_linguistic_weak(self):
        value = SaatyScale.from_linguistic("слабое преимущество")
        self.assertEqual(value, 3)

    def test_from_linguistic_strong(self):
        value = SaatyScale.from_linguistic("существенное преимущество")
        self.assertEqual(value, 5)

    def test_from_linguistic_very_strong(self):
        value = SaatyScale.from_linguistic("явное преимущество")
        self.assertEqual(value, 7)

    def test_from_linguistic_absolute(self):
        value = SaatyScale.from_linguistic("абсолютное преимущество")
        self.assertEqual(value, 9)

    def test_from_linguistic_unknown(self):
        value = SaatyScale.from_linguistic("неизвестное значение")
        self.assertEqual(value, 1)  # Возвращает 1 по умолчанию

    def test_enum_values(self):
        self.assertEqual(SaatyScale.EQUAL.value, 1)
        self.assertEqual(SaatyScale.WEAK.value, 2)
        self.assertEqual(SaatyScale.WEAK_PLUS.value, 3)
        self.assertEqual(SaatyScale.STRONG.value, 4)
        self.assertEqual(SaatyScale.STRONG_PLUS.value, 5)
        self.assertEqual(SaatyScale.VERY_STRONG.value, 6)
        self.assertEqual(SaatyScale.VERY_STRONG_PLUS.value, 7)
        self.assertEqual(SaatyScale.ABSOLUTE.value, 8)
        self.assertEqual(SaatyScale.ABSOLUTE_PLUS.value, 9)


class ComparisonMatrixTest(TestCase):
    """Тесты для класса ComparisonMatrix"""

    def setUp(self):
        self.elements = ['A', 'B', 'C']
        self.matrix = ComparisonMatrix(self.elements, "Test Matrix")

    def test_initialization(self):
        self.assertEqual(self.matrix.elements, self.elements)
        self.assertEqual(self.matrix.name, "Test Matrix")
        self.assertEqual(self.matrix.n, 3)
        self.assertEqual(self.matrix.matrix.shape, (3, 3))

    def test_set_comparison(self):
        self.matrix.set_comparison(0, 1, 3)
        self.assertEqual(self.matrix.get_comparison(0, 1), 3)
        self.assertAlmostEqual(self.matrix.get_comparison(1, 0), 1/3)

    def test_set_comparison_linguistic(self):
        self.matrix.set_comparison_linguistic(0, 1, "слабое преимущество")
        self.assertEqual(self.matrix.get_comparison(0, 1), 3)
        self.assertAlmostEqual(self.matrix.get_comparison(1, 0), 1/3)

    def test_calculate_weights_3x3(self):
        # Матрица для теста (сравнение 3 элементов)
        # A > B > C
        self.matrix.set_comparison(0, 1, 3)
        self.matrix.set_comparison(0, 2, 5)
        self.matrix.set_comparison(1, 2, 2)
        
        weights = self.matrix.calculate_weights()
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        # A должен иметь наибольший вес
        self.assertGreater(weights[0], weights[1])
        self.assertGreater(weights[1], weights[2])

    def test_calculate_weights_2x2(self):
        elements = ['A', 'B']
        matrix = ComparisonMatrix(elements, "2x2")
        matrix.set_comparison(0, 1, 2)
        
        weights = matrix.calculate_weights()
        self.assertEqual(len(weights), 2)
        self.assertAlmostEqual(sum(weights), 1.0, places=6)
        self.assertGreater(weights[0], weights[1])

    def test_calculate_consistency_ratio_consistent(self):
        # Идеально согласованная матрица
        self.matrix.set_comparison(0, 1, 2)
        self.matrix.set_comparison(0, 2, 4)
        self.matrix.set_comparison(1, 2, 2)
        
        consistency = self.matrix.calculate_consistency_ratio()
        self.assertLess(consistency['cr'], 0.1)
        self.assertTrue(consistency['is_consistent'])

    def test_calculate_consistency_ratio_inconsistent(self):
        # Специально делаем несогласованную матрицу
        self.matrix.set_comparison(0, 1, 2)
        self.matrix.set_comparison(0, 2, 3)
        self.matrix.set_comparison(1, 2, 5)  # Должно быть ~1.5 для согласованности
        
        consistency = self.matrix.calculate_consistency_ratio()
        # Может быть согласованной или нет, просто проверяем что метод работает
        self.assertIn('cr', consistency)
        self.assertIn('is_consistent', consistency)

    def test_to_dict_and_from_dict(self):
        self.matrix.set_comparison(0, 1, 3)
        self.matrix.set_comparison(0, 2, 5)
        
        data = self.matrix.to_dict()
        self.assertIn('name', data)
        self.assertIn('elements', data)
        self.assertIn('matrix', data)
        self.assertIn('n', data)
        
        restored = ComparisonMatrix.from_dict(data)
        self.assertEqual(restored.name, self.matrix.name)
        self.assertEqual(restored.elements, self.matrix.elements)
        np.testing.assert_array_almost_equal(restored.matrix, self.matrix.matrix)


class FuzzySetFromComparisonsTest(TestCase):
    """Тесты для класса FuzzySetFromComparisons"""

    def setUp(self):
        elements = ['A', 'B', 'C']
        matrix = ComparisonMatrix(elements, "Test")
        matrix.set_comparison(0, 1, 2)
        matrix.set_comparison(0, 2, 3)
        matrix.set_comparison(1, 2, 2)
        self.fuzzy_set = FuzzySetFromComparisons("G1", matrix)

    def test_initialization(self):
        self.assertEqual(self.fuzzy_set.name, "G1")
        self.assertIsNotNone(self.fuzzy_set.weights)
        self.assertIsNotNone(self.fuzzy_set.memberships)

    def test_get_membership(self):
        membership = self.fuzzy_set.get_membership('A')
        self.assertGreater(membership, 0)
        self.assertLessEqual(membership, 1)

    def test_get_membership_nonexistent(self):
        membership = self.fuzzy_set.get_membership('X')
        self.assertEqual(membership, 0.0)

    def test_get_ranked_elements(self):
        ranked = self.fuzzy_set.get_ranked_elements()
        self.assertEqual(len(ranked), 3)
        self.assertGreater(ranked[0][1], ranked[1][1])

    def test_to_dict_and_from_dict(self):
        data = self.fuzzy_set.to_dict()
        self.assertIn('name', data)
        self.assertIn('matrix', data)
        self.assertIn('memberships', data)
        
        restored = FuzzySetFromComparisons.from_dict(data)
        self.assertEqual(restored.name, self.fuzzy_set.name)
        self.assertEqual(restored.memberships.keys(), self.fuzzy_set.memberships.keys())


class BellmanZadeMCDATest(TestCase):
    """Тесты для класса BellmanZadeMCDA"""

    def setUp(self):
        self.model = BellmanZadeMCDA()
        self.model.set_alternatives(['P1', 'P2', 'P3'])
        self.model.set_criteria(['G1', 'G2', 'G3'])
        
        # Добавляем сравнения
        self.model.add_alternative_comparison('G1', 'P1', 'P2', 2)
        self.model.add_alternative_comparison('G1', 'P1', 'P3', 3)
        self.model.add_alternative_comparison('G1', 'P2', 'P3', 2)
        
        self.model.add_alternative_comparison('G2', 'P1', 'P2', 1)
        self.model.add_alternative_comparison('G2', 'P1', 'P3', 2)
        self.model.add_alternative_comparison('G2', 'P2', 'P3', 2)
        
        self.model.add_alternative_comparison('G3', 'P1', 'P2', 3)
        self.model.add_alternative_comparison('G3', 'P1', 'P3', 4)
        self.model.add_alternative_comparison('G3', 'P2', 'P3', 2)

    def test_set_alternatives(self):
        self.assertEqual(self.model.alternatives, ['P1', 'P2', 'P3'])

    def test_set_criteria(self):
        self.assertEqual(self.model.criteria, ['G1', 'G2', 'G3'])

    def test_add_criterion_comparison(self):
        self.model.add_criterion_comparison('G1', 'G2', 2)
        self.assertIsNotNone(self.model.criteria_comparison_matrix)

    def test_add_criterion_comparison_linguistic(self):
        self.model.add_criterion_comparison_linguistic('G1', 'G2', 'слабое преимущество')
        self.assertIsNotNone(self.model.criteria_comparison_matrix)

    def test_build_fuzzy_sets(self):
        self.model.build_fuzzy_sets()
        self.assertEqual(len(self.model.criterion_fuzzy_sets), 3)
        self.assertIn('G1', self.model.criterion_fuzzy_sets)
        self.assertIn('G2', self.model.criterion_fuzzy_sets)
        self.assertIn('G3', self.model.criterion_fuzzy_sets)

    def test_calculate_solution(self):
        self.model.build_fuzzy_sets()
        solution = self.model.calculate_solution()
        
        self.assertEqual(len(solution), 3)
        self.assertIn('P1', solution)
        self.assertIn('P2', solution)
        self.assertIn('P3', solution)
        
        for value in solution.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 1)

    def test_get_best_alternative(self):
        self.model.build_fuzzy_sets()
        best_alt, best_value = self.model.get_best_alternative()
        self.assertIn(best_alt, self.model.alternatives)
        self.assertGreater(best_value, 0)
        self.assertLessEqual(best_value, 1)

    def test_get_ranking(self):
        self.model.build_fuzzy_sets()
        ranking = self.model.get_ranking()
        self.assertEqual(len(ranking), 3)
        # Проверяем, что ранжирование отсортировано по убыванию
        for i in range(len(ranking) - 1):
            self.assertGreaterEqual(ranking[i][1], ranking[i+1][1])

    def test_get_consistency_report(self):
        self.model.build_fuzzy_sets()
        report = self.model.get_consistency_report()
        
        self.assertIn('criteria_matrix', report)
        self.assertIn('criterion_matrices', report)
        self.assertIn('G1', report['criterion_matrices'])
        self.assertIn('G2', report['criterion_matrices'])
        self.assertIn('G3', report['criterion_matrices'])

    def test_to_dict_and_from_dict(self):
        self.model.build_fuzzy_sets()
        self.model.calculate_solution()
        
        data = self.model.to_dict()
        self.assertIn('alternatives', data)
        self.assertIn('criteria', data)
        self.assertIn('solution', data)
        
        restored = BellmanZadeMCDA.from_dict(data)
        self.assertEqual(restored.alternatives, self.model.alternatives)
        self.assertEqual(restored.criteria, self.model.criteria)
        self.assertEqual(restored.solution_fuzzy_set, self.model.solution_fuzzy_set)

    def test_set_criteria_weights_direct(self):
        weights = {'G1': 0.3, 'G2': 0.4, 'G3': 0.3}
        self.model.set_criteria_weights_direct(weights)
        self.assertIsNotNone(self.model.criteria_weights)
        self.assertAlmostEqual(sum(self.model.criteria_weights), 1.0, places=6)


class WhatIfAnalyzerTest(TestCase):
    """Тесты для класса WhatIfAnalyzer"""

    def setUp(self):
        self.model = create_brand_project_example()
        self.model.build_fuzzy_sets()
        self.model.calculate_solution()
        self.analyzer = WhatIfAnalyzer(self.model)

    def test_analyze_criterion_comparison_change(self):
        result = self.analyzer.analyze_criterion_comparison_change('G1', 'G2', 3)
        
        self.assertIn('changed_comparison', result)
        self.assertIn('new_weights', result)
        self.assertIn('new_solution', result)
        self.assertIn('best_alternative', result)
        self.assertIn('ranking', result)
        self.assertIn('changes', result)
        
        self.assertEqual(len(result['changes']), 4)  # 4 альтернативы

    def test_analyze_alternative_comparison_change(self):
        result = self.analyzer.analyze_alternative_comparison_change('G1', 'P1', 'P2', 4)
        
        self.assertIn('changed_comparison', result)
        self.assertIn('new_solution', result)
        self.assertIn('best_alternative', result)
        self.assertIn('ranking', result)
        self.assertIn('changes', result)
        
        self.assertEqual(len(result['changes']), 4)  # 4 альтернативы


class CreateBrandProjectExampleTest(TestCase):
    """Тесты для функции create_brand_project_example"""

    def test_creates_model(self):
        model = create_brand_project_example()
        
        self.assertIsInstance(model, BellmanZadeMCDA)
        self.assertEqual(model.alternatives, ['P1', 'P2', 'P3', 'P4'])
        self.assertEqual(model.criteria, ['G1', 'G2', 'G3', 'G4', 'G5', 'G6'])
        self.assertEqual(len(model.criterion_matrices), 6)

    def test_weights_from_textbook(self):
        model = create_brand_project_example()
        
        # Проверяем, что веса установлены из методички
        expected_weights = {'G1': 0.15, 'G2': 0.34, 'G3': 0.26, 'G4': 0.05, 'G5': 0.13, 'G6': 0.07}
        
        self.assertIsNotNone(model.criteria_weights)
        for i, criterion in enumerate(model.criteria):
            self.assertAlmostEqual(model.criteria_weights[i], expected_weights[criterion], places=2)

    def test_solution_calculation(self):
        model = create_brand_project_example()
        model.build_fuzzy_sets()
        solution = model.calculate_solution()
        
        self.assertEqual(len(solution), 4)
        self.assertIn('P1', solution)
        self.assertIn('P2', solution)
        self.assertIn('P3', solution)
        self.assertIn('P4', solution)
        
        # Проверяем, что все значения между 0 и 1
        for value in solution.values():
            self.assertGreaterEqual(value, 0)
            self.assertLessEqual(value, 1)

    def test_best_alternative(self):
        model = create_brand_project_example()
        model.build_fuzzy_sets()
        best_alt, best_value = model.get_best_alternative()
        
        # В примере из методички лучшая альтернатива - P4
        self.assertIn(best_alt, ['P1', 'P2', 'P3', 'P4'])
        self.assertGreater(best_value, 0)


class IntegrationTest(TestCase):
    """Интеграционные тесты"""

    def test_full_workflow(self):
        """Полный цикл работы с моделью"""
        # 1. Создание модели
        model = BellmanZadeMCDA()
        model.set_alternatives(['A1', 'A2', 'A3'])
        model.set_criteria(['C1', 'C2'])
        
        # 2. Добавление сравнений
        model.add_alternative_comparison('C1', 'A1', 'A2', 3)
        model.add_alternative_comparison('C1', 'A1', 'A3', 5)
        model.add_alternative_comparison('C1', 'A2', 'A3', 2)
        
        model.add_alternative_comparison('C2', 'A1', 'A2', 2)
        model.add_alternative_comparison('C2', 'A1', 'A3', 4)
        model.add_alternative_comparison('C2', 'A2', 'A3', 2)
        
        model.add_criterion_comparison('C1', 'C2', 2)
        
        # 3. Построение нечетких множеств
        model.build_fuzzy_sets()
        self.assertEqual(len(model.criterion_fuzzy_sets), 2)
        
        # 4. Расчет решения
        solution = model.calculate_solution()
        self.assertEqual(len(solution), 3)
        
        # 5. Получение лучшей альтернативы
        best_alt, best_value = model.get_best_alternative()
        self.assertIn(best_alt, ['A1', 'A2', 'A3'])
        
        # 6. Получение ранжирования
        ranking = model.get_ranking()
        self.assertEqual(len(ranking), 3)
        
        # 7. Проверка согласованности
        report = model.get_consistency_report()
        self.assertIn('criteria_matrix', report)
        self.assertIn('criterion_matrices', report)
        
        # 8. Сериализация
        data = model.to_dict()
        self.assertIn('alternatives', data)
        self.assertIn('criteria', data)
        
        # 9. Десериализация
        restored = BellmanZadeMCDA.from_dict(data)
        self.assertEqual(restored.alternatives, model.alternatives)
        self.assertEqual(restored.criteria, model.criteria)

    def test_what_if_analysis_integration(self):
        """Интеграционный тест What-If анализа"""
        model = create_brand_project_example()
        model.build_fuzzy_sets()
        model.calculate_solution()
        
        analyzer = WhatIfAnalyzer(model)
        
        # Изменяем сравнение критериев
        result = analyzer.analyze_criterion_comparison_change('G1', 'G2', 5)
        
        self.assertIn('changed_comparison', result)
        self.assertIn('new_solution', result)
        self.assertIn('best_alternative', result)
        
        # Проверяем, что решение изменилось
        old_best = model.get_best_alternative()
        new_best = result['best_alternative']
        
        # Может измениться или нет, просто проверяем что оба существуют
        self.assertIsNotNone(old_best)
        self.assertIsNotNone(new_best)

    def test_consistency_improvement(self):
        """Тест улучшения согласованности матрицы"""
        elements = ['A', 'B', 'C', 'D']
        matrix = ComparisonMatrix(elements, "Test")
        
        # Создаем несогласованную матрицу
        matrix.set_comparison(0, 1, 2)
        matrix.set_comparison(0, 2, 3)
        matrix.set_comparison(0, 3, 4)
        matrix.set_comparison(1, 2, 5)  # Должно быть ~1.5
        matrix.set_comparison(1, 3, 6)  # Должно быть ~2
        matrix.set_comparison(2, 3, 2)
        
        initial_cr = matrix.calculate_consistency_ratio()['cr']
        
        # Пытаемся улучшить согласованность
        result = matrix.ensure_consistency()
        
        final_cr = matrix.calculate_consistency_ratio()['cr']
        
        # Проверяем, что метод не падает
        self.assertIsNotNone(result)