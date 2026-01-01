from fastapi import HTTPException, APIRouter, Depends, status, BackgroundTasks

from app.exception.NoteConflictError import NoteConflictError
from app.service.note_mng.note_mng_biz_service import NoteService, get_note_service
from app.spec.endpoint.note_service_file_response_ivo import NoteSaveRequest
from app.spec.endpoint.note_service_file_tree_response_ivo import NoteServiceFileTreeResponseIVO

router = APIRouter(prefix="/notes", tags=["note"])


@router.get("")
async def get_notes(keyword: str = None, page: int = 1, size: int = 20,
                    service: NoteService = Depends(get_note_service)):
    items, total_count = await service.get_notes_with_complex_search(keyword, page, size)
    # items, total_count = await service.get_notes_with_pagination(keyword, page, size)

    # 전체 페이지 수 계산
    total_pages = (total_count + size - 1) // size

    # 다음/이전 페이지 URL 생성
    base_url = "/notes"
    next_page = f"{base_url}?page={page + 1}&size={size}" if page < total_pages else None
    prev_page = f"{base_url}?page={page - 1}&size={size}" if page > 1 else None

    # 검색어가 있었다면, URL에도 붙여줌
    if keyword:
        if next_page: next_page += f"&keyword={keyword}"
        if prev_page: prev_page += f"&keyword={keyword}"

    return {
        "status": "success",
        "metadata": {
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "size": size,
            "next_link": next_page,
            "prev_link": prev_page,
        },
        "items": items,
    }


@router.get("/folder-tree")
async def get_folder_tree(service: NoteService = Depends(get_note_service)):
    try:
        tree_data = await service.get_folder_tree_data()
        return NoteServiceFileTreeResponseIVO(
            success=True,
            data=tree_data,
            message="Folder tree retrieved successfully",
        )
    except Exception as e:
        return NoteServiceFileTreeResponseIVO(
            success=False,
            data=[],
            message=f"Error: {str(e)}",
        )


@router.post("/save")
async def save_note(request: NoteSaveRequest, background_tasks: BackgroundTasks,
                    service: NoteService = Depends(get_note_service)):
    try:
        # 핵심 로직 실행
        result = await service.save_or_update_note(
            title=request.title,
            content=request.content,
            user_name=request.user_name,
            last_hash=request.last_hash,
        )

        # 2. 무거운 색인 작업은 백그라운드에서 실행
        background_tasks.add_task(
            service.search_manager.update_index,
            request.title,
            request.content,
        )

        return {
            "status": "success",
            **result,
        }
    except NoteConflictError as ne:
        print(f"❌ NoteConflictError in save_note: {str(ne)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "NOTE_CONFLICT",
                "message": "편집 중 다른 사용자가 내용을 수정했습니다.",
                "conflict_data": ne.conflict_data.dict()
            }
        )

    except Exception as e:
        print(f"❌ Error in save_note: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{title}/history")
async def get_note_history(title: str, service: NoteService = Depends(get_note_service)):
    detail = await service.get_note_detail(title)
    if not detail:
        raise HTTPException(status_code=404, detail="Not Found")
    return detail


note_service_controller = router
