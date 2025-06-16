from django.urls import reverse
from django.contrib.auth import get_user_model

from child.models import Child
from child.tests.utils import ChildTestBase

User = get_user_model()


class ChildViewsTest(ChildTestBase):
    def test_list_view(self):
        response = self.client.get(reverse("child:my_children"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Петя")

    def test_create_view(self):
        data = {
            "name": "Саша",
            "info": "Инфо",
            "gender": self.gender.id,
            "date_birth": "2012-03-03",
        }
        response = self.client.post(reverse("child:create_my_child"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Child.objects.filter(name="Саша").exists())

    def test_update_view(self):
        url = reverse("child:edit_my_child", kwargs={"pk": self.child.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Петя")

        response_post = self.client.post(
            url,
            {
                "name": "Обновлённый Петя",
                "info": "Новая информация",
                "gender": self.gender.id,
                "date_birth": "2014-01-01",
            },
        )
        self.assertRedirects(response_post, url)
        self.child.refresh_from_db()
        self.assertEqual(self.child.name, "Обновлённый Петя")

    def test_delete_view(self):
        url = reverse("child:child_confirm_delete", kwargs={"pk": self.child.pk})
        response = self.client.post(url)
        self.assertRedirects(response, reverse("child:my_children"))
        self.assertFalse(Child.objects.filter(pk=self.child.pk).exists())

    def test_detail_view(self):
        response = self.client.get(
            reverse("child:public_child_detail", kwargs={"pk": self.child.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Петя")
