from child.forms import ChildForm
from child.tests.utils import ChildTestBase


class ChildFormTest(ChildTestBase):
    def test_valid_form(self):
        data = {
            "name": "Маша",
            "info": "Описание",
            "gender": self.gender.id,
            "date_birth": "2016-06-15",
            "violation_types": [self.violation.id],
        }
        form = ChildForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = ChildForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("date_birth", form.errors)
