from resume.forms import ResumeForm
from resume.models import Resume
from resume.tests.utils import ResumeTestBase


class ResumeFormTest(ResumeTestBase):
    def test_valid_form(self):
        data = {
            "short_info": "Инфо",
            "detailed_info": "Описание",
            "status": Resume.DRAFT,
            "documents": [self.document.id],
            "violation_types": [self.violation.id],
        }
        form = ResumeForm(data=data, user=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = ResumeForm(data={}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('short_info', form.errors)
        self.assertIn('detailed_info', form.errors)
