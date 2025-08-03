import json
import os

def load_settings(settings_file="settings.json"):
    """설정 파일을 로드합니다."""
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        return settings
    except FileNotFoundError:
        print(f"⚠️ 설정 파일 '{settings_file}'을 찾을 수 없습니다. 기본 설정을 사용합니다.")
        return get_default_settings()
    except json.JSONDecodeError as e:
        print(f"⚠️ 설정 파일 형식 오류: {e}. 기본 설정을 사용합니다.")
        return get_default_settings()

def get_default_settings():
    """기본 설정을 반환합니다."""
    return {
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

def get_docs_path(filename=None):
    """docs 폴더 경로 또는 특정 파일의 전체 경로를 반환합니다."""
    settings = load_settings()
    docs_folder = settings["paths"]["docs_folder"]
    
    if filename is None:
        return docs_folder
    
    # 절대 경로인 경우 그대로 반환
    if os.path.isabs(filename):
        return filename
    
    # 상대 경로이지만 이미 전체 경로인 경우 그대로 반환
    if os.path.exists(filename):
        return filename
    
    # docs 폴더에서 파일 찾기
    docs_path = os.path.join(docs_folder, filename)
    if os.path.exists(docs_path):
        return docs_path
    
    # 원본 경로 반환 (파일이 존재하지 않더라도)
    return filename
