from django.test import TestCase
from django.contrib.auth import get_user_model

from resume.forms import ResumeForm
from resume.models import Resume

User = get_user_model()


class ResumeFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_valid_form(self):
        # Добавляем все обязательные поля
        form_data = {
            'short_info': 'Краткая информация о кандидате',
            'detailed_info': 'Детальная информация о кандидате с опытом работы',
            'education_level': 'Высшее',
            'experience_years': 5,
            'status': Resume.DRAFT,
        }
        form = ResumeForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Form errors: {form.errors}")

    def test_invalid_form_missing_required_fields(self):
        # Отсутствуют обязательные поля
        form_data = {
            'short_info': 'Только краткая информация',
        }
        form = ResumeForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('education_level', form.errors)
        self.assertIn('experience_years', form.errors)

    def test_form_save(self):
        form_data = {
            'short_info': 'Новое резюме',
            'detailed_info': 'Детальное описание',
            'education_level': 'Среднее специальное',
            'experience_years': 3,
            'status': Resume.DRAFT,
        }
        form = ResumeForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Сохраняем без commit
        resume = form.save(commit=False)
        resume.user = self.user
        resume.save()
        
        self.assertEqual(resume.short_info, 'Новое резюме')
        self.assertEqual(resume.user, self.user)