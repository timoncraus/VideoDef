from document.models import Document, DocumentImage
from document.tests.utils import DocumentTestBase


class DocumentModelTest(DocumentTestBase):
    def test_document_str(self):
        expected = f"Документ №{self.document.id} ({self.document.ver_status})"
        self.assertEqual(str(self.document), expected)

    def test_document_image_str(self):
        image = DocumentImage.objects.create(document=self.document, image="test.jpg")
        self.assertIn(f"Изображение №{image.id}", str(image))
