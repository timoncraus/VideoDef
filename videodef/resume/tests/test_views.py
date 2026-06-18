from django.urls import reverse
from django.contrib.auth import get_user_model

from resume.models import Resume
from resume.tests.utils import ResumeTestBase

User = get_user_model()


class ResumeViewsTest(ResumeTestBase):
    def setUp(self):
        super().setUp()
        # Убедимся, что пользователь авторизован
        self.client.login(username='testuser', password='testpass123')
        
        self.resume = Resume.objects.create(
            user=self.user,
            short_info="Резюме",
            detailed_info="Описание",
            status=Resume.DRAFT,
            education_level="Высшее",
            experience_years=3,
        )

    def test_list_view(self):
        response = self.client.get(reverse("resume:my_resumes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Резюме")

    def test_create_view(self):
        # Добавляем все обязательные поля
        data = {
            "short_info": "Новое резюме",
            "detailed_info": "Детали",
            "status": Resume.DRAFT,
            "education_level": "Высшее",
            "experience_years": 5,
            "documents": [self.document.id] if hasattr(self, 'document') else [],
            "violation_types": [self.violation.id] if hasattr(self, 'violation') else [],
        }
        response = self.client.post(reverse("resume:create_my_resume"), data)
        
        # Проверяем редирект
        self.assertEqual(response.status_code, 302)
        
        # Проверяем, что резюме создано
        self.assertTrue(
            Resume.objects.filter(
                short_info="Новое резюме",
                user=self.user
            ).exists()
        )

    def test_update_view(self):
        url = reverse("resume:edit_my_resume", kwargs={"pk": self.resume.pk})
        
        # Проверяем GET запрос
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Резюме")
        
        # Проверяем POST запрос с обновленными данными
        response_post = self.client.post(
            url,
            {
                "short_info": "Обновлённое резюме",
                "detailed_info": "Новое описание",
                "status": Resume.ACTIVE,
                "education_level": "Высшее",
                "experience_years": 5,
            },
            follow=True  # Следуем за редиректом
        )
        
        # Проверяем успешное обновление
        self.assertEqual(response_post.status_code, 200)
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.short_info, "Обновлённое резюме")
        self.assertEqual(self.resume.status, Resume.ACTIVE)

    def test_delete_view(self):
        url = reverse("resume:resume_confirm_delete", kwargs={"pk": self.resume.pk})
        
        # Проверяем GET запрос (страница подтверждения)
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        
        # Проверяем POST запрос (удаление)
        response_post = self.client.post(url, follow=True)
        self.assertEqual(response_post.status_code, 200)
        
        # Проверяем, что резюме удалено
        self.assertFalse(Resume.objects.filter(pk=self.resume.pk).exists())

    def test_public_list_view(self):
        # Создаем активное резюме
        active_resume = Resume.objects.create(
            user=self.user,
            short_info="Публичное резюме",
            detailed_info="Публичное описание",
            status=Resume.ACTIVE,
            education_level="Высшее",
            experience_years=5,
        )
        
        # Выходим из системы для просмотра публичной страницы
        self.client.logout()
        
        # Проверяем публичный список
        response = self.client.get(reverse("resume:public_resume_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Публичное резюме")

    def test_public_detail_view(self):
        # Создаем активное резюме
        active_resume = Resume.objects.create(
            user=self.user,
            short_info="Детальное резюме",
            detailed_info="Детальное описание",
            status=Resume.ACTIVE,
            education_level="Высшее",
            experience_years=5,
        )
        
        # Выходим из системы для просмотра публичной страницы
        self.client.logout()
        
        # Проверяем публичную детальную страницу
        url = reverse("resume:public_resume_detail", kwargs={"pk": active_resume.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Детальное описание")