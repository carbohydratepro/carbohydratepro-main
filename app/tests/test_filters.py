"""
テンプレートフィルターのテスト
"""
from decimal import Decimal

from django.test import TestCase

from app.templatetags.app_filters import highlight, comma_format, darker


class HighlightFilterTest(TestCase):
    """ハイライトフィルターのテスト"""

    def test_highlight_simple_match(self) -> None:
        """シンプルなマッチのハイライトテスト"""
        result = highlight('Hello World', 'World')
        self.assertIn('<mark>World</mark>', result)
        self.assertIn('Hello', result)

    def test_highlight_case_insensitive(self) -> None:
        """大文字小文字を区別しないハイライトテスト"""
        result = highlight('Hello World', 'world')
        self.assertIn('<mark>World</mark>', result)

    def test_highlight_no_match(self) -> None:
        """マッチなしのテスト"""
        result = highlight('Hello World', 'xyz')
        self.assertNotIn('<mark>', result)
        self.assertIn('Hello World', result)

    def test_highlight_empty_search(self) -> None:
        """空の検索文字列のテスト"""
        result = highlight('Hello World', '')
        self.assertNotIn('<mark>', result)

    def test_highlight_none_search(self) -> None:
        """None検索文字列のテスト"""
        result = highlight('Hello World', None)
        self.assertNotIn('<mark>', result)

    def test_highlight_multiple_matches(self) -> None:
        """複数マッチのハイライトテスト"""
        result = highlight('Hello World Hello', 'Hello')
        self.assertEqual(result.count('<mark>'), 2)

    def test_highlight_xss_prevention(self) -> None:
        """XSS防止テスト（テキストのエスケープ）"""
        result = highlight('<script>alert("xss")</script>', 'script')
        # 元のscriptタグがそのまま出力されていないことを確認
        self.assertNotIn('<script>', result)
        # エスケープされた文字列が含まれている（検索語 'script' はハイライトされる）
        self.assertIn('&lt;', result)
        self.assertIn('&gt;', result)

    def test_highlight_xss_prevention_in_search(self) -> None:
        """XSS防止テスト（検索文字列のエスケープ）"""
        result = highlight('Hello World', '<script>')
        self.assertNotIn('<script>', result)

    def test_highlight_japanese(self) -> None:
        """日本語のハイライトテスト"""
        result = highlight('こんにちは世界', '世界')
        self.assertIn('<mark>世界</mark>', result)

    def test_highlight_special_regex_chars(self) -> None:
        """正規表現特殊文字のテスト"""
        result = highlight('Hello (World)', '(World)')
        self.assertIn('<mark>(World)</mark>', result)


class CommaFormatFilterTest(TestCase):
    """三桁区切りフィルターのテスト"""

    def test_format_integer(self) -> None:
        """整数のフォーマットテスト"""
        result = comma_format(1234567)
        self.assertEqual(result, '1,234,567')

    def test_format_decimal(self) -> None:
        """Decimal型のフォーマットテスト"""
        result = comma_format(Decimal('1234567.89'))
        self.assertEqual(result, '1,234,567')

    def test_format_float(self) -> None:
        """浮動小数点数のフォーマットテスト"""
        result = comma_format(1234567.89)
        self.assertEqual(result, '1,234,567')

    def test_format_string_integer(self) -> None:
        """文字列整数のフォーマットテスト"""
        result = comma_format('1234567')
        self.assertEqual(result, '1,234,567')

    def test_format_string_float(self) -> None:
        """文字列浮動小数点数のフォーマットテスト"""
        result = comma_format('1234567.89')
        self.assertEqual(result, '1,234,567')

    def test_format_zero(self) -> None:
        """ゼロのフォーマットテスト"""
        result = comma_format(0)
        self.assertEqual(result, '0')

    def test_format_negative(self) -> None:
        """負の数のフォーマットテスト"""
        result = comma_format(-1234567)
        self.assertEqual(result, '-1,234,567')

    def test_format_none(self) -> None:
        """Noneのフォーマットテスト"""
        result = comma_format(None)
        self.assertEqual(result, '0')

    def test_format_small_number(self) -> None:
        """3桁以下の数のフォーマットテスト"""
        result = comma_format(123)
        self.assertEqual(result, '123')

    def test_format_invalid_string(self) -> None:
        """無効な文字列のテスト"""
        result = comma_format('invalid')
        self.assertEqual(result, 'invalid')


class DarkerFilterTest(TestCase):
    """色を暗くするフィルターのテスト"""

    def test_darker_hex_color(self) -> None:
        """16進数カラーコードを暗くするテスト"""
        result = darker('#FFFFFF')
        self.assertNotEqual(result, '#FFFFFF')
        self.assertTrue(result.startswith('#'))
        self.assertEqual(len(result), 7)

    def test_darker_without_hash(self) -> None:
        """#なしのカラーコードテスト"""
        result = darker('FFFFFF')
        self.assertTrue(result.startswith('#'))

    def test_darker_three_digit_color(self) -> None:
        """3桁カラーコードテスト"""
        result = darker('#FFF')
        self.assertTrue(result.startswith('#'))
        self.assertEqual(len(result), 7)

    def test_darker_black_remains_black(self) -> None:
        """黒色は黒のままであることをテスト"""
        result = darker('#000000')
        self.assertEqual(result, '#000000')

    def test_darker_factor(self) -> None:
        """デフォルトのfactor（0.7）で適切に暗くなることをテスト"""
        result = darker('#FFFFFF')
        # RGBそれぞれが255*0.7=178.5→178になる
        self.assertEqual(result.lower(), '#b2b2b2')

    def test_darker_empty_color(self) -> None:
        """空の色のテスト"""
        result = darker('')
        self.assertEqual(result, '')

    def test_darker_none_color(self) -> None:
        """Noneの色のテスト"""
        result = darker(None)
        self.assertIsNone(result)

    def test_darker_invalid_length(self) -> None:
        """不正な長さのカラーコードテスト"""
        result = darker('#FF')
        self.assertEqual(result, '#FF')

    def test_darker_preserves_color_tone(self) -> None:
        """色調が維持されることをテスト"""
        # 赤色を暗くしても赤系のまま
        result = darker('#FF0000')
        self.assertTrue(result.startswith('#'))
        # Rは大きく、GとBは0に近いはず
        r = int(result[1:3], 16)
        g = int(result[3:5], 16)
        b = int(result[5:7], 16)
        self.assertGreater(r, g)
        self.assertGreater(r, b)
