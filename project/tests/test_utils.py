"""
共通ユーティリティのテスト
"""
from unittest.mock import patch, MagicMock

from django.test import TestCase, override_settings

from project.utils import strip_html_tags, send_html_email, CHART_COLORS, MAJOR_CATEGORY_LABELS


class StripHtmlTagsTest(TestCase):
    """HTMLタグ除去関数のテスト"""

    def test_remove_simple_tags(self) -> None:
        """シンプルなHTMLタグの除去テスト"""
        html = '<p>Hello World</p>'
        result = strip_html_tags(html)
        self.assertEqual(result, 'Hello World')

    def test_remove_nested_tags(self) -> None:
        """ネストしたHTMLタグの除去テスト"""
        html = '<div><p><strong>Hello</strong> World</p></div>'
        result = strip_html_tags(html)
        self.assertEqual(result, 'Hello World')

    def test_remove_tags_with_attributes(self) -> None:
        """属性付きHTMLタグの除去テスト"""
        html = '<a href="https://example.com" class="link">Click here</a>'
        result = strip_html_tags(html)
        self.assertEqual(result, 'Click here')

    def test_collapse_whitespace(self) -> None:
        """連続する空白の圧縮テスト"""
        html = '<p>Hello</p>   <p>World</p>'
        result = strip_html_tags(html)
        self.assertEqual(result, 'Hello World')

    def test_strip_leading_trailing_whitespace(self) -> None:
        """前後の空白の除去テスト"""
        html = '  <p>Hello</p>  '
        result = strip_html_tags(html)
        self.assertEqual(result, 'Hello')

    def test_empty_string(self) -> None:
        """空文字列のテスト"""
        result = strip_html_tags('')
        self.assertEqual(result, '')

    def test_no_tags(self) -> None:
        """タグなし文字列のテスト"""
        result = strip_html_tags('Hello World')
        self.assertEqual(result, 'Hello World')

    def test_japanese_content(self) -> None:
        """日本語コンテンツのテスト"""
        html = '<p>こんにちは</p><p>世界</p>'
        result = strip_html_tags(html)
        # タグを除去した後、連続するテキストはそのまま結合される
        self.assertEqual(result, 'こんにちは世界')


@override_settings(
    DEFAULT_FROM_EMAIL='no-reply@example.com',
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class SendHtmlEmailTest(TestCase):
    """HTMLメール送信関数のテスト"""

    @patch('project.utils.EmailMultiAlternatives')
    @patch('project.utils.render_to_string')
    def test_send_email_success(self, mock_render, mock_email_class) -> None:
        """メール送信成功テスト"""
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance

        result = send_html_email(
            subject='Test Subject',
            template_name='test_template.html',
            context={'key': 'value'},
            recipient_list=['recipient@example.com']
        )

        self.assertTrue(result)
        mock_render.assert_called_once_with('test_template.html', {'key': 'value'})
        mock_email_instance.attach_alternative.assert_called_once()
        mock_email_instance.send.assert_called_once()

    @patch('project.utils.EmailMultiAlternatives')
    @patch('project.utils.render_to_string')
    def test_send_email_failure(self, mock_render, mock_email_class) -> None:
        """メール送信失敗テスト"""
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_email_instance = MagicMock()
        mock_email_instance.send.side_effect = Exception('Send failed')
        mock_email_class.return_value = mock_email_instance

        result = send_html_email(
            subject='Test Subject',
            template_name='test_template.html',
            context={},
            recipient_list=['recipient@example.com']
        )

        self.assertFalse(result)

    @patch('project.utils.EmailMultiAlternatives')
    @patch('project.utils.render_to_string')
    def test_send_email_with_custom_from(self, mock_render, mock_email_class) -> None:
        """カスタム送信元メールアドレスのテスト"""
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance

        result = send_html_email(
            subject='Test Subject',
            template_name='test_template.html',
            context={},
            recipient_list=['recipient@example.com'],
            from_email='custom@example.com'
        )

        self.assertTrue(result)
        mock_email_class.assert_called_once()
        call_kwargs = mock_email_class.call_args[1]
        self.assertEqual(call_kwargs['from_email'], 'custom@example.com')

    @patch('project.utils.EmailMultiAlternatives')
    @patch('project.utils.render_to_string')
    def test_send_email_multiple_recipients(self, mock_render, mock_email_class) -> None:
        """複数宛先へのメール送信テスト"""
        mock_render.return_value = '<html><body>Test</body></html>'
        mock_email_instance = MagicMock()
        mock_email_class.return_value = mock_email_instance

        recipients = ['user1@example.com', 'user2@example.com']
        result = send_html_email(
            subject='Test Subject',
            template_name='test_template.html',
            context={},
            recipient_list=recipients
        )

        self.assertTrue(result)
        call_kwargs = mock_email_class.call_args[1]
        self.assertEqual(call_kwargs['to'], recipients)


class ChartColorsTest(TestCase):
    """グラフ用カラーパレットのテスト"""

    def test_category_colors_exist(self) -> None:
        """カテゴリ色が存在することをテスト"""
        self.assertIn('category', CHART_COLORS)
        self.assertEqual(len(CHART_COLORS['category']), 5)

    def test_major_category_colors_exist(self) -> None:
        """大分類色が存在することをテスト"""
        self.assertIn('major_category', CHART_COLORS)
        self.assertIn('variable', CHART_COLORS['major_category'])
        self.assertIn('fixed', CHART_COLORS['major_category'])
        self.assertIn('special', CHART_COLORS['major_category'])

    def test_no_data_color_exists(self) -> None:
        """データなし色が存在することをテスト"""
        self.assertIn('no_data', CHART_COLORS)

    def test_expense_bar_color_exists(self) -> None:
        """支出棒グラフ色が存在することをテスト"""
        self.assertIn('expense_bar', CHART_COLORS)

    def test_balance_line_color_exists(self) -> None:
        """残高折れ線グラフ色が存在することをテスト"""
        self.assertIn('balance_line', CHART_COLORS)

    def test_colors_are_valid_hex(self) -> None:
        """色が有効な16進数カラーコードであることをテスト"""
        import re
        hex_pattern = re.compile(r'^#[0-9A-Fa-f]{6}$')

        for color in CHART_COLORS['category']:
            self.assertRegex(color, hex_pattern)

        for color in CHART_COLORS['major_category'].values():
            self.assertRegex(color, hex_pattern)

        self.assertRegex(CHART_COLORS['no_data'], hex_pattern)
        self.assertRegex(CHART_COLORS['expense_bar'], hex_pattern)
        self.assertRegex(CHART_COLORS['balance_line'], hex_pattern)


class MajorCategoryLabelsTest(TestCase):
    """大分類ラベルのテスト"""

    def test_all_labels_exist(self) -> None:
        """すべてのラベルが存在することをテスト"""
        self.assertIn('variable', MAJOR_CATEGORY_LABELS)
        self.assertIn('fixed', MAJOR_CATEGORY_LABELS)
        self.assertIn('special', MAJOR_CATEGORY_LABELS)

    def test_labels_are_japanese(self) -> None:
        """ラベルが日本語であることをテスト"""
        self.assertEqual(MAJOR_CATEGORY_LABELS['variable'], '変動費')
        self.assertEqual(MAJOR_CATEGORY_LABELS['fixed'], '固定費')
        self.assertEqual(MAJOR_CATEGORY_LABELS['special'], '特別費')
