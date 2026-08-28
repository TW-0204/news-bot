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
    "조선비즈": 90,
    
    # 2티어 (주요 경제/온라인 통신사)
    "머니투데이": 85, "이데일리": 85, "헤럴드경제": 85, "파이낸셜뉴스": 85, 
    "아시아경제": 80, "뉴시스": 80, "뉴스1": 80, "디지털타임스": 80, "전자신문": 80,
    "뉴스핌": 80, "세계일보": 80, "국민일보": 80,
    
    # 3티어 (전문지 및 주요 인터넷 언론)
    "데일리안": 70, "시사오늘": 70, "이투데이": 70, "비즈워치": 70, "더벨": 70,
    "아이뉴스24": 70, "하우징헤럴드": 65, "대한경제": 65, "MTN": 65, "MTN뉴스": 65,
    "프레시안": 60, "신아일보": 60
}

# 슬롯 기반 전용 세부 테마 (한 카테고리 내에서 4개 주제가 100% 분리되도록 구성)
CATEGORY_THEMES = {
    "은행/카드": [
        # 슬롯 1: 기준금리 / 통화정책 / 거시경제
        {
            "theme": "기준금리/통화정책",
            "queries": ["한국은행 기준금리 인상 동결", "금융통화위원회 금리", "시중은행 예금 금리 인하 인상"]
        },
        # 슬롯 2: 금융지주 인사 / 지배구조 / 실적
        {
            "theme": "금융지주/지배구조/인사",
            "queries": ["금융지주 회장 후보 3연임", "KB금융 신한금융 하나금융 우리금융 이사회", "금융지주 실적 순이익"]
        },
        # 슬롯 3: 금융당국 검사 / ELS / 규제 / 내부통제
        {
            "theme": "금융감독/검사/내부통제",
            "queries": ["금감원 본검사 ELS 지배구조", "금융감독원 은행 제재 착수", "은행 내부통제 횡령 방지"]
        },
        # 슬롯 4: 카드사 / 인터넷은행 / 가계대출 / 노사
        {
            "theme": "카드/인터넷은행/대출/노사",
            "queries": ["카카오뱅크 토스뱅크 케이뱅크 파업", "카드사 연체율 가맹점 수수료", "5대은행 가계대출 집단대출 목표치"]
        }
    ],
    "보험": [
        # 슬롯 1: 대출채권 / 자산건전성 / K-ICS
        {
            "theme": "자산건전성/대출채권",
            "queries": ["보험사 대출채권 잔액 기업대출 건전성", "보험사 연체율 건전성 K-ICS", "보험사 순이익 투자손익"]
        },
        # 슬롯 2: 자산운용 / 투자 / 퇴직연금
        {
            "theme": "자산운용/투자/퇴직연금",
            "queries": ["보험사 돈 굴리는 자산운용", "보험사 DB형 퇴직연금 디폴트옵션", "생명보험 손해보험 투자손익"]
        },
        # 슬롯 3: 신사업 / 시니어 / 헬스케어 / 제도
        {
            "theme": "신사업/제도개선/GA",
            "queries": ["보험사 시니어 헬스케어 신사업", "보험사 GA 정보보안 협의체", "상장 보험사 이사회 반대"]
        },
        # 슬롯 4: 보험 상품 / 주담대 / 실손보험
        {
            "theme": "상품/주담대/여신",
            "queries": ["삼성화재 보험사 주담대 재개", "실손보험 청구 간소화 보험금", "생보사 손보사 신계약 보험료"]
        }
    ],
    "증권": [
        # 슬롯 1: 증권사 M&A / 글로벌 / 인수
        {
            "theme": "M&A/글로벌",
            "queries": ["미래에셋 토스 증권사 인수", "증권사 해외 법인 M&A", "증권사 합병 인수 검토"]
        },
        # 슬롯 2: 토큰증권 STO / 신기술 인프라
        {
            "theme": "토큰증권/인프라",
            "queries": ["토큰증권 코스콤 증권사 공동 발행소", "STO 토큰증권 인프라 구축", "증권사 디지털자산 STO"]
        },
        # 슬롯 3: IPO / 주식발행 / 유상증자 / 밸류업
        {
            "theme": "IPO/주식발행/밸류업",
            "queries": ["증권사 IPO 실사 상장", "기업 유상증자 주식 발행 단기사채", "증권사 자사주 소각 배당 주주환원 밸류업"]
        },
        # 슬롯 4: 금융투자상품 / IMA / 발행어음 / 빚투
        {
            "theme": "상품/IMA/반대매매/리스크",
            "queries": ["증권사 IMA 운용수익 발행어음", "증권사 반대매매 빚투 미수금", "증권사 단기사채 PF 충당금"]
        }
    ],
    "디지털 금융": [
        # 슬롯 1: 가상자산 / 거래소 / 대주주 지분 규제
        {
            "theme": "가상자산/규제/법안",
            "queries": ["디지털자산기본법 가상자산 대주주 지분 20%", "가상자산거래소 지분 의결권 제한", "금융위 1거래소 1은행 가상자산"]
        },
        # 슬롯 2: 스테이블코인 / 미래금융 / 핀테크
        {
            "theme": "스테이블코인/미래금융",
            "queries": ["신한금융 비자 스테이블코인 미래금융", "중앙은행 디지털화폐 CBDC 테스트", "인터넷전문은행 핀테크 혁신금융"]
        }
    ],
    "부동산": [
        # 슬롯 1: 정비사업 / 재개발 / 재건축 / 지주택
        {
            "theme": "정비사업/재개발재건축",
            "queries": ["지역주택조합 사업승인 토지소유권", "노량진 재개발 1+1 분양 조합원 갈등", "재건축 공사비 조합 시공사"]
        },
        # 슬롯 2: 노후계획도시 / 선도지구 / 분양
        {
            "theme": "노후계획도시/선도지구/분양",
            "queries": ["노후계획도시 정비 선도지구 인천 분당", "아파트 분양가 상한제 청약 경쟁률", "공공분양 사전청약"]
        },
        # 슬롯 3: 기업 부동산 / 사옥 유동화 / 리츠
        {
            "theme": "기업부동산/사옥유동화/리츠",
            "queries": ["기업 부동산 사옥 유동화 매각 리츠", "대한제당 현대차 삼성생명 부동산", "상업용 부동산 오피스 빌딩 매각"]
        },
        # 슬롯 4: 부동산 정책 / 임대주택 / 대출
        {
            "theme": "정책/임대주택/대출규제",
            "queries": ["성남 재개발 임대주택 의무비율", "국토부 주택법 개정안", "디딤돌대출 가계대출 한도 축소"]
        }
    ]
}

def get_media_score(source_name):
    clean_source = source_name.strip()
    for name, score in MEDIA_TIER_SCORES.items():
        if name in clean_source:
            return score
    return 30

def extract_keywords(title):
    cleaned = re.sub(r'[\'\"\[\]\(\)<>…·,\.\!\?]', ' ', title)
    stopwords = {"등", "및", "위해", "통해", "지난", "올해", "내달", "전년비", "대비", "가장", "최대", "최고", "논란", "속도"}
    words = []
    for token in cleaned.split():
        token = token.strip()
        if len(token) >= 2 and token not in stopwords:
            words.append(token)
    return set(words)

def is_same_topic(title1, title2):
    kw1 = extract_keywords(title1)
    kw2 = extract_keywords(title2)
    if not kw1 or not kw2:
        return False
    intersection = kw1.intersection(kw2)
    union = kw1.union(kw2)
    jaccard_sim = len(intersection) / len(union) if union else 0
    if jaccard_sim >= 0.25:
        return True
    if len(intersection) >= 2:
        return True
    for word in intersection:
        if len(word) >= 3 or any(char.isdigit() for char in word):
            return True
    return False

def clean_title_and_source(raw_title):
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

def fetch_single_slot_news(queries, used_articles):
    """
    하나의 슬롯(서브 테마)에 대해 가장 점수가 높은 메이저 언론사 기사 1개를 선별합니다.
    """
    candidates = []
    
    # 1. 24시간 이내 기사 검색
    for q in queries:
        encoded_query = urllib.parse.quote(f"{q} when:1d")
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            title, source = clean_title_and_source(entry.title)
            link = entry.link
            if is_spam(title, source):
                continue
            score = get_media_score(source)
            candidates.append({
                "title": title,
                "source": source,
                "link": link,
                "score": score
            })

    # 24시간 이내 기사가 부족하면 7일 이내 기사로 폴백 검색
    if len(candidates) < 2:
        for q in queries:
            encoded_query = urllib.parse.quote(f"{q} when:7d")
            rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                title, source = clean_title_and_source(entry.title)
                link = entry.link
                if is_spam(title, source):
                    continue
                score = get_media_score(source)
                candidates.append({
                    "title": title,
                    "source": source,
                    "link": link,
                    "score": score
                })

    # 메이저 언론사 점수 높은 순 정렬
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # 이미 선택된 기사들과 중복되지 않는 최상위 기사 1개 선택
    for cand in candidates:
        is_dup = False
        for used in used_articles:
            if cand["link"] == used["link"] or is_same_topic(cand["title"], used["title"]):
                is_dup = True
                break
        if not is_dup:
            return cand
            
    return candidates[0] if candidates else None

def get_daily_briefing():
    """
    슬롯별 전용 테마를 순회하며 완전히 분리된 다양한 뉴스를 수집합니다.
    """
    kst = pytz.timezone('Asia/Seoul')
    now = datetime.now(kst)
    date_header = f"{now.year % 100}/{now.month}/{now.day}"

    news_data = {
        "date_str": date_header,
        "categories": {}
    }

    all_used_articles = []

    for cat_name, slots in CATEGORY_THEMES.items():
        cat_articles = []
        for slot_info in slots:
            chosen = fetch_single_slot_news(slot_info["queries"], all_used_articles)
            if chosen:
                cat_articles.append(chosen)
                all_used_articles.append(chosen)
        news_data["categories"][cat_name] = cat_articles

    return news_data

def format_news_text(news_data):
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
