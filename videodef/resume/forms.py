from django import forms
from django.forms.models import inlineformset_factory

from .models import Resume, ResumeImage
from document.models import Document


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            "short_info",
            "detailed_info",
            "status",
            "documents",
            "violation_types",
        ]
        widgets = {
            "violation_types": forms.CheckboxSelectMultiple,
            "documents": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["documents"].queryset = Document.objects.filter(user=user)


ResumeImageFormSet = inlineformset_factory(
    Resume, ResumeImage, fields=("image",), extra=3, max_num=3, can_delete=True
)


ResumeInitialImageFormSet = inlineformset_factory(
    Resume, ResumeImage, fields=("image",), extra=3, max_num=3, can_delete=False
)
