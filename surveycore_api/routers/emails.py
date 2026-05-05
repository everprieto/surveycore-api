"""Email sending router - independent generic email service."""
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..services.email_service import send_email, send_bulk_emails

router = APIRouter(prefix="/emails", tags=["emails"])


class SendEmailRequest(BaseModel):
    """Send single email request."""
    to_email: str
    to_name: str
    subject: str
    html_content: str
    plain_text: Optional[str] = None


class SendBulkEmailRequest(BaseModel):
    """Send multiple emails request."""
    recipients: List[Dict[str, str]]  # List of {email, name}
    subject: str
    html_content: str
    plain_text: Optional[str] = None


class SendEmailResponse(BaseModel):
    """Email sending response."""
    message_id: Optional[str] = None
    status: str
    error: Optional[str] = None


class SendBulkEmailResponse(BaseModel):
    """Bulk email sending response."""
    success_count: int
    failed_count: int
    total: int
    results: List[Dict[str, Any]]


@router.post("/send", response_model=SendEmailResponse)
def send_single_email(request: SendEmailRequest):
    """Send a single email."""
    result = send_email(
        to_email=request.to_email,
        to_name=request.to_name,
        subject=request.subject,
        html_content=request.html_content,
        plain_text=request.plain_text,
    )
    return result


@router.post("/send-bulk", response_model=SendBulkEmailResponse)
def send_multiple_emails(request: SendBulkEmailRequest):
    """Send multiple emails to different recipients."""
    if not request.recipients:
        raise HTTPException(status_code=400, detail="Recipients list is empty")

    result = send_bulk_emails(
        recipients=request.recipients,
        subject=request.subject,
        html_content=request.html_content,
        plain_text=request.plain_text,
    )
    return result
