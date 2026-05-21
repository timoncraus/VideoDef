import json
import math
from typing import List, Dict, Any, Tuple
from django.http import JsonResponse, HttpResponseBadRequest
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

from .models import Resume, ViolationType, TeacherReview
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
        """Получение координат пользователя (по ребенку или по умолчанию)"""
        # Координаты по умолчанию (Москва)
        default_lat = 55.751244
        default_lon = 37.618423
        
        if child_id:
            try:
                child = Child.objects.get(id=child_id, user=self.request.user)
                if hasattr(child, 'location_lat') and hasattr(child, 'location_lon'):
                    if child.location_lat and child.location_lon:
                        return float(child.location_lat), float(child.location_lon)
            except Child.DoesNotExist:
                pass
        
        # Пробуем получить из профиля пользователя
        if hasattr(self.request.user, 'profile'):
            profile = self.request.user.profile
            if profile.location_lat and profile.location_lon:
                return float(profile.location_lat), float(profile.location_lon)
        
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
        Веса критериев берутся из экспертных настроек (админка).
        Сравнения альтернатив строятся автоматически на основе реальных данных.
        """
        model = BellmanZadeMCDA()
        
        # Устанавливаем альтернативы
        alternatives = [f"T_{tid}" for tid in teacher_ids]
        model.set_alternatives(alternatives)
        print(f"=== build_fuzzy_model ===")
        print(f"Alternatives set: {alternatives}")
        
        # Критерии
        criteria = ['price', 'distance', 'experience', 'rating', 'education']
        model.set_criteria(criteria)
        
        # Загружаем экспертные настройки из админки
        expert_data = self.get_expert_comparisons()
        print(f"Expert data: use_expert_comparisons={expert_data['use_expert_comparisons']}")
        
        # ============================================================
        # 1. Загружаем ЭКСПЕРТНЫЕ ВЕСА КРИТЕРИЕВ из админки
        # ============================================================
        if expert_data['use_expert_comparisons'] and expert_data['criteria_comparisons']:
            print("=" * 50)
            print("Загружаем ЭКСПЕРТНЫЕ ВЕСА КРИТЕРИЕВ из админки")
            print("=" * 50)
            
            # Загружаем сравнения критериев для расчета весов
            for comp in expert_data['criteria_comparisons']:
                if 'linguistic_value' in comp:
                    print(f"  Criteria: {comp['criterion1']} vs {comp['criterion2']} = {comp['linguistic_value']}")
                    model.add_criterion_comparison_linguistic(
                        comp['criterion1'], 
                        comp['criterion2'], 
                        comp['linguistic_value']
                    )
                elif 'value' in comp:
                    print(f"  Criteria: {comp['criterion1']} vs {comp['criterion2']} = {comp['value']}")
                    model.add_criterion_comparison(
                        comp['criterion1'], 
                        comp['criterion2'], 
                        float(comp['value'])
                    )
            
            # ПРОВЕРЯЕМ, что матрица создалась
            if model.criteria_comparison_matrix is None:
                print("ОШИБКА: criteria_comparison_matrix не создалась!")
            else:
                print("criteria_comparison_matrix успешно создана")
                print("Содержимое матрицы:")
                for i, row in enumerate(model.criteria_comparison_matrix.matrix):
                    print(f"  {criteria[i]}: {row}")
            
            # Пересчитываем веса
            print("Пересчитываем веса критериев...")
            model.calculate_criteria_weights()
            
        else:
            print("=" * 50)
            print("Экспертные веса критериев не найдены, используем равные веса")
            print("=" * 50)
            # Устанавливаем равные веса
            n = len(criteria)
            model.criteria_weights = np.ones(n) / n
        
        # Выводим веса критериев после загрузки
        if model.criteria_weights is not None:
            print("\nВеса критериев ПОСЛЕ загрузки из админки:")
            for i, criterion in enumerate(criteria):
                print(f"  {criterion.upper()}: {model.criteria_weights[i]:.4f} ({model.criteria_weights[i]*100:.1f}%)")
        
        # ============================================================
        # 2. АВТОМАТИЧЕСКОЕ построение матриц сравнения АЛЬТЕРНАТИВ
        # ============================================================
        print("\n" + "=" * 50)
        print("Строим матрицы сравнения АЛЬТЕРНАТИВ на основе реальных данных")
        print("=" * 50)
        self._build_auto_matrices(model, alternatives_data, teacher_ids)
        
        # ============================================================
        # 3. Строим нечеткие множества и рассчитываем решение
        # ============================================================
        print("\nCalling build_fuzzy_sets...")
        model.build_fuzzy_sets()
        
        print("Calling calculate_solution...")
        model.calculate_solution(use_weights=True)
        
        return model

    def _build_auto_matrices(self, model: BellmanZadeMCDA, alternatives_data: List[Dict], teacher_ids: List[int]):
        """
        Автоматическое построение матриц парных сравнений на основе данных.
        """
        n = len(teacher_ids)
        print(f"Building auto matrices for {n} teachers")  # Отладка
        
        for criterion in model.criteria:
            print(f"Processing criterion: {criterion}")  # Отладка
            
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
                    print(f"  Distance: {val} -> {normalized}")
                elif criterion == 'experience':
                    val = data.get('experience', 0)
                    normalized = max(1, min(10, 1 + (val / 30) * 9))
                    values.append(normalized)
                    print(f"  Experience: {val} -> {normalized}")
                elif criterion == 'rating':
                    val = data.get('rating', 0)
                    normalized = max(1, min(10, 1 + (val / 5) * 9))
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
                    ratio = values[i] / values[j]
                    
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
                        # Убедимся, что значение не None
                        if membership is None:
                            membership = 0.0
                        memberships[criterion] = membership
                    else:
                        memberships[criterion] = 0.0
                
                # DEBUG: выводим в консоль
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Получаем параметры фильтрации из GET-запроса
        price_min = self.safe_float('price_min', 0)
        price_max = self.safe_float('price_max', 10000)
        max_distance = self.safe_float('max_distance', 20)
        min_experience = self.safe_float('min_experience', 0)
        min_rating = self.safe_float('min_rating', 0)
        selected_child_id = self.request.GET.get('child')
        selected_violations = self.request.GET.getlist('violation_types')
        
        # Получаем цели пользователя (для лингвистических переменных)
        price_goal = self.request.GET.get('price_goal', 'low')
        distance_goal = self.request.GET.get('distance_goal', 'close')
        experience_goal = self.request.GET.get('experience_goal', 'expert')
        rating_goal = self.request.GET.get('rating_goal', 'high')
        
        # Базовый queryset с фильтрацией
        resumes = self.get_queryset()
        
        # Фильтрация по видам нарушений (если выбраны)
        if selected_violations:
            resumes = resumes.filter(violation_types__id__in=selected_violations).distinct()
        
        # Фильтрация по цене
        resumes = resumes.filter(
            Q(price_min__lte=price_max) | Q(price_min__isnull=True),
            Q(price_max__gte=price_min) | Q(price_max__isnull=True)
        )
        
        # Фильтрация по опыту
        if min_experience > 0:
            resumes = resumes.filter(experience_years__gte=min_experience)
        
        # Фильтрация по рейтингу
        if min_rating > 0:
            resumes = resumes.filter(rating__gte=min_rating)
        
        # Получаем координаты пользователя
        user_lat, user_lon = self.get_user_location(
            int(selected_child_id) if selected_child_id and selected_child_id.isdigit() else None
        )
        
        # Подготовка данных для метода Беллмана-Заде
        alternatives_data = []
        teacher_ids = []
        
        for resume in resumes:
            # Рассчитываем расстояние
            distance = max_distance
            if resume.location_lat and resume.location_lon:
                distance = calculate_distance(
                    user_lat, user_lon,
                    float(resume.location_lat), float(resume.location_lon)
                )
            
            # Пропускаем, если расстояние превышает лимит
            if distance > max_distance:
                continue
            
            avg_price = resume.get_average_price()
            
            alternatives_data.append({
                'price': avg_price,
                'distance': distance,
                'experience': float(resume.experience_years),
                'rating': float(resume.rating),
                'education': float(resume.education_level),
                'reviews_count': TeacherReview.objects.filter(teacher=resume.user, is_approved=True).count()
            })
            teacher_ids.append(resume.id)
        
        # Применяем метод Беллмана-Заде
        results = []
        consistency_report = None
        criteria_weights = {}
        
        if alternatives_data:
            # Строим модель
            model = self.build_fuzzy_model(alternatives_data, teacher_ids)
            
            # Получаем отчет о согласованности
            consistency_report = model.get_consistency_report()
            
            # Получаем веса критериев
            if model.criteria_weights is not None:
                for i, criterion in enumerate(model.criteria):
                    criteria_weights[criterion] = model.criteria_weights[i]
            
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
            
            # Сохраняем модель в сессию для What-If анализа
            self.request.session['bz_model_json'] = json.dumps(model.to_dict(), default=str)
        
        # Сортируем результаты по рангу
        results.sort(key=lambda x: x['rank'])
        
        # Добавляем в контекст
        context['results'] = results
        context['user_children'] = Child.objects.filter(user=self.request.user)
        context['all_violations'] = ViolationType.objects.all()
        context['selected_violations'] = [int(v) for v in selected_violations]
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


# Для родителя: подробная страничка резюме
class ResumeDetailView(DetailView):
    model = Resume
    template_name = "resume/public_resume_detail.html"
    context_object_name = "resume"


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
    return user.is_authenticated and user.profile.role and user.profile.role.name == 'Родитель'


def is_teacher(user):
    return user.is_authenticated and user.profile.role and user.profile.role.name == 'Преподаватель'


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
            review.is_approved = False
            review.save()
            messages.success(request, "Отзыв отправлен на проверку!")
            return redirect('account:view_other_user', user_id=teacher_id)
    else:
        form = TeacherReviewForm(instance=existing_review)
    
    reviews = TeacherReview.objects.filter(teacher=teacher, is_approved=True)
    
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


@staff_member_required
@csrf_exempt
def api_calculate_criteria_weights(request):
    """API для расчета весов критериев (для админ-панели)"""
    from .bellman_zade import ComparisonMatrix
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comparisons = data.get('comparisons', {})
            
            # Критерии в правильном порядке
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
            
            weights = matrix.calculate_weights()
            consistency = matrix.calculate_consistency_ratio()
            
            return JsonResponse({
                'weights': {c: float(weights[i]) for i, c in enumerate(criteria)},
                'lambda_max': float(consistency['lambda_max']),
                'ci': float(consistency['ci']),
                'cr': float(consistency['cr']),
                'is_consistent': consistency['is_consistent']
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


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