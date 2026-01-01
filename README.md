# 🚀 새 AI를 위한 프로젝트 인수인계 프롬프트

## 프로젝트 소개

"지금부터 새로운 프로젝트 개발을 도와줘. 아래는 현재까지 완료된 백엔드 엔진의 구조와 상태야."

---

## 1. 프로젝트 개요

**제목:** FastAPI + Git + Whoosh 기반 노트 관리 시스템 PoC 인수인계

- **목적:** Git 기반의 마크다운 노트 관리 시스템 PoC (저장, 버전 관리, 검색 기능)
- **핵심 스택:**
    - Python 3.12
    - FastAPI
    - SQLAlchemy (SQLite)
    - PyKomoran (한글 형태소 분석)
    - Whoosh (전문 검색 엔진)
    - GitPython

---

## 2. 현재 구현된 핵심 로직

### 데이터 저장

사용자가 노트를 저장하면 다음 프로세스가 진행됨:

1. `.md` 파일로 로컬 저장
2. Git Commit 수행
3. SQLite에 메타데이터(제목, 마지막 해시, 수정자) 저장

### 검색 엔진

- Whoosh를 활용하며, `KoEnTokenizer`를 직접 구현해 한영 혼용 및 복합 명사 분석을 지원함

### 동의어 처리

- `CustomSynonymFilter`를 구현하여 동의어 검색 지원
    - 예시: 'fastapi-백엔드', '휴대폰-스마트폰' 등

### 동기화

- 서버 기동 시 `lifespan` 이벤트를 통해 기존 `.md` 파일들을 Whoosh 인덱스에 자동 스캔/색인함

---

## 3. 주요 트러블슈팅 완료 사항 (중요)

### Pickle 에러

- **문제:** Whoosh의 스키마 직렬화 시 `PyKomoran` 객체나 `dict_keys`가 포함되어 발생하는 `TypeError`
- **해결책:**
    - `Komoran` 인스턴스를 전역 변수로 관리
    - 동의어 사전을 순수 `dict/list`로 강제 변환

### Path 객체

- `repo_path`를 문자열이 아닌 `pathlib.Path` 객체로 유지하여 `.glob()` 등 파일 시스템 연산을 정상화함

---

## 4. 현재 파일 구조

- `app/service/note_mng/note_mng_biz_service.py`: 비즈니스 로직 (Git, DB, 검색 연동)
- `app/service/lang_analyzer/search_manager.py`: Whoosh 인덱스 관리 및 검색 로직
- `app/service/lang_analyzer/synonym_filter.py`: 커스텀 동의어 필터

---

## 5. 다음 목표

- 백엔드 엔진은 검증되었으므로, 이제 이 API들을 호출할 **프론트엔드(React + Tailwind CSS)** 개발로 넘어가려고 해
- 주요 과제:
    - 검색 결과 시각화(Highlighting)
    - Git Diff 결과의 시각적 처리

---

## 요청사항

"위 내용을 이해했다면, 앞으로의 개발 방향에 대해 요약해주고 프론트엔드 구성을 위한 첫 번째 단계부터 가이드해줘."