# MoneyLog - AI 가계부

> 지출을 입력하면 Gemini AI가 카테고리를 자동 분류하고 월간 소비 패턴을 분석해주는 스마트 가계부

## 소개

MoneyLog는 지출 내역을 입력하면 AI가 자동으로 카테고리를 분류하고, 월간 소비 패턴을 분석해 절약 방법을 코칭해주는 AI 가계부 앱입니다. 반복 지출 자동 등록, 예산 관리, 리포트 등 가계부에 필요한 모든 기능을 제공합니다.

## 주요 기능

- 지출 입력 → Gemini AI 카테고리 자동 분류
- 월간 소비 패턴 분석 및 시각화
- 예산 설정 및 초과 알림
- 반복 지출 자동 등록 (월별/주별)
- 카테고리별 지출 통계
- CSV/Excel 내보내기

## 수익 구조

| 플랜 | 가격 | 월간 입력 건수 | 기능 |
|------|------|---------------|------|
| 무료 | 0원 | 월 50건 | 기본 카테고리 분류 + 월간 통계 |
| 프리미엄 | 월 4,900원 | 무제한 | 모든 기능 + AI 절약 코칭 + 데이터 내보내기 |

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | FastAPI, Python 3.11 |
| Database | SQLite (aiosqlite) |
| AI | Google Gemini API |
| 배포 | Docker, Docker Compose |

## 설치 및 실행

### 사전 요구사항

- Python 3.11+
- Docker (선택)
- Google Gemini API 키

### 로컬 실행

```bash
# 저장소 클론
git clone https://github.com/your-username/MoneyLog.git
cd MoneyLog

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 입력

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

### Docker 실행

```bash
docker-compose up -d
```

서버 실행 후 http://localhost:8000 접속

## 주요 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| `GET` | `/` | 메인 페이지 |
| `GET` | `/api/expenses` | 지출 목록 조회 |
| `POST` | `/api/expenses` | 지출 등록 (AI 자동 분류) |
| `PUT` | `/api/expenses/{id}` | 지출 수정 |
| `DELETE` | `/api/expenses/{id}` | 지출 삭제 |
| `GET` | `/api/categories` | 카테고리 목록 조회 |
| `GET` | `/api/budgets` | 예산 조회 |
| `PUT` | `/api/budgets` | 예산 설정 |
| `GET` | `/api/reports/monthly` | 월간 소비 리포트 |
| `GET` | `/api/recurring` | 반복 지출 목록 |
| `POST` | `/api/recurring` | 반복 지출 등록 |
| `GET` | `/api/exports/csv` | CSV 내보내기 (프리미엄) |

## 카테고리 목록

| 아이콘 | 카테고리 | 예시 |
|--------|----------|------|
| 🍽️ | 식비 | 마트, 편의점, 카페 |
| 🛵 | 배달 | 배달의민족, 쿠팡이츠 |
| 🚌 | 교통 | 버스, 지하철, 택시 |
| 🛍️ | 쇼핑 | 온라인쇼핑, 의류 |
| 💊 | 의료/건강 | 병원, 약국, 헬스장 |
| 🎬 | 문화/여가 | 영화, 공연, 게임 |
| 📱 | 통신 | 휴대폰 요금 |
| 🏠 | 공과금 | 전기, 수도, 가스 |
| 🔔 | 구독 | 넷플릭스, 유튜브 프리미엄 |
| ✈️ | 여행 | 항공권, 숙박 |
| 💰 | 기타 | 분류 불가 항목 |

## 환경 변수

```env
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
DATABASE_URL=sqlite+aiosqlite:///./moneylog.db
```

## 라이선스

MIT
