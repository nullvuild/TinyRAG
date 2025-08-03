import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import os
import warnings
from config import load_settings

# FutureWarning 경고 메시지 숨기기
warnings.filterwarnings("ignore", category=FutureWarning)

print("=== TinyRAG - 가벼운 문서 검색 시스템 ===")

class TinyRAG:
    def __init__(self, settings_file="settings.json"):
        # 설정 로드
        self.settings = load_settings(settings_file)
        
        # ChromaDB 설정
        chroma_db_path = self.settings["paths"]["chroma_db"]
        self.client = chromadb.PersistentClient(path=chroma_db_path)
        print("✅ ChromaDB 클라이언트 연결 성공")
        
        # SentenceTransformer 모델 로딩
        model_path = os.path.abspath(self.settings["embedding_model"]["local_path"])
        self.embedding_model = SentenceTransformer(model_path)
        print("✅ 임베딩 모델 로딩 완료")
        
        # Ollama 설정
        self.ollama_url = self.settings["ollama"]["url"]
        self.model_name = self.settings["ollama"]["model_name"]
        
        # Ollama 연결 테스트
        if self._test_ollama_connection():
            print(f"✅ Ollama 연결 성공 (모델: {self.model_name})")
        else:
            print(f"❌ Ollama 연결 실패. {self.ollama_url}에서 {self.model_name} 모델이 실행 중인지 확인하세요.")
            self._suggest_available_models()
    
    def _test_ollama_connection(self):
        """Ollama 서버 연결 테스트"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _suggest_available_models(self):
        """사용 가능한 모델 확인 및 제안"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if models:
                    print(f"💡 사용 가능한 모델: {[m['name'] for m in models]}")
                    # 첫 번째 모델을 기본값으로 설정
                    self.model_name = models[0]['name']
                    print(f"자동으로 '{self.model_name}' 모델을 선택했습니다.")
        except:
            pass
    
    def list_collections(self):
        """사용 가능한 컬렉션 목록 출력"""
        collections = self.client.list_collections()
        print(f"\n📚 사용 가능한 문서 컬렉션:")
        for i, collection in enumerate(collections):
            count = collection.count()
            print(f"  {i+1}. {collection.name} ({count}개 청크)")
        return collections
    
    def search_documents(self, query, collection_name=None, n_results=None):
        """문서 검색 - 모든 컬렉션에서 검색하거나 특정 컬렉션에서 검색"""
        if n_results is None:
            n_results = self.settings["search"]["default_n_results"]
        
        # 유사도 임계값 설정 (0.01로 더 낮춤 - 더 많은 결과 포함)
        similarity_threshold = 0.01
            
        try:
            # 쿼리 임베딩 생성
            query_embedding = self.embedding_model.encode([query])
            
            all_results = {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]]
            }
            
            # 특정 컬렉션이 지정된 경우
            if collection_name:
                collection = self.client.get_collection(name=collection_name)
                results = collection.query(
                    query_embeddings=query_embedding.tolist(),
                    n_results=n_results,
                    include=['documents', 'metadatas', 'distances']
                )
                return results
            
            # 모든 컬렉션에서 검색
            collections = self.client.list_collections()
            collection_results = []
            
            print(f"🔍 {len(collections)}개 컬렉션에서 검색 중...")
            
            for collection in collections:
                try:
                    results = collection.query(
                        query_embeddings=query_embedding.tolist(),
                        n_results=n_results,
                        include=['documents', 'metadatas', 'distances']
                    )
                    
                    # 결과가 유효한지 확인
                    if not results or not results.get('documents') or not results['documents'][0]:
                        continue  # 조용히 넘어감
                    
                    print(f"🔍 컬렉션 '{collection.name}'에서 {len(results['documents'][0])}개 결과 발견")
                    
                    # 컬렉션 이름을 메타데이터에 추가
                    for i, metadata in enumerate(results['metadatas'][0]):
                        if metadata is not None:  # metadata가 None이 아닌 경우만 처리
                            metadata['collection_name'] = collection.name
                        else:
                            # metadata가 None인 경우 새로 생성
                            results['metadatas'][0][i] = {'collection_name': collection.name}
                    
                    # 결과를 거리순으로 정렬하기 위해 저장
                    for doc, metadata, distance in zip(
                        results['documents'][0],
                        results['metadatas'][0], 
                        results['distances'][0]
                    ):
                        # 유사도 계산 및 임계값 필터링
                        similarity = 1 - distance
                        if similarity < similarity_threshold:
                            continue  # 관련성이 너무 낮은 결과는 제외
                            
                        # metadata가 None인 경우 기본값 설정
                        if metadata is None:
                            metadata = {'collection_name': collection.name}
                        else:
                            metadata['collection_name'] = collection.name
                        
                        collection_results.append({
                            'document': doc,
                            'metadata': metadata,
                            'distance': distance,
                            'similarity': similarity
                        })
                        
                except Exception as e:
                    print(f"컬렉션 '{collection.name}' 검색 중 오류: {e}")
                    continue
            
            # 컬렉션별 결과 분석 및 지능적 선택
            if collection_results:
                # 컬렉션별로 그룹화
                collection_groups = {}
                for result in collection_results:
                    collection_name = result['metadata'].get('collection_name', '알 수 없음')
                    if collection_name not in collection_groups:
                        collection_groups[collection_name] = []
                    collection_groups[collection_name].append(result)
                
                # 컬렉션별 점수 계산 (화면 출력 없이)
                collection_scores = {}
                for collection_name, results in collection_groups.items():
                    # 최고 유사도와 평균 유사도 계산
                    similarities = [r['similarity'] for r in results]
                    max_similarity = max(similarities)
                    avg_similarity = sum(similarities) / len(similarities)
                    
                    # 고품질 결과 비율 계산 (유사도 0.1 이상으로 더 낮춤)
                    high_quality_count = sum(1 for s in similarities if s >= 0.1)
                    quality_ratio = high_quality_count / len(similarities)
                    
                    # 컬렉션 점수 = (최고 유사도 * 0.5) + (평균 유사도 * 0.5) (품질 비율 제거)
                    collection_score = (max_similarity * 0.5) + (avg_similarity * 0.5)
                    collection_scores[collection_name] = {
                        'score': collection_score,
                        'max_sim': max_similarity,
                        'avg_sim': avg_similarity,
                        'quality_ratio': quality_ratio,
                        'count': len(results)
                    }
                
                # 가장 적합한 컬렉션들에서 결과 선택
                sorted_collections = sorted(collection_scores.items(), key=lambda x: x[1]['score'], reverse=True)
                
                # 상위 컬렉션들에서 균형있게 결과 선택
                selected_results = []
                for collection_name, score_info in sorted_collections:
                    collection_results_sorted = sorted(collection_groups[collection_name], key=lambda x: x['distance'])
                    
                    # 각 컬렉션에서 선택할 개수 결정
                    remaining_slots = n_results - len(selected_results)
                    if remaining_slots <= 0:
                        break
                    
                    # 상위 컬렉션은 더 많이, 하위 컬렉션은 적게 선택
                    if score_info['score'] >= 0.2:  # 고품질 컬렉션 (임계값 더 낮춤)
                        take_count = min(3, remaining_slots, len(collection_results_sorted))
                    elif score_info['score'] >= 0.1:  # 중품질 컬렉션 (임계값 더 낮춤)
                        take_count = min(2, remaining_slots, len(collection_results_sorted))
                    else:  # 저품질 컬렉션
                        take_count = min(1, remaining_slots, len(collection_results_sorted))
                    
                    # 유사도가 0.05 이상인 결과만 선택 (임계값 더 낮춤)
                    quality_results = [r for r in collection_results_sorted if r['similarity'] >= 0.05]
                    if quality_results:
                        selected_results.extend(quality_results[:take_count])
                    else:  # 품질 결과가 없으면 최소한 1개는 선택
                        selected_results.extend(collection_results_sorted[:min(1, len(collection_results_sorted))])
                
                # 최종 결과를 유사도순으로 정렬
                top_results = sorted(selected_results, key=lambda x: x['distance'])[:n_results]
                
                # 결과를 ChromaDB 형식으로 재구성
                for result in top_results:
                    all_results['documents'][0].append(result['document'])
                    all_results['metadatas'][0].append(result['metadata'])
                    all_results['distances'][0].append(result['distance'])
            else:
                print("⚠️ 모든 컬렉션에서 검색 결과를 찾을 수 없습니다.")
                print(f"   검색어: '{query}'")
                print(f"   검색한 컬렉션 수: {len(collections)}")
                print("   임계값을 낮추거나 다른 검색어를 시도해보세요.")
            
            return all_results
            
        except Exception as e:
            print(f"문서 검색 중 오류: {e}")
            return None
    
    def format_search_results(self, results):
        """검색 결과를 정리하여 표시"""
        if not results or not results['documents'][0]:
            return [], ""
        
        formatted_results = []
        context_parts = []
        
        # 검색된 문서 목록과 유사도 정보 표시
        doc_list = []
        similarity_info = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0], 
            results['metadatas'][0], 
            results['distances'][0]
        )):
            similarity = 1 - distance
            
            # metadata가 None인 경우 기본값 설정
            if metadata is None:
                metadata = {}
            
            doc_name = metadata.get('document_name', '알 수 없는 문서')
            chunk_id = metadata.get('chunk_id', i)
            collection_name = metadata.get('collection_name', '알 수 없음')
            
            # 결과 정보 저장
            result_info = {
                'rank': i + 1,
                'document_name': doc_name,
                'chunk_id': chunk_id,
                'similarity': similarity,
                'content': doc,
                'metadata': metadata
            }
            formatted_results.append(result_info)
            
            # 문서 목록에 추가 (중복 제거)
            doc_info = f"[{collection_name}] {doc_name}"
            if doc_info not in doc_list:
                doc_list.append(doc_info)
                # 유사도 정보도 함께 저장
                similarity_info.append(f"   • {doc_info} (관련도: {similarity:.1%})")
            
            # 컨텍스트 생성용
            context_parts.append(f"[문서: {doc_name}]\n{doc}")
        
        # 검색된 문서 목록과 유사도 표시
        print(f"\n📚 검색된 문서 ({len(doc_list)}개):")
        for sim_info in similarity_info:
            print(sim_info)
        
        context = "\n\n".join(context_parts)
        return formatted_results, context
    
    def generate_answer_with_sources(self, query, context, search_results):
        """근거가 포함된 답변 생성"""
        try:
            # 프롬프트 생성
            prompt = f"""다음은 사용자의 질문과 관련성이 높은 문서들의 내용입니다. 이 문서들을 바탕으로 정확하고 유용한 답변을 제공해주세요.

검색된 문서 내용:
{context}

사용자 질문: {query}

답변 지침:
1. 위의 문서 내용에서 질문과 직접적으로 관련된 정보만을 사용하여 답변하세요.
2. 문서에 명시적으로 언급되지 않은 내용은 추측하거나 추가하지 마세요.
3. 여러 문서의 내용이 있다면, 가장 관련성이 높고 신뢰할 수 있는 정보를 우선적으로 사용하세요.
4. 답변은 명확하고 구체적으로 작성하되, 자연스러운 한국어로 표현하세요.
5. 문서 내용으로는 질문에 완전히 답할 수 없다면, 답할 수 있는 부분만 명시하고 한계를 설명하세요.

답변:"""

            print("🔗 Ollama API 호출 중...")
            
            # Ollama API 호출
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            }
            
            print(f"📡 요청 URL: {self.ollama_url}/api/generate")
            print(f"🎯 모델: {self.model_name}")
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120,  # 타임아웃을 120초로 증가
                headers={'Content-Type': 'application/json'}
            )
            
            print(f"📊 응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                ai_answer = result.get("response", "").strip()
                
                if not ai_answer:
                    print("⚠️ 경고: Ollama에서 빈 응답을 받았습니다.")
                    print(f"📋 전체 응답: {result}")
                    ai_answer = "죄송합니다. AI 모델에서 응답을 생성하지 못했습니다."
                else:
                    print(f"✅ AI 답변 생성 완료 (길이: {len(ai_answer)}자)")
                
                # 근거 정보 추가
                sources_info = "\n\n📚 답변 근거:"
                for result in search_results:
                    collection_name = result['metadata'].get('collection_name', '알 수 없음')
                    
                    # 자연스러운 지점에서 내용 자르기
                    content = result['content']
                    if len(content) > 150:
                        # 150자 근처에서 자연스러운 구분점 찾기
                        truncated = content[:150]
                        
                        # 마지막 문장의 끝(.)을 찾기
                        last_period = truncated.rfind('.')
                        if last_period > 100:  # 너무 짧지 않다면 문장 끝에서 자르기
                            content_preview = content[:last_period + 1]
                        else:
                            # 문장 끝이 없으면 마지막 공백에서 자르기
                            last_space = truncated.rfind(' ')
                            if last_space > 100:  # 너무 짧지 않다면 단어 경계에서 자르기
                                content_preview = content[:last_space] + "..."
                            else:
                                # 줄바꿈에서 자르기
                                last_newline = truncated.rfind('\n')
                                if last_newline > 100:
                                    content_preview = content[:last_newline] + "..."
                                else:
                                    # 마지막 수단으로 150자에서 자르기
                                    content_preview = truncated + "..."
                    else:
                        content_preview = content
                    
                    sources_info += f"\n• [{collection_name}] {result['document_name']} - 관련도: {result['similarity']:.1%}"
                    sources_info += f"\n  📄 참고 내용: \"{content_preview}\"\n"
                
                return ai_answer + sources_info
            else:
                error_msg = f"Ollama API 오류: {response.status_code}"
                try:
                    error_detail = response.json()
                    error_msg += f" - {error_detail}"
                except:
                    error_msg += f" - {response.text}"
                print(f"❌ {error_msg}")
                return error_msg
                
        except requests.exceptions.Timeout:
            error_msg = "⏰ Ollama API 응답 시간 초과 (120초). 모델이 너무 오래 걸리거나 서버에 문제가 있을 수 있습니다."
            print(f"❌ {error_msg}")
            return error_msg
        except requests.exceptions.ConnectionError:
            error_msg = f"🔌 Ollama 서버({self.ollama_url})에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
            print(f"❌ {error_msg}")
            return error_msg
        except Exception as e:
            error_msg = f"답변 생성 중 예상치 못한 오류: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def search_and_answer(self, query, collection_name=None, n_results=None):
        """완전한 RAG 검색 및 답변 - 모든 컬렉션에서 검색하거나 특정 컬렉션에서 검색"""
        if n_results is None:
            n_results = self.settings["search"]["default_n_results"]
            
        print(f"\n🔍 검색 쿼리: {query}")
        if collection_name:
            print(f"📚 대상 컬렉션: {collection_name}")
        else:
            print(f"📚 검색 범위: 모든 컬렉션")
        print("=" * 60)
        
        # 0. Ollama 연결 상태 확인
        if not self._test_ollama_connection():
            print("⚠️ Ollama 서버 연결을 재확인 중...")
            self._suggest_available_models()
            if not self._test_ollama_connection():
                print("❌ Ollama 서버에 연결할 수 없습니다. 검색만 수행합니다.")
        
        # 1. 문서 검색
        search_results_raw = self.search_documents(query, collection_name, n_results)
        if not search_results_raw or not search_results_raw['documents'][0]:
            print("❌ 관련 문서를 찾을 수 없습니다.")
            return
        
        # 2. 검색 결과 정리 및 표시
        search_results, context = self.format_search_results(search_results_raw)
        
        # 3. Ollama로 답변 생성
        print("🤖 AI 답변 생성 중...")
        answer = self.generate_answer_with_sources(query, context, search_results)
        
        print("\n💬 AI 답변:")
        print("=" * 60)
        print(answer)
        print("=" * 60)
    
    def show_help(self):
        """도움말 표시"""
        print("\n" + "="*80)
        print("🔍 TinyRAG - 가벼운 오프라인 문서 검색 시스템")
        print("이제 모든 컬렉션에서 자동으로 가장 관련성 높은 문서를 찾습니다!")
        print(f"\n🔧 현재 설정:")
        print(f"   - Ollama 서버: {self.settings['ollama']['url']}")
        print(f"   - Ollama 모델: {self.settings['ollama']['model_name']}")
        print(f"   - 임베딩 모델: {self.settings['embedding_model']['model_name']}")
        print(f"   - 문서 폴더: {self.settings['paths']['docs_folder']}")
        print("\n명령어:")
        print("  <질문>                : 모든 컬렉션에서 검색")
        print("  use <컬렉션명> <질문>  : 특정 컬렉션에서만 검색")
        print("  list                  : 컬렉션 목록 보기")
        print("  help                  : 이 도움말 표시")
        print("  quit                  : 종료")
        print("="*80)

def main():
    # Tiny RAG 시스템 초기화
    rag = TinyRAG()
    
    # 컬렉션 목록 확인
    collections = rag.list_collections()
    if not collections:
        print("\n❌ 사용 가능한 문서 컬렉션이 없습니다.")
        print("먼저 create_db.py를 실행하여 문서를 ChromaDB에 추가하세요.")
        return
    
    # 기본 컬렉션 설정 (더 이상 필요하지 않음)
    # default_collection = collections[0].name if collections else "main_documents"
    # current_collection = default_collection
    
    # 대화형 검색
    print("\n💭 질문을 입력하세요 (help: 도움말, quit: 종료)")
    
    while True:
        try:
            user_input = input(f"\n💭 질문: ").strip()
            
            if user_input.lower() in ['quit', 'exit', '종료', 'q']:
                print("👋 검색 시스템을 종료합니다.")
                break
            
            elif user_input.lower() == 'list':
                rag.list_collections()
            
            elif user_input.lower() in ['help', 'h', '도움말']:
                rag.show_help()
            
            elif user_input.startswith('use '):
                # "use <컬렉션명> <질문>" 형태로 특정 컬렉션에서 검색
                parts = user_input[4:].strip().split(' ', 1)
                if len(parts) == 2:
                    collection_name, question = parts
                    try:
                        rag.client.get_collection(name=collection_name)
                        print(f"🎯 '{collection_name}' 컬렉션에서만 검색합니다.")
                        rag.search_and_answer(question, collection_name)
                    except:
                        print(f"❌ '{collection_name}' 컬렉션을 찾을 수 없습니다.")
                else:
                    print("❌ 사용법: use <컬렉션명> <질문>")
            
            elif user_input == '':
                continue
            
            else:
                # 모든 컬렉션에서 RAG 검색 및 답변
                rag.search_and_answer(user_input)
            
        except KeyboardInterrupt:
            print("\n\n👋 검색 시스템을 종료합니다.")
            break
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
