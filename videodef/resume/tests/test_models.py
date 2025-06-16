from resume.models import Resume, ResumeImage
from resume.tests.utils import ResumeTestBase


class ResumeModelTest(ResumeTestBase):
    def test_create_resume(self):
        resume = Resume.objects.create(
            user=self.user,
            short_info="Инфо",
            detailed_info="Подробности",
            status=Resume.ACTIVE,
        )
        resume.documents.add(self.document)
        resume.violation_types.add(self.violation)
        self.assertEqual(str(resume), "Инфо (Активно)")
        self.assertIn(self.violation, resume.violation_types.all())
        self.assertIn(self.document, resume.documents.all())

    def test_resume_image_str(self):
        resume = Resume.objects.create(
            user=self.user,
            short_info="Резюме",
            detailed_info="Описание",
        )
        image = ResumeImage.objects.create(resume=resume, image="image.jpg")
        self.assertIn(f"Изображение №{image.id}", str(image))
