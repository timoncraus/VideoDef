"""
Полноценная реализация метода нечеткого многокритериального анализа 
вариантов Беллмана-Заде с использованием парных сравнений по шкале Саати.
"""

import math
import json
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Расчет расстояния между двумя точками на сфере (в километрах)
    по формуле гаверсинуса.
    """
    R = 6371  # Радиус Земли в километрах
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


class SaatyScale(Enum):
    """Шкала относительной важности Саати"""
    EQUAL = 1                    # Одинаковая важность
    WEAK = 2                     # Слабое преимущество
    WEAK_PLUS = 3                # Почти существенное
    STRONG = 4                   # Существенное преимущество
    STRONG_PLUS = 5              # Очень существенное
    VERY_STRONG = 6              # Явное преимущество
    VERY_STRONG_PLUS = 7         # Очень явное
    ABSOLUTE = 8                 # Абсолютное преимущество
    ABSOLUTE_PLUS = 9            # Полное превосходство
    
    @classmethod
    def from_linguistic(cls, text: str) -> int:
        """Преобразование лингвистической оценки в число шкалы Саати"""
        linguistic_map = {
            'отсутствует преимущество': 1,
            'одинаковая важность': 1,
            'почти слабое преимущество': 2,
            'слабое преимущество': 3,
            'почти существенное преимущество': 4,
            'существенное преимущество': 5,
            'почти сильное преимущество': 6,
            'явное преимущество': 7,
            'очень сильное преимущество': 8,
            'абсолютное преимущество': 9,
        }
        text_lower = text.lower().strip()
        for key, value in linguistic_map.items():
            if key in text_lower:
                return value
        return 1


class ComparisonMatrix:
    """
    Матрица парных сравнений с методами для расчета весов
    и обеспечения непротиворечивости.
    """
    
    def __init__(self, elements: List[str], name: str = ""):
        self.elements = elements
        self.name = name
        self.n = len(elements)
        # Инициализация матрицы единицами (диагональ)
        self.matrix = np.ones((self.n, self.n))
        # Заполняем диагональ единицами
        for i in range(self.n):
            self.matrix[i][i] = 1.0
    
    def set_comparison(self, i: int, j: int, value: float):
        """Установка значения сравнения элемента i над j"""
        self.matrix[i][j] = value
        self.matrix[j][i] = 1.0 / value
    
    def set_comparison_linguistic(self, i: int, j: int, linguistic: str):
        """Установка сравнения на основе лингвистической оценки"""
        value = SaatyScale.from_linguistic(linguistic)
        self.set_comparison(i, j, value)
    
    def get_comparison(self, i: int, j: int) -> float:
        """Получение значения сравнения"""
        return self.matrix[i][j]
    
    def calculate_weights(self) -> np.ndarray:
        """
        Расчет вектора приоритетов (собственный вектор матрицы)
        Метод: нормализация геометрического среднего
        """
        # Геометрическое среднее по строкам
        geometric_means = np.zeros(self.n)
        for i in range(self.n):
            product = np.prod(self.matrix[i, :])
            geometric_means[i] = product ** (1.0 / self.n)
        
        # Нормализация
        weights = geometric_means / np.sum(geometric_means)
        return weights
    
    def calculate_consistency_ratio(self) -> Dict[str, float]:
        """
        Расчет отношения согласованности матрицы
        Возвращает: CI (индекс согласованности), CR (отношение согласованности)
        """
        # Случайные индексы для n до 15
        random_indices = {
            1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
            11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
        }
        
        # Расчет максимального собственного значения
        weights = self.calculate_weights()
        aw = self.matrix @ weights
        lambda_max = np.mean(aw / weights)
        
        # Индекс согласованности
        ci = (lambda_max - self.n) / (self.n - 1) if self.n > 1 else 0
        
        # Отношение согласованности
        ri = random_indices.get(self.n, 1.59)
        cr = ci / ri if ri > 0 else 0
        
        return {
        'lambda_max': float(lambda_max),
        'ci': float(ci),
        'ri': float(ri),
        'cr': float(cr),
        'is_consistent': bool(cr < 0.1)
    }
    
    def ensure_consistency(self, max_iterations: int = 10):
        """
        Обеспечение непротиворечивости матрицы с использованием правил из методички
        """
        cr = self.calculate_consistency_ratio()['cr']
        if cr < 0.1:
            return True
        
        # Применяем правила (2.38) - (2.41) из методички
        for iteration in range(max_iterations):
            changes_made = False
            
            for i in range(self.n):
                for j in range(self.n):
                    if i == j:
                        continue
                    for k in range(self.n):
                        if k == i or k == j:
                            continue
                        
                        a_ij = self.matrix[i][j]
                        a_jk = self.matrix[j][k]
                        a_ik = self.matrix[i][k]
                        
                        # Правило 1: если a_ij > a_ik, то a_jk ≤ 1
                        if a_ij > a_ik and a_jk > 1:
                            new_value = 1.0
                            self.set_comparison(j, k, new_value)
                            changes_made = True
                        
                        # Правило 2: если a_ij > a_kj, то a_ik ≥ 1
                        if a_ij > 1 / a_jk and a_ik < 1:
                            new_value = 1.0
                            self.set_comparison(i, k, new_value)
                            changes_made = True
                        
                        # Правило 3: если a_ij > 1 и a_jk > 1, то a_ik ≥ max(a_ij, a_jk)
                        if a_ij > 1 and a_jk > 1:
                            new_value = max(a_ij, a_jk)
                            if a_ik < new_value:
                                self.set_comparison(i, k, new_value)
                                changes_made = True
                        
                        # Правило 4: если a_ij < 1 и a_jk < 1, то a_ik ≤ min(a_ij, a_jk)
                        if a_ij < 1 and a_jk < 1:
                            new_value = min(a_ij, a_jk)
                            if a_ik > new_value:
                                self.set_comparison(i, k, new_value)
                                changes_made = True
            
            if not changes_made:
                break
        
        return self.calculate_consistency_ratio()['cr'] < 0.1
    
    def to_dict(self) -> Dict:
        """Сериализация матрицы в словарь"""
        return {
            'name': self.name,
            'elements': self.elements,
            'matrix': self.matrix.tolist(),
            'n': self.n
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ComparisonMatrix':
        """Десериализация матрицы из словаря"""
        matrix = cls(data['elements'], data['name'])
        matrix.matrix = np.array(data['matrix'])
        return matrix


class FuzzySetFromComparisons:
    """
    Нечеткое множество, построенное на основе матрицы парных сравнений
    """
    
    def __init__(self, name: str, matrix: ComparisonMatrix):
        self.name = name
        self.matrix = matrix
        self.weights = matrix.calculate_weights()
        self.memberships = {}
        
        # Степени принадлежности = нормированные веса
        for i, element in enumerate(matrix.elements):
            self.memberships[element] = self.weights[i]
    
    def get_membership(self, element: str) -> float:
        """Получение степени принадлежности элемента"""
        value = self.memberships.get(element, 0.0)
        # Убедимся, что возвращается число от 0 до 1
        if value is None or value == 0:
            return 0.0
        return min(1.0, max(0.0, float(value)))
    
    def get_ranked_elements(self) -> List[Tuple[str, float]]:
        """Получение отсортированного списка элементов по степени принадлежности"""
        return sorted(self.memberships.items(), key=lambda x: x[1], reverse=True)
    
    def to_dict(self) -> Dict:
        """Сериализация"""
        return {
            'name': self.name,
            'matrix': self.matrix.to_dict(),
            'memberships': self.memberships
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FuzzySetFromComparisons':
        """Десериализация"""
        matrix = ComparisonMatrix.from_dict(data['matrix'])
        return cls(data['name'], matrix)


class BellmanZadeMCDA:
    """
    Полноценная реализация метода нечеткого многокритериального анализа
    вариантов по схеме Беллмана-Заде.
    """
    
    def __init__(self):
        self.alternatives: List[str] = []
        self.criteria: List[str] = []
        self.criterion_matrices: Dict[str, ComparisonMatrix] = {}
        self.criterion_fuzzy_sets: Dict[str, FuzzySetFromComparisons] = {}
        self.criteria_weights: Optional[np.ndarray] = None
        self.criteria_comparison_matrix: Optional[ComparisonMatrix] = None
        
        # Результаты
        self.solution_fuzzy_set: Dict[str, float] = {}
        self.alternative_scores: Dict[str, Dict[str, float]] = {}
    
    def set_alternatives(self, alternatives: List[str]):
        """Установка списка альтернатив (вариантов)"""
        self.alternatives = alternatives
    
    def set_criteria(self, criteria: List[str]):
        """Установка списка критериев"""
        self.criteria = criteria
    
    def add_criterion_comparison(self, criterion1: str, criterion2: str, value: float):
        """Добавление сравнения критериев (для расчета важности)"""
        print(f"=== add_criterion_comparison called: {criterion1} vs {criterion2} = {value} ===")
        
        if self.criteria_comparison_matrix is None:
            self.criteria_comparison_matrix = ComparisonMatrix(self.criteria, "Критерии")
            print(f"Created new criteria comparison matrix with criteria: {self.criteria}")
        
        i = self.criteria.index(criterion1)
        j = self.criteria.index(criterion2)
        self.criteria_comparison_matrix.set_comparison(i, j, value)
        print(f"Set matrix[{i}][{j}] = {value}")
        
        # Выводим текущую матрицу для отладки
        print("Current criteria matrix:")
        for row in self.criteria_comparison_matrix.matrix:
            print(f"  {row}")
    
    def add_criterion_comparison_linguistic(self, criterion1: str, criterion2: str, linguistic: str):
        """Добавление лингвистического сравнения критериев"""
        if self.criteria_comparison_matrix is None:
            self.criteria_comparison_matrix = ComparisonMatrix(self.criteria, "Критерии")
        
        i = self.criteria.index(criterion1)
        j = self.criteria.index(criterion2)
        
        # ИСПРАВЛЕНО: используем шкалу Саати для преобразования лингвистической оценки
        from .bellman_zade import SaatyScale
        value = SaatyScale.from_linguistic(linguistic)
        
        self.criteria_comparison_matrix.set_comparison(i, j, value)
        print(f"Added linguistic comparison: {criterion1} vs {criterion2} = {linguistic} -> {value}")
    
    def add_alternative_comparison(self, criterion: str, alt1: str, alt2: str, value: float):
        """Добавление сравнения альтернатив по конкретному критерию"""
        if criterion not in self.criterion_matrices:
            self.criterion_matrices[criterion] = ComparisonMatrix(self.alternatives, criterion)
        
        i = self.alternatives.index(alt1)
        j = self.alternatives.index(alt2)
        self.criterion_matrices[criterion].set_comparison(i, j, value)
        print(f"Added comparison: {criterion}: {alt1} vs {alt2} = {value}")
    
    def add_alternative_comparison_linguistic(self, criterion: str, alt1: str, alt2: str, linguistic: str):
        """Добавление лингвистического сравнения альтернатив по критерию"""
        if criterion not in self.criterion_matrices:
            self.criterion_matrices[criterion] = ComparisonMatrix(self.alternatives, criterion)
        
        i = self.alternatives.index(alt1)
        j = self.alternatives.index(alt2)
        self.criterion_matrices[criterion].set_comparison_linguistic(i, j, linguistic)
    
    def calculate_criteria_weights(self) -> Dict[str, float]:
        """
        Расчет коэффициентов относительной важности критериев (α_i)
        """
        print("\n=== calculate_criteria_weights called ===")
        print(f"criteria_comparison_matrix is None: {self.criteria_comparison_matrix is None}")
        
        if self.criteria_comparison_matrix is None:
            # Если нет матрицы сравнений, все критерии равноважны
            weights = np.ones(len(self.criteria)) / len(self.criteria)
            print("No criteria comparison matrix, using equal weights")
        else:
            # Выводим матрицу для отладки
            print("Criteria comparison matrix:")
            for i, row in enumerate(self.criteria_comparison_matrix.matrix):
                print(f"  {self.criteria[i]}: {row}")
            
            weights = self.criteria_comparison_matrix.calculate_weights()
            print(f"Calculated weights from matrix: {weights}")
        
        self.criteria_weights = weights
        result = {criterion: weights[i] for i, criterion in enumerate(self.criteria)}
        print(f"Criteria weights result: {result}")
        return result

    def build_fuzzy_sets(self, skip_weights_calculation: bool = False):
        """
        Построение нечетких множеств для каждого критерия
        """
        print(f"=== build_fuzzy_sets called ===")
        print(f"Criterion matrices: {list(self.criterion_matrices.keys())}")
        
        if not self.criterion_matrices:
            print("ERROR: No criterion matrices found!")
            return
        
        for criterion, matrix in self.criterion_matrices.items():
            print(f"Building fuzzy set for criterion: {criterion}")
            print(f"Matrix elements: {matrix.elements}")
            print(f"Matrix shape: {matrix.matrix.shape}")
            
            fuzzy_set = FuzzySetFromComparisons(criterion, matrix)
            self.criterion_fuzzy_sets[criterion] = fuzzy_set
            
            print(f"Fuzzy set memberships for {criterion}:")
            for alt, mu in fuzzy_set.memberships.items():
                print(f"  {alt}: {mu}")
        
        print(f"Total fuzzy sets built: {len(self.criterion_fuzzy_sets)}")
        
        # Расчет весов критериев (если есть матрица И не запрещено)
        if not skip_weights_calculation:
            self.calculate_criteria_weights()
        
        # Если веса не установлены, используем равные
        if self.criteria_weights is None:
            n = len(self.criteria)
            self.criteria_weights = np.ones(n) / n
            print(f"Using equal weights: {self.criteria_weights}")

    def calculate_solution(self, use_weights: bool = True) -> Dict[str, float]:
        """
        Расчет нечеткого решения D по формуле (2.34) или (2.35)
        
        Формула (2.34) для равноважных критериев:
            μ_D(P) = min_{j=1..n} μ_{G_j}(P)
        
        Формула (2.35) для неравноважных критериев:
            μ_D(P) = min_{j=1..n} (μ_{G_j}(P))^{α_j}
        
        где α_j - коэффициенты относительной важности критериев, ∑α_j = 1
        """
        if not self.criterion_fuzzy_sets:
            self.build_fuzzy_sets()
        
        self.solution_fuzzy_set = {}
        
        for alternative in self.alternatives:
            memberships = []
            
            for j, criterion in enumerate(self.criteria):
                fuzzy_set = self.criterion_fuzzy_sets.get(criterion)
                if fuzzy_set:
                    mu = fuzzy_set.get_membership(alternative)
                    
                    if use_weights and self.criteria_weights is not None:
                        # Формула (2.35): возведение в степень α_j
                        alpha = self.criteria_weights[j]
                        # Показатель степени концентрирует нечеткое множество
                        mu_weighted = mu ** alpha
                        memberships.append(mu_weighted)
                        
                        # Сохраняем для детального анализа
                        if alternative not in self.alternative_scores:
                            self.alternative_scores[alternative] = {}
                        self.alternative_scores[alternative][f"{criterion} (степень {alpha:.3f})"] = mu_weighted
                    else:
                        memberships.append(mu)
                    
                    # Сохраняем исходные значения
                    if alternative not in self.alternative_scores:
                        self.alternative_scores[alternative] = {}
                    self.alternative_scores[alternative][criterion] = mu
            
            # Формулы (2.34) и (2.35): пересечение = минимум
            self.solution_fuzzy_set[alternative] = min(memberships) if memberships else 0.0
        
        return self.solution_fuzzy_set
    
    def get_best_alternative(self) -> Tuple[str, float]:
        """Получение наилучшей альтернативы (максимум μ_D)"""
        if not self.solution_fuzzy_set:
            self.calculate_solution()
        
        best = max(self.solution_fuzzy_set.items(), key=lambda x: x[1])
        return best
    
    def get_ranking(self) -> List[Tuple[str, float]]:
        """Получение ранжированного списка альтернатив"""
        if not self.solution_fuzzy_set:
            self.calculate_solution()
        
        return sorted(self.solution_fuzzy_set.items(), key=lambda x: x[1], reverse=True)
    
    def get_consistency_report(self) -> Dict[str, Any]:
        """Отчет о согласованности всех матриц"""
        report = {
            'criteria_matrix': None,
            'criterion_matrices': {}
        }
        
        if self.criteria_comparison_matrix:
            report['criteria_matrix'] = self.criteria_comparison_matrix.calculate_consistency_ratio()
        
        for criterion, matrix in self.criterion_matrices.items():
            report['criterion_matrices'][criterion] = matrix.calculate_consistency_ratio()
        
        return report
    
    def to_dict(self) -> Dict:
        """Сериализация всей модели"""
        return {
            'alternatives': self.alternatives,
            'criteria': self.criteria,
            'criteria_comparison_matrix': self.criteria_comparison_matrix.to_dict() if self.criteria_comparison_matrix else None,
            'criterion_matrices': {
                name: matrix.to_dict() 
                for name, matrix in self.criterion_matrices.items()
            },
            'criteria_weights': self.criteria_weights.tolist() if self.criteria_weights is not None else None,
            'solution': self.solution_fuzzy_set,
            'alternative_scores': self.alternative_scores
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BellmanZadeMCDA':
        """Десериализация модели"""
        model = cls()
        model.alternatives = data['alternatives']
        model.criteria = data['criteria']
        
        if data.get('criteria_comparison_matrix'):
            model.criteria_comparison_matrix = ComparisonMatrix.from_dict(data['criteria_comparison_matrix'])
        
        for name, matrix_data in data.get('criterion_matrices', {}).items():
            model.criterion_matrices[name] = ComparisonMatrix.from_dict(matrix_data)
        
        if data.get('criteria_weights'):
            model.criteria_weights = np.array(data['criteria_weights'])
        
        if data.get('solution'):
            model.solution_fuzzy_set = data['solution']
        
        if data.get('alternative_scores'):
            model.alternative_scores = data['alternative_scores']
        
        return model


class WhatIfAnalyzer:
    """
    Анализатор "Что-Если" для чувствительности решения
    (методика из подраздела 2.3.4)
    """
    
    def __init__(self, model: BellmanZadeMCDA):
        self.model = model
        self.original_solution = model.solution_fuzzy_set.copy() if model.solution_fuzzy_set else {}
    
    def analyze_criterion_comparison_change(
        self, 
        criterion1: str, 
        criterion2: str, 
        new_value: float
    ) -> Dict[str, Any]:
        """
        Анализ изменения сравнения критериев
        """
        # Сохраняем исходное состояние
        original_matrix = self.model.criteria_comparison_matrix
        
        # Создаем копию для анализа
        test_model = BellmanZadeMCDA()
        test_model.alternatives = self.model.alternatives.copy()
        test_model.criteria = self.model.criteria.copy()
        
        # Копируем матрицы сравнений альтернатив
        for criterion, matrix in self.model.criterion_matrices.items():
            test_model.criterion_matrices[criterion] = ComparisonMatrix(
                matrix.elements.copy(), matrix.name
            )
            test_model.criterion_matrices[criterion].matrix = matrix.matrix.copy()
        
        # Устанавливаем новое сравнение критериев
        i = test_model.criteria.index(criterion1)
        j = test_model.criteria.index(criterion2)
        
        if test_model.criteria_comparison_matrix is None:
            test_model.criteria_comparison_matrix = ComparisonMatrix(
                test_model.criteria, "Критерии"
            )
        
        test_model.criteria_comparison_matrix.set_comparison(i, j, new_value)
        
        # Пересчитываем решение
        test_model.build_fuzzy_sets()
        new_solution = test_model.calculate_solution()
        
        # Анализируем изменения
        changes = {}
        for alt in test_model.alternatives:
            old_mu = self.original_solution.get(alt, 0)
            new_mu = new_solution.get(alt, 0)
            changes[alt] = {
                'old': old_mu,
                'new': new_mu,
                'delta': new_mu - old_mu,
                'percent_change': ((new_mu - old_mu) / old_mu * 100) if old_mu > 0 else 0
            }
        
        return {
            'changed_comparison': f"{criterion1} vs {criterion2} = {new_value}",
            'new_weights': {c: w for c, w in zip(test_model.criteria, test_model.criteria_weights)},
            'new_solution': new_solution,
            'best_alternative': test_model.get_best_alternative(),
            'ranking': test_model.get_ranking(),
            'changes': changes
        }
    
    def analyze_alternative_comparison_change(
        self,
        criterion: str,
        alt1: str,
        alt2: str,
        new_value: float
    ) -> Dict[str, Any]:
        """
        Анализ изменения сравнения альтернатив по критерию
        (методика "Что-Если" из подраздела 2.3.4)
        
        Применяются правила (2.38) - (2.41) из методички
        """
        test_model = BellmanZadeMCDA()
        test_model.alternatives = self.model.alternatives.copy()
        test_model.criteria = self.model.criteria.copy()
        
        # Копируем матрицу сравнений критериев
        if self.model.criteria_comparison_matrix:
            test_model.criteria_comparison_matrix = ComparisonMatrix(
                self.model.criteria, "Критерии"
            )
            test_model.criteria_comparison_matrix.matrix = self.model.criteria_comparison_matrix.matrix.copy()
        
        # Копируем матрицы сравнений альтернатив
        for crit, matrix in self.model.criterion_matrices.items():
            test_model.criterion_matrices[crit] = ComparisonMatrix(
                matrix.elements.copy(), matrix.name
            )
            test_model.criterion_matrices[crit].matrix = matrix.matrix.copy()
        
        # Изменяем указанное сравнение
        i = test_model.alternatives.index(alt1)
        j = test_model.alternatives.index(alt2)
        
        if criterion not in test_model.criterion_matrices:
            test_model.criterion_matrices[criterion] = ComparisonMatrix(test_model.alternatives, criterion)
        
        # Устанавливаем новое значение
        test_model.criterion_matrices[criterion].set_comparison(i, j, new_value)
        
        # Применяем правила обеспечения непротиворечивости
        test_model.criterion_matrices[criterion].ensure_consistency()
        
        # Пересчитываем решение
        test_model.build_fuzzy_sets()
        new_solution = test_model.calculate_solution()
        
        # Сравниваем с исходным
        changes = {}
        for alt in test_model.alternatives:
            old_mu = self.original_solution.get(alt, 0)
            new_mu = new_solution.get(alt, 0)
            changes[alt] = {
                'old': old_mu,
                'new': new_mu,
                'delta': new_mu - old_mu
            }
        
        return {
            'changed_comparison': f"{criterion}: {alt1} vs {alt2} = {new_value}",
            'new_solution': new_solution,
            'best_alternative': test_model.get_best_alternative(),
            'ranking': test_model.get_ranking(),
            'changes': changes
        }


# Пример использования (как в методичке, раздел 2.3.3)
def create_brand_project_example() -> BellmanZadeMCDA:
    """
    Создание примера из методички: анализ бренд-проектов
    Используются ТОЧНЫЕ матрицы парных сравнений из методички (2.36)
    """
    model = BellmanZadeMCDA()
    
    # Альтернативы (проекты)
    model.set_alternatives(['P1', 'P2', 'P3', 'P4'])
    
    # Критерии
    model.set_criteria(['G1', 'G2', 'G3', 'G4', 'G5', 'G6'])
    
    # Матрицы парных сравнений ТОЧНО из методички (2.36)
    # A(G1) - матрица из методички
    model.add_alternative_comparison('G1', 'P1', 'P2', 3)
    model.add_alternative_comparison('G1', 'P1', 'P3', 5)
    model.add_alternative_comparison('G1', 'P1', 'P4', 5)
    model.add_alternative_comparison('G1', 'P2', 'P3', 1/3)
    model.add_alternative_comparison('G1', 'P2', 'P4', 1/3)
    model.add_alternative_comparison('G1', 'P3', 'P4', 1/5)
    
    # A(G2)
    model.add_alternative_comparison('G2', 'P1', 'P2', 1/3)
    model.add_alternative_comparison('G2', 'P1', 'P3', 1/5)
    model.add_alternative_comparison('G2', 'P1', 'P4', 1/7)
    model.add_alternative_comparison('G2', 'P2', 'P3', 1/2)
    model.add_alternative_comparison('G2', 'P2', 'P4', 1/3)
    model.add_alternative_comparison('G2', 'P3', 'P4', 1/2)
    
    # A(G3)
    model.add_alternative_comparison('G3', 'P1', 'P2', 1)
    model.add_alternative_comparison('G3', 'P1', 'P3', 5)
    model.add_alternative_comparison('G3', 'P1', 'P4', 1)
    model.add_alternative_comparison('G3', 'P2', 'P3', 1/5)
    model.add_alternative_comparison('G3', 'P2', 'P4', 1/3)
    model.add_alternative_comparison('G3', 'P3', 'P4', 1/7)
    
    # A(G4)
    model.add_alternative_comparison('G4', 'P1', 'P2', 3)
    model.add_alternative_comparison('G4', 'P1', 'P3', 5)
    model.add_alternative_comparison('G4', 'P1', 'P4', 3)
    model.add_alternative_comparison('G4', 'P2', 'P3', 1/3)
    model.add_alternative_comparison('G4', 'P2', 'P4', 1/3)
    model.add_alternative_comparison('G4', 'P3', 'P4', 1/5)
    
    # A(G5)
    model.add_alternative_comparison('G5', 'P1', 'P2', 1/3)
    model.add_alternative_comparison('G5', 'P1', 'P3', 1/3)
    model.add_alternative_comparison('G5', 'P1', 'P4', 1/5)
    model.add_alternative_comparison('G5', 'P2', 'P3', 1)
    model.add_alternative_comparison('G5', 'P2', 'P4', 1/3)
    model.add_alternative_comparison('G5', 'P3', 'P4', 1/2)
    
    # A(G6)
    model.add_alternative_comparison('G6', 'P1', 'P2', 1/7)
    model.add_alternative_comparison('G6', 'P1', 'P3', 1/3)
    model.add_alternative_comparison('G6', 'P1', 'P4', 1/7)
    model.add_alternative_comparison('G6', 'P2', 'P3', 3)
    model.add_alternative_comparison('G6', 'P2', 'P4', 1)
    model.add_alternative_comparison('G6', 'P3', 'P4', 1/3)
    
    # Матрица сравнения критериев из методички
    # Используем лингвистические оценки, которые преобразуются в числа
    model.add_criterion_comparison_linguistic('G1', 'G2', 'слабое преимущество G2 над G1')  # G2 > G1 (3)
    model.add_criterion_comparison_linguistic('G1', 'G3', 'слабое преимущество G3 над G1')  # G3 > G1 (3)
    model.add_criterion_comparison_linguistic('G1', 'G4', 'почти существенное преимущество G1 над G4')  # G1 > G4 (4)
    model.add_criterion_comparison_linguistic('G1', 'G5', 'отсутствует преимущество')  # G1 = G5 (1)
    model.add_criterion_comparison_linguistic('G1', 'G6', 'слабое преимущество G1 над G6')  # G1 > G6 (3)
    
    model.add_criterion_comparison_linguistic('G2', 'G3', 'почти слабое преимущество G2 над G3')  # G2 > G3 (2)
    model.add_criterion_comparison_linguistic('G2', 'G4', 'почти сильное преимущество G2 над G4')  # G2 > G4 (6)
    model.add_criterion_comparison_linguistic('G2', 'G5', 'слабое преимущество G2 над G5')  # G2 > G5 (3)
    model.add_criterion_comparison_linguistic('G2', 'G6', 'существенное преимущество G2 над G6')  # G2 > G6 (5)
    
    model.add_criterion_comparison_linguistic('G3', 'G4', 'существенное преимущество G3 над G4')  # G3 > G4 (5)
    model.add_criterion_comparison_linguistic('G3', 'G5', 'почти слабое преимущество G3 над G5')  # G3 > G5 (2)
    model.add_criterion_comparison_linguistic('G3', 'G6', 'слабое преимущество G3 над G6')  # G3 > G6 (3)
    
    model.add_criterion_comparison_linguistic('G4', 'G5', 'слабое преимущество G5 над G4')  # G5 > G4 (3) -> значение 1/3
    model.add_criterion_comparison_linguistic('G4', 'G6', 'почти слабое преимущество G6 над G4')  # G6 > G4 (2) -> значение 1/2
    
    model.add_criterion_comparison_linguistic('G5', 'G6', 'слабое преимущество G5 над G6')  # G5 > G6 (3)
    
    return model
    