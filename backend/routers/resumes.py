from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from controllers.resume_controller import delete_resume, get_resume, list_resumes
from core.responses import api_error, api_success
from core.security import get_current_user
from services.file_storage_service import safe_storage_path

router = APIRouter(prefix="/resumes")


@router.get("")
async def get_resumes(current_user: dict = Depends(get_current_user)):
    return api_success({"items": list_resumes(current_user=current_user)})


@router.get("/{resume_id}")
async def get_resume_detail(resume_id: str, current_user: dict = Depends(get_current_user)):
    resume = get_resume(current_user=current_user, resume_id=resume_id)
    if not resume:
        return api_error("Resume not found")
    return api_success(resume)


@router.get("/{resume_id}/file")
async def get_resume_file(resume_id: str, current_user: dict = Depends(get_current_user)):
    resume = get_resume(current_user=current_user, resume_id=resume_id)
    if not resume:
        return api_error("Resume not found")
    path = safe_storage_path(resume["storage_key"])
    return FileResponse(path, media_type="application/pdf", filename=resume["original_filename"])


@router.delete("/{resume_id}")
async def delete_resume_detail(resume_id: str, current_user: dict = Depends(get_current_user)):
    deleted = delete_resume(current_user=current_user, resume_id=resume_id)
    if not deleted:
        return api_error("Resume not found")
    return api_success({"deleted": True})
