from fastapi import HTTPException, APIRouter, Depends, status

from app.exception.NoteConflictError import NoteConflictError
from app.service.note_mng.note_mng_biz_service import NoteService, get_note_service
from app.spec.endpoint.NoteServiceIvo import NoteSaveRequest

router = APIRouter(prefix="/notes", tags=["note"])


@router.post("/save")
async def save_note(request: NoteSaveRequest, service: NoteService = Depends(get_note_service)):
    try:
        # 핵심 로직 실행
        result = await service.save_or_update_note(
            title=request.title,
            content=request.content,
            user_name=request.user_name,
            last_hash=request.last_hash,
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


@router.get("")
async def list_notes(service: NoteService = Depends(get_note_service)):
    return await service.get_all_notes()


@router.get("/{title}/history")
async def get_note_history(title: str, service: NoteService = Depends(get_note_service)):
    detail = await service.get_note_detail(title)
    if not detail:
        raise HTTPException(status_code=404, detail="Not Found")
    return detail


note_service_controller = router
