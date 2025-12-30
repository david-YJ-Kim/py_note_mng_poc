import logging
import os
import subprocess
from pathlib import Path

from git import Repo, Actor


class GitService:
    def __init__(self, repo_path=None):
        if repo_path is None:
            # 현재 테스트 폴더는 Root 폴더에 위치함
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            self.repo_path = str(base_dir / "data/note")
            print(f"base_dir: {base_dir}, repo_path: {self.repo_path}")
        else:
            self.repo_path = repo_path

        # GIT 저장소 초기화
        if not os.path.exists(os.path.join(self.repo_path, ".git")):
            self.repo = Repo.init(self.repo_path)
            print("initialize git in repo")
        else:
            self.repo = Repo(self.repo_path)

    def get_file_history(self, file_path:str):
        """ 특정 파일의 커밋 히스토리를 반환 """
        try:
            # git log를 사용하여 커밋 해시, 작성자, 날짜, 메시지를 가져옴
            commits = self.repo.iter_commits(paths=file_path)
            history = []
            for c in commits:
                history.append({
                    "hash": c.hexsha,
                    "author": c.author.name,
                    "date": c.authored_datetime.isoformat(),
                    "message": c.message.strip(),
                })
            return history
        except Exception as e:
            print(f"Git history error: {e}")
            return []


    def write_and_commit(self, file_name, content, author_name, message):
        """ 신규 노트 생성 및 커밋 """

        full_path = os.path.join(self.repo_path, file_name)
        with open(full_path, "w", encoding="UTF-8") as f:
            f.write(content)

        self.repo.index.add([file_name])
        author = f"{author_name} <{author_name}@company.com>"
        commit = self.repo.index.commit(message, author=Actor(author, None))
        return commit.hexsha

    def get_history_with_diff(self, file_name):
        """파일의 수정 이력과 실제 변경 내용(diff) 가져오기"""
        try:
            # 해당 파일의 커밋들을 가져옴
            commits = list(self.repo.iter_commits(paths=[file_name]))
            history = []

            for i, commit in enumerate(commits):
                diff_data = ""

                # 이전 커밋(Parent)이 있다면 비교하여 diff 생성
                if i + 1 < len(commits):
                    parent = commits[i + 1]
                    # 현재 커밋과 이전 커밋 간의 차이점 추출
                    diff_index = parent.diff(commit, paths=[file_name], create_patch=True)

                    for d in diff_index:
                        # d.diff는 바이너리 형태이므로 decode가 필요합니다.
                        diff_data += d.diff.decode("utf-8")
                else:
                    # 첫 번째 커밋인 경우 (비교 대상이 없음)
                    diff_data = "Initial Commit (New File)"

                history.append({
                    "hash": commit.hexsha,
                    "author": commit.author.name,
                    "date": commit.authored_datetime,
                    "message": commit.message.strip(),
                    "diff": diff_data  # 변경된 내용 (Patch 형태)
                })

            return history
        except Exception as e:
            print(f"이력 및 Diff 조회 중 오류 발생: {e}")
            return []

    def merge_contents(self, base_content, local_content, remote_content):
        """
        git merge-file 기능을 시뮬레이션하여 세 버전을 병합한다.
        :param base_content: 수정을 시작했던 당시의 원본 (Ancestor)
        :param local_content: 내가 수정한 내용
        :param remote_content: 그사이 다른 사람이 저장한 내용
        :return:
        """

        # 임시 파일 생성 (Git merge-file은 파일 단위로 작동)
        paths= {
            "base": os.path.join(self.repo_path, "tmp_base.txt"),
            "local": os.path.join(self.repo_path, "tmp_local.txt"),
            "remote": os.path.join(self.repo_path, "tmp_remote.txt")
        }

        try:
            for key, content in [
                ("base", base_content),
                ("local", local_content),
                ("remote", remote_content)
            ]:
                with open(paths[key], "w", encoding="UTF-8") as f:
                    f.write(content)
            # git merge-file <current> <base> <remote>
            # 실행 결과 local 파일에 병합 결과가 뎦어씌워집니다.
            cmd = [
                "git", "merge-file", paths["base"], paths["local"], paths["remote"], "-p"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, encoding="UTF-8")

            # exit code : 깨긋하게 병함된 / 0 보다 크면 충돌 발생
            is_conflict = result.returncode > 0
            merged_text = result.stdout

            return is_conflict, merged_text
        finally:
            # 임시 파일 삭제
            for p in paths.values():
                if os.path.exists(p):
                    os.remove(p)

    def get_file_diff(self, commit_hash: str, file_path: str) -> str:
        """특정 커밋의 변경 사항(Diff)을 안정적으로 가져옵니다."""
        try:
            # 1. 해당 커밋의 부모(이전 커밋) 해시를 가져옴
            # ^1은 바로 이전 커밋을 의미함
            try:
                # git show를 사용하여 특정 파일의 patch만 추출
                # --pretty=format:은 커밋 메시지 출력을 없애고 순수 diff만 가져오기 위함
                diff_output = self.repo.git.show(
                    "--pretty=format:",
                    commit_hash,
                    "--",
                    file_path
                )
                return diff_output.strip() if diff_output else "변경 사항이 없습니다."
            except Exception as git_err:
                # 첫 번째 커밋 등 부모가 없는 경우 처리
                return self.repo.git.show(commit_hash, "--", file_path)

        except Exception as e:
            return f"Diff 추출 실패: {str(e)}"

    def read_file_content(self, file_name: str) -> str:
        """ 현재 워킹 디렉토리의 파일 내용을 읽어옵니다. """
        import os
        file_path = os.path.join(self.repo.working_dir, file_name)
        if not os.path.exists(file_path):
            logging.warn(f"file is not exist. path:{file_path}")
            return ""

        with open(file_path, "r", encoding="UTF-8") as f:
            return f.read()




if __name__ == '__main__':
    poc = GitService()

    """ 충돌 테스트 """
    # [시나리오: 동일한 줄 수정으로 인한 충돌 발생]
    base_txt = "오늘 점심은 김치찌개입니다."
    user_a_txt = "오늘 점심은 부대찌개입니다."  # A는 부대찌개로 수정
    user_b_txt = "오늘 점심은 된장찌개입니다."  # B는 된장찌개로 수정

    print("\n" + "=" * 50)
    print("[충돌 발생 테스트 시작]")
    print("=" * 50)

    # 병합 실행
    is_conflict, result_txt = poc.merge_contents(base_txt, user_a_txt, user_b_txt)

    if is_conflict:
        print("⚠️ 예상대로 충돌이 발생했습니다!")
        print("\n--- Git이 생성한 충돌 마커 내용 ---")
        print(result_txt)
        print("----------------------------------")

        # 실제 서비스라면 이 result_txt를 유저에게 보내서
        # "부대찌개"와 "된장찌개" 중 하나를 고르게 해야 합니다.
    else:
        print("✅ 어라? 자동 병합되었습니다.")
        print(f"결과:\n{result_txt}")
    """ 충돌 테스트 """


    """ Merge 테스트 """
    # # [시나리오]
    # base_txt = "사과\n포도\n바나나"
    # user_a_txt = "사과\n포도\n바나나\n딸기"  # A는 끝에 딸기 추가
    # user_b_txt = "망고\n사과\n포도\n바나나"  # B는 앞에 망고 추가
    #
    # print("\n[병합 테스트 시작]")
    # is_conflict, merged_text = poc.merge_contents(base_txt, user_a_txt, user_b_txt)
    #
    # if not is_conflict:
    #     print(" 자동 병합 성공")
    #     print(f"결과물: \n{merged_text}")
    # else:
    #     print(" 충돌 발생! 수동 병합 필요")
    #     print(f"충돌 내용: \n{merged_text}")
    """ Merge 테스트 """

    """ 기본 저장 테스트 """
    # note_name = "note1.md"
    #
    # # 1. 첫번째 저장
    # h1 = poc.write_and_commit(note_name,  "첫번째 내용", "David", "Init Commit")
    # print(f"첫번째 저장 완료: {h1}")
    #
    # # 2. 두번째 저장
    # h2 = poc.write_and_commit(note_name,  "듀번째 내용", "Andy", "Add New Content")
    # print(f"두번째 저장 완료: {h2}")
    #
    # # 3. 이력 확인
    # history = poc.get_history_with_diff(note_name)
    # print("\n ---- 수정 이력 ----")
    # for h in history:
    #     print(f"{h['date']} {h['author']}: {h['hash']} {h['diff']} {h['date']}")
    """ 기본 저장 테스트 """


