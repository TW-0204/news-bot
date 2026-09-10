# 📰 금융 & 부동산 데일리 뉴스 자동 발송 봇

매일 아침 금융 5대 카테고리(`은행/카드`, `보험`, `증권`, `디지털 금융`, `부동산`)의 주요 뉴스를 자동 수집하여 지정된 양식으로 네이버 메일을 발송하는 GitHub Actions 자동화 봇입니다.

---

## 📌 출력 양식 예시

```text
금융데일리: 26/8/27

[은행/카드]
금융지주 회장 3연임 금지 … 법으로 명문화 안 하기로 <매일경제>
https://news.google.com/...

[보험]
상반기 보험사 순이익 9조138억…투자손익 개선에 전년비 13%↑ <뉴시스>
https://news.google.com/...

[증권]
미래에셋·토스, 日 증권사 인수한다 <한국경제>
https://news.google.com/...

[디지털 금융]
신한금융, 비자와 스테이블코인 등 '미래금융' 협력 <연합뉴스>
https://news.google.com/...

[부동산]
지역주택조합 사업승인 80%… 서울 9곳 개발 ‘청신호’ <매일경제>
https://news.google.com/...

*위 내용은 국내외 언론사 뉴스 등을 인용한 자료로 별도의 승인 절차 없이 제공합니다.
```

---

## 🚀 설정 및 배포 방법 (3단계)

### 1단계: 네이버 메일 SMTP 설정하기

1. [네이버 메일](https://mail.naver.com/)에 접속합니다.
2. 좌측 사이드바 하단의 **환경설정(톱니바퀴 아이콘)**을 클릭합니다.
3. 상단 탭에서 **[POP3/IMAP 설정]** ➔ **[POP3/SMTP 설정]**을 선택합니다.
4. **POP3/SMTP 사용**을 **[사용함]**으로 체크하고 하단의 **[확인]**을 누릅니다.
5. *(중요)* 네이버 **2단계 인증**을 사용 중이신 경우:
   - [네이버 내정보] ➔ [보안설정] ➔ [2단계 인증] ➔ **[애플리케이션 비밀번호 생성]**에서 `종류: 기타, 이름: 뉴스봇`을 입력하여 생성된 비밀번호를 발송용 비밀번호로 사용해야 합니다.

---

### 2단계: GitHub에 코드 올리기

본인의 개인 GitHub 계정에서 새로운 저장소(Private 또는 Public)를 만든 후 코드를 업로드합니다.

```bash
cd finance-news-bot
git init
git add .
git commit -m "feat: 금융 및 부동산 데일리 뉴스 자동 발송 봇 구현"
git branch -M main
git remote add origin https://github.com/당신의깃허브아이디/저장소이름.git
git push -u origin main
```

---

### 3단계: GitHub Secrets(보안 환경변수) 등록하기

GitHub Actions가 안전하게 네이버 메일을 보낼 수 있도록 인증 정보를 등록합니다.

1. GitHub 저장소 상단의 **[Settings]** 탭으로 이동합니다.
2. 좌측 메뉴에서 **[Secrets and variables]** ➔ **[Actions]**를 클릭합니다.
3. **[New repository secret]** 버튼을 눌러 다음 3가지 항목을 각각 추가합니다:

| Name (이름) | Secret Value (값) | 설명 |
| :--- | :--- | :--- |
| `NAVER_USER` | `your_naver_id@naver.com` | 발송할 네이버 계정 아이디/이메일 |
| `NAVER_PASS` | `네이버 비밀번호` 또는 `앱 비밀번호` | 네이버 로그인 비밀번호 |
| `RECEIVER_EMAIL` | `recipient_email@domain.com` | 뉴스를 수신할 이메일 주소 |

---

## ⏰ 실행 스케줄 및 수동 테스트

- **자동 실행**: 매일 한국 시간(KST) **오전 07:37**에 자동으로 동작합니다.
- **수동 테스트**:
  - GitHub 저장소의 **[Actions]** 탭 ➔ 좌측의 **[Daily Finance News Mailer]** 워크플로우 클릭 ➔ 우측 **[Run workflow]** 버튼을 클릭하면 즉시 테스트 메일이 발송됩니다.
