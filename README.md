# TinyRAG - 가벼운 오프라인 문서 검색 시스템

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

TinyRAG는 **완전 오프라인**으로 동작하는 가벼운 RAG(Retrieval-Augmented Generation) 시스템입니다. 
자신의 문서들을 안전하게 로컬에서 검색하고, AI 모델을 통해 자연스러운 답변을 얻을 수 있습니다.

## ✨ 주요 기능

- 🔒 **완전 오프라인**: 인터넷 연결 없이 로컬에서 동작
- 🚀 **Microsoft MarkItDown 지원**: 고품질 문서 변환 (PDF, Office 문서)
- 📄 **다양한 문서 형식 지원**: PDF, Word, Excel, PowerPoint, 텍스트 파일
- 🧠 **지능적 검색**: 여러 컬렉션에서 자동으로 최적의 문서 찾기
- 💬 **자연어 답변**: Ollama를 통한 한국어 AI 답변 생성
- ⚙️ **JSON 설정 시스템**: 모든 설정을 간편하게 관리
- 📁 **스마트 파일 경로**: docs 폴더 내 파일은 파일명만으로 접근 가능

## 🛠️ 시스템 구성

```
TinyRAG/
├── document_manager.py    # 문서 관리 및 임베딩 생성
├── search_cli.py         # 검색 및 AI 답변 생성
├── config.py             # 설정 유틸리티
├── settings.json         # 시스템 설정 파일
├── models/              # 임베딩 모델 (로컬)
├── chroma_db/          # 벡터 데이터베이스 (로컬)
└── docs/               # 문서 파일들
```

## 📋 필요 조건

### Python 환경
- Python 3.8 이상
- 권장: Anaconda 또는 가상환경 사용

### Ollama (AI 답변용)
```bash
# Ollama 설치 (https://ollama.ai/)
ollama pull exaone3.5:latest
# 또는 다른 한국어 모델
ollama pull llama3.1:8b
```

## 🚀 설치 및 설정

### 1. 저장소 클론
```bash
git clone <repository-url>
cd TinyRAG
```

### 2. 가상환경 생성 (권장)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 설치

**기본 설치:**
```bash
pip install -r requirements.txt
```

**권장 설치 (MarkItDown 포함):**
```bash
pip install markitdown
```

MarkItDown은 Microsoft에서 개발한 고품질 문서 변환 라이브러리로, PDF 및 Office 문서를 더 정확하게 Markdown으로 변환합니다.

### 4. 설정 파일 확인
시스템 설정은 `settings.json` 파일로 관리됩니다:

```json
{
  "embedding_model": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "local_path": "./models/all-MiniLM-L6-v2"
  },
  "ollama": {
    "url": "http://localhost:11434",
    "model_name": "exaone3.5:latest"
  },
  "paths": {
    "docs_folder": "./docs",
    "chroma_db": "./chroma_db"
  },
  "search": {
    "default_n_results": 3,
    "chunk_size": 300,
    "overlap": 50,
    "large_doc_chunk_size": 500,
    "large_doc_overlap": 75,
    "large_doc_threshold": 100000
  }
}
```

## 📖 사용 방법

### 1. 문서 추가
```bash
python document_manager.py
```

**사용 가능한 명령어:**
- `add <파일경로>` - 문서 추가 (컬렉션명 자동생성)
- `add <파일명>` - docs 폴더의 파일을 파일명만으로 추가
- `add <파일경로> <컬렉션명>` - 문서를 특정 컬렉션으로 추가
- `add "파일 이름.pdf"` - 공백이 있는 파일명은 따옴표 사용
- `list` - 저장된 컬렉션 목록 보기
- `detail <컬렉션명>` - 컬렉션 상세 정보
- `delete <컬렉션명>` - 컬렉션 삭제
- `cleanup` - 데이터베이스 정리
- `extensions` - 지원되는 파일 형식 확인
- `help` - 도움말

**예시:**
```bash
💾 명령: add manual.pdf
💾 명령: add "ISO_14229-1_2013.en.PDF.pdf"
💾 명령: add "docs/Report.docx" project_docs
💾 명령: list
```

### 2. 문서 검색 및 질문
```bash
python search_cli.py
```

**사용 가능한 명령어:**
- `<질문>` - 모든 컬렉션에서 검색
- `use <컬렉션명> <질문>` - 특정 컬렉션에서만 검색
- `list` - 컬렉션 목록 보기
- `help` - 도움말 (현재 설정 정보 포함)
- `quit` - 종료

**예시:**
```bash
💭 질문: ISO 14229 프로토콜이 뭐야?
💭 질문: use project_docs 프로젝트 일정은?
```

## 📁 지원 파일 형식

### 🚀 MarkItDown 지원 (권장)
Microsoft MarkItDown을 사용하면 최고 품질의 문서 변환을 제공합니다:
- **PDF**: 고품질 텍스트 추출 및 구조 유지
- **Word**: `.docx`, `.doc` - 완벽한 Markdown 변환
- **Excel**: `.xlsx`, `.xls` - 표 구조 유지
- **PowerPoint**: `.pptx`, `.ppt` - 슬라이드 구조 유지

### 기본 지원
| 형식 | 확장자 | 필요 라이브러리 | 우선순위 |
|------|--------|----------------|---------|
| 텍스트 | `.txt`, `.md` | 기본 지원 | - |
| PDF | `.pdf` | MarkItDown → PyMuPDF → PyPDF2 | 1순위 |
| Word | `.docx`, `.doc` | MarkItDown → python-docx | 1순위 |
| Excel | `.xlsx`, `.xls` | MarkItDown → openpyxl | 1순위 |
| PowerPoint | `.pptx`, `.ppt` | MarkItDown → python-pptx | 1순위 |

### 설치 옵션

**최고 품질 (권장):**
```bash
pip install markitdown
```

**기본 지원:**
```bash
# 모든 형식 지원
pip install PyMuPDF python-docx openpyxl python-pptx

# 또는 필요한 것만
pip install PyMuPDF  # PDF 지원 (권장)
pip install python-docx  # Word 지원
```

## ⚙️ 설정 관리

### 설정 파일 구조
모든 설정은 `settings.json`에서 중앙집중식으로 관리됩니다:

```json
{
  "embedding_model": {
    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
    "local_path": "./models/all-MiniLM-L6-v2"
  },
  "ollama": {
    "url": "http://localhost:11434",
    "model_name": "exaone3.5:latest"
  },
  "paths": {
    "docs_folder": "./docs",
    "chroma_db": "./chroma_db"
  },
  "search": {
    "default_n_results": 3,
    "chunk_size": 300,
    "overlap": 50,
    "large_doc_chunk_size": 500,
    "large_doc_overlap": 75,
    "large_doc_threshold": 100000
  }
}
```

### 주요 설정 옵션

**임베딩 모델 변경:**
```json
{
  "embedding_model": {
    "model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "local_path": "./models/custom-model"
  }
}
```

**Ollama 서버 설정:**
```json
{
  "ollama": {
    "url": "http://192.168.1.100:11434",
    "model_name": "llama3.1:8b"
  }
}
```

**검색 파라미터 조정:**
```json
{
  "search": {
    "default_n_results": 5,
    "chunk_size": 400,
    "overlap": 75
  }
}
```

## 🔧 트러블슈팅

### 일반적인 문제

**1. MarkItDown 설치 문제**
```bash
# 최신 버전 설치
pip install --upgrade markitdown

# 의존성 문제 시
pip install --no-deps markitdown
```

**2. 임베딩 모델 로딩 오류**
```bash
# 모델 수동 다운로드
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
```

**3. Ollama 연결 오류**
```bash
# Ollama 서비스 확인
ollama serve
# 다른 터미널에서
ollama list
```

**4. 설정 파일 오류**
- `settings.json`이 없으면 자동으로 기본 설정을 사용합니다
- JSON 형식 오류 시 기본 설정으로 대체됩니다

**5. 파일 경로 문제**
```bash
# docs 폴더 내 파일은 파일명만으로 접근
💾 명령: add manual.pdf

# 전체 경로도 지원
💾 명령: add "C:\Documents\manual.pdf"
```

### 성능 최적화

**메모리 사용량 줄이기:**
- 큰 문서는 자동으로 배치 처리됩니다
- `large_doc_threshold` 설정으로 임계값 조정 가능
- 불필요한 컬렉션 정리: `cleanup`

**검색 속도 향상:**
- 특정 컬렉션 지정: `use <컬렉션명> <질문>`
- `default_n_results` 설정으로 검색 결과 수 조정

**문서 변환 품질 향상:**
- MarkItDown 사용 (권장)
- PDF의 경우 PyMuPDF가 PyPDF2보다 우수