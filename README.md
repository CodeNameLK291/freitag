# Freitag

Exchange 메일 서버 연동 시스템 - AI 개발 루프 시스템이 적용된 Python 프로젝트입니다.

## 🤖 AI 개발 루프란?

1. **코딩 AI**: 코드 작성 → PR 생성
2. **자동 테스트**: GitHub Actions가 자동 실행
3. **리뷰 AI**: 결과 분석 → PR에 피드백
4. **코딩 AI**: 피드백 확인 → 수정 → 재테스트
5. 반복...

## 📋 프로젝트 개요

Exchange 메일 서버에 연결하여 메일을 읽어오는 Python 라이브러리입니다.

### 주요 기능

- Exchange 서버 연결 및 인증
- 받은편지함 메일 조회
- 메일 정보 추출 (제목, 발신자, 본문, 첨부파일 등)
- 메일함 폴더 목록 조회
- 환경 변수 기반 설정 관리
- 구조화된 로깅

## 🚀 시작하기


### 요구사항

- Python 3.8 이상
- Exchange 서버 접근 권한

### 설치

```bash
# 저장소 클론
git clone https://github.com/CodeNameLK291/freitag.git
cd freitag

# 의존성 설치
pip install -r requirements.txt
```

### 설정

```bash
# 환경 변수 파일 생성
cp .env.example .env

# .env 파일을 편집하여 실제 Exchange 서버 정보 입력
# EXCHANGE_SERVER, EXCHANGE_DOMAIN, EXCHANGE_USERNAME, EXCHANGE_PASSWORD
```

### 사용 예제

```python
from src.exchange_client import ExchangeClient

# 클라이언트 생성 및 연결
client = ExchangeClient()
client.connect()

# 최근 메일 가져오기
messages = client.get_inbox_messages(limit=10, days_back=7)

for msg in messages:
    print(f"제목: {msg['subject']}")
    print(f"발신자: {msg['sender']}")
    print(f"수신일: {msg['datetime_received']}")

# 연결 종료
client.disconnect()
```

자세한 사용 예제는 `examples/example_usage.py`를 참조하세요.

## 🖥️ GUI 사용법

### 설치
```bash
pip install -r requirements.txt
```

### 실행
```bash
python main.py
```

### 설정
1. 프로그램 실행
2. "설정" 버튼 클릭
3. Exchange 서버 정보 입력:
   - Exchange 서버: outlook.hmc.co.kr
   - 도메인: autos
   - 사용자명: your_username
   - 비밀번호: your_password
4. "저장" 클릭

### 사용법
1. "연결" 버튼 클릭하여 서버 연결
2. "새로고침" 버튼으로 메일 가져오기
3. 왼쪽 목록에서 메일 선택
4. 오른쪽에서 메일 내용 확인

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest tests/

# 커버리지 포함 테스트
pytest tests/ --cov=src --cov-report=term-missing

# 현재 테스트 커버리지: 100%
```

## 🔍 코드 품질

```bash
# Black 포맷팅 확인
black --check src/ tests/

# Flake8 린팅
flake8 src/ tests/
```

## 📦 프로젝트 구조

```
freitag/
├── .github/workflows/    # GitHub Actions 워크플로우
├── src/                  # 소스 코드
│   ├── ui/              # PyQt5 GUI
│   │   ├── main_window.py
│   │   └── settings_dialog.py
│   ├── utils/           # 유틸리티
│   │   ├── config.py
│   │   └── logger.py
│   ├── exchange_client.py
│   └── __init__.py
├── tests/               # 테스트 코드
│   ├── test_ui/
│   │   └── test_main_window.py
│   ├── test_config.py
│   ├── test_exchange_client.py
│   └── test_logger.py
├── examples/
│   └── example_usage.py
├── main.py             # GUI 실행 파일
├── requirements.txt     # Python 의존성
├── .env.example        # 환경 변수 예시
└── README.md           # 프로젝트 문서
```

## 🔐 보안

- `.env` 파일은 절대 커밋하지 마세요
- `.gitignore`에 `.env`가 포함되어 있습니다
- 실제 비밀번호는 `.env` 파일에만 저장하세요

## 🔄 개발 워크플로우

1. 새 기능 개발 시 브랜치 생성
2. 코드 작성 및 커밋
3. PR 생성
4. GitHub Actions가 자동으로 테스트 실행
5. 결과 확인 및 수정
6. 모든 테스트 통과 시 머지

## 👤 작성자

CodeNameLK291

## 📝 라이선스

MIT License
