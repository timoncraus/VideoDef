from django import forms
from .models import Resume, ResumeImage
from django.forms.models import inlineformset_factory

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['short_info', 'detailed_info', 'status', 'document', 'violation_types']
        widgets = {
            'violation_types': forms.CheckboxSelectMultiple,
        }

ResumeImageFormSet = inlineformset_factory(
    Resume,
    ResumeImage,
    fields=('image',),
    extra=5,
    max_num=5,
    can_delete=True
)
