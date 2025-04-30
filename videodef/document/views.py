from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse, reverse_lazy
from .models import Document
from .forms import DocumentForm, DocumentImageFormSet, DocumentInitialImageFormSet
from django.contrib.auth.mixins import LoginRequiredMixin
import django_filters
from django import forms
from django_filters.views import FilterView

# Для преподавателя: список документов
class DocumentListView(LoginRequiredMixin, ListView):
    model = Document
    template_name = 'document/my_documents.html'
    context_object_name = 'documents'

    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)


# Для преподавателя: создание документа
class DocumentCreateView(LoginRequiredMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document/my_document_create.html'
    success_url = reverse_lazy('my_documents')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        images_formset = DocumentInitialImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = DocumentInitialImageFormSet()
        return context


# Для преподавателя: редактирование документа
class DocumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document/my_document_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = DocumentImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images_formset = DocumentImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response
    
    def get_success_url(self):
        return reverse('edit_my_document', kwargs={'pk': self.object.pk})


# Для преподавателя: удаление документа
class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    model = Document
    template_name = 'document/my_document_confirm_delete.html'
    success_url = reverse_lazy('my_documents')
