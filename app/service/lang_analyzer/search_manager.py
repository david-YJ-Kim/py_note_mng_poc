# search_manager.py

import re
from pathlib import Path

from PyKomoran import Komoran
from whoosh.analysis import Tokenizer, LowercaseFilter, Token
from whoosh.fields import Schema, ID, TEXT
from whoosh.index import open_dir, create_in, exists_in

from app.service.lang_analyzer.synonym_filter import CustomSynonymFilter

# 동의어 사전: 반드시 순수 dict/list 형태로 관리 (dict_keys 사용 금지)
my_synonyms = {
    "휴대폰": ["스마트폰", "핸드폰"],
    "노트": ["문서", "기록"],
    "fastapi": ["파스트api", "백엔드"]
}

# 💡 1. Komoran 객체를 전역(Global) 영역에서 초기화
# 이렇게 하면 KoEnTokenizer 인스턴스 내부에 포함되지 않아 pickle 에러가 발생하지 않습니다.
_KOMORAN_INSTANCE = Komoran("EXP")


class KoEnTokenizer(Tokenizer):
    """ 한글/영어 복합 명사 분해 및 조사 제거 토크나이저 """

    def __init__(self):
        # 명사 추출을 위한 Komoran 객체 생성
        # 영어 및 숫자를 걸러내기 위한 정규표현식 (대소문자 구분 없음)
        self.en_pattern = re.compile(r'[a-zA-Z0-9]+')

    def __call__(self, value, positions=False, chars=False, **kwargs):
        """
        :param value: 인덱싱할 원문 텍스트 (예: "FastAPI를 이용한 Note 프로젝트")
        :param positions:
        :param chars:
        :param kwargs:
        :return:
        """
        # 1. 한글 형탯 분석 (복합 명사 분해 포함)
        # get_plain_text는 '단어/품사' 형태로 반환하믈 명사 (NNG, NNP)만 추출
        # get_nouns는 [FastAPI, 이용, Note, 프로젝트] 같은 결과를 반환하려 하지만
        # 영어는 분석기에 따라 누락될 수 있으르모 명시적 처리가 좋음
        nouns = _KOMORAN_INSTANCE.get_nouns(value)

        # 2. 영어 및 숫자 추출
        en_words = self.en_pattern.findall(value)

        # 3. 중복 제거 및 토큰 생성
        # 한글 명사와 영어 단어를 합친 뒤 중복을 제거합니다.
        all_keywords = set(nouns + [w.lower() for w in en_words])

        for i, word in enumerate(all_keywords):
            # Whoosh가 이해할 수 있는 Token 객체로 변환하여 양보(yield)합니다.
            t = Token(positions, chars, pos=i)
            t.text = word
            yield t


class NoteSearchManager:
    def __init__(self, index_dir="data/index"):
        # 1. 프로젝트 루트 경로 계산
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        # 2. 인덱스 저장 경로 저장
        self.index_path = self.base_dir / index_dir
        analyzer = KoEnTokenizer() | LowercaseFilter() | CustomSynonymFilter(my_synonyms)

        if not self.index_path.exists():
            self.index_path.mkdir(parents=True, exist_ok=True)

        self.schema = Schema(
            title=ID(stored=True, unique=True),  # 파일 제목 (고유 식별자)
            content=TEXT(stored=True, analyzer=analyzer),
        )

        # 💡 폴더는 있지만 유효한 인덱스 파일이 없는 경우를 확실히 체크
        if not exists_in(str(self.index_path)):
            print(f"🔍 [System] 새 인덱스 생성 중: {self.index_path}")
            create_in(str(self.index_path), self.schema)

        # 4. 인덱스 열기 (Whoosh는 문자열 경로를 받으므로 str 변환)
        self.ix = open_dir(str(self.index_path))

    def update_index(self, title, content):
        """ 파일 저장/수정 시 호출: 검색 지도를 갱신 합니다. """
        writer = self.ix.writer()
        writer.update_document(title=title, content=content)
        writer.commit()
        print(f"index {title} updated")

    def delete_index(self, title):
        """ 파일 삭제 시 호출: 검색 지도에서 삭제합니다. """
        writer = self.ix.writer()
        writer.delete_by_term("title", title)
        writer.commit()
        print(f"index {title} deleted")

    def search(self, keyword, limit=10):
        """ 본문 검색: 키워드가 포함된 파일 제목 리스트를 반환 합니다. """
        from whoosh.qparser import QueryParser

        with self.ix.searcher() as searcher:
            parser = QueryParser("content", self.ix.schema)
            query = parser.parse(keyword)
            results = searcher.search(query, limit=limit)
            return [hit['title'] for hit in results]
