from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
import django_filters
from django import forms
from django_filters.views import FilterView

from .models import Resume, ViolationType
from .forms import ResumeForm, ResumeImageFormSet, ResumeInitialImageFormSet


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
    success_url = reverse_lazy('resume:my_resumes')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        images_formset = ResumeInitialImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = ResumeInitialImageFormSet()
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


# Для преподавателя: редактирование резюме
class ResumeUpdateView(LoginRequiredMixin, UpdateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'resume/my_resume_create.html'

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
    
    def get_success_url(self):
        return reverse('resume:edit_my_resume', kwargs={'pk': self.object.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


# Для преподавателя: удаление резюме
class ResumeDeleteView(LoginRequiredMixin, DeleteView):
    model = Resume
    template_name = 'resume/my_resume_confirm_delete.html'
    success_url = reverse_lazy('resume:my_resumes')


# Для родителя: фильтрация резюме по видам нарушений
class ResumeFilter(django_filters.FilterSet):
    violation_types = django_filters.ModelMultipleChoiceFilter(
        queryset=ViolationType.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="Виды нарушений",
        method='filter_violation_types',
    )

    class Meta:
        model = Resume
        fields = ['violation_types']

    def filter_violation_types(self, queryset, name, value):
        if not value:
            return queryset

        for violation_type in value:
            queryset = queryset.filter(violation_types=violation_type)
        return queryset



# Для родителя: поиск преподавателей
class PublicResumeListView(FilterView):
    model = Resume
    template_name = 'resume/public_resume_list.html'
    context_object_name = 'resumes'
    filterset_class = ResumeFilter

    def get_queryset(self):
        return Resume.objects.filter(status=Resume.ACTIVE)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['selected_violation_types'] = self.request.GET.getlist('violation_types')
        return context


# Для родителя: подробная страничка резюме
class ResumeDetailView(DetailView):
    model = Resume
    template_name = 'resume/public_resume_detail.html'
    context_object_name = 'resume'
