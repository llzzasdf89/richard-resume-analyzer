from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from controllers.report_controller import delete_report, get_report, list_reports
from core.responses import api_error, api_success
from core.security import get_current_user
from services.file_storage_service import safe_storage_path

router = APIRouter(prefix="/reports")


@router.get("")
async def get_reports(current_user: dict = Depends(get_current_user)):
    return api_success({"items": list_reports(current_user=current_user)})


@router.get("/{report_id}")
async def get_report_detail(report_id: str, current_user: dict = Depends(get_current_user)):
    report = get_report(current_user=current_user, report_id=report_id)
    if not report:
        return api_error("Report not found")
    return api_success(report)


@router.get("/{report_id}/file")
async def get_report_file(report_id: str, current_user: dict = Depends(get_current_user)):
    report = get_report(current_user=current_user, report_id=report_id)
    if not report:
        return api_error("Report not found")
    path = safe_storage_path(report["storage_key"])
    return FileResponse(path, media_type="application/pdf", filename=f"{report['title']}.pdf")


@router.delete("/{report_id}")
async def delete_report_detail(report_id: str, current_user: dict = Depends(get_current_user)):
    deleted = delete_report(current_user=current_user, report_id=report_id)
    if not deleted:
        return api_error("Report not found")
    return api_success({"deleted": True})
