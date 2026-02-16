# Freitag

AI 개발 루프 시스템이 적용된 Python 프로젝트입니다.

## 🤖 AI 개발 루프란?

1. **코딩 AI**: 코드 작성 → PR 생성
2. **자동 테스트**: GitHub Actions가 자동 실행
3. **리뷰 AI**: 결과 분석 → PR에 피드백
4. **코딩 AI**: 피드백 확인 → 수정 → 재테스트
5. 반복...

## 🚀 시작하기

### 설치
```bash
pip install -r requirements.txt
```

### 테스트 실행
```bash
pytest tests/
```

### 코드 포맷팅
```bash
black src/ tests/
```

### 린팅
```bash
flake8 src/ tests/
```

## 📁 프로젝트 구조

```
freitag/
├── .github/workflows/    # GitHub Actions 워크플로우
├── src/                  # 소스 코드
├── tests/               # 테스트 코드
├── requirements.txt     # Python 의존성
├── pytest.ini          # pytest 설정
└── README.md           # 프로젝트 문서
```

## 🔄 개발 워크플로우

1. 새 기능 개발 시 브랜치 생성
2. 코드 작성 및 커밋
3. PR 생성
4. GitHub Actions가 자동으로 테스트 실행
5. 결과 확인 및 수정
6. 모든 테스트 통과 시 머지

## 📝 라이선스

MIT License