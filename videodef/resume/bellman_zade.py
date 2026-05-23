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
    EQUAL = 1
    WEAK = 2
    WEAK_PLUS = 3
    STRONG = 4
    STRONG_PLUS = 5
    VERY_STRONG = 6
    VERY_STRONG_PLUS = 7
    ABSOLUTE = 8
    ABSOLUTE_PLUS = 9
    
    @classmethod
    def from_linguistic(cls, text: str) -> int:
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
    def __init__(self, elements: List[str], name: str = ""):
        self.elements = elements
        self.name = name
        self.n = len(elements)
        self.matrix = np.ones((self.n, self.n))
        for i in range(self.n):
            self.matrix[i][i] = 1.0
    
    def set_comparison(self, i: int, j: int, value: float):
        self.matrix[i][j] = value
        self.matrix[j][i] = 1.0 / value
    
    def set_comparison_linguistic(self, i: int, j: int, linguistic: str):
        value = SaatyScale.from_linguistic(linguistic)
        self.set_comparison(i, j, value)
    
    def get_comparison(self, i: int, j: int) -> float:
        return self.matrix[i][j]
    
    def calculate_weights(self) -> np.ndarray:
        """
        Расчет весов (степеней принадлежности) через собственный вектор,
        соответствующий максимальному собственному значению.
        Соответствует формулам (1.2) и (1.3) из методички.
        """
        # Вычисляем собственные значения и векторы
        eigenvalues, eigenvectors = np.linalg.eig(self.matrix)
        
        # Находим индекс максимального собственного значения
        max_eigenvalue_idx = np.argmax(eigenvalues.real)
        
        # Извлекаем соответствующий собственный вектор (действительную часть)
        principal_eigenvector = eigenvectors[:, max_eigenvalue_idx].real
        
        # Нормализуем вектор, чтобы сумма элементов была равна 1
        weights = principal_eigenvector / principal_eigenvector.sum()
        
        return weights
    
    def calculate_consistency_ratio(self) -> Dict[str, float]:
        """
        Расчет коэффициента согласованности (CR)
        """
        random_indices = {
            1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
            6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
            11: 1.51, 12: 1.48, 13: 1.56, 14: 1.57, 15: 1.59
        }
        
        # Сначала получаем корректные веса через собственный вектор
        weights = self.calculate_weights()
        
        # Вычисляем λ_max (формула 1.4 в методичке)
        # λ_max = (1/n) * Σ ( (A*w)_i / w_i )
        aw = self.matrix @ weights
        lambda_max = np.mean(aw / weights)
        
        # Индекс согласованности CI
        ci = (lambda_max - self.n) / (self.n - 1) if self.n > 1 else 0
        
        # Случайный индекс RI
        ri = random_indices.get(self.n, 1.59)
        
        # Отношение согласованности CR
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
        Метод для приближенного улучшения согласованности матрицы
        (для What-If анализа)
        """
        cr = self.calculate_consistency_ratio()['cr']
        if cr < 0.1:
            return True
        
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
                        
                        # Правила для корректировки (из методички 2.3.4)
                        if a_ij > a_ik and a_jk > 1:
                            new_value = 1.0
                            self.set_comparison(j, k, new_value)
                            changes_made = True
                        
                        if a_ij > 1 / a_jk and a_ik < 1:
                            new_value = 1.0
                            self.set_comparison(i, k, new_value)
                            changes_made = True
                        
                        if a_ij > 1 and a_jk > 1:
                            new_value = max(a_ij, a_jk)
                            if a_ik < new_value:
                                self.set_comparison(i, k, new_value)
                                changes_made = True
                        
                        if a_ij < 1 and a_jk < 1:
                            new_value = min(a_ij, a_jk)
                            if a_ik > new_value:
                                self.set_comparison(i, k, new_value)
                                changes_made = True
            
            if not changes_made:
                break
        
        return self.calculate_consistency_ratio()['cr'] < 0.1
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'elements': self.elements,
            'matrix': self.matrix.tolist(),
            'n': self.n
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ComparisonMatrix':
        matrix = cls(data['elements'], data['name'])
        matrix.matrix = np.array(data['matrix'])
        return matrix


class FuzzySetFromComparisons:
    def __init__(self, name: str, matrix: ComparisonMatrix):
        self.name = name
        self.matrix = matrix
        # Теперь weights вычисляются корректно через собственный вектор
        self.weights = matrix.calculate_weights()
        self.memberships = {}
        for i, element in enumerate(matrix.elements):
            self.memberships[element] = self.weights[i]
    
    def get_membership(self, element: str) -> float:
        value = self.memberships.get(element, 0.0)
        if value is None or value == 0:
            return 0.0
        return min(1.0, max(0.0, float(value)))
    
    def get_ranked_elements(self) -> List[Tuple[str, float]]:
        return sorted(self.memberships.items(), key=lambda x: x[1], reverse=True)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'matrix': self.matrix.to_dict(),
            'memberships': self.memberships
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FuzzySetFromComparisons':
        matrix = ComparisonMatrix.from_dict(data['matrix'])
        return cls(data['name'], matrix)


class BellmanZadeMCDA:
    def __init__(self):
        self.alternatives: List[str] = []
        self.criteria: List[str] = []
        self.criterion_matrices: Dict[str, ComparisonMatrix] = {}
        self.criterion_fuzzy_sets: Dict[str, FuzzySetFromComparisons] = {}
        self.criteria_weights: Optional[np.ndarray] = None
        self.criteria_comparison_matrix: Optional[ComparisonMatrix] = None
        self.solution_fuzzy_set: Dict[str, float] = {}
        self.alternative_scores: Dict[str, Dict[str, float]] = {}
    
    def set_alternatives(self, alternatives: List[str]):
        self.alternatives = alternatives
    
    def set_criteria(self, criteria: List[str]):
        self.criteria = criteria
    
    def add_criterion_comparison(self, criterion1: str, criterion2: str, value: float):
        if self.criteria_comparison_matrix is None:
            self.criteria_comparison_matrix = ComparisonMatrix(self.criteria, "Критерии")
        
        i = self.criteria.index(criterion1)
        j = self.criteria.index(criterion2)
        self.criteria_comparison_matrix.set_comparison(i, j, value)
    
    def add_criterion_comparison_linguistic(self, criterion1: str, criterion2: str, linguistic: str):
        if self.criteria_comparison_matrix is None:
            self.criteria_comparison_matrix = ComparisonMatrix(self.criteria, "Критерии")
        
        i = self.criteria.index(criterion1)
        j = self.criteria.index(criterion2)
        value = SaatyScale.from_linguistic(linguistic)
        self.criteria_comparison_matrix.set_comparison(i, j, value)
    
    def add_alternative_comparison(self, criterion: str, alt1: str, alt2: str, value: float):
        if criterion not in self.criterion_matrices:
            self.criterion_matrices[criterion] = ComparisonMatrix(self.alternatives, criterion)
        
        i = self.alternatives.index(alt1)
        j = self.alternatives.index(alt2)
        self.criterion_matrices[criterion].set_comparison(i, j, value)
    
    def add_alternative_comparison_linguistic(self, criterion: str, alt1: str, alt2: str, linguistic: str):
        if criterion not in self.criterion_matrices:
            self.criterion_matrices[criterion] = ComparisonMatrix(self.alternatives, criterion)
        
        i = self.alternatives.index(alt1)
        j = self.alternatives.index(alt2)
        self.criterion_matrices[criterion].set_comparison_linguistic(i, j, linguistic)
    
    def set_criteria_weights_direct(self, weights: Dict[str, float]):
        """Прямая установка весов критериев (из методички)"""
        weight_values = [weights.get(c, 0) for c in self.criteria]
        total = sum(weight_values)
        if total > 0:
            self.criteria_weights = np.array([w / total for w in weight_values])
        else:
            self.criteria_weights = np.ones(len(self.criteria)) / len(self.criteria)
    
    def calculate_criteria_weights(self) -> Dict[str, float]:
        if self.criteria_comparison_matrix is None:
            weights = np.ones(len(self.criteria)) / len(self.criteria)
        else:
            weights = self.criteria_comparison_matrix.calculate_weights()
        
        self.criteria_weights = weights
        return {criterion: weights[i] for i, criterion in enumerate(self.criteria)}
    
    def build_fuzzy_sets(self, skip_weights_calculation: bool = False):
        """
        Построение нечетких множеств на основе матриц парных сравнений.
        Если skip_weights_calculation=True, веса критериев не пересчитываются.
        Если веса уже были заданы вручную (через set_criteria_weights_direct),
        они сохраняются независимо от skip_weights_calculation.
        """
        if not self.criterion_matrices:
            print("ERROR: No criterion matrices found!")
            return
        
        for criterion, matrix in self.criterion_matrices.items():
            fuzzy_set = FuzzySetFromComparisons(criterion, matrix)
            self.criterion_fuzzy_sets[criterion] = fuzzy_set
        
        # Пересчитываем веса только если:
        # - это не запрещено явно (skip_weights_calculation=False)
        # - и веса ещё не были установлены вручную (self.criteria_weights is None)
        if not skip_weights_calculation and self.criteria_weights is None:
            self.calculate_criteria_weights()
        
        # Если после всех проверок веса всё ещё None (например, нет матриц сравнения критериев),
        # назначаем равномерные веса как fallback
        if self.criteria_weights is None:
            n = len(self.criteria)
            self.criteria_weights = np.ones(n) / n
    
    def calculate_solution(self, use_weights: bool = True) -> Dict[str, float]:
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
                        alpha = self.criteria_weights[j]
                        mu_weighted = mu ** alpha
                        memberships.append(mu_weighted)
                        
                        if alternative not in self.alternative_scores:
                            self.alternative_scores[alternative] = {}
                        # Сохраняем для отчета в Excel
                        self.alternative_scores[alternative][f"{criterion}_weighted"] = mu_weighted
                    else:
                        memberships.append(mu)
                    
                    if alternative not in self.alternative_scores:
                        self.alternative_scores[alternative] = {}
                    self.alternative_scores[alternative][criterion] = mu
            
            self.solution_fuzzy_set[alternative] = min(memberships) if memberships else 0.0
        
        return self.solution_fuzzy_set
    
    def get_best_alternative(self) -> Tuple[str, float]:
        if not self.solution_fuzzy_set:
            self.calculate_solution()
        best = max(self.solution_fuzzy_set.items(), key=lambda x: x[1])
        return best
    
    def get_ranking(self) -> List[Tuple[str, float]]:
        if not self.solution_fuzzy_set:
            self.calculate_solution()
        return sorted(self.solution_fuzzy_set.items(), key=lambda x: x[1], reverse=True)
    
    def get_consistency_report(self) -> Dict[str, Any]:
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
    def __init__(self, model: BellmanZadeMCDA):
        self.model = model
        self.original_solution = model.solution_fuzzy_set.copy() if model.solution_fuzzy_set else {}
    
    def analyze_criterion_comparison_change(self, criterion1: str, criterion2: str, new_value: float) -> Dict[str, Any]:
        test_model = BellmanZadeMCDA()
        test_model.alternatives = self.model.alternatives.copy()
        test_model.criteria = self.model.criteria.copy()
        
        for criterion, matrix in self.model.criterion_matrices.items():
            test_model.criterion_matrices[criterion] = ComparisonMatrix(
                matrix.elements.copy(), matrix.name
            )
            test_model.criterion_matrices[criterion].matrix = matrix.matrix.copy()
        
        i = test_model.criteria.index(criterion1)
        j = test_model.criteria.index(criterion2)
        
        if test_model.criteria_comparison_matrix is None:
            test_model.criteria_comparison_matrix = ComparisonMatrix(test_model.criteria, "Критерии")
        
        test_model.criteria_comparison_matrix.set_comparison(i, j, new_value)
        
        test_model.build_fuzzy_sets()
        new_solution = test_model.calculate_solution()
        
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
    
    def analyze_alternative_comparison_change(self, criterion: str, alt1: str, alt2: str, new_value: float) -> Dict[str, Any]:
        test_model = BellmanZadeMCDA()
        test_model.alternatives = self.model.alternatives.copy()
        test_model.criteria = self.model.criteria.copy()
        
        if self.model.criteria_comparison_matrix:
            test_model.criteria_comparison_matrix = ComparisonMatrix(self.model.criteria, "Критерии")
            test_model.criteria_comparison_matrix.matrix = self.model.criteria_comparison_matrix.matrix.copy()
        
        for crit, matrix in self.model.criterion_matrices.items():
            test_model.criterion_matrices[crit] = ComparisonMatrix(matrix.elements.copy(), matrix.name)
            test_model.criterion_matrices[crit].matrix = matrix.matrix.copy()
        
        i = test_model.alternatives.index(alt1)
        j = test_model.alternatives.index(alt2)
        
        if criterion not in test_model.criterion_matrices:
            test_model.criterion_matrices[criterion] = ComparisonMatrix(test_model.alternatives, criterion)
        
        test_model.criterion_matrices[criterion].set_comparison(i, j, new_value)
        test_model.criterion_matrices[criterion].ensure_consistency()
        
        test_model.build_fuzzy_sets()
        new_solution = test_model.calculate_solution()
        
        changes = {}
        for alt in test_model.alternatives:
            old_mu = self.original_solution.get(alt, 0)
            new_mu = new_solution.get(alt, 0)
            changes[alt] = {'old': old_mu, 'new': new_mu, 'delta': new_mu - old_mu}
        
        return {
            'changed_comparison': f"{criterion}: {alt1} vs {alt2} = {new_value}",
            'new_solution': new_solution,
            'best_alternative': test_model.get_best_alternative(),
            'ranking': test_model.get_ranking(),
            'changes': changes
        }


def create_brand_project_example() -> BellmanZadeMCDA:
    """
    Создание примера из методички: анализ бренд-проектов.
    Используются МАТРИЦЫ, ДАЮЩИЕ ОЖИДАЕМЫЕ НЕЧЕТКИЕ МНОЖЕСТВА (2.37)
    """
    model = BellmanZadeMCDA()
    
    model.set_alternatives(['P1', 'P2', 'P3', 'P4'])
    model.set_criteria(['G1', 'G2', 'G3', 'G4', 'G5', 'G6'])
    
    # ---------- Матрица G1 (ожидаемые μ: P1=0.39, P2=0.39, P3=0.15, P4=0.07) ----------
    # P1 и P2 равны, P3 хуже, P4 ещё хуже
    model.add_alternative_comparison('G1', 'P1', 'P2', 1)    # отсутствует преимущество
    model.add_alternative_comparison('G1', 'P1', 'P3', 3)    # слабое преимущество
    model.add_alternative_comparison('G1', 'P1', 'P4', 5)    # существенное преимущество
    model.add_alternative_comparison('G1', 'P2', 'P3', 3)    # слабое преимущество
    model.add_alternative_comparison('G1', 'P2', 'P4', 5)    # существенное преимущество
    model.add_alternative_comparison('G1', 'P3', 'P4', 3)    # слабое преимущество
    
    # ---------- Матрица G2 (ожидаемые μ: P1=0.59, P2=0.22, P3=0.12, P4=0.07) ----------
    model.add_alternative_comparison('G2', 'P1', 'P2', 3)    # слабое преимущество
    model.add_alternative_comparison('G2', 'P1', 'P3', 5)    # существенное
    model.add_alternative_comparison('G2', 'P1', 'P4', 7)    # явное
    model.add_alternative_comparison('G2', 'P2', 'P3', 2)    # почти слабое? используем 2
    model.add_alternative_comparison('G2', 'P2', 'P4', 3)    # слабое
    model.add_alternative_comparison('G2', 'P3', 'P4', 2)    # почти слабое
    
    # ---------- Матрица G3 (ожидаемые μ: P1=0.42, P2=0.11, P3=0.42, P4=0.05) ----------
    # P1 и P3 одинаково хороши, P2 хуже, P4 очень плох
    model.add_alternative_comparison('G3', 'P1', 'P2', 4)    # почти существенное? (даёт 0.42/0.105)
    model.add_alternative_comparison('G3', 'P1', 'P3', 1)    # равны
    model.add_alternative_comparison('G3', 'P1', 'P4', 8)    # очень сильное
    model.add_alternative_comparison('G3', 'P2', 'P3', 1/4)  # обратное (P2 хуже P3)
    model.add_alternative_comparison('G3', 'P2', 'P4', 2)    # слабое
    model.add_alternative_comparison('G3', 'P3', 'P4', 8)    # очень сильное
    
    # ---------- Матрица G4 (ожидаемые μ: P1=0.08, P2=0.23, P3=0.48, P4=0.21) ----------
    # P3 лучший, P2 и P4 средние, P1 худший
    model.add_alternative_comparison('G4', 'P1', 'P2', 1/3)   # P1 хуже P2
    model.add_alternative_comparison('G4', 'P1', 'P3', 1/6)   # P1 значительно хуже P3
    model.add_alternative_comparison('G4', 'P1', 'P4', 1/3)   # P1 хуже P4
    model.add_alternative_comparison('G4', 'P2', 'P3', 1/2)   # P2 хуже P3
    model.add_alternative_comparison('G4', 'P2', 'P4', 1)     # P2 равен P4
    model.add_alternative_comparison('G4', 'P3', 'P4', 3)     # P3 лучше P4
    
    # ---------- Матрица G5 (ожидаемые μ: P1=0.08, P2=0.23, P3=0.48, P4=0.21) ----------
    # Аналогична G4
    model.add_alternative_comparison('G5', 'P1', 'P2', 1/3)
    model.add_alternative_comparison('G5', 'P1', 'P3', 1/6)
    model.add_alternative_comparison('G5', 'P1', 'P4', 1/3)
    model.add_alternative_comparison('G5', 'P2', 'P3', 1/2)
    model.add_alternative_comparison('G5', 'P2', 'P4', 1)
    model.add_alternative_comparison('G5', 'P3', 'P4', 3)
    
    # ---------- Матрица G6 (ожидаемые μ: P1=0.06, P2=0.40, P3=0.14, P4=0.40) ----------
    # P2 и P4 лучшие, P3 хуже, P1 самый плохой
    model.add_alternative_comparison('G6', 'P1', 'P2', 1/7)   # очень сильное преимущество P2
    model.add_alternative_comparison('G6', 'P1', 'P3', 1/3)   # слабое преимущество P3
    model.add_alternative_comparison('G6', 'P1', 'P4', 1/7)   # очень сильное преимущество P4
    model.add_alternative_comparison('G6', 'P2', 'P3', 3)     # слабое преимущество P2
    model.add_alternative_comparison('G6', 'P2', 'P4', 1)     # равны
    model.add_alternative_comparison('G6', 'P3', 'P4', 1/3)   # P3 хуже P4
    
    # Явная установка весов критериев из методички (α1=0.15, α2=0.34, α3=0.26, α4=0.05, α5=0.13, α6=0.07)
    textbook_weights = {
        'G1': 0.15, 'G2': 0.34, 'G3': 0.26,
        'G4': 0.05, 'G5': 0.13, 'G6': 0.07
    }
    model.set_criteria_weights_direct(textbook_weights)
    
    return model