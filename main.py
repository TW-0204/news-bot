import sys
from news_collector import get_daily_briefing, format_news_text
from mailer import send_email

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def main():
    print(">>> 1. 금융 & 부동산 뉴스 수집 중...")
    news_data = get_daily_briefing()
    
    total_articles = sum(len(arts) for arts in news_data["categories"].values())
    print(f"수집 완료: 총 {total_articles}개 기사")
    
    email_body = format_news_text(news_data)
    subject = f"금융데일리: {news_data['date_str']}"
    
    print("\n--- [생성된 브리핑 내용] ---")
    print(email_body)
    print("-----------------------------\n")
    
    print(">>> 2. 이메일 발송 중...")
    try:
        send_email(subject, email_body)
        print(">>> 모든 작업이 성공적으로 완료되었습니다.")
    except Exception as e:
        print(f">>> 이메일 발송 실패: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
