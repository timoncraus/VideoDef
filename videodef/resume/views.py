import io
import base64
import json
import math
from datetime import datetime
from typing import List, Dict, Any, Tuple

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Avg, F
from django.core.cache import cache
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    DetailView,
)
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
import django_filters
from django import forms
from django_filters.views import FilterView

from .bellman_zade import (
    BellmanZadeMCDA, 
    WhatIfAnalyzer, 
    ComparisonMatrix, 
    FuzzySetFromComparisons,
    calculate_distance
)

from document.forms import DocumentForm
from document.models import Document
from child.models import Child

from .models import Resume, ViolationType, TeacherReview, FuzzyComparisonSettings, UserCriteriaWeights
from .forms import ResumeForm, ResumeImageFormSet, ResumeInitialImageFormSet, TeacherReviewForm

# Для преподавателя: список резюме
class ResumeListView(LoginRequiredMixin, ListView):
    model = Resume
    template_name = "resume/my_resumes.html"
    context_object_name = "resumes"

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


# Для преподавателя: создание резюме
class ResumeCreateView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeForm
    template_name = "resume/my_resume_create.html"
    success_url = reverse_lazy("resume:my_resumes")

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        images_formset = ResumeInitialImageFormSet(
            self.request.POST, self.request.FILES, instance=self.object
        )
        if images_formset.is_valid():
            images_formset.save()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images_formset"] = ResumeInitialImageFormSet()
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


# Для преподавателя: редактирование резюме
class ResumeUpdateView(LoginRequiredMixin, UpdateView):
    model = Resume
    form_class = ResumeForm
    template_name = "resume/my_resume_create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["images_formset"] = ResumeImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images_formset = ResumeImageFormSet(
            self.request.POST, self.request.FILES, instance=self.object
        )
        if images_formset.is_valid():
            images_formset.save()
        return response

    def get_success_url(self):
        return reverse("resume:edit_my_resume", kwargs={"pk": self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs


# Для преподавателя: удаление резюме
class ResumeDeleteView(LoginRequiredMixin, DeleteView):
    model = Resume
    template_name = "resume/my_resume_confirm_delete.html"
    success_url = reverse_lazy("resume:my_resumes")


# Для родителя: фильтрация резюме по видам нарушений
class ResumeFilter(django_filters.FilterSet):
    violation_types = django_filters.ModelMultipleChoiceFilter(
        queryset=ViolationType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Виды нарушений",
        method="filter_violation_types",
    )

    class Meta:
        model = Resume
        fields = ["violation_types"]

    def filter_violation_types(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(violation_types__in=value).distinct()


# Для родителя: поиск преподавателей

class PublicResumeListView(LoginRequiredMixin, FilterView):
    """
    Поиск преподавателей с использованием полноценного метода 
    нечеткого многокритериального анализа Беллмана-Заде.
    
    Используются экспертные парные сравнения, настроенные администратором.
    """
    model = Resume
    template_name = "resume/public_resume_list.html"
    context_object_name = "resumes"
    filterset_class = ResumeFilter
    
    def get_queryset(self):
        """Базовый queryset с активными резюме"""
        return Resume.objects.filter(status=Resume.ACTIVE).select_related(
            'user__profile'
        ).prefetch_related('violation_types', 'user__profile__role')
    
    def safe_float(self, param, default):
        """Безопасное преобразование строки в float"""
        value = self.request.GET.get(param, str(default))
        if isinstance(value, str):
            value = value.replace(',', '.')
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_user_location(self, child_id: int = None) -> Tuple[float, float]:
        """
        Получение координат пользователя.
        Сначала пытается получить из профиля пользователя,
        затем из ребенка (если есть поля геолокации),
        иначе возвращает координаты по умолчанию.
        """
        # Координаты по умолчанию (Москва)
        default_lat = 55.751244
        default_lon = 37.618423
        
        print(f"=== get_user_location called with child_id={child_id} ===")
        
        # Пробуем получить из профиля пользователя
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            print(f"Profile exists: {profile}")
            print(f"Profile.location_lat: {profile.location_lat}")
            print(f"Profile.location_lon: {profile.location_lon}")
            
            if profile.location_lat is not None and profile.location_lon is not None:
                try:
                    lat = float(profile.location_lat)
                    lon = float(profile.location_lon)
                    print(f"Using profile coordinates: lat={lat}, lon={lon}")
                    return lat, lon
                except (ValueError, TypeError) as e:
                    print(f"Error converting profile coordinates: {e}")
        
        # Если указан ребенок, пробуем получить координаты из модели Child
        if child_id:
            try:
                child = Child.objects.get(id=child_id, user=self.request.user)
                print(f"Child found: {child}")
                print(f"Child has location_lat: {hasattr(child, 'location_lat')}")
                print(f"Child has location_lon: {hasattr(child, 'location_lon')}")
                
                if hasattr(child, 'location_lat') and hasattr(child, 'location_lon'):
                    print(f"Child.location_lat value: {child.location_lat}")
                    print(f"Child.location_lon value: {child.location_lon}")
                    
                    if child.location_lat is not None and child.location_lon is not None:
                        try:
                            lat = float(child.location_lat)
                            lon = float(child.location_lon)
                            print(f"Using child coordinates: lat={lat}, lon={lon}")
                            return lat, lon
                        except (ValueError, TypeError) as e:
                            print(f"Error converting child coordinates: {e}")
                    else:
                        print("Child coordinates are None")
                else:
                    print("Child model has no location fields")
            except Child.DoesNotExist as e:
                print(f"Child not found: {e}")
            except Exception as e:
                print(f"Error getting child: {e}")
        
        print(f"Using default coordinates: {default_lat}, {default_lon}")
        return default_lat, default_lon
    
    def get_criteria_weights_from_admin(self) -> Dict[str, float]:
        """
        Получение коэффициентов важности критериев из настроек администратора.
        Если настройки отсутствуют, используются значения по умолчанию.
        """
        from .models import FuzzyComparisonSettings
        
        try:
            settings = FuzzyComparisonSettings.objects.first()
            if settings and settings.criteria_weights:
                return json.loads(settings.criteria_weights)
        except:
            pass
        
        # Значения по умолчанию (равновесные критерии)
        return {
            'price': 0.2,
            'distance': 0.2,
            'experience': 0.2,
            'rating': 0.2,
            'education': 0.1,
            'reviews_count': 0.1
        }
    
    def get_expert_comparisons(self) -> Dict[str, Any]:
        """
        Получение экспертных парных сравнений из настроек администратора.
        Эти сравнения используются для построения нечетких множеств.
        """
        from .models import FuzzyComparisonSettings
        
        try:
            settings = FuzzyComparisonSettings.objects.first()
            if settings:
                return {
                    'criteria_comparisons': json.loads(settings.criteria_comparisons) if settings.criteria_comparisons else [],
                    'alternative_comparisons': json.loads(settings.alternative_comparisons) if settings.alternative_comparisons else {},
                    'use_expert_comparisons': settings.use_expert_comparisons
                }
        except:
            pass
        
        return {
            'criteria_comparisons': [],
            'alternative_comparisons': {},
            'use_expert_comparisons': False
        }
    
    def build_fuzzy_model(self, alternatives_data: List[Dict], teacher_ids: List[int]) -> BellmanZadeMCDA:
        """
        Построение модели Беллмана-Заде.
        Веса критериев берутся из экспертных настроек (админка) или пользовательских.
        Сравнения альтернатив строятся автоматически на основе реальных данных.
        """
        import numpy as np
        model = BellmanZadeMCDA()
        
        # Устанавливаем альтернативы
        alternatives = [f"T_{tid}" for tid in teacher_ids]
        model.set_alternatives(alternatives)
        print(f"=== build_fuzzy_model ===")
        print(f"Alternatives set: {alternatives}")
        print(f"Number of alternatives: {len(alternatives)}")
        
        # Критерии
        criteria = ['price', 'distance', 'experience', 'rating', 'education']
        model.set_criteria(criteria)
        
        # ============================================================
        # 1. Определяем режим использования весов
        # ============================================================
        weight_mode = self.request.GET.get('weight_mode', 'expert')
        print(f"Weight mode from GET: {weight_mode}")
        
        # Флаг, использованы ли пользовательские веса
        user_weights_used = False
        user_weights_values = None
        
        if weight_mode == 'custom':
            # Используем пользовательские веса
            user_weights = self.get_user_weights()
            print(f"User weights from DB: {user_weights}")
            
            if user_weights:
                print("=" * 50)
                print("Используем ПОЛЬЗОВАТЕЛЬСКИЕ веса критериев")
                print("=" * 50)
                
                # Получаем веса для каждого критерия
                weight_values = []
                for c in criteria:
                    w = user_weights.get(c, 0.2)
                    weight_values.append(w)
                    print(f"  {c}: {w}")
                
                # Нормализуем веса (сумма = 1)
                total = sum(weight_values)
                if total > 0:
                    user_weights_values = np.array([w / total for w in weight_values])
                else:
                    user_weights_values = np.ones(len(criteria)) / len(criteria)
                
                print(f"Normalized user weights: {dict(zip(criteria, user_weights_values))}")
                user_weights_used = True
        
        # ============================================================
        # 2. АВТОМАТИЧЕСКОЕ построение матриц сравнения АЛЬТЕРНАТИВ
        # ============================================================
        print("\n" + "=" * 50)
        print("Строим матрицы сравнения АЛЬТЕРНАТИВ на основе реальных данных")
        print("=" * 50)
        self._build_auto_matrices(model, alternatives_data, teacher_ids)
        
        # ============================================================
        # 3. Строим нечеткие множества (без пересчета весов)
        # ============================================================
        print("\nCalling build_fuzzy_sets...")
        model.build_fuzzy_sets(skip_weights_calculation=True)  # <-- НЕ пересчитываем веса
        
        # ============================================================
        # 4. Устанавливаем веса (пользовательские или экспертные)
        # ============================================================
        if user_weights_used and user_weights_values is not None:
            # Используем пользовательские веса
            model.criteria_weights = user_weights_values
            print("\n" + "=" * 50)
            print("Установлены ПОЛЬЗОВАТЕЛЬСКИЕ веса критериев:")
            print("=" * 50)
            for i, criterion in enumerate(criteria):
                print(f"  {criterion.upper()}: {model.criteria_weights[i]:.4f} ({model.criteria_weights[i]*100:.1f}%)")
        else:
            # Используем экспертные веса из админки
            expert_data = self.get_expert_comparisons()
            print(f"Expert data: use_expert_comparisons={expert_data['use_expert_comparisons']}")
            
            if expert_data['use_expert_comparisons'] and expert_data['criteria_comparisons']:
                print("=" * 50)
                print("Загружаем ЭКСПЕРТНЫЕ ВЕСА КРИТЕРИЕВ из админки")
                print("=" * 50)
                
                # Создаем временную матрицу для расчета весов
                temp_matrix = ComparisonMatrix(criteria, "Критерии")
                for comp in expert_data['criteria_comparisons']:
                    if 'linguistic_value' in comp:
                        i = criteria.index(comp['criterion1'])
                        j = criteria.index(comp['criterion2'])
                        if '/' in comp['linguistic_value']:
                            num, den = comp['linguistic_value'].split('/')
                            value = float(num) / float(den)
                        else:
                            value = float(comp['linguistic_value'])
                        temp_matrix.set_comparison(i, j, value)
                    elif 'value' in comp:
                        i = criteria.index(comp['criterion1'])
                        j = criteria.index(comp['criterion2'])
                        temp_matrix.set_comparison(i, j, float(comp['value']))
                
                model.criteria_weights = temp_matrix.calculate_weights()
                print(f"Expert weights calculated: {model.criteria_weights}")
            else:
                print("=" * 50)
                print("Экспертные веса критериев не найдены, используем равные веса")
                print("=" * 50)
                model.criteria_weights = np.ones(len(criteria)) / len(criteria)
        
        # Выводим итоговые веса
        if model.criteria_weights is not None:
            print("\n" + "=" * 50)
            print("ИТОГОВЫЕ ВЕСА КРИТЕРИЕВ:")
            print("=" * 50)
            for i, criterion in enumerate(criteria):
                print(f"  {criterion.upper()}: {model.criteria_weights[i]:.4f} ({model.criteria_weights[i]*100:.1f}%)")
        
        print("Calling calculate_solution...")
        model.calculate_solution(use_weights=True)
        
        self.bz_model = model  # Сохраняем модель для экспорта
        return model
    
    def get_context_data(self, **kwargs):
        self.bz_model = None  # Инициализация

        context = super().get_context_data(**kwargs)
        
        print("=" * 60)
        print("=== PublicResumeListView.get_context_data START ===")
        print(f"GET params: {dict(self.request.GET)}")
        
        # Получаем параметры фильтрации из GET-запроса
        price_min = self.safe_float('price_min', 0)
        price_max = self.safe_float('price_max', 10000)
        min_experience = self.safe_float('min_experience', 0)
        min_rating = self.safe_float('min_rating', 0)
        selected_child_id = self.request.GET.get('child')
        selected_violations = self.request.GET.getlist('violation_types')
        ordering = self.request.GET.get('ordering', 'rank')
        weight_mode = self.request.GET.get('weight_mode', 'expert')

        default_max_distance = 20
        if hasattr(self.request.user, 'profile') and self.request.user.profile.max_search_distance:
            default_max_distance = self.request.user.profile.max_search_distance

        max_distance = self.safe_float('max_distance', default_max_distance)
        print(f"max_distance from GET or profile: {max_distance}")
        
        print(f"Filters: price_min={price_min}, price_max={price_max}, max_distance={max_distance}")
        print(f"selected_child_id={selected_child_id}, selected_violations={selected_violations}")
        
        # Получаем цели пользователя (для лингвистических переменных)
        price_goal = self.request.GET.get('price_goal', 'low')
        distance_goal = self.request.GET.get('distance_goal', 'close')
        experience_goal = self.request.GET.get('experience_goal', 'expert')
        rating_goal = self.request.GET.get('rating_goal', 'high')
        
        # Базовый queryset с фильтрацией
        resumes = self.get_queryset()
        print(f"Initial resumes count: {resumes.count()}")
        
        # Фильтрация по видам нарушений (если выбраны)
        if selected_violations:
            resumes = resumes.filter(violation_types__id__in=selected_violations).distinct()
            print(f"After violation filter: {resumes.count()}")
        
        # Фильтрация по цене
        resumes = resumes.filter(
            Q(price_min__lte=price_max) | Q(price_min__isnull=True),
            Q(price_max__gte=price_min) | Q(price_max__isnull=True)
        )
        print(f"After price filter: {resumes.count()}")
        
        # Фильтрация по опыту
        if min_experience > 0:
            resumes = resumes.filter(experience_years__gte=min_experience)
            print(f"After experience filter: {resumes.count()}")
        
        # Фильтрация по рейтингу
        if min_rating > 0:
            resumes = resumes.filter(rating__gte=min_rating)
            print(f"After rating filter: {resumes.count()}")
        
        # Получаем координаты пользователя
        child_id_int = None
        if selected_child_id and selected_child_id.isdigit():
            child_id_int = int(selected_child_id)
        
        user_lat, user_lon = self.get_user_location(child_id_int)
        print(f"User location: lat={user_lat}, lon={user_lon}")
        
        # Подготовка данных для метода Беллмана-Заде
        alternatives_data = []
        teacher_ids = []
        
        for resume in resumes:
            # Рассчитываем расстояние
            distance = max_distance
            if resume.location_lat and resume.location_lon:
                try:
                    distance = calculate_distance(
                        user_lat, user_lon,
                        float(resume.location_lat), float(resume.location_lon)
                    )
                except Exception as e:
                    print(f"Error calculating distance for resume {resume.id}: {e}")
            
            # Пропускаем, если расстояние превышает лимит
            if distance > max_distance:
                continue
            
            avg_price = resume.get_average_price()
            
            alternatives_data.append({
                'price': avg_price,
                'distance': distance,
                'experience': float(resume.experience_years),
                'rating': resume.get_rating(),
                'education': float(resume.education_level),
                'reviews_count': TeacherReview.objects.filter(teacher=resume.user).count()
            })
            teacher_ids.append(resume.id)
        
        print(f"Alternatives prepared: {len(alternatives_data)}")
        
        # Применяем метод Беллмана-Заде
        results = []
        consistency_report = None
        criteria_weights = {}
        
        if alternatives_data:
            try:
                # Строим модель
                model = self.build_fuzzy_model(alternatives_data, teacher_ids)
                
                # Получаем отчет о согласованности
                consistency_report = model.get_consistency_report()
                
                # Получаем веса критериев
                if model.criteria_weights is not None:
                    for i, criterion in enumerate(model.criteria):
                        criteria_weights[criterion] = float(model.criteria_weights[i])
                
                # Рассчитываем оценки
                scored_results = self.calculate_alternative_scores(model, alternatives_data, teacher_ids)
                
                # Собираем полные данные для отображения
                for sr in scored_results:
                    resume = next((r for r in resumes if r.id == sr['teacher_id']), None)
                    if resume:
                        results.append({
                            'resume': resume,
                            'mu': sr['mu'] * 100,
                            'rank': sr['rank'],
                            'is_best': sr['is_best'],
                            'memberships': {k: v * 100 for k, v in sr['memberships'].items()},
                            'criteria_weights': criteria_weights,
                            'distance': sr['raw_data']['distance'],
                            'price': sr['raw_data']['price'],
                            'experience': sr['raw_data']['experience'],
                            'rating': sr['raw_data']['rating']
                        })
                
                print(f"Results after fuzzy model: {len(results)}")
                
                # Сохраняем модель в сессию для What-If анализа
                self.request.session['bz_model_json'] = json.dumps(model.to_dict(), default=str)
            except Exception as e:
                print(f"Error in fuzzy model: {e}")
                import traceback
                traceback.print_exc()
                messages.error(self.request, f"Ошибка при анализе: {str(e)}")
        else:
            print("No alternatives data available")
        
        # Сортируем результаты по рангу
        if results:
            if ordering == 'price':
                results.sort(key=lambda x: x['price'])
            elif ordering == '-price':
                results.sort(key=lambda x: x['price'], reverse=True)
            elif ordering == '-rating':
                results.sort(key=lambda x: x['rating'], reverse=True)
            elif ordering == '-experience':
                results.sort(key=lambda x: x['experience'], reverse=True)
            else:  # rank
                results.sort(key=lambda x: x['rank'])
        
        print(f"Final results count: {len(results)}")
        print("=== PublicResumeListView.get_context_data END ===")
        print("=" * 60)
        
        context['weight_mode'] = weight_mode
        context['ordering'] = ordering
        
        # Добавляем в контекст
        context['results'] = results
        context['user_children'] = Child.objects.filter(user=self.request.user)
        context['all_violations'] = ViolationType.objects.all()
        context['selected_violations'] = [int(v) for v in selected_violations if v.isdigit()]
        context['selected_child_id'] = int(selected_child_id) if selected_child_id and selected_child_id.isdigit() else None
        context['price_min'] = int(price_min)
        context['price_max'] = int(price_max)
        context['max_distance'] = int(max_distance)
        context['min_experience'] = int(min_experience)
        context['min_rating'] = min_rating
        
        # Цели пользователя
        context['price_goal'] = price_goal
        context['distance_goal'] = distance_goal
        context['experience_goal'] = experience_goal
        context['rating_goal'] = rating_goal
        
        # Дополнительная информация
        context['criteria_list'] = ['price', 'distance', 'experience', 'rating', 'education']
        context['criteria_names'] = {
            'price': '💰 Цена',
            'distance': '📍 Расстояние',
            'experience': '⏳ Опыт',
            'rating': '⭐ Рейтинг',
            'education': '🎓 Образование'
        }
        context['consistency_report'] = consistency_report
        context['criteria_weights'] = criteria_weights
        
        return context
        
    def get_user_weights(self):
        """Получение пользовательских весов из БД (приоритет - сессия)"""
        from .models import UserCriteriaWeights
        
        # Сначала проверяем сессию (если пользователь выбрал "Использовать мои веса")
        if self.request.session.get('use_custom_weights'):
            weights = self.request.session.get('user_criteria_weights')
            if weights:
                print(f"User weights from session: {weights}")
                return weights
        
        # Затем проверяем БД
        try:
            user_weights_obj = UserCriteriaWeights.objects.filter(user=self.request.user).first()
            if user_weights_obj and user_weights_obj.weights:
                print(f"User weights from DB: {user_weights_obj.weights}")
                # Сохраняем в сессию для быстрого доступа
                self.request.session['user_criteria_weights'] = user_weights_obj.weights
                return user_weights_obj.weights
        except Exception as e:
            print(f"Error getting user weights: {e}")
        
        return None

    def _build_auto_matrices(self, model: BellmanZadeMCDA, alternatives_data: List[Dict], teacher_ids: List[int]):
        """
        Автоматическое построение матриц парных сравнений на основе данных.
        """
        n = len(teacher_ids)
        print(f"Building auto matrices for {n} teachers")
        
        for criterion in model.criteria:
            print(f"Processing criterion: {criterion}")
            
            # Собираем значения по критерию
            values = []
            for data in alternatives_data:
                if criterion == 'price':
                    val = data.get('price', 5000)
                    # Инвертируем: чем меньше цена, тем лучше
                    # Нормализуем от 1 до 10
                    normalized = max(1, min(10, 10 - (val / 10000) * 9))
                    values.append(normalized)
                    print(f"  Price: {val} -> {normalized}")
                elif criterion == 'distance':
                    val = data.get('distance', 50)
                    normalized = max(1, min(10, 10 - (val / 50) * 9))
                    values.append(normalized)
                    print(f"  Distance: {val} km -> {normalized}")
                elif criterion == 'experience':
                    val = data.get('experience', 0)
                    normalized = max(1, min(10, 1 + (val / 30) * 9))
                    values.append(normalized)
                    print(f"  Experience: {val} years -> {normalized}")
                elif criterion == 'rating':
                    val = data.get('rating', 0)
                    normalized = max(0.1, min(10.0, 1.0 + (val / 5.0) * 9.0))
                    values.append(normalized)
                    print(f"  Rating: {val} -> {normalized}")
                elif criterion == 'education':
                    val = data.get('education', 0)
                    normalized = max(1, min(10, 1 + (val / 10) * 9))
                    values.append(normalized)
                    print(f"  Education: {val} -> {normalized}")
                else:
                    values.append(5)
            
            # Строим матрицу парных сравнений
            for i in range(n):
                for j in range(i + 1, n):
                    if values[i] > 0 and values[j] > 0:
                        ratio = values[i] / values[j]
                    else:
                        ratio = 1.0
                    
                    # Преобразуем в шкалу Саати
                    if ratio > 1:
                        saaty_value = min(ratio, 9)
                    else:
                        saaty_value = max(1/ratio, 1/9)
                    
                    alt1 = f"T_{teacher_ids[i]}"
                    alt2 = f"T_{teacher_ids[j]}"
                    
                    print(f"  Adding comparison: {alt1} vs {alt2} = {saaty_value:.3f} (ratio={ratio:.3f})")
                    model.add_alternative_comparison(criterion, alt1, alt2, saaty_value)


    def calculate_alternative_scores(self, model: BellmanZadeMCDA, 
                                    alternatives_data: List[Dict],
                                    teacher_ids: List[int]) -> List[Dict]:
        """
        Расчет итоговых оценок для каждой альтернативы
        """
        results = []
        ranking = model.get_ranking()
        
        # Получаем веса критериев
        criteria_weights = {}
        if model.criteria_weights is not None:
            for i, criterion in enumerate(model.criteria):
                criteria_weights[criterion] = model.criteria_weights[i]
        
        for rank, (alt, mu) in enumerate(ranking, 1):
            teacher_id = int(alt.split('_')[1])
            
            # Находим соответствующие данные
            alt_data = None
            for i, tid in enumerate(teacher_ids):
                if tid == teacher_id:
                    alt_data = alternatives_data[i]
                    break
            
            if alt_data:
                # Получаем степени принадлежности по каждому критерию
                memberships = {}
                for criterion in model.criteria:
                    fuzzy_set = model.criterion_fuzzy_sets.get(criterion)
                    if fuzzy_set:
                        membership = fuzzy_set.get_membership(alt)
                        if membership is None:
                            membership = 0.0
                        memberships[criterion] = membership
                    else:
                        memberships[criterion] = 0.0
                
                print(f"=== Teacher {teacher_id} ===")
                print(f"Memberships: {memberships}")
                print(f"mu: {mu}")
                
                results.append({
                    'teacher_id': teacher_id,
                    'mu': mu,
                    'rank': rank,
                    'is_best': rank == 1,
                    'memberships': memberships,
                    'criteria_weights': criteria_weights,
                    'raw_data': alt_data
                })
        
        return results

    def export_current_results_to_excel(self, results, alternatives_data, teacher_ids,
                                         user_lat, user_lon, criteria_weights,
                                         consistency_report, user_filters):
        """
        Экспорт текущих результатов поиска в Excel с полными вычислениями
        
        Возвращает tuple: (excel_data_bytes, filename)
        """
        from .excel_export import TeacherSearchExcelExporter
        from .models import FuzzyComparisonSettings
        
        # Определяем, использовались ли экспертные веса
        weight_mode = self.request.GET.get('weight_mode', 'expert')
        use_expert = weight_mode == 'expert'
        
        # Получаем экспертные сравнения (для отчета)
        criteria_comparisons = []
        alternative_comparisons = {}
        
        if use_expert:
            try:
                settings = FuzzyComparisonSettings.objects.first()
                if settings:
                    if settings.criteria_comparisons:
                        criteria_comparisons = json.loads(settings.criteria_comparisons)
                    if settings.alternative_comparisons:
                        alternative_comparisons = json.loads(settings.alternative_comparisons)
            except Exception as e:
                print(f"Error loading expert comparisons: {e}")
        
        # Создаем экспортер
        exporter = TeacherSearchExcelExporter(
            model=self.bz_model,
            results=results,
            alternatives_data=alternatives_data,
            teacher_ids=teacher_ids,
            user_location=(user_lat, user_lon),
            criteria_weights=criteria_weights,
            consistency_report=consistency_report,
            user_filters=user_filters,
            use_expert_weights=use_expert,
            criteria_comparisons=criteria_comparisons,
            alternative_comparisons=alternative_comparisons
        )
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        mode_str = "expert" if use_expert else "user"
        filename = f"teacher_search_{mode_str}_{timestamp}.xlsx"
        
        # Экспортируем в BytesIO
        excel_data = exporter.export_to_bytesio()
        
        return excel_data, filename

# Для родителя: подробная страничка резюме
class ResumeDetailView(DetailView):
    model = Resume
    template_name = "resume/public_resume_detail.html"
    context_object_name = "resume"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        resume = self.get_object()
        
        # Получаем отзывы
        from .models import TeacherReview
        context['reviews'] = TeacherReview.objects.filter(teacher=resume.user).order_by('-created_at')
        
        return context

@login_required
@require_POST
def ajax_create_document(request):
    form = DocumentForm(request.POST, request.FILES)
    if form.is_valid():
        document = form.save(commit=False)
        document.user = request.user
        document.save()
        return JsonResponse({
            'status': 'success',
            'document': {
                'id': document.id,
                'name': document.name,
                'info': document.info
            }
        })
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors}, status=400)


def get_child_violations(request):
    child_id = request.GET.get('child_id')
    if not child_id:
        return HttpResponseBadRequest("child_id is required")
    child = get_object_or_404(Child, pk=child_id, user=request.user)
    violations = list(child.violation_types.values('id', 'name'))
    return JsonResponse({'violations': violations})

def is_parent(user):
    if not user.is_authenticated:
        return False
    if not hasattr(user, 'profile') or user.profile is None:
        return False
    if not user.profile.role:
        return False
    return user.profile.role.name == 'Родитель'


def is_teacher(user):
    if not user.is_authenticated:
        return False
    if not hasattr(user, 'profile') or user.profile is None:
        return False
    if not user.profile.role:
        return False
    return user.profile.role.name == 'Преподаватель'

@login_required
@user_passes_test(is_parent, login_url='account:home')
def create_review(request, teacher_id):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    teacher = get_object_or_404(User, unique_id=teacher_id)
    
    if not is_teacher(teacher):
        messages.error(request, "Можно оставить отзыв только преподавателю")
        return redirect('account:view_other_user', user_id=teacher_id)
    
    existing_review = TeacherReview.objects.filter(
        teacher=teacher, parent=request.user
    ).first()
    
    if request.method == 'POST':
        form = TeacherReviewForm(request.POST, instance=existing_review)
        if form.is_valid():
            review = form.save(commit=False)
            review.teacher = teacher
            review.parent = request.user
            review.save()
            messages.success(request, "Отзыв успешно добавлен!")
            return redirect('account:view_other_user', user_id=teacher_id)
    else:
        form = TeacherReviewForm(instance=existing_review)
    
    # Получаем все отзывы
    reviews = TeacherReview.objects.filter(teacher=teacher)
    
    return render(request, 'resume/create_review.html', {
        'form': form,
        'teacher': teacher,
        'reviews': reviews,
        'existing_review': existing_review
    })

from .bellman_zade import BellmanZadeMCDA, WhatIfAnalyzer, create_brand_project_example
import json


@login_required
@user_passes_test(is_parent, login_url='account:home')
def fuzzy_teacher_search(request):
    """
    Расширенный поиск преподавателей с использованием метода Беллмана-Заде
    с полной поддержкой парных сравнений (как администратор/эксперт)
    """
    bz_model = BellmanZadeMCDA()
    
    # Получаем активных преподавателей
    teachers = Resume.objects.filter(status=Resume.ACTIVE).select_related('user__profile')
    
    # Список альтернатив (ID преподавателей)
    alternatives = [f"T_{t.id}" for t in teachers]
    bz_model.set_alternatives(alternatives)
    
    # Критерии оценки
    criteria = ['price', 'distance', 'experience', 'rating', 'education', 'reviews']
    bz_model.set_criteria(criteria)
    
    # --- Загрузка парных сравнений из БД или создание по умолчанию ---
    
    # Вариант 1: Загружаем сохраненные сравнения из модели SiteSettings
    # (нужно создать модель SiteSettings или использовать существующую)
    saved_comparisons = get_saved_comparisons()  # Функция для загрузки из БД
    
    if saved_comparisons:
        # Загружаем сравнения критериев
        if 'criteria_comparisons' in saved_comparisons:
            for comp in saved_comparisons['criteria_comparisons']:
                bz_model.add_criterion_comparison_linguistic(
                    comp['criterion1'], comp['criterion2'], comp['linguistic_value']
                )
        
        # Загружаем сравнения альтернатив по критериям
        for criterion in criteria:
            if criterion in saved_comparisons.get('alternative_comparisons', {}):
                for comp in saved_comparisons['alternative_comparisons'][criterion]:
                    bz_model.add_alternative_comparison_linguistic(
                        criterion, comp['alt1'], comp['alt2'], comp['linguistic_value']
                    )
    else:
        # Вариант 2: Создаем начальные сравнения на основе реальных данных
        initialize_comparisons_from_data(bz_model, teachers, request.user)
    
    # Построение нечетких множеств и расчет решения
    bz_model.build_fuzzy_sets()
    solution = bz_model.calculate_solution(use_weights=True)
    best_alternative = bz_model.get_best_alternative()
    ranking = bz_model.get_ranking()
    consistency_report = bz_model.get_consistency_report()
    
    # Подготовка результатов для отображения
    results = []
    for alt, mu in ranking:
        teacher_id = int(alt.split('_')[1])
        teacher = next((t for t in teachers if t.id == teacher_id), None)
        if teacher:
            results.append({
                'teacher': teacher,
                'mu': mu,
                'is_best': alt == best_alternative[0],
                'scores': bz_model.alternative_scores.get(alt, {}),
                'rank': len(results) + 1
            })
    
    # Сохраняем модель в сессии для What-If анализа
    request.session['bz_model_json'] = json.dumps(bz_model.to_dict(), default=str)
    
    context = {
        'results': results,
        'criteria': criteria,
        'criteria_weights': {c: w for c, w in zip(criteria, bz_model.criteria_weights)} if bz_model.criteria_weights is not None else {},
        'consistency_report': consistency_report,
        'best_alternative': best_alternative,
    }
    
    return render(request, 'resume/fuzzy_search_results.html', context)



def get_saved_comparisons():
    """
    Загрузка сохраненных парных сравнений из БД
    (нужно создать модель FuzzyComparisonSettings)
    """
    from .models import FuzzyComparisonSettings
    
    try:
        settings = FuzzyComparisonSettings.objects.first()
        if settings:
            return {
                'criteria_comparisons': json.loads(settings.criteria_comparisons) if settings.criteria_comparisons else [],
                'alternative_comparisons': json.loads(settings.alternative_comparisons) if settings.alternative_comparisons else {},
                'last_updated': settings.updated_at
            }
    except:
        pass
    
    return None


def save_comparisons_from_request(post_data):
    """Сохранение парных сравнений из POST-запроса"""
    from .models import FuzzyComparisonSettings
    
    # Сбор сравнений критериев
    criteria_comparisons = []
    for key, value in post_data.items():
        if key.startswith('criteria_comp_'):
            parts = key.split('_')
            if len(parts) >= 4:
                criteria_comparisons.append({
                    'criterion1': parts[2],
                    'criterion2': parts[3],
                    'linguistic_value': value
                })
    
    # Сбор сравнений альтернатив
    alternative_comparisons = {}
    for key, value in post_data.items():
        if key.startswith('alt_comp_'):
            parts = key.split('_')
            if len(parts) >= 5:
                criterion = parts[2]
                if criterion not in alternative_comparisons:
                    alternative_comparisons[criterion] = []
                alternative_comparisons[criterion].append({
                    'alt1': parts[3],
                    'alt2': parts[4],
                    'linguistic_value': value
                })
    
    settings, created = FuzzyComparisonSettings.objects.get_or_create(id=1)
    settings.criteria_comparisons = json.dumps(criteria_comparisons, ensure_ascii=False)
    settings.alternative_comparisons = json.dumps(alternative_comparisons, ensure_ascii=False)
    settings.save()


def initialize_comparisons_from_data(model: BellmanZadeMCDA, teachers, user):
    """
    Инициализация парных сравнений на основе реальных данных
    (как альтернатива экспертным оценкам)
    """
    # Нормализация данных для получения значений шкалы Саати
    # Пример: для цены - чем меньше цена, тем лучше (обратная зависимость)
    
    teacher_data = []
    for teacher in teachers:
        avg_price = teacher.get_average_price()
        teacher_data.append({
            'id': f"T_{teacher.id}",
            'price': avg_price,
            'experience': teacher.experience_years,
            'rating': teacher.rating,
            'education': teacher.education_level
        })
    
    # Нормализация и создание сравнений
    for criterion in model.criteria:
        if criterion == 'price':
            # Цена: чем меньше, тем лучше
            prices = [d['price'] for d in teacher_data if d['price'] > 0]
            if prices:
                min_price = min(prices)
                max_price = max(prices)
                for i, t1 in enumerate(teacher_data):
                    for j, t2 in enumerate(teacher_data):
                        if i < j:
                            # Сравнение по цене
                            ratio = (t2['price'] / t1['price']) if t1['price'] > 0 else 1
                            # Преобразуем в шкалу 1/9 - 9
                            if ratio > 1:
                                value = min(ratio, 9)
                            else:
                                value = max(1/ratio, 1/9)
                            model.add_alternative_comparison(criterion, t1['id'], t2['id'], value)
        
        elif criterion == 'experience':
            # Опыт: чем больше, тем лучше
            experiences = [d['experience'] for d in teacher_data]
            if experiences:
                max_exp = max(experiences)
                for i, t1 in enumerate(teacher_data):
                    for j, t2 in enumerate(teacher_data):
                        if i < j:
                            ratio = (t1['experience'] / t2['experience']) if t2['experience'] > 0 else 1
                            if ratio > 1:
                                value = min(ratio, 9)
                            else:
                                value = max(1/ratio, 1/9)
                            model.add_alternative_comparison(criterion, t1['id'], t2['id'], value)
        
        elif criterion == 'rating':
            # Рейтинг: чем выше, тем лучше
            ratings = [d['rating'] for d in teacher_data]
            if ratings:
                for i, t1 in enumerate(teacher_data):
                    for j, t2 in enumerate(teacher_data):
                        if i < j:
                            ratio = (t1['rating'] / t2['rating']) if t2['rating'] > 0 else 1
                            if ratio > 1:
                                value = min(ratio, 9)
                            else:
                                value = max(1/ratio, 1/9)
                            model.add_alternative_comparison(criterion, t1['id'], t2['id'], value)

# Добавьте эти функции в конец файла resume/views.py

from django.contrib.admin.views.decorators import staff_member_required
from .bellman_zade import BellmanZadeMCDA, WhatIfAnalyzer, create_brand_project_example
import json


@staff_member_required
def admin_fuzzy_settings(request):
    """
    Административная панель для настройки парных сравнений.
    Только для администратора/эксперта.
    """
    from .models import FuzzyComparisonSettings
    from .bellman_zade import SaatyScale
    
    if request.method == 'POST':
        # Сохраняем настройки
        criteria_comparisons = []
        alternative_comparisons = {}
        
        # Собираем сравнения критериев
        for key, value in request.POST.items():
            if key.startswith('criteria_comp_'):
                parts = key.split('_')
                if len(parts) >= 4:
                    criteria_comparisons.append({
                        'criterion1': parts[2],
                        'criterion2': parts[3],
                        'linguistic_value': value,
                        'value': SaatyScale.from_linguistic(value)
                    })
            
            elif key.startswith('alt_comp_'):
                parts = key.split('_')
                if len(parts) >= 5:
                    criterion = parts[2]
                    alt1 = parts[3]
                    alt2 = parts[4]
                    if criterion not in alternative_comparisons:
                        alternative_comparisons[criterion] = []
                    alternative_comparisons[criterion].append({
                        'alt1': alt1,
                        'alt2': alt2,
                        'linguistic_value': value,
                        'value': SaatyScale.from_linguistic(value)
                    })
        
        # Сохраняем веса критериев, если были рассчитаны
        criteria_weights = request.POST.get('criteria_weights', '{}')
        
        settings, created = FuzzyComparisonSettings.objects.get_or_create(id=1)
        settings.criteria_comparisons = json.dumps(criteria_comparisons, ensure_ascii=False)
        settings.alternative_comparisons = json.dumps(alternative_comparisons, ensure_ascii=False)
        settings.criteria_weights = criteria_weights
        settings.use_expert_comparisons = request.POST.get('use_expert_comparisons') == 'on'
        settings.updated_by = request.user
        settings.save()
        
        messages.success(request, 'Настройки метода Беллмана-Заде сохранены')
        return redirect('resume:admin_fuzzy_settings')
    
    # GET: показываем форму
    current_settings = None
    try:
        settings = FuzzyComparisonSettings.objects.first()
        if settings:
            current_settings = {
                'criteria_comparisons': json.loads(settings.criteria_comparisons) if settings.criteria_comparisons else [],
                'alternative_comparisons': json.loads(settings.alternative_comparisons) if settings.alternative_comparisons else {},
                'use_expert_comparisons': settings.use_expert_comparisons,
                'criteria_weights': json.loads(settings.criteria_weights) if settings.criteria_weights else {}
            }
    except:
        pass
    
    # Получаем список преподавателей для выбора
    teachers = Resume.objects.filter(status=Resume.ACTIVE).select_related('user__profile')
    teacher_choices = [(f"T_{t.id}", t.user.profile.get_full_name() or f"Преподаватель {t.id}") for t in teachers]
    
    context = {
        'criteria': ['price', 'distance', 'experience', 'rating', 'education'],
        'criteria_names': {
            'price': 'Цена занятия',
            'distance': 'Расстояние',
            'experience': 'Опыт работы',
            'rating': 'Рейтинг',
            'education': 'Уровень образования'
        },
        'teacher_choices': teacher_choices,
        'current_settings': current_settings,
        'saaty_scale': {
            '1': '1 - Одинаковая важность',
            '2': '2 - Почти слабое преимущество',
            '3': '3 - Слабое преимущество',
            '4': '4 - Почти существенное преимущество',
            '5': '5 - Существенное преимущество',
            '6': '6 - Почти сильное преимущество',
            '7': '7 - Явное преимущество',
            '8': '8 - Очень сильное преимущество',
            '9': '9 - Абсолютное преимущество'
        }
    }
    
    return render(request, 'resume/admin_fuzzy_settings.html', context)


@login_required
def what_if_analysis(request):
    """
    Анализ "Что-Если" - позволяет изменять парные сравнения
    и видеть, как изменится результат.
    """
    saved_model = request.session.get('bz_model_json')
    if not saved_model:
        messages.error(request, 'Сначала выполните поиск преподавателей')
        return redirect('resume:public_resume_list')
    
    model_data = json.loads(saved_model)
    bz_model = BellmanZadeMCDA.from_dict(model_data)
    analyzer = WhatIfAnalyzer(bz_model)
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX запрос для динамического анализа
        analysis_type = request.POST.get('analysis_type')
        
        if analysis_type == 'criterion':
            criterion1 = request.POST.get('criterion1')
            criterion2 = request.POST.get('criterion2')
            new_value = float(request.POST.get('new_value', 1))
            
            result = analyzer.analyze_criterion_comparison_change(
                criterion1, criterion2, new_value
            )
            
        elif analysis_type == 'alternative':
            criterion = request.POST.get('criterion')
            alt1 = request.POST.get('alt1')
            alt2 = request.POST.get('alt2')
            new_value = float(request.POST.get('new_value', 1))
            
            result = analyzer.analyze_alternative_comparison_change(
                criterion, alt1, alt2, new_value
            )
        else:
            return JsonResponse({'error': 'Unknown analysis type'}, status=400)
        
        return JsonResponse(result)
    
    # GET: показываем форму
    context = {
        'criteria': bz_model.criteria,
        'alternatives': bz_model.alternatives,
        'current_solution': {k: v * 100 for k, v in bz_model.solution_fuzzy_set.items()},
        'current_best': bz_model.get_best_alternative(),
        'current_weights': {c: w for c, w in zip(bz_model.criteria, bz_model.criteria_weights)} if bz_model.criteria_weights is not None else {},
        'consistency_report': bz_model.get_consistency_report(),
        'saaty_scale': {
            1: '1 - Одинаковая важность',
            2: '2 - Почти слабое преимущество',
            3: '3 - Слабое преимущество',
            4: '4 - Почти существенное преимущество',
            5: '5 - Существенное преимущество',
            6: '6 - Почти сильное преимущество',
            7: '7 - Явное преимущество',
            8: '8 - Очень сильное преимущество',
            9: '9 - Абсолютное преимущество'
        }
    }
    
    return render(request, 'resume/what_if_analysis.html', context)


def fuzzy_demo(request):
    """
    Демонстрация работы метода Беллмана-Заде с визуализацией
    (пример из методички)
    """
    from .bellman_zade import create_brand_project_example
    
    # Создаем демо-модель (пример из методички)
    model = create_brand_project_example()
    
    # Рассчитываем решение
    solution = model.calculate_solution(use_weights=True)
    best = model.get_best_alternative()
    ranking = model.get_ranking()
    consistency = model.get_consistency_report()
    
    # Получаем нечеткие множества для визуализации
    fuzzy_sets_data = {}
    for criterion, fuzzy_set in model.criterion_fuzzy_sets.items():
        fuzzy_sets_data[criterion] = {
            'memberships': fuzzy_set.memberships,
            'ranked': fuzzy_set.get_ranked_elements()
        }
    
    context = {
        'model': model,
        'solution': {k: v * 100 for k, v in solution.items()},
        'best': best,
        'ranking': [(alt, mu * 100) for alt, mu in ranking],
        'consistency': consistency,
        'fuzzy_sets': fuzzy_sets_data,
        'criteria_weights': {c: w for c, w in zip(model.criteria, model.criteria_weights)} if model.criteria_weights is not None else {},
        'alternatives': model.alternatives,
        'criteria': model.criteria
    }
    
    return render(request, 'resume/fuzzy_demo.html', context)


from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required
import json


@csrf_exempt
def api_calculate_criteria_weights(request):
    """API для расчета весов критериев (для админ-панели)"""
    from .bellman_zade import ComparisonMatrix
    
    print(f"=== API called ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"Is staff: {request.user.is_staff}")
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comparisons = data.get('comparisons', {})
            print(f"Comparisons received: {comparisons}")
            
            criteria = ['price', 'distance', 'experience', 'rating', 'education']
            matrix = ComparisonMatrix(criteria, "Критерии")
            
            for key, value in comparisons.items():
                parts = key.split('_')
                if len(parts) >= 4:
                    crit1 = parts[2]
                    crit2 = parts[3]
                    if crit1 in criteria and crit2 in criteria:
                        i = criteria.index(crit1)
                        j = criteria.index(crit2)
                        try:
                            val = float(value)
                        except:
                            if '/' in str(value):
                                num, den = str(value).split('/')
                                val = float(num) / float(den)
                            else:
                                val = 1.0
                        print(f"Setting matrix[{i}][{j}] = {val}")
                        matrix.set_comparison(i, j, val)
            
            weights = matrix.calculate_weights()
            consistency = matrix.calculate_consistency_ratio()
            
            result = {
                'weights': {c: float(weights[i]) for i, c in enumerate(criteria)},
                'lambda_max': float(consistency['lambda_max']),
                'ci': float(consistency['ci']),
                'cr': float(consistency['cr']),
                'is_consistent': bool(consistency['is_consistent'])
            }
            print(f"Result: {result}")
            return JsonResponse(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@staff_member_required
@csrf_exempt
def api_calculate_alternatives_weights(request):
    """API для расчета нечетких множеств по критерию"""
    from .bellman_zade import ComparisonMatrix
    from .models import Resume
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            criterion = data.get('criterion')
            comparisons = data.get('comparisons', {})
            
            # Получаем активных преподавателей
            teachers = Resume.objects.filter(status='active').order_by('id')
            alternatives = [f"T_{t.id}" for t in teachers]
            
            if not alternatives:
                return JsonResponse({'weights': {}, 'message': 'Нет активных преподавателей'})
            
            matrix = ComparisonMatrix(alternatives, criterion)
            
            for key, value in comparisons.items():
                parts = key.split('_')
                if len(parts) >= 5 and parts[0] == 'alt' and parts[1] == 'comp':
                    alt1 = parts[3]
                    alt2 = parts[4]
                    if alt1 in alternatives and alt2 in alternatives:
                        i = alternatives.index(alt1)
                        j = alternatives.index(alt2)
                        matrix.set_comparison(i, j, float(value))
            
            weights = matrix.calculate_weights()
            consistency = matrix.calculate_consistency_ratio()
            
            # Формируем результат с именами преподавателей
            result_weights = {}
            for i, alt in enumerate(alternatives):
                teacher_id = int(alt.split('_')[1])
                teacher = next((t for t in teachers if t.id == teacher_id), None)
                name = teacher.user.profile.get_full_name() if teacher and teacher.user.profile else alt
                result_weights[name] = float(weights[i])
            
            return JsonResponse({
                'weights': result_weights,
                'consistency': {
                    'lambda_max': float(consistency['lambda_max']),
                    'ci': float(consistency['ci']),
                    'cr': float(consistency['cr']),
                    'is_consistent': consistency['is_consistent']
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@staff_member_required
@csrf_exempt
def api_check_consistency(request):
    """API для проверки согласованности матрицы"""
    from .bellman_zade import ComparisonMatrix
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comparisons = data.get('comparisons', {})
            
            criteria = ['price', 'distance', 'experience', 'rating', 'education']
            matrix = ComparisonMatrix(criteria, "Критерии")
            
            for key, value in comparisons.items():
                parts = key.split('_')
                if len(parts) >= 4 and parts[0] == 'criteria' and parts[1] == 'comp':
                    crit1 = parts[2]
                    crit2 = parts[3]
                    if crit1 in criteria and crit2 in criteria:
                        i = criteria.index(crit1)
                        j = criteria.index(crit2)
                        matrix.set_comparison(i, j, float(value))
            
            consistency = matrix.calculate_consistency_ratio()
            
            return JsonResponse({
                'lambda_max': float(consistency['lambda_max']),
                'ci': float(consistency['ci']),
                'cr': float(consistency['cr']),
                'is_consistent': consistency['is_consistent']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
@user_passes_test(is_parent, login_url='account:home')
def user_weights_settings(request):
    """Страница настройки пользовательских весов критериев"""
    from .models import UserCriteriaWeights
    
    if request.method == 'POST':
        # Сохраняем пользовательские настройки
        use_custom = request.POST.get('use_custom') == 'on'
        
        # Сохраняем в сессию
        request.session['use_custom_weights'] = use_custom
        
        # Сохраняем парные сравнения и веса в БД
        pairwise_comparisons = request.POST.get('pairwise_comparisons')
        calculated_weights = request.POST.get('calculated_weights')
        
        obj, created = UserCriteriaWeights.objects.get_or_create(user=request.user)
        if pairwise_comparisons:
            obj.pairwise_comparisons = json.loads(pairwise_comparisons)
        if calculated_weights:
            obj.weights = json.loads(calculated_weights)
            # Обновляем сессию
            request.session['user_criteria_weights'] = obj.weights
        obj.save()
        
        messages.success(request, 'Настройки весов сохранены')
        return redirect('resume:user_weights_settings')
    
    # GET: загружаем текущие настройки
    user_weights_obj = UserCriteriaWeights.objects.filter(user=request.user).first()
    use_custom = request.session.get('use_custom_weights', False)
    
    # Если есть сохраненные веса в БД, но нет в сессии - загружаем
    if user_weights_obj and user_weights_obj.weights and not request.session.get('user_criteria_weights'):
        request.session['user_criteria_weights'] = user_weights_obj.weights
    
    context = {
        'use_custom': use_custom
    }
    
    return render(request, 'resume/user_weights_settings.html', context)


def verification_report(request):
    """Страница с отчетом верификации"""
    from .tests.test_verification import VerifyAgainstTextbook
    import matplotlib.pyplot as plt
    import io
    import base64
    import numpy as np
    
    test = VerifyAgainstTextbook()
    test.setUp()
    
    # Рассчитываем данные
    calculated_weights = test.model.calculate_criteria_weights()
    solution = test.solution
    
    # Получаем эталонные данные
    expected_memberships = getattr(test, 'expected_memberships', {})
    expected_weights = getattr(test, 'expected_weights', {})
    expected_mu = getattr(test, 'expected_mu', {})
    
    # Генерируем графики
    plots = {}
    
    # График 1: Веса критериев
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Подготавливаем данные для весов критериев
    criteria = list(calculated_weights.keys())
    weights_values = list(calculated_weights.values())
    
    # Если есть эталонные веса, показываем сравнение
    if expected_weights:
        expected_values = [expected_weights.get(c, 0) for c in criteria]
        x = np.arange(len(criteria))
        width = 0.35
        
        ax.bar(x - width/2, expected_values, width, label='Эталонные', alpha=0.7, color='blue')
        ax.bar(x + width/2, weights_values, width, label='Расчетные', alpha=0.7, color='green')
        ax.set_title('Сравнение весов критериев (α-коэффициенты)')
    else:
        ax.bar(criteria, weights_values, color='steelblue', alpha=0.7)
        ax.set_title('Веса критериев (α-коэффициенты)')
    
    ax.set_xlabel('Критерии')
    ax.set_ylabel('Вес')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Добавляем значения на столбцы
    for i, v in enumerate(weights_values):
        ax.text(i, v + 0.01, f'{v:.3f}', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    plots['weights_chart'] = _fig_to_base64(fig)
    plt.close(fig)
    
    # График 2: Финальное решение μD
    fig, ax = plt.subplots(figsize=(10, 6))
    
    alternatives = list(solution.keys())
    mu_values = list(solution.values())
    
    # Сортируем по убыванию (меньшее значение = лучшая альтернатива)
    sorted_pairs = sorted(zip(alternatives, mu_values), key=lambda x: x[1])
    sorted_alts = [p[0] for p in sorted_pairs]
    sorted_mus = [p[1] for p in sorted_pairs]
    
    colors = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1'][:len(sorted_alts)]
    
    bars = ax.bar(sorted_alts, sorted_mus, color=colors, alpha=0.7)
    ax.set_xlabel('Альтернативы')
    ax.set_ylabel('Степень принадлежности (μD)')
    ax.set_title('Финальное решение - μD (меньше = лучше)')
    ax.grid(True, alpha=0.3)
    
    # Добавляем значения на столбцы
    for bar, mu in zip(bars, sorted_mus):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height + 0.01, 
                f'{mu:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plots['solution_chart'] = _fig_to_base64(fig)
    plt.close(fig)
    
    # График 3: Сравнение расчетных и эталонных значений μD
    if expected_mu:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        alt_names = list(expected_mu.keys())
        expected_values = [expected_mu.get(alt, 0) for alt in alt_names]
        actual_values = [solution.get(alt, 0) for alt in alt_names]
        
        x = np.arange(len(alt_names))
        width = 0.35
        
        bars1 = ax.bar(x - width/2, expected_values, width, label='Эталонные', alpha=0.7, color='blue')
        bars2 = ax.bar(x + width/2, actual_values, width, label='Расчетные', alpha=0.7, color='green')
        
        ax.set_xlabel('Альтернативы')
        ax.set_ylabel('Степень принадлежности (μD)')
        ax.set_title('Сравнение эталонных и расчетных значений μD')
        ax.set_xticks(x)
        ax.set_xticklabels(alt_names)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Добавляем значения
        for bar in bars1:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.01, 
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        for bar in bars2:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.01, 
                   f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plots['comparison_chart'] = _fig_to_base64(fig)
        plt.close(fig)
        
        # График 4: Погрешность
        fig, ax = plt.subplots(figsize=(10, 6))
        
        errors = []
        for alt in alt_names:
            expected = expected_mu.get(alt, 0)
            actual = solution.get(alt, 0)
            error = abs(actual - expected)
            relative_error = (error / expected * 100) if expected > 0 else 0
            errors.append(relative_error)
        
        colors = ['green' if e < 5 else 'orange' if e < 10 else 'red' for e in errors]
        bars = ax.bar(alt_names, errors, color=colors, alpha=0.7)
        
        ax.axhline(y=5, color='green', linestyle='--', label='Допустимая погрешность (5%)', linewidth=2)
        ax.axhline(y=10, color='orange', linestyle='--', label='Критическая погрешность (10%)', linewidth=2)
        
        ax.set_xlabel('Альтернативы')
        ax.set_ylabel('Относительная погрешность (%)')
        ax.set_title('Относительная погрешность вычислений')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Добавляем значения
        for bar, error in zip(bars, errors):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, height + 0.5, 
                   f'{error:.1f}%', ha='center', va='bottom', fontsize=10)
        
        plt.tight_layout()
        plots['errors_chart'] = _fig_to_base64(fig)
        plt.close(fig)
    
    # Рассчитываем погрешности
    errors = {}
    verification_passed = True
    
    if expected_mu and solution:
        for alt, actual in solution.items():
            expected = expected_mu.get(alt, 0)
            if expected > 0:
                error = abs(actual - expected)
                relative_error = error / expected * 100
                errors[alt] = {
                    'expected': expected,
                    'actual': actual,
                    'error': error,
                    'relative_error': relative_error
                }
                if relative_error > 5:
                    verification_passed = False
    
    # Определяем лучшее ранжирование
    sorted_solution = sorted(solution.items(), key=lambda x: x[1])
    ranking_text = " > ".join([f"{alt} ({mu:.3f})" for alt, mu in sorted_solution])
    best_alternative = sorted_solution[0][0] if sorted_solution else "N/A"
    
    # Проверяем, что лучшая альтернатива - P4 (как в эталоне)
    best_correct = best_alternative == 'P4'
    
    context = {
        'plots': plots,
        'weights': calculated_weights,
        'solution': solution,
        'expected_mu': expected_mu,
        'expected_memberships': expected_memberships,
        'expected_weights': expected_weights,
        'errors': errors,
        'verification_passed': verification_passed and best_correct,
        'best_correct': best_correct,
        'ranking_text': ranking_text,
        'best_alternative': best_alternative,
    }
    
    return render(request, 'resume/verification_report.html', context)


def _fig_to_base64(fig):
    """Конвертирует matplotlib figure в base64 строку"""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return img_base64


@login_required
@user_passes_test(is_parent, login_url='account:home')
def export_search_results_excel(request):
    """
    Экспорт результатов поиска преподавателей в Excel
    Использует ТУ ЖЕ логику определения весов, что и PublicResumeListView.build_fuzzy_model
    """
    from .bellman_zade import BellmanZadeMCDA, calculate_distance, ComparisonMatrix
    from .models import FuzzyComparisonSettings, UserCriteriaWeights
    
    print("=" * 80)
    print("=== EXPORT_SEARCH_RESULTS_EXCEL START ===")
    print(f"GET params: {dict(request.GET)}")
    
    # ============================================================
    # 1. Получаем параметры фильтрации
    # ============================================================
    def safe_float(param, default):
        value = request.GET.get(param, str(default))
        if isinstance(value, str):
            value = value.replace(',', '.')
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    price_min = safe_float('price_min', 0)
    price_max = safe_float('price_max', 10000)
    min_experience = safe_float('min_experience', 0)
    min_rating = safe_float('min_rating', 0)
    selected_child_id = request.GET.get('child')
    selected_violations = request.GET.getlist('violation_types')
    weight_mode = request.GET.get('weight_mode', 'expert')
    
    default_max_distance = 20
    if hasattr(request.user, 'profile') and request.user.profile.max_search_distance:
        default_max_distance = request.user.profile.max_search_distance
    
    max_distance = safe_float('max_distance', default_max_distance)
    
    print(f"Weight mode: {weight_mode}")
    print(f"Filters: price_min={price_min}, price_max={price_max}, max_distance={max_distance}")
    
    # ============================================================
    # 2. Получаем активные резюме с фильтрацией
    # ============================================================
    resumes = Resume.objects.filter(status=Resume.ACTIVE).select_related(
        'user__profile'
    ).prefetch_related('violation_types')
    
    if selected_violations:
        resumes = resumes.filter(violation_types__id__in=selected_violations).distinct()
    
    resumes = resumes.filter(
        Q(price_min__lte=price_max) | Q(price_min__isnull=True),
        Q(price_max__gte=price_min) | Q(price_max__isnull=True)
    )
    
    if min_experience > 0:
        resumes = resumes.filter(experience_years__gte=min_experience)
    
    if min_rating > 0:
        resumes = resumes.filter(rating__gte=min_rating)
    
    # ============================================================
    # 3. Получаем координаты пользователя
    # ============================================================
    def get_user_location(child_id):
        if hasattr(request.user, 'profile') and request.user.profile.location_lat and request.user.profile.location_lon:
            try:
                return (float(request.user.profile.location_lat), float(request.user.profile.location_lon))
            except:
                pass
        
        if child_id:
            try:
                child = Child.objects.get(id=child_id, user=request.user)
                if hasattr(child, 'location_lat') and child.location_lat and child.location_lon:
                    return (float(child.location_lat), float(child.location_lon))
            except:
                pass
        
        return (55.751244, 37.618423)
    
    child_id_int = int(selected_child_id) if selected_child_id and selected_child_id.isdigit() else None
    user_lat, user_lon = get_user_location(child_id_int)
    print(f"User location: lat={user_lat}, lon={user_lon}")
    
    # ============================================================
    # 4. Подготовка данных альтернатив
    # ============================================================
    alternatives_data = []
    teacher_ids = []
    
    for resume in resumes:
        distance = max_distance
        if resume.location_lat and resume.location_lon:
            try:
                distance = calculate_distance(
                    user_lat, user_lon,
                    float(resume.location_lat), float(resume.location_lon)
                )
            except:
                pass
        
        if distance > max_distance:
            continue
        
        avg_price = resume.get_average_price()
        
        alternatives_data.append({
            'price': avg_price,
            'distance': distance,
            'experience': float(resume.experience_years),
            'rating': resume.get_rating(),
            'education': float(resume.education_level),
        })
        teacher_ids.append(resume.id)
    
    if not alternatives_data:
        messages.warning(request, "Нет преподавателей, соответствующих критериям поиска")
        return redirect('resume:public_resume_list')
    
    print(f"Alternatives prepared: {len(alternatives_data)}")
    
    # ============================================================
    # 5. Строим модель Беллмана-Заде (как в build_fuzzy_model)
    # ============================================================
    bz_model = BellmanZadeMCDA()
    criteria = ['price', 'distance', 'experience', 'rating', 'education']
    alternatives = [f"T_{tid}" for tid in teacher_ids]
    
    bz_model.set_alternatives(alternatives)
    bz_model.set_criteria(criteria)
    
    # Строим матрицы сравнений альтернатив (как в _build_auto_matrices)
    n = len(teacher_ids)
    for criterion in criteria:
        values = []
        for data in alternatives_data:
            if criterion == 'price':
                val = data.get('price', 5000)
                normalized = max(1, min(10, 10 - (val / 10000) * 9))
            elif criterion == 'distance':
                val = data.get('distance', 50)
                normalized = max(1, min(10, 10 - (val / 50) * 9))
            elif criterion == 'experience':
                val = data.get('experience', 0)
                normalized = max(1, min(10, 1 + (val / 30) * 9))
            elif criterion == 'rating':
                val = data.get('rating', 0)
                normalized = max(0.1, min(10.0, 1.0 + (val / 5.0) * 9.0))
            elif criterion == 'education':
                val = data.get('education', 0)
                normalized = max(1, min(10, 1 + (val / 10) * 9))
            else:
                normalized = 5
            values.append(normalized)
        
        for i in range(n):
            for j in range(i + 1, n):
                if values[i] > 0 and values[j] > 0:
                    ratio = values[i] / values[j]
                else:
                    ratio = 1.0
                
                if ratio > 1:
                    saaty_value = min(ratio, 9)
                else:
                    saaty_value = max(1/ratio, 1/9)
                
                alt1 = f"T_{teacher_ids[i]}"
                alt2 = f"T_{teacher_ids[j]}"
                bz_model.add_alternative_comparison(criterion, alt1, alt2, saaty_value)
    
    # Строим нечеткие множества без пересчета весов
    bz_model.build_fuzzy_sets(skip_weights_calculation=True)
    
    # ============================================================
    # 6. ОПРЕДЕЛЯЕМ ВЕСА КРИТЕРИЕВ (как в build_fuzzy_model)
    # ============================================================
    criteria_weights = {}
    user_weights_used = False
    use_expert = (weight_mode == 'expert')
    
    if weight_mode == 'custom':
        # Пользовательские веса
        print("=" * 50)
        print("Используем ПОЛЬЗОВАТЕЛЬСКИЕ веса критериев")
        print("=" * 50)
        
        user_weights = None
        # Сначала проверяем сессию
        if request.session.get('use_custom_weights'):
            user_weights = request.session.get('user_criteria_weights')
        
        # Затем проверяем БД
        if not user_weights:
            try:
                user_weights_obj = UserCriteriaWeights.objects.filter(user=request.user).first()
                if user_weights_obj and user_weights_obj.weights:
                    user_weights = user_weights_obj.weights
            except Exception as e:
                print(f"Error getting user weights: {e}")
        
        if user_weights:
            weight_values = []
            for c in criteria:
                w = user_weights.get(c, 0.2)
                weight_values.append(w)
                print(f"  {c}: {w}")
            
            total = sum(weight_values)
            if total > 0:
                user_weights_values = np.array([w / total for w in weight_values])
            else:
                user_weights_values = np.ones(len(criteria)) / len(criteria)
            
            bz_model.criteria_weights = user_weights_values
            user_weights_used = True
            
            for i, criterion in enumerate(criteria):
                criteria_weights[criterion] = float(user_weights_values[i])
    
    if not user_weights_used:
        # Экспертные веса из админки (как в build_fuzzy_model)
        print("=" * 50)
        print("Загружаем ЭКСПЕРТНЫЕ ВЕСА КРИТЕРИЕВ из админки")
        print("=" * 50)
        
        try:
            settings = FuzzyComparisonSettings.objects.first()
            if settings and settings.use_expert_comparisons and settings.criteria_comparisons:
                # Создаем матрицу парных сравнений критериев
                temp_matrix = ComparisonMatrix(criteria, "Критерии")
                for comp in json.loads(settings.criteria_comparisons):
                    criterion1 = comp.get('criterion1')
                    criterion2 = comp.get('criterion2')
                    if criterion1 in criteria and criterion2 in criteria:
                        i = criteria.index(criterion1)
                        j = criteria.index(criterion2)
                        
                        # Получаем значение сравнения
                        value = comp.get('value')
                        if value is None:
                            ling = comp.get('linguistic_value', '1')
                            if '/' in ling:
                                num, den = ling.split('/')
                                value = float(num) / float(den)
                            else:
                                try:
                                    value = float(ling)
                                except:
                                    value = 1
                        
                        temp_matrix.set_comparison(i, j, float(value))
                
                # Рассчитываем веса методом собственного вектора
                weights = temp_matrix.calculate_weights()
                bz_model.criteria_weights = weights
                
                for i, criterion in enumerate(criteria):
                    criteria_weights[criterion] = float(weights[i])
                    print(f"  {criterion}: {weights[i]:.4f} ({weights[i]*100:.1f}%)")
            else:
                print("Экспертные веса не найдены, используем равные")
                criteria_weights = {c: 0.2 for c in criteria}
                criteria_weights['education'] = 0.2
                bz_model.criteria_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        except Exception as e:
            print(f"Error loading expert weights: {e}")
            criteria_weights = {c: 0.2 for c in criteria}
            criteria_weights['education'] = 0.2
            bz_model.criteria_weights = np.array([0.2, 0.2, 0.2, 0.2, 0.2])
    
    # Выводим итоговые веса
    print("\n" + "=" * 50)
    print("ИТОГОВЫЕ ВЕСА КРИТЕРИЕВ:")
    print("=" * 50)
    for criterion, weight in criteria_weights.items():
        print(f"  {criterion.upper()}: {weight:.4f} ({weight*100:.1f}%)")
    
    # Рассчитываем решение с весами
    bz_model.calculate_solution(use_weights=True)
    
    # ============================================================
    # 7. Получаем результаты
    # ============================================================
    results = []
    ranking = bz_model.get_ranking()
    
    for rank, (alt, mu) in enumerate(ranking, 1):
        teacher_id = int(alt.split('_')[1])
        resume = next((r for r in resumes if r.id == teacher_id), None)
        if not resume:
            continue
        
        alt_data = None
        for i, tid in enumerate(teacher_ids):
            if tid == teacher_id:
                alt_data = alternatives_data[i]
                break
        
        memberships = {}
        for criterion in criteria:
            fuzzy_set = bz_model.criterion_fuzzy_sets.get(criterion)
            if fuzzy_set:
                membership = fuzzy_set.get_membership(alt)
                memberships[criterion] = membership * 100 if membership else 0
            else:
                memberships[criterion] = 0
        
        results.append({
            'resume': resume,
            'mu': mu * 100,
            'rank': rank,
            'is_best': rank == 1,
            'memberships': memberships,
            'price': alt_data.get('price', 0) if alt_data else 0,
            'distance': alt_data.get('distance', 0) if alt_data else 0,
            'experience': alt_data.get('experience', 0) if alt_data else 0,
            'rating': alt_data.get('rating', 0) if alt_data else 0,
            'raw_data': alt_data if alt_data else {}
        })
    
    print(f"Results count: {len(results)}")
    
    # Получаем отчет о согласованности
    consistency_report = bz_model.get_consistency_report()
    
    # Фильтры для отчета
    filters = {
        'price_min': price_min,
        'price_max': price_max,
        'max_distance': max_distance,
        'min_experience': min_experience,
        'min_rating': min_rating,
        'weight_mode': weight_mode
    }
    
    # ============================================================
    # 8. Экспорт в Excel
    # ============================================================
    from .excel_export import TeacherSearchExcelExporter
    
    # Получаем экспертные сравнения для отчета
    criteria_comparisons = []
    alternative_comparisons = {}
    
    if use_expert:
        try:
            settings = FuzzyComparisonSettings.objects.first()
            if settings:
                if settings.criteria_comparisons:
                    criteria_comparisons = json.loads(settings.criteria_comparisons)
                if settings.alternative_comparisons:
                    alternative_comparisons = json.loads(settings.alternative_comparisons)
        except:
            pass
    
    exporter = TeacherSearchExcelExporter(
        model=bz_model,
        results=results,
        alternatives_data=alternatives_data,
        teacher_ids=teacher_ids,
        user_location=(user_lat, user_lon),
        criteria_weights=criteria_weights,
        consistency_report=consistency_report,
        user_filters=filters,
        use_expert_weights=use_expert,
        criteria_comparisons=criteria_comparisons,
        alternative_comparisons=alternative_comparisons
    )
    
    # Экспортируем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    mode_str = "expert" if use_expert else "user"
    filename = f"teacher_search_{mode_str}_{timestamp}.xlsx"
    
    excel_data = exporter.export_to_bytesio()
    
    # Формируем HTTP ответ
    response = HttpResponse(
        excel_data.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    print(f"=== EXPORT_COMPLETE: {filename} ===")
    print(f"Weights used: {criteria_weights}")
    print("=" * 80)
    
    return response