from django.urls import reverse
from django.contrib.auth import get_user_model

from resume.models import Resume
from resume.tests.utils import ResumeTestBase

User = get_user_model()


class ResumeViewsTest(ResumeTestBase):
    def setUp(self):
        super().setUp()
        # Пользователь уже создан в ResumeTestBase
        
        # Создаем резюме с обязательными полями
        self.resume = Resume.objects.create(
            user=self.user,
            short_info="Резюме",
            detailed_info="Описание",
            status=Resume.DRAFT,
            education_level=5,
            experience_years=3,
            price_min=500,
            price_max=1000,
        )

    def test_list_view(self):
        response = self.client.get(reverse("resume:my_resumes"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Резюме")

    def test_create_view(self):
        data = {
            "short_info": "Новое резюме",
            "detailed_info": "Детали",
            "status": Resume.DRAFT,
            "education_level": 5,
            "experience_years": 5,
            "price_min": 600,
            "price_max": 1200,
        }
        response = self.client.post(reverse("resume:create_my_resume"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resume.objects.filter(short_info="Новое резюме").exists())

    def test_update_view(self):
        url = reverse("resume:edit_my_resume", kwargs={"pk": self.resume.pk})
        
        response_get = self.client.get(url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, "Резюме")
        
        response_post = self.client.post(
            url,
            {
                "short_info": "Обновлённое резюме",
                "detailed_info": "Новое описание",
                "status": Resume.ACTIVE,
                "education_level": 8,
                "experience_years": 7,
                "price_min": 400,
                "price_max": 900,
            },
            follow=True
        )
        self.assertEqual(response_post.status_code, 200)
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.short_info, "Обновлённое резюме")

    def test_delete_view(self):
        url = reverse("resume:resume_confirm_delete", kwargs={"pk": self.resume.pk})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Resume.objects.filter(pk=self.resume.pk).exists())

    def test_public_list_view(self):
        active_resume = Resume.objects.create(
            user=self.user,
            short_info="Публичное резюме",
            detailed_info="Публичное описание",
            status=Resume.ACTIVE,
            education_level=5,
            experience_years=5,
            price_min=500,
            price_max=1000,
        )
        
        self.client.logout()
        
        response = self.client.get(reverse("resume:public_resume_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Публичное резюме")

    def test_public_detail_view(self):
        active_resume = Resume.objects.create(
            user=self.user,
            short_info="Детальное резюме",
            detailed_info="Детальное описание",
            status=Resume.ACTIVE,
            education_level=5,
            experience_years=5,
            price_min=500,
            price_max=1000,
        )
        
        self.client.logout()
        
        url = reverse("resume:public_resume_detail", kwargs={"pk": active_resume.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Детальное описание")