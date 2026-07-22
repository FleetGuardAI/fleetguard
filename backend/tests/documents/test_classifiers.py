import unittest
from infrastructure.documents.models import DocumentFamily
from infrastructure.documents.classifiers import classify_document

class TestClassifiers(unittest.TestCase):
    def test_classify_invoice(self):
        self.assertEqual(classify_document("THIS IS A TAX INVOICE"), DocumentFamily.INVOICE)
        self.assertEqual(classify_document("MONTHLY BILL"), DocumentFamily.INVOICE)

    def test_classify_receipt(self):
        self.assertEqual(classify_document("FUEL RECEIPT 123"), DocumentFamily.RECEIPT)

    def test_classify_certificate(self):
        self.assertEqual(classify_document("POLLUTION UNDER CONTROL"), DocumentFamily.CERTIFICATE)
        self.assertEqual(classify_document("FITNESS CERTIFICATE"), DocumentFamily.CERTIFICATE)

    def test_classify_identity(self):
        self.assertEqual(classify_document("DRIVER LICENSE"), DocumentFamily.IDENTITY_DOCUMENT)
        self.assertEqual(classify_document("VEHICLE REGISTRATION"), DocumentFamily.IDENTITY_DOCUMENT)

    def test_classify_form(self):
        self.assertEqual(classify_document("APPLICATION FORM A"), DocumentFamily.FORM)

    def test_classify_unknown(self):
        self.assertEqual(classify_document("JUST SOME RANDOM TEXT"), DocumentFamily.UNKNOWN)
