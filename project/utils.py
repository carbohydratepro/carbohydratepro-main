"""
共通ユーティリティ関数
"""
import re
import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def strip_html_tags(html_content: str) -> str:
    """HTMLタグを除去してプレーンテキストを返す"""
    text = re.sub('<[^<]+?>', '', html_content)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def send_html_email(
    subject: str,
    template_name: str,
    context: dict,
    recipient_list: list[str],
    from_email: str | None = None,
) -> bool:
    """
    HTMLメールを送信する

    Args:
        subject: メール件名
        template_name: HTMLテンプレートのパス
        context: テンプレートに渡すコンテキスト
        recipient_list: 送信先メールアドレスのリスト
        from_email: 送信元メールアドレス（省略時はDEFAULT_FROM_EMAIL）

    Returns:
        送信成功時はTrue、失敗時はFalse
    """
    if from_email is None:
        from_email = settings.DEFAULT_FROM_EMAIL

    try:
        html_message = render_to_string(template_name, context)
        text_message = strip_html_tags(html_message)

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=recipient_list
        )
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

        logger.info(f"Email sent successfully to: {', '.join(recipient_list)}")
        return True

    except Exception as e:
        logger.error(f"Email sending failed to {', '.join(recipient_list)}: {str(e)}")
        return False


# グラフ用カラーパレット
CHART_COLORS = {
    'category': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'],
    'major_category': {
        'variable': '#E74C3C',
        'fixed': '#3498DB',
        'special': '#9B59B6',
    },
    'no_data': '#BDC3C7',
    'expense_bar': '#FF6384',
    'balance_line': '#36A2EB',
}

# 大分類の日本語ラベル
MAJOR_CATEGORY_LABELS = {
    'variable': '変動費',
    'fixed': '固定費',
    'special': '特別費',
}
