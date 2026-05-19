import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

from document.forms import DocumentForm
from document.models import Document
from child.models import Child
from .bellman_zade import TeacherSearchModel, calculate_distance

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
    model = Resume
    template_name = "resume/public_resume_list.html"
    context_object_name = "resumes"
    filterset_class = ResumeFilter
    
    def get_queryset(self):
        return Resume.objects.filter(status=Resume.ACTIVE).select_related(
            'user__profile'
        ).prefetch_related('violation_types')
    
    def safe_float(self, param, default):
        """Безопасное преобразование строки в float с заменой запятой на точку"""
        value = self.request.GET.get(param, str(default))
        if isinstance(value, str):
            value = value.replace(',', '.')
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Создаем модель Беллмана-Заде
        bz_model = TeacherSearchModel()
        
        # Получаем параметры из запроса
        price_min = self.safe_float('price_min', 0)
        price_max = self.safe_float('price_max', 5000)
        max_distance = self.safe_float('max_distance', 10)
        min_experience = self.safe_float('min_experience', 0)
        min_rating = self.safe_float('min_rating', 0)
        selected_child_id = self.request.GET.get('child')
        
        # Получаем выбранные пользователем цели (goal)
        price_goal = self.request.GET.get('price_goal', 'low')
        distance_goal = self.request.GET.get('distance_goal', 'close')
        experience_goal = self.request.GET.get('experience_goal', 'expert')
        rating_goal = self.request.GET.get('rating_goal', 'high')
        education_goal = self.request.GET.get('education_goal', 'expert')
        
        # Настройка предпочтений пользователя
        user_preferences = {
            'price': {
                'min': price_min,
                'max': price_max,
                'goal': price_goal
            },
            'distance': {
                'max': max_distance,
                'goal': distance_goal
            },
            'experience': {
                'min': min_experience,
                'goal': experience_goal
            },
            'rating': {
                'min': min_rating,
                'goal': rating_goal
            },
            'education': {
                'min': min_experience / 2,
                'goal': education_goal
            }
        }
        
        bz_model.setup_user_preferences(user_preferences)
        
        # Получаем отфильтрованные резюме (уже с учетом violation_types через FilterView)
        resumes = context.get('filter').qs if 'filter' in context else self.get_queryset()
        
        # Дополнительная фильтрация по числовым параметрам
        resumes = resumes.filter(
            price_min__lte=price_max,
            price_max__gte=price_min
        )
        
        # Координаты пользователя (по умолчанию Москва)
        user_lat = 55.751244
        user_lon = 37.618423
        
        if selected_child_id and selected_child_id.isdigit():
            try:
                child = Child.objects.get(id=int(selected_child_id), user=self.request.user)
                if hasattr(child, 'location_lat') and hasattr(child, 'location_lon'):
                    if child.location_lat and child.location_lon:
                        user_lat = float(child.location_lat)
                        user_lon = float(child.location_lon)
            except Child.DoesNotExist:
                pass
        
        # Подготовка альтернатив
        alternatives = []
        resume_objects = []
        
        for resume in resumes:
            # Рассчитываем расстояние
            distance = max_distance
            if resume.location_lat and resume.location_lon:
                distance = calculate_distance(
                    user_lat, user_lon,
                    float(resume.location_lat), float(resume.location_lon)
                )
            
            avg_price = resume.get_average_price()
            
            # Проверяем ограничения
            if avg_price < price_min or avg_price > price_max:
                continue
            if distance > max_distance:
                continue
            if resume.experience_years < min_experience:
                continue
            if resume.rating < min_rating:
                continue
            
            alternatives.append({
                'price': avg_price,
                'distance': distance,
                'experience': float(resume.experience_years),
                'rating': float(resume.rating),
                'education': float(resume.education_level)
            })
            resume_objects.append(resume)
        
        # Применяем метод Беллмана-Заде
        results = []
        if alternatives:
            rankings = bz_model.rank_alternatives(alternatives)
            
            for rank_data in rankings:
                idx = rank_data['alternative_id']
                if idx < len(resume_objects):
                    resume = resume_objects[idx]
                    results.append({
                        'resume': resume,
                        'mu_aggregated': rank_data['mu_aggregated'] * 100,
                        'mu_weighted': rank_data['mu_weighted'] * 100,
                        'mu_combined': rank_data['mu_combined'] * 100,
                        'satisfaction_level': rank_data['satisfaction_level'],
                        'membership_values': rank_data['membership_values'],
                        'linguistic_evaluation': rank_data['linguistic_evaluation'],
                        'rank': rank_data['rank'],
                        'distance': alternatives[idx]['distance']
                    })
        
        context['results'] = results
        context['resumes'] = resumes
        context['user_children'] = Child.objects.filter(user=self.request.user)
        context['all_violations'] = ViolationType.objects.all()
        context['selected_child_id'] = int(selected_child_id) if selected_child_id and selected_child_id.isdigit() else None
        context['price_min'] = int(price_min)
        context['price_max'] = int(price_max)
        context['max_distance'] = int(max_distance)
        context['min_experience'] = int(min_experience)
        context['min_rating'] = min_rating
        
        # Передаем выбранные цели в контекст
        context['price_goal'] = price_goal
        context['distance_goal'] = distance_goal
        context['experience_goal'] = experience_goal
        context['rating_goal'] = rating_goal
        context['education_goal'] = education_goal
        
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