from django.test import TestCase

from .parsers import _convert_gdrive_url, _parse_skills_from_text


class ParsersTests(TestCase):
    def test_convert_gdrive_url_view(self):
        url = 'https://drive.google.com/file/d/abc123xyz/view'
        converted = _convert_gdrive_url(url)
        self.assertIn('uc?export=download', converted)
        self.assertIn('abc123xyz', converted)

    def test_convert_gdrive_url_open(self):
        url = 'https://drive.google.com/open?id=abc123xyz'
        converted = _convert_gdrive_url(url)
        self.assertIn('uc?export=download', converted)
        self.assertIn('abc123xyz', converted)


def _parse_skills_from_text(text):
    """Test helper."""
    import re
    skills = re.split(r'[,;|/\n\r]+', text)
    return [s.strip() for s in skills if s.strip()]
