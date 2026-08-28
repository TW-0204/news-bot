import urllib.parse
import feedparser
import re
import sys
from datetime import datetime
import pytz

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# 언론사 영향력 및 신뢰도 티어 점수 (점수가 높을수록 우선 채택)
MEDIA_TIER_SCORES = {
    # 1티어 (주요 일간지, 경제지, 지상파/공영통신)
    "매일경제": 100, "한국경제": 100, "조선일보": 100, "중앙일보": 100, "동아일보": 100,
    "서울경제": 95, "연합뉴스": 95, "SBS Biz": 95, "ZDNet Korea": 95, "한국일보": 90,
    "경향신문": 90, "한겨레": 90, "KBS": 90, "MBC": 90, "SBS": 90, "YTN": 90,
    
    # 2티어 (주요 경제/온라인 통신사)
    "머니투데이": 85, "이데일리": 85, "헤럴드경제": 85, "파이낸셜뉴스": 85, 
    "아시아경제": 80, "뉴시스": 80, "뉴스1": 80, "디지털타임스": 80, "전자신문": 80,
    
    # 3티어 (전문지 및 주요 인터넷 언론)
    "데일리안": 70, "시사오늘": 70, "이투데이": 70, "비즈워치": 70, "더벨": 70,
    "아이뉴스24": 70, "하우징헤럴드": 65, "대한경제": 65, "프레시안": 60, "신아일보": 60
}

CATEGORY_CONFIG = {
    "은행/카드": {
        "queries": [
            "은행 주담대 금리",
            "금융지주 회장 연임 은행",
            "카드사 연체율 수수료",
            "5대은행 가계대출 집단대출",
            "시중은행 예금 금리 인하"
        ],
        "count": 4
    },
    "보험": {
        "queries": [
            "보험사 상반기 순이익 투자손익",
            "보험사 GA 정보보안 협의체",
            "보험사 퇴직연금 디폴트옵션",
            "생명보험 손해보험 이사회 의결",
            "실손보험 청구 간소화 보험금"
        ],
        "count": 4
    },
    "증권": {
        "queries": [
            "증권사 인수 합병 토스 미래에셋",
            "증권사 반대매매 빚투 미수금",
            "유상증자 주식 발행 단기사채",
            "자사주 소각 배당 주주환원 밸류업",
            "증권사 부동산 PF 충당금"
        ],
        "count": 4
    },
    "디지털 금융": {
        "queries": [
            "디지털자산기본법 가상자산 대주주 지분",
            "스테이블코인 신한금융 비자 미래금융",
            "토큰증권 STO 법제화 인프라",
            "인터넷전문은행 케이뱅크 토스뱅크 카카오뱅크",
            "CBDC 중앙은행 디지털화폐 테스트"
        ],
        "count": 2
    },
    "부동산": {
        "queries": [
            "지역주택조합 사업승인 토지소유권",
            "재개발 재건축 1+1 분양 조합원",
            "노후계획도시 정비 선도지구 분당 인천",
            "기업 부동산 사옥 유동화 매각 리츠",
            "아파트 분양가 상한제 청약 경쟁률"
        ],
        "count": 4
    }
}

def get_media_score(source_name):
    """
    언론사명의 티어 점수를 반환합니다.
    """
    clean_source = source_name.strip()
    for name, score in MEDIA_TIER_SCORES.items():
        if name in clean_source:
            return score
    # 등록되지 않은 군소 언론사 기본 점수
    return 30

def extract_keywords(title):
    """
    기사 제목에서 핵심 형태소/키워드(2글자 이상)를 추출합니다.
    """
    # 불필요한 따옴표, 괄호, 특수기호 제거
    cleaned = re.sub(r'[\'\"\[\]\(\)<>…·,\.\!\?]', ' ', title)
    # 조사 및 불용어성 단어
    stopwords = {"등", "및", "위해", "통해", "지난", "올해", "내달", "전년비", "대비", "가장", "최대", "최고", "논란", "속도"}
    
    words = []
    for token in cleaned.split():
        token = token.strip()
        if len(token) >= 2 and token not in stopwords:
            words.append(token)
    return set(words)

def is_same_topic(title1, title2):
    """
    두 기사가 완전히 동일한 사건/주제/기업 이슈를 다루는지 정밀하게 판별합니다.
    """
    kw1 = extract_keywords(title1)
    kw2 = extract_keywords(title2)
    
    if not kw1 or not kw2:
        return False
        
    intersection = kw1.intersection(kw2)
    union = kw1.union(kw2)
    
    jaccard_sim = len(intersection) / len(union) if union else 0
    
    # 조건 1: Jaccard 유사도가 0.25 이상인 경우 (유사도 기준 강화)
    if jaccard_sim >= 0.25:
        return True
        
    # 조건 2: 공통 키워드가 2개 이상인 경우
    if len(intersection) >= 2:
        return True

    # 조건 3: 핵심 고유명사/기업명(예: 미래에셋, 카카오, 토스, 신한, 현대차 등)이 일치하고 공통 단어가 있을 때
    for word in intersection:
        if len(word) >= 3 or any(char.isdigit() for char in word):
            # 3글자 이상 고유단어가 일치하면 동일 토픽으로 간주
            return True
            
    return False

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
    
    title = title.replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return title, source

SPAM_KEYWORDS = [
    "토토", "꽁머니", "카지노", "바카라", "파워볼", "홀덤", "슬롯", "성인", "사설", "먹튀", "지속적 통합 핵심 전략"
]

def is_spam(title, source):
    for spam in SPAM_KEYWORDS:
        if spam in title or spam in source:
            return True
    return False

def fetch_category_news(category_name, queries, count=4):
    """
    1. 카테고리별 후보 기사를 넉넉히 수집 (20~30건)
    2. 언론사 티어 점수 기반 정렬 (스팸/불량 매체 자동 제외)
    3. 토픽 유사도 클러스터링을 통해 중복 주제를 제거하고 최고 언론사 1개만 선별
    """
    candidates = []
    seen_urls = set()

    # 1. 여러 세부 쿼리로 다양한 주제의 후보군 수집
    for q in queries:
        encoded_query = urllib.parse.quote(f"{q} when:1d")
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        
        feed = feedparser.parse(rss_url)
        for entry in feed.entries:
            title, source = clean_title_and_source(entry.title)
            link = entry.link
            
            if link in seen_urls or is_spam(title, source):
                continue
            seen_urls.add(link)
            
            score = get_media_score(source)
            # 기본 점수가 60점 이상인 신뢰할 수 있는 언론사 우선
            candidates.append({
                "title": title,
                "source": source,
                "link": link,
                "score": score
            })

    # 2. 메이저 언론사 점수가 높은 순으로 정렬 (동일 점수면 먼저 수집된 최신순)
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 3. 토픽 중복 제거 (Greedy Selection)
    # 가장 높은 점수의 언론사 기사부터 담되, 이미 담긴 기사와 주제가 겹치면 제외
    selected_articles = []
    
    for candidate in candidates:
        # 이미 선택된 기사들과 같은 주제인지 비교
        duplicate_topic = False
        for selected in selected_articles:
            if is_same_topic(candidate["title"], selected["title"]):
                duplicate_topic = True
                break
        
        if not duplicate_topic:
            selected_articles.append(candidate)
            if len(selected_articles) >= count:
                break

    return selected_articles[:count]

def get_daily_briefing():
    """
    전체 카테고리의 뉴스를 수집하여 딕셔너리로 반환합니다.
    """
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    # YY/M/D 형식 (예: 26/8/28)
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
