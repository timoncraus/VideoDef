from django import forms
from django.forms.models import inlineformset_factory

from .models import Child, ChildImage


class ChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'info', 'gender', 'date_birth', 'violation_types']
        widgets = {
            'date_birth': forms.DateInput(attrs={'type': 'date'}),
            'violation_types': forms.CheckboxSelectMultiple,
        }


ChildImageFormSet = inlineformset_factory(
    Child,
    ChildImage,
    fields=('image',),
    extra=2,
    max_num=2,
    can_delete=True
)


ChildInitialImageFormSet = inlineformset_factory(
    Child,
    ChildImage,
    fields=('image',),
    extra=2,
    max_num=2,
    can_delete=False
)