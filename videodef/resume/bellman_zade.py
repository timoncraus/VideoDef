"""
Полноценная реализация метода нечеткого многокритериального анализа вариантов Беллмана-Заде.
"""

import math
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum


class MembershipFunctionType(Enum):
    TRIANGULAR = "triangular"
    TRAPEZOIDAL = "trapezoidal"
    GAUSSIAN = "gaussian"
    BELL = "bell"
    SIGMOID = "sigmoid"
    Z_SHAPED = "z_shaped"
    S_SHAPED = "s_shaped"
    PI_SHAPED = "pi_shaped"


@dataclass
class FuzzySet:
    name: str
    type: MembershipFunctionType
    params: Dict[str, float]
    linguistic_label: str
    
    def membership(self, x: float) -> float:
        if self.type == MembershipFunctionType.TRIANGULAR:
            return self._triangular(x)
        elif self.type == MembershipFunctionType.TRAPEZOIDAL:
            return self._trapezoidal(x)
        elif self.type == MembershipFunctionType.GAUSSIAN:
            return self._gaussian(x)
        elif self.type == MembershipFunctionType.BELL:
            return self._bell(x)
        elif self.type == MembershipFunctionType.SIGMOID:
            return self._sigmoid(x)
        elif self.type == MembershipFunctionType.Z_SHAPED:
            return self._z_shaped(x)
        elif self.type == MembershipFunctionType.S_SHAPED:
            return self._s_shaped(x)
        elif self.type == MembershipFunctionType.PI_SHAPED:
            return self._pi_shaped(x)
        return 0.0
    
    def _triangular(self, x: float) -> float:
        a, b, c = self.params['a'], self.params['b'], self.params['c']
        if x <= a or x >= c:
            return 0.0
        if a < x <= b:
            return (x - a) / (b - a)
        if b < x < c:
            return (c - x) / (c - b)
        return 1.0 if x == b else 0.0
    
    def _trapezoidal(self, x: float) -> float:
        a, b, c, d = self.params['a'], self.params['b'], self.params['c'], self.params['d']
        if x <= a or x >= d:
            return 0.0
        if a < x < b:
            return (x - a) / (b - a)
        if b <= x <= c:
            return 1.0
        if c < x < d:
            return (d - x) / (d - c)
        return 0.0
    
    def _gaussian(self, x: float) -> float:
        c, sigma = self.params['c'], self.params['sigma']
        return math.exp(-((x - c) ** 2) / (2 * sigma ** 2))
    
    def _bell(self, x: float) -> float:
        a, b, c = self.params['a'], self.params['b'], self.params['c']
        return 1.0 / (1.0 + abs((x - c) / a) ** (2 * b))
    
    def _sigmoid(self, x: float) -> float:
        a, c = self.params['a'], self.params['c']
        return 1.0 / (1.0 + math.exp(-a * (x - c)))
    
    def _z_shaped(self, x: float) -> float:
        a, b = self.params['a'], self.params['b']
        if x <= a:
            return 1.0
        if a < x <= (a + b) / 2:
            return 1.0 - 2.0 * ((x - a) / (b - a)) ** 2
        if (a + b) / 2 < x <= b:
            return 2.0 * ((b - x) / (b - a)) ** 2
        return 0.0
    
    def _s_shaped(self, x: float) -> float:
        a, b = self.params['a'], self.params['b']
        if x <= a:
            return 0.0
        if a < x <= (a + b) / 2:
            return 2.0 * ((x - a) / (b - a)) ** 2
        if (a + b) / 2 < x <= b:
            return 1.0 - 2.0 * ((b - x) / (b - a)) ** 2
        return 1.0
    
    def _pi_shaped(self, x: float) -> float:
        a, b, c, d = self.params['a'], self.params['b'], self.params['c'], self.params['d']
        if x <= a:
            return 0.0
        if a < x <= (a + b) / 2:
            return 2.0 * ((x - a) / (b - a)) ** 2
        if (a + b) / 2 < x <= b:
            return 1.0 - 2.0 * ((b - x) / (b - a)) ** 2
        if b < x <= c:
            return 1.0
        if c < x <= (c + d) / 2:
            return 1.0 - 2.0 * ((x - c) / (d - c)) ** 2
        if (c + d) / 2 < x <= d:
            return 2.0 * ((d - x) / (d - c)) ** 2
        return 0.0


@dataclass
class LinguisticVariable:
    name: str
    description: str
    min_value: float
    max_value: float
    unit: str
    fuzzy_sets: List[FuzzySet] = field(default_factory=list)
    
    def add_fuzzy_set(self, fuzzy_set: FuzzySet):
        self.fuzzy_sets.append(fuzzy_set)
    
    def fuzzify(self, value: float) -> Dict[str, float]:
        result = {}
        for fs in self.fuzzy_sets:
            result[fs.name] = fs.membership(value)
        return result
    
    def get_best_label(self, value: float) -> str:
        memberships = self.fuzzify(value)
        best = max(memberships, key=memberships.get)
        return self.fuzzy_sets[[fs.name for fs in self.fuzzy_sets].index(best)].linguistic_label


class BellmanZadeModel:
    def __init__(self):
        self.linguistic_variables: Dict[str, LinguisticVariable] = {}
        self.goals: List[Dict[str, Any]] = []
        self.constraints: List[Dict[str, Any]] = []
        self.alternatives: List[Dict[str, float]] = []
        self.results: List[Dict[str, Any]] = []
    
    def add_linguistic_variable(self, variable: LinguisticVariable):
        self.linguistic_variables[variable.name] = variable
    
    def add_goal(self, variable_name: str, fuzzy_set_name: str, importance: float = 1.0):
        if variable_name not in self.linguistic_variables:
            raise ValueError(f"Лингвистическая переменная '{variable_name}' не найдена")
        
        fuzzy_set = None
        for fs in self.linguistic_variables[variable_name].fuzzy_sets:
            if fs.name == fuzzy_set_name:
                fuzzy_set = fs
                break
        
        if fuzzy_set is None:
            raise ValueError(f"Нечеткое множество '{fuzzy_set_name}' не найдено")
        
        self.goals.append({
            'variable': variable_name,
            'fuzzy_set': fuzzy_set,
            'importance': importance
        })
    
    def add_constraint(self, variable_name: str, constraint_type: str, params: Dict[str, float], importance: float = 1.0):
        self.constraints.append({
            'variable': variable_name,
            'type': constraint_type,
            'params': params,
            'importance': importance
        })
    
    def _evaluate_goal(self, alternative: Dict[str, float], goal: Dict) -> float:
        variable_name = goal['variable']
        fuzzy_set = goal['fuzzy_set']
        value = alternative.get(variable_name)
        if value is None:
            return 0.0
        return fuzzy_set.membership(value)
    
    def _evaluate_constraint(self, alternative: Dict[str, float], constraint: Dict) -> float:
        variable_name = constraint['variable']
        value = alternative.get(variable_name)
        constraint_type = constraint['type']
        params = constraint['params']
        
        if value is None:
            return 0.0
        
        if constraint_type == 'less_than':
            threshold = params['threshold']
            tolerance = params.get('tolerance', max(100, threshold * 0.2))
            return FuzzySet(
                name='less_than',
                type=MembershipFunctionType.Z_SHAPED,
                params={'a': max(0, threshold - tolerance), 'b': threshold + tolerance},
                linguistic_label=''
            ).membership(value)
            
        elif constraint_type == 'greater_than':
            threshold = params['threshold']
            tolerance = params.get('tolerance', max(1, threshold * 0.2))
            return FuzzySet(
                name='greater_than',
                type=MembershipFunctionType.S_SHAPED,
                params={'a': max(0, threshold - tolerance), 'b': threshold + tolerance},
                linguistic_label=''
            ).membership(value)
        
        return 0.0
    
    def evaluate_alternative(self, alternative: Dict[str, float]) -> Dict[str, Any]:
        membership_values = {}
        
        goals_mu_unweighted = []
        goals_mu_weighted = []
        
        for goal in self.goals:
            mu = self._evaluate_goal(alternative, goal)
            goals_mu_unweighted.append(mu)
            goals_mu_weighted.append(mu * goal['importance'])
            membership_values[f"Цель: {goal['variable']}"] = mu
        
        constraints_mu_unweighted = []
        constraints_mu_weighted = []
        
        for constraint in self.constraints:
            mu = self._evaluate_constraint(alternative, constraint)
            constraints_mu_unweighted.append(mu)
            constraints_mu_weighted.append(mu * constraint['importance'])
            membership_values[f"Ограничение: {constraint['variable']}"] = mu
        
        all_mu_unweighted = goals_mu_unweighted + constraints_mu_unweighted
        mu_aggregated = min(all_mu_unweighted) if all_mu_unweighted else 0.0
        
        all_mu_weighted = goals_mu_weighted + constraints_mu_weighted
        mu_weighted = np.mean(all_mu_weighted) if all_mu_weighted else 0.0
        
        mu_combined = (mu_aggregated + mu_weighted) / 2.0
        
        return {
            'values': alternative,
            'membership_values': membership_values,
            'mu_aggregated': mu_aggregated,
            'mu_weighted': mu_weighted,
            'mu_combined': mu_combined,
            'satisfaction_level': self._get_satisfaction_level(mu_combined),
            'linguistic_evaluation': self._get_linguistic_evaluation(alternative)
        }
    
    def _get_satisfaction_level(self, mu: float) -> Dict[str, str]:
        if mu >= 0.9:
            return {'level': 'A', 'description': 'Идеально подходит'}
        elif mu >= 0.7:
            return {'level': 'B', 'description': 'Отлично подходит'}
        elif mu >= 0.5:
            return {'level': 'C', 'description': 'Хорошо подходит'}
        elif mu >= 0.3:
            return {'level': 'D', 'description': 'Удовлетворительно'}
        elif mu >= 0.1:
            return {'level': 'E', 'description': 'Условно подходит'}
        else:
            return {'level': 'F', 'description': 'Не подходит'}
    
    def _get_linguistic_evaluation(self, alternative: Dict[str, float]) -> Dict[str, str]:
        evaluation = {}
        for var_name, variable in self.linguistic_variables.items():
            if var_name in alternative:
                evaluation[var_name] = variable.get_best_label(alternative[var_name])
        return evaluation
    
    def rank_alternatives(self, alternatives: List[Dict[str, float]]) -> List[Dict[str, Any]]:
        self.alternatives = alternatives
        self.results = []
        
        for i, alt in enumerate(alternatives):
            evaluation = self.evaluate_alternative(alt)
            evaluation['alternative_id'] = i
            evaluation['rank'] = 0
            self.results.append(evaluation)
        
        self.results.sort(key=lambda x: (-x['mu_aggregated'], -x['mu_combined']))
        
        for rank, result in enumerate(self.results, 1):
            result['rank'] = rank
        
        return self.results


class TeacherSearchModel(BellmanZadeModel):
    def __init__(self):
        super().__init__()
        self._initialize_variables()
    
    def _initialize_variables(self):
        # 1. Цена занятия
        price_var = LinguisticVariable(
            name='price',
            description='Стоимость одного занятия',
            min_value=0,
            max_value=5000,
            unit='₽'
        )
        price_var.add_fuzzy_set(FuzzySet('low', MembershipFunctionType.Z_SHAPED,
                                        {'a': 1000, 'b': 2500}, 'Низкая'))
        price_var.add_fuzzy_set(FuzzySet('medium', MembershipFunctionType.TRIANGULAR,
                                        {'a': 1500, 'b': 2500, 'c': 3500}, 'Средняя'))
        price_var.add_fuzzy_set(FuzzySet('high', MembershipFunctionType.S_SHAPED,
                                        {'a': 3000, 'b': 4500}, 'Высокая'))
        self.add_linguistic_variable(price_var)
        
        # 2. Расстояние
        distance_var = LinguisticVariable(
            name='distance',
            description='Расстояние до преподавателя',
            min_value=0,
            max_value=50,
            unit='км'
        )
        distance_var.add_fuzzy_set(FuzzySet('close', MembershipFunctionType.Z_SHAPED,
                                            {'a': 2, 'b': 10}, 'Близко'))
        distance_var.add_fuzzy_set(FuzzySet('medium', MembershipFunctionType.TRIANGULAR,
                                            {'a': 5, 'b': 15, 'c': 25}, 'Средне'))
        distance_var.add_fuzzy_set(FuzzySet('far', MembershipFunctionType.S_SHAPED,
                                            {'a': 15, 'b': 35}, 'Далеко'))
        self.add_linguistic_variable(distance_var)
        
        # 3. Опыт работы
        experience_var = LinguisticVariable(
            name='experience',
            description='Опыт работы преподавателем',
            min_value=0,
            max_value=30,
            unit='лет'
        )
        experience_var.add_fuzzy_set(FuzzySet('beginner', MembershipFunctionType.Z_SHAPED,
                                            {'a': 1, 'b': 3}, 'Начинающий'))
        experience_var.add_fuzzy_set(FuzzySet('intermediate', MembershipFunctionType.TRIANGULAR,
                                            {'a': 2, 'b': 5, 'c': 8}, 'Средний'))
        experience_var.add_fuzzy_set(FuzzySet('expert', MembershipFunctionType.S_SHAPED,
                                            {'a': 4, 'b': 10}, 'Опытный'))
        self.add_linguistic_variable(experience_var)
        
        # 4. Рейтинг
        rating_var = LinguisticVariable(
            name='rating',
            description='Рейтинг преподавателя',
            min_value=0,
            max_value=5,
            unit='звезд'
        )
        rating_var.add_fuzzy_set(FuzzySet('low', MembershipFunctionType.Z_SHAPED,
                                        {'a': 1, 'b': 2.5}, 'Низкий'))
        rating_var.add_fuzzy_set(FuzzySet('medium', MembershipFunctionType.TRIANGULAR,
                                        {'a': 2, 'b': 3.5, 'c': 4.5}, 'Средний'))
        rating_var.add_fuzzy_set(FuzzySet('high', MembershipFunctionType.S_SHAPED,
                                        {'a': 3, 'b': 4.5}, 'Высокий'))
        self.add_linguistic_variable(rating_var)
        
        # 5. Образование
        education_var = LinguisticVariable(
            name='education',
            description='Уровень образования',
            min_value=0,
            max_value=10,
            unit='баллов'
        )
        education_var.add_fuzzy_set(FuzzySet('basic', MembershipFunctionType.Z_SHAPED,
                                            {'a': 2, 'b': 4}, 'Базовое'))
        education_var.add_fuzzy_set(FuzzySet('advanced', MembershipFunctionType.TRIANGULAR,
                                            {'a': 3, 'b': 5, 'c': 7}, 'Продвинутое'))
        education_var.add_fuzzy_set(FuzzySet('expert', MembershipFunctionType.S_SHAPED,
                                            {'a': 5, 'b': 8}, 'Экспертное'))
        self.add_linguistic_variable(education_var)
    
    def setup_user_preferences(self, preferences: Dict[str, Any]):
        self.goals = []
        self.constraints = []
        
        # Цена
        if 'price' in preferences:
            price_prefs = preferences['price']
            price_min = price_prefs.get('min', 0)
            price_max = price_prefs.get('max', 5000)
            price_goal = price_prefs.get('goal', 'low')
            
            self.add_goal('price', price_goal, importance=0.8)
            
            if price_max < 5000:
                self.add_constraint('price', 'less_than', 
                                  {'threshold': price_max, 'tolerance': max(200, price_max * 0.2)})
            if price_min > 0:
                self.add_constraint('price', 'greater_than',
                                  {'threshold': price_min, 'tolerance': max(100, price_min * 0.2)})
        
        # Расстояние
        if 'distance' in preferences:
            dist_prefs = preferences['distance']
            max_distance = dist_prefs.get('max', 50)
            distance_goal = dist_prefs.get('goal', 'close')
            
            self.add_goal('distance', distance_goal, importance=0.7)
            
            if max_distance < 50:
                self.add_constraint('distance', 'less_than',
                                  {'threshold': max_distance, 'tolerance': 2})
        
        # Опыт
        if 'experience' in preferences:
            exp_prefs = preferences['experience']
            min_experience = exp_prefs.get('min', 0)
            experience_goal = exp_prefs.get('goal', 'expert')
            
            self.add_goal('experience', experience_goal, importance=0.6)
            
            if min_experience > 0:
                self.add_constraint('experience', 'greater_than',
                                  {'threshold': min_experience, 'tolerance': 1})
        
        # Рейтинг
        if 'rating' in preferences:
            rat_prefs = preferences['rating']
            min_rating = rat_prefs.get('min', 0)
            rating_goal = rat_prefs.get('goal', 'high')
            
            self.add_goal('rating', rating_goal, importance=0.7)
            
            if min_rating > 0:
                self.add_constraint('rating', 'greater_than',
                                  {'threshold': min_rating, 'tolerance': 0.5})
        
        # Образование
        if 'education' in preferences:
            edu_prefs = preferences['education']
            min_education = edu_prefs.get('min', 0)
            education_goal = edu_prefs.get('goal', 'expert')
            
            self.add_goal('education', education_goal, importance=0.5)
            
            if min_education > 0:
                self.add_constraint('education', 'greater_than',
                                  {'threshold': min_education, 'tolerance': 1})


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c