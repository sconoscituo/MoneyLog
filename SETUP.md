# MoneyLog - AI 가계부 서비스

## 필요한 API 키 및 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 (지출 분석/조언용, 선택사항) | https://aistudio.google.com/app/apikey |
| `SECRET_KEY` | 앱 시크릿 키 (임의 문자열) | - |
| `DATABASE_URL` | 데이터베이스 연결 URL (기본: SQLite) | - |
| `APP_ENV` | 실행 환경 (`development` / `production`) | - |

## GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 (선택사항) |
| `SECRET_KEY` | 앱 시크릿 키 |

## 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/MoneyLog.git
cd MoneyLog

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 아래 항목 입력:
# SECRET_KEY=your_random_secret_key
# GEMINI_API_KEY=your_gemini_api_key (선택사항)

# 5. 서버 실행
uvicorn app.main:app --reload
```

서버 기동 후 http://localhost:8000 에서 웹 UI를, http://localhost:8000/docs 에서 API 문서를 확인할 수 있습니다.

## Docker로 실행

```bash
docker-compose up --build
```

## 주요 기능 사용법

### 수입/지출 기록
- 수입과 지출 내역을 카테고리별로 기록합니다.
- 날짜, 금액, 카테고리, 메모를 함께 저장할 수 있습니다.

### 통계 및 리포트
- 월간/연간 지출 통계를 카테고리별로 시각화합니다.
- 예산 대비 지출 현황을 확인할 수 있습니다.

### Excel 내보내기
- `openpyxl`을 사용해 가계부 데이터를 Excel(.xlsx) 파일로 내보낼 수 있습니다.

### PDF 리포트
- `WeasyPrint`를 사용해 월간 재정 리포트를 PDF로 생성합니다.
- PDF 생성을 위해 시스템에 WeasyPrint 의존 라이브러리가 필요합니다:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0
  ```

### AI 지출 분석 (선택사항)
- `GEMINI_API_KEY` 설정 시 AI가 소비 패턴을 분석하고 절약 방법을 제안합니다.
- API 키 없이도 기본 가계부 기능은 정상 동작합니다.

## 프로젝트 구조

```
MoneyLog/
├── app/
│   ├── config.py       # 환경변수 설정
│   ├── database.py     # DB 연결 관리
│   ├── main.py         # FastAPI 앱 진입점
│   ├── models/         # SQLAlchemy 모델
│   ├── routers/        # API 라우터
│   ├── schemas/        # Pydantic 스키마
│   ├── services/       # 비즈니스 로직
│   ├── static/         # 정적 파일 (CSS, JS)
│   └── templates/      # Jinja2 HTML 템플릿
├── tests/
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
