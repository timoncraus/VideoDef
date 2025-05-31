from django.test import TestCase
from account.models import User, Gender
from resume.models import ViolationType
from document.models import Document, DocumentVerificationStatus


class ResumeTestBase(TestCase):
    def setUp(self):
        self.violation = ViolationType.objects.create(name="Нарушение слуха")
        self.user = User.objects.create_user(username="teacher",
                                             email="teacher@example.com",
                                             password="pass123")
        
        self.ver_status = DocumentVerificationStatus.objects.create(name="На проверке")
        self.document = Document.objects.create(user=self.user,
                                                name="Диплом",
                                                info="Диплом с отличием о высшем образовании",
                                                ver_status=self.ver_status)
        self.client.login(username="teacher", password="pass123")
