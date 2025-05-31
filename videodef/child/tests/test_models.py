from django.test import TestCase
from django.utils import timezone

from account.models import User, Gender
from resume.models import ViolationType
from child.models import Child, ChildImage
from child.tests.utils import ChildTestBase

class ChildModelTest(ChildTestBase):
    def test_create_child(self):
        self.child.violation_types.add(self.violation)
        self.assertEqual(str(self.child), f"Ребенок №{self.child.id} ({self.child.name})")
        self.assertEqual(self.child.user.username, "parent")
        self.assertEqual(self.child.gender.name, "Мужской")

    def test_child_image_str(self):
        image = ChildImage.objects.create(child=self.child, image="test.jpg")
        self.assertIn(f"Изображение №{image.id}", str(image))
