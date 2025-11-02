from django.urls import reverse

from resume.models import Resume
from resume.tests.utils import ResumeTestBase


class ResumeViewsTest(ResumeTestBase):
    def setUp(self):
        super().setUp()
        self.resume = Resume.objects.create(
            user=self.user,
            short_info="Резюме",
            detailed_info="Описание",
            status=Resume.DRAFT,
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
            "documents": [self.document.id],
            "violation_types": [self.violation.id],
        }
        response = self.client.post(reverse("resume:create_my_resume"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Resume.objects.filter(short_info="Новое резюме").exists())

    def test_update_view(self):
        url = reverse("resume:edit_my_resume", kwargs={"pk": self.resume.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Резюме")

        response_post = self.client.post(
            url,
            {
                "short_info": "Обновлённое резюме",
                "detailed_info": "Новое описание",
                "status": Resume.ACTIVE,
            },
        )
        self.assertRedirects(response_post, url)
        self.resume.refresh_from_db()
        self.assertEqual(self.resume.short_info, "Обновлённое резюме")

    def test_delete_view(self):
        url = reverse("resume:resume_confirm_delete", kwargs={"pk": self.resume.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("resume:my_resumes"))
        self.assertFalse(Resume.objects.filter(pk=self.resume.pk).exists())

    def test_public_list_view(self):
        self.resume.status = Resume.ACTIVE
        self.resume.save()
        response = self.client.get(reverse("resume:public_resume_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Резюме")

    def test_public_detail_view(self):
        self.resume.status = Resume.ACTIVE
        self.resume.save()
        url = reverse("resume:public_resume_detail", kwargs={"pk": self.resume.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Описание")
