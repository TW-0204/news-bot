import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

def send_email(subject, text_content):
    """
    네이버 SMTP를 사용하여 메일을 발송합니다.
    """
    smtp_user = os.getenv("NAVER_USER", "401x1127@naver.com")
    smtp_pass = os.getenv("NAVER_PASS")  # 네이버 비밀번호 또는 2단계 인증 애플리케이션 비밀번호
    recipient = os.getenv("RECEIVER_EMAIL", "401x1127@naver.com")

    if not smtp_pass:
        raise ValueError("환경변수 NAVER_PASS 가 설정되지 않았습니다.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = recipient

    # 순수 텍스트 본문
    part_text = MIMEText(text_content, "plain", "utf-8")
    msg.attach(part_text)

    # 이메일 클라이언트에서 가독성을 높이기 위한 간단한 HTML 버전도 함께 첨부
    html_lines = []
    for line in text_content.split("\n"):
        line_clean = line.strip()
        if line_clean.startswith("금융데일리:"):
            html_lines.append(f"<h2 style='color:#1e3a8a; margin-bottom:15px;'>{line_clean}</h2>")
        elif line_clean.startswith("[") and line_clean.endswith("]"):
            html_lines.append(f"<h3 style='color:#0369a1; border-bottom:1px solid #e2e8f0; padding-bottom:5px; margin-top:20px;'>{line_clean}</h3>")
        elif line_clean.startswith("http://") or line_clean.startswith("https://"):
            html_lines.append(f"<p style='margin-top:2px; margin-bottom:12px;'><a href='{line_clean}' target='_blank' style='color:#2563eb; font-size:13px; text-decoration:underline;'>{line_clean}</a></p>")
        elif line_clean.startswith("*위 내용"):
            html_lines.append(f"<p style='color:#64748b; font-size:12px; margin-top:30px;'>{line_clean}</p>")
        elif line_clean:
            html_lines.append(f"<p style='margin-bottom:2px; font-weight:500; font-size:15px; color:#1e293b;'>{line_clean}</p>")
        else:
            html_lines.append("<div style='height:4px;'></div>")

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 680px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
        {''.join(html_lines)}
    </div>
    """
    part_html = MIMEText(html_content, "html", "utf-8")
    msg.attach(part_html)

    # 네이버 SMTP 포트 465 (SSL) 연결
    with smtplib.SMTP_SSL("smtp.naver.com", 465) as server:
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)

    print(f"[{recipient}] 메일 발송 완료!")

if __name__ == "__main__":
    # 테스트용
    pass
