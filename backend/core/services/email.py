import logging
from typing import Optional

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import settings

logger = logging.getLogger(__name__)


async def send_email(
    to: str,
    subject: str,
    html: str,
    from_addr: Optional[str] = None,
) -> bool:
    """发送 HTML 邮件"""
    if not settings.smtp_user or not settings.smtp_pass:
        logger.warning("SMTP 未配置，跳过邮件发送")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = from_addr or settings.smtp_from or settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject

    html_part = MIMEText(html, "html", "utf-8")
    msg.attach(html_part)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_pass,
            use_tls=settings.smtp_port == 465,
            start_tls=settings.smtp_port == 587,
        )
        logger.info(f"邮件已发送至 {to}")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False


async def send_verification_email(email: str, code: str) -> bool:
    """发送验证码邮件"""
    html = f"""
    <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">AI 调研平台 - 验证码</h2>
        <p style="color: #666;">您的验证码是：</p>
        <div style="background: #f5f5f5; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; color: #333; letter-spacing: 8px;">{code}</span>
        </div>
        <p style="color: #999; font-size: 14px;">验证码 5 分钟内有效。如果不是您本人操作，请忽略此邮件。</p>
    </div>
    """
    return await send_email(email, "AI 调研平台 - 验证码", html)


async def send_reset_password_email(email: str, code: str) -> bool:
    """发送密码重置邮件"""
    html = f"""
    <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #333;">AI 调研平台 - 密码重置</h2>
        <p style="color: #666;">您的密码重置码是：</p>
        <div style="background: #f5f5f5; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0;">
            <span style="font-size: 32px; font-weight: bold; color: #333; letter-spacing: 8px;">{code}</span>
        </div>
        <p style="color: #999; font-size: 14px;">重置码 10 分钟内有效。如果您没有请求重置密码，请忽略此邮件。</p>
    </div>
    """
    return await send_email(email, "AI 调研平台 - 密码重置", html)
