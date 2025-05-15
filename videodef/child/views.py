from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse, reverse_lazy
from .models import Child
from .forms import ChildForm, ChildImageFormSet, ChildInitialImageFormSet
from django.contrib.auth.mixins import LoginRequiredMixin

# Для родителя: список детей
class ChildListView(LoginRequiredMixin, ListView):
    model = Child
    template_name = 'child/my_children.html'
    context_object_name = 'children'

    def get_queryset(self):
        return Child.objects.filter(user=self.request.user)


# Для родителя: создание ребенка
class ChildCreateView(LoginRequiredMixin, CreateView):
    model = Child
    form_class = ChildForm
    template_name = 'child/my_child_create.html'
    success_url = reverse_lazy('my_children')

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        images_formset = ChildInitialImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = ChildInitialImageFormSet()
        return context


# Для родителя: редактирование ребенка
class ChildUpdateView(LoginRequiredMixin, UpdateView):
    model = Child
    form_class = ChildForm
    template_name = 'child/my_child_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['images_formset'] = ChildImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        images_formset = ChildImageFormSet(self.request.POST, self.request.FILES, instance=self.object)
        if images_formset.is_valid():
            images_formset.save()
        return response
    
    def get_success_url(self):
        return reverse('edit_my_child', kwargs={'pk': self.object.pk})


# Для родителя: удаление ребенка
class ChildDeleteView(LoginRequiredMixin, DeleteView):
    model = Child
    template_name = 'child/my_child_confirm_delete.html'
    success_url = reverse_lazy('my_children')

# Для преподавателя: подробная страничка ребенка
class ChildDetailView(DetailView):
    model = Child
    template_name = 'child/public_child_detail.html'
    context_object_name = 'child'