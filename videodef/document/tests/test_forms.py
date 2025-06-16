from document.forms import DocumentForm
from document.tests.utils import DocumentTestBase


class DocumentFormTest(DocumentTestBase):
    def test_valid_form(self):
        form = DocumentForm(data={"name": "Документ 1", "info": "Описание документа"})
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = DocumentForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
        self.assertIn("info", form.errors)
