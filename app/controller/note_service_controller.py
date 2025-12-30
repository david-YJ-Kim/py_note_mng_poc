from fastapi import HTTPException, APIRouter, Depends, status

from app.service.note_mng.note_mng_biz_service import NoteService, get_note_service
from app.spec.ivo.NoteServiceIvo import NoteSaveRequest

router = APIRouter(prefix="/notes", tags=["note"])

@router.post("/save")
async def save_note(request: NoteSaveRequest, service: NoteService = Depends(get_note_service)):

    try:


        # 핵심 로직 실행
        result = await service.save_or_update_note(
            title=request.title,
            content=request.content,
            user_name=request.user_name,
        )

        return {
            "status": "success",
            **result,
        }
    except Exception as e:
        # 에러 발생 시 get_db에서 자동으로 rollback 처리 됨
        print(f"❌ Error in save_note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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