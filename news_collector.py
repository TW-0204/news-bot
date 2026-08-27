import urllib.parse
import feedparser
import re
import sys
from datetime import datetime
import pytz

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CATEGORY_CONFIG = {
    "은행/카드": {
        "queries": [
            "은행 주담대 금리",
            "금융지주 은행 카드",
            "5대은행 가계대출"
        ],
        "count": 4
    },
    "보험": {
        "queries": [
            "보험사 순이익",
            "생명보험 손해보험 GA",
            "보험사 퇴직연금"
        ],
        "count": 4
    },
    "증권": {
        "queries": [
            "증권사 주식 발행",
            "증권 인수 주주환원 자사주",
            "증권사 반대매매 채권"
        ],
        "count": 4
    },
    "디지털 금융": {
        "queries": [
            "디지털자산기본법 가상자산",
            "스테이블코인 디지털금융",
            "인터넷은행 핀테크 토큰증권"
        ],
        "count": 2
    },
    "부동산": {
        "queries": [
            "지역주택조합 재개발 재건축",
            "아파트 분양 조합원",
            "노후계획도시 선도지구 부동산"
        ],
        "count": 4
    }
}

def clean_title_and_source(raw_title):
    """
    Google News RSS 제목 형식: '기사 제목 - 언론사명'
    원하는 형식: '기사 제목 <언론사명>'
    """
    if " - " in raw_title:
        parts = raw_title.rsplit(" - ", 1)
        title = parts[0].strip()
        source = parts[1].strip()
    else:
        title = raw_title.strip()
        source = "언론사"
    
    # HTML 특수문자나 불필요한 따옴표 정리
    title = title.replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return title, source

def fetch_category_news(category_name, queries, count=4):
    """
    구글 뉴스 RSS를 통해 카테고리별 최신 24시간 뉴스를 수집합니다.
    """
    collected = []
    seen_titles = set()

    for q in queries:
        encoded_query = urllib.parse.quote(f"{q} when:1d")
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title, source = clean_title_and_source(entry.title)
            
            # 중복 기사 필터링 (간단한 키워드/제목 기반)
            title_key = re.sub(r'[^가-힣a-zA-Z0-9]', '', title)[:15]
            if title_key in seen_titles:
                continue
            
            seen_titles.add(title_key)
            collected.append({
                "title": title,
                "source": source,
                "link": entry.link
            })
            
            if len(collected) >= count:
                break
        
        if len(collected) >= count:
            break
            
    return collected[:count]

def get_daily_briefing():
    """
    전체 카테고리의 뉴스를 수집하여 딕셔너리로 반환합니다.
    """
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    # YY/M/D 형식 (예: 26/8/27)
    date_header = f"{now.year % 100}/{now.month}/{now.day}"

    news_data = {
        "date_str": date_header,
        "categories": {}
    }

    for cat_name, config in CATEGORY_CONFIG.items():
        articles = fetch_category_news(cat_name, config["queries"], config["count"])
        news_data["categories"][cat_name] = articles

    return news_data

def format_news_text(news_data):
    """
    사용자가 요청한 텍스트 포맷으로 변환합니다.
    """
    lines = [f"금융데일리: {news_data['date_str']}", ""]
    
    for cat_name, articles in news_data["categories"].items():
        lines.append(f"[{cat_name}]")
        lines.append("")
        for art in articles:
            lines.append(f"{art['title']} <{art['source']}>")
            lines.append(art['link'])
            lines.append("")
            
    lines.append("*위 내용은 국내외 언론사 뉴스 등을 인용한 자료로 별도의 승인 절차 없이 제공합니다.")
    return "\n".join(lines)

if __name__ == "__main__":
    data = get_daily_briefing()
    print(format_news_text(data))
