from django import forms
from .models import Document, DocumentImage
from django.forms.models import inlineformset_factory

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['name', 'info']

DocumentImageFormSet = inlineformset_factory(
    Document,
    DocumentImage,
    fields=('image',),
    extra=5,
    max_num=5,
    can_delete=True
)

DocumentInitialImageFormSet = inlineformset_factory(
    Document,
    DocumentImage,
    fields=('image',),
    extra=5,
    max_num=5,
    can_delete=False
)