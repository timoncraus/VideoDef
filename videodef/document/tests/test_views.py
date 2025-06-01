from django.urls import reverse

from document.models import Document
from document.tests.utils import DocumentTestBase


class DocumentViewsTest(DocumentTestBase):
    def test_list_view(self):
        response = self.client.get(reverse("document:my_documents"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовый документ")

    def test_create_view(self):
        data = {
            "name": "Новый документ",
            "info": "Описание",
        }
        response = self.client.post(reverse("document:create_my_document"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Document.objects.filter(name="Новый документ").exists())

    def test_update_view(self):
        url = reverse("document:edit_my_document", kwargs={"pk": self.document.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовый документ")

        response_post = self.client.post(
            url, {"name": "Обновлённый документ", "info": "Новое описание"}
        )
        self.assertRedirects(response_post, url)
        self.document.refresh_from_db()
        self.assertEqual(self.document.name, "Обновлённый документ")

    def test_delete_view(self):
        url = reverse(
            "document:document_confirm_delete", kwargs={"pk": self.document.pk}
        )
        response = self.client.post(url)
        self.assertRedirects(response, reverse("document:my_documents"))
        self.assertFalse(Document.objects.filter(pk=self.document.pk).exists())

    def test_detail_view(self):
        url = reverse(
            "document:public_document_detail", kwargs={"pk": self.document.pk}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Тестовый документ")
