from app.spec.biz.NoteConflictDetail import NoteConflictDetail


class NoteConflictError(Exception):
    """Note 충돌 발생 시 정보를 담아 던질 커스터 예외 클래스"""

    def __init__(self, conflict_data: NoteConflictDetail):
        self.conflict_data = conflict_data
        super().__init__("Note conflict occurred.")
