"""Tests. Run with:  python -m unittest discover tests"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402
from pdf_generator import THEMES  # noqa: E402

FULL_FORM = {
    "name": "Jane Doe",
    "headline": "Software Developer",
    "email": "jane@example.com",
    "phone": "+91 98765 43210",
    "location": "Hyderabad, India",
    "links": "https://github.com/jane, https://linkedin.com/in/jane",
    "summary": "Developer who enjoys building useful web apps.",
    "skills": "Python, Flask, SQL",
    "languages": "English (Fluent), Hindi, Telugu",
    "experience_role[]": ["Python Intern"],
    "experience_company[]": ["ABC Tech"],
    "experience_dates[]": ["Jun 2026 - Aug 2026"],
    "experience_details[]": ["Built an API\nWrote tests"],
    "projects_title[]": ["Resume Generator"],
    "projects_link[]": ["https://github.com/jane/resume-generator"],
    "projects_description[]": ["Builds PDFs\nUses Flask"],
    "education_degree[]": ["B.Tech in Computer Science"],
    "education_school[]": ["Example College"],
    "education_year[]": ["2023 - 2027"],
    "certificates_name[]": ["Python for Everybody"],
    "certificates_issuer[]": ["Coursera"],
    "certificates_year[]": ["2025"],
}


class ResumeAppTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_home_page_loads(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ResumeGen", response.data)

    def test_every_template_builds_a_pdf(self):
        for key in THEMES:
            with self.subTest(template=key):
                response = self.client.post(
                    "/download", data={**FULL_FORM, "template": key})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, "application/pdf")
                self.assertTrue(response.data.startswith(b"%PDF"))

    def test_minimal_form_works(self):
        response = self.client.post("/download", data={"name": "Jane"})
        self.assertEqual(response.status_code, 200)

    def test_special_characters_do_not_break_pdf(self):
        response = self.client.post("/download", data={
            "name": "Tom & Jerry <script>",
            "summary": "R&D <b>engineer</b> & more",
            "languages": "English & <Hindi>",
        })
        self.assertEqual(response.status_code, 200)

    def test_unknown_template_falls_back(self):
        response = self.client.post(
            "/download", data={"name": "Jane", "template": "does-not-exist"})
        self.assertEqual(response.status_code, 200)

    def test_name_is_required(self):
        response = self.client.post("/download", data={"name": ""})
        self.assertEqual(response.status_code, 400)

    def test_bad_email_is_rejected(self):
        response = self.client.post("/download", data={
            "name": "Jane", "email": "not-an-email"})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
