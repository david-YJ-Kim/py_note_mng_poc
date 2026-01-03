from app.spec.biz.NoteConflictDetail import NoteConflictDetail


class NoteConflictError(Exception):
    """Note 충돌 발생 시 정보를 담아 던질 커스터 예외 클래스"""

    def __init__(self, conflict_data: NoteConflictDetail):
        self.conflict_data = conflict_data
        super().__init__("Note conflict occurred.")


class NoteServiceError(Exception):
    """Note 서비스 기본 예외"""
    pass


class NoteNotFoundError(NoteServiceError):
    """DB에 노트 정보가 없을 때"""
    pass


class NoteFileNotFoundError(NoteServiceError):
    """DB에는 있으나 실제 물리 파일이 없을 때"""
    pass
