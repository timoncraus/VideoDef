from django import forms
from django.forms.models import inlineformset_factory
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import Resume, ResumeImage, TeacherReview
from document.models import Document


class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = [
            "short_info",
            "detailed_info",
            "status",
            "price_min",
            "price_max",
            "experience_years",
            "education_level",
            "location_address",
            "documents",
            "violation_types",
        ]
        widgets = {
            "violation_types": forms.CheckboxSelectMultiple,
            "documents": forms.CheckboxSelectMultiple,
            "short_info": forms.TextInput(attrs={
                "placeholder": "Кратко опишите вашу специализацию",
                "class": "form-input"
            }),
            "detailed_info": forms.Textarea(attrs={
                "rows": 5,
                "placeholder": "Подробно расскажите о методиках работы, образовании и опыте",
                "class": "form-textarea"
            }),
            "location_address": forms.TextInput(attrs={
                "placeholder": "Например: г. Москва, ул. Тверская, д. 1",
                "class": "form-input"
            }),
        }
        labels = {
            "short_info": "Краткая информация",
            "detailed_info": "Подробная информация",
            "status": "Статус резюме",
            "price_min": "Минимальная цена (₽)",
            "price_max": "Максимальная цена (₽)",
            "experience_years": "Опыт работы (лет)",
            "education_level": "Уровень образования (0-10)",
            "location_address": "Адрес",
            "documents": "Прикреплённые документы",
            "violation_types": "Виды нарушений",
        }
        help_texts = {
            "education_level": "0 — без проф. образования, 5 — бакалавриат, 10 — кандидат/доктор наук по профилю",
            "price_min": "Укажите минимальную стоимость одного занятия",
            "price_max": "Укажите максимальную стоимость одного занятия",
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


class TeacherReviewForm(forms.ModelForm):
    """Форма для отзыва о преподавателе"""
    class Meta:
        model = TeacherReview
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.RadioSelect(choices=[
                (5, '⭐⭐⭐⭐⭐ Отлично'),
                (4, '⭐⭐⭐⭐ Хорошо'),
                (3, '⭐⭐⭐ Удовлетворительно'),
                (2, '⭐⭐ Плохо'),
                (1, '⭐ Очень плохо')
            ]),
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Поделитесь вашим опытом работы с этим преподавателем...',
                'class': 'form-textarea'
            })
        }
        labels = {
            'rating': 'Ваша оценка',
            'comment': 'Комментарий'
        }