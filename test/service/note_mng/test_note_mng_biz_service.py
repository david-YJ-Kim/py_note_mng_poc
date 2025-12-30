import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import git_service
from app.service.note_mng.note_mng_biz_service import NoteService
from app.exception.NoteConflictError import NoteConflictError
from app.spec.biz.NoteConflictDetail import NoteConflictDetail
from app.database.note_mng.model.note_model import NoteMetadata


class TestNoteConflict(unittest.IsolatedAsyncioTestCase):
    """ 비동기 테스트를 위해 IsolatedAsyncioTestCase 를 상속 받습니다. """

    async def asyncSetUp(self):
        """각 테스트 시작 전 실행되는 설정"""
        self.mock_db = AsyncMock()  # 비동기 DB 세션 모킹

    # **"그 클래스가 사용되는(Import된) 시점의 경로"**를 패치
    # NoteService에 정의된 Mock 대상을 넣어하는 듯
    @patch("app.service.note_mng.note_mng_biz_service.GitService")  # GitService 클래스 위치를 패치
    async def test_save_note_conflict_raises_error(self, MockGitClass):
        """내부에서 생성된 GitService를 Mocking하여 Conflict 검증"""

        # 1. Mock 설정
        # MockGitClass()는 NoteService 내부의 self.git_service가 됩니다.
        mock_git_instance = MockGitClass.return_value
        service = NoteService(self.mock_db)

        title = "TestNoteConflict"
        client_hash = "old_123"
        server_hash = "new_456"
        server_content = "Latest server content"

        # 2. DB 조회 결과 모킹
        mock_note = NoteMetadata(title=title, last_commit_hash=server_hash, file_path=f"{title}.md",
                                 updated_at=datetime.now(), last_modified_by="Others")

        service._get_note_by_title_first = AsyncMock(return_value=mock_note)

        # 3. 내부 git_service의 메소드 결과 설정
        mock_git_instance.read_file_content.return_value = server_content

        # 4. 검증: 예외 발생 여부 확인
        with self.assertRaises(NoteConflictError) as context:
            await service.save_or_update_note(
                title=title,
                content="My update",
                user_name="davidKim",
                last_hash=client_hash
            )

        # 5. 결과 데이터 확인
        error = context.exception
        self.assertEqual(error.conflict_data.server_last_hash, server_hash)
        self.assertEqual(error.conflict_data.server_content, server_content)

        print("\n✅ 내부 GitService 모킹을 통한 Conflict 테스트 성공")

    @patch("app.service.note_mng.note_mng_biz_service.GitService")
    async def test_save_note_success_when_hash_matches(self, MockGitClass):
        """해시가 일치할 때 내부 GitService가 정상 동작하는지 확인"""
        mock_git_instance = MockGitClass.return_value
        service = NoteService(db=self.mock_db)

        matching_hash = "same_123"

        # 2. DB 조회 결과 모킹
        mock_note = NoteMetadata(title="Test", last_commit_hash=matching_hash, file_path="Test.md",
                                 updated_at=datetime.now(), last_modified_by="Others")

        service._get_note_by_title_first = AsyncMock(return_value=mock_note)

        # 정상 커밋 시나리오 모킹
        mock_git_instance.write_and_commit.return_value = "new_hash_789"

        result = await service.save_or_update_note(
            title="Test",
            content="Content",
            user_name="user",
            last_hash=matching_hash
        )

        self.assertEqual(result["commit_hash"], "new_hash_789")
        # 실제 git_service의 메소드가 호출되었는지도 검증 가능
        mock_git_instance.write_and_commit.assert_called_once()
        print("✅ 정상 저장 케이스 테스트 성공")


if __name__ == '__main__':
    unittest.main()
