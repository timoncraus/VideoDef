from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from .models import Resume, ResumeImage, ViolationType
from .forms import ResumeForm, ResumeImageFormSet
from django.contrib.auth.mixins import LoginRequiredMixin
import django_filters
from django import forms
from django_filters.views import FilterView

# Для преподавателя: список резюме
class ResumeListView(LoginRequiredMixin, ListView):
    model = Resume
    template_name = 'resume/my_resumes.html'
    context_object_name = 'resumes'

    def get_queryset(self):
        return Resume.objects.filter(user=self.request.user)


# Для преподавателя: создание резюме
class ResumeCreateView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'resume/my_resume_create.html'
    success_url = reverse_lazy('my_resumes')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        images_formset = ResumeImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = ResumeImageFormSet()
        return context


# Для преподавателя: редактирование резюме
class ResumeUpdateView(LoginRequiredMixin, UpdateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'resume/my_resume_create.html'
    success_url = reverse_lazy('my_resumes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = ResumeImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images_formset = ResumeImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response


# Для преподавателя: удаление резюме
class ResumeDeleteView(LoginRequiredMixin, DeleteView):
    model = Resume
    template_name = 'resume/my_resume_confirm_delete.html'
    success_url = reverse_lazy('my_resumes')


# Для родителя: фильтрация резюме по видам нарушений
class ResumeFilter(django_filters.FilterSet):
    violation_types = django_filters.ModelMultipleChoiceFilter(
        queryset=ViolationType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Виды нарушений",
    )

    class Meta:
        model = Resume
        fields = ['violation_types']


# Для родителя: поиск преподавателей
class PublicResumeListView(FilterView):
    model = Resume
    template_name = 'resume/public_resume_list.html'
    context_object_name = 'resumes'
    filterset_class = ResumeFilter

    def get_queryset(self):
        return Resume.objects.filter(status=Resume.ACTIVE)


# Для родителя: подробная страничка резюме
class ResumeDetailView(DetailView):
    model = Resume
    template_name = 'resume/public_resume_detail.html'
    context_object_name = 'resume'
