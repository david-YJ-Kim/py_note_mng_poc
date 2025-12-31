# synonym_filter

from whoosh.analysis import Filter, Tokenizer, LowercaseFilter


class CustomSynonymFilter(Filter):
    """ 동의어 사전을 바탕으로 토큰을 확장하는 필터 """

    def __init__(self, synonyms):
        # pickle 에러 방지를 위해 확실히 dict/list로 변환
        self.synonyms = {str(k): list(v) for k, v in synonyms.items()}

    def __call__(self, tokens):
        for t in tokens:
            yield t  # 원복 단어 내보내기
            if t.text in self.synonyms:
                for syn in self.synonyms[t.text]:
                    # 동의어들을 새로운 토큰으로 추가 생성
                    new_t = t.copy()
                    new_t.text = syn
                    yield new_t
