from django.test import TestCase
from account.models import User
from document.models import DocumentVerificationStatus, Document


class DocumentTestBase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="teacher",
            email="teacher@example.com",
            password="pass123",
            phone_number="+79991234567"
        )
        self.ver_status = DocumentVerificationStatus.objects.create(name="На проверке")
        self.client.login(username="teacher", password="pass123")

        self.document = Document.objects.create(
            user=self.user,
            name="Тестовый документ",
            info="Некоторая информация",
            ver_status=self.ver_status
        )
