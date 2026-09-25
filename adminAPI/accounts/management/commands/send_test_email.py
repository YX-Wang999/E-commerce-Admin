"""Send a test email to verify SMTP / QQ Mail configuration."""

from django.core.management.base import BaseCommand, CommandError

from accounts.email_utils import is_email_configured, send_system_email


class Command(BaseCommand):
    """Send a test email to the given address."""

    help = '发送测试邮件，验证 QQ 邮箱 SMTP 配置是否正确'

    def add_arguments(self, parser):
        """Register command arguments."""
        parser.add_argument(
            'recipient',
            type=str,
            help='收件人邮箱，例如 colleague@163.com',
        )

    def handle(self, *args, **options):
        """Send test email."""
        recipient = options['recipient'].strip()
        if not recipient:
            raise CommandError('请提供收件人邮箱')

        if not is_email_configured():
            raise CommandError(
                '邮件未配置：请复制 adminAPI/.env.example 为 .env，'
                '并填写 QQ 邮箱 SMTP 与 16 位授权码后重试',
            )

        try:
            send_system_email(
                subject='【管理系统】邮件发送测试',
                message=(
                    '这是一封测试邮件。\n\n'
                    '若您收到此邮件，说明 QQ 邮箱 SMTP 配置正确，'
                    '激活邮件与找回密码邮件均可正常投递。\n'
                ),
                recipient_list=[recipient],
            )
        except Exception as exc:
            raise CommandError(f'发送失败：{exc}') from exc

        self.stdout.write(
            self.style.SUCCESS(f'测试邮件已发送至 {recipient}，请查收收件箱（及垃圾箱）'),
        )
