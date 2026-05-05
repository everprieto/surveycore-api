"""Azure Communication Services Email integration."""
from azure.communication.email import EmailClient
from typing import List, Optional, Dict, Any
import os


def get_email_client() -> EmailClient:
    """Initialize Azure Communication Services Email client."""
    connection_string = os.getenv("AZURE_COMMUNICATION_CONNECTION_STRING")
    if not connection_string:
        raise ValueError("AZURE_COMMUNICATION_CONNECTION_STRING not set in environment")
    return EmailClient.from_connection_string(connection_string)


def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Send a single email via Azure Communication Services.

    Args:
        to_email: Recipient email address
        to_name: Recipient display name
        subject: Email subject
        html_content: HTML body content
        plain_text: Plain text body (optional)
        attachments: List of attachment dicts with name, contentType, contentInBase64

    Returns:
        dict with keys: message_id, status, error (if failed)
    """
    sender = "DoNotReply@6605ddb4-825d-444a-bbdb-a64e9cf3cd2b.azurecomm.net"
    client = get_email_client()

    try:
        message: Dict[str, Any] = {
            "senderAddress": sender,
            "recipients": {
                "to": [{"address": to_email, "displayName": to_name}]
            },
            "content": {
                "subject": subject,
                "html": html_content,
            }
        }

        if plain_text:
            message["content"]["plainText"] = plain_text

        if attachments:
            message["attachments"] = attachments

        poller = client.begin_send(message)
        result = poller.result()

        return {
            "message_id": result.get("id") if isinstance(result, dict) else getattr(result, "id", None),
            "status": "Succeeded",
            "error": None,
        }

    except Exception as e:
        return {
            "message_id": None,
            "status": "Failed",
            "error": str(e),
        }


def send_bulk_emails(
    recipients: List[Dict[str, str]],
    subject: str,
    html_content: str,
    plain_text: Optional[str] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Send emails to multiple recipients.

    Args:
        recipients: List of dicts with keys: email, name
        subject: Email subject
        html_content: HTML body content
        plain_text: Plain text body (optional)
        attachments: Attachments list

    Returns:
        dict with keys: success_count, failed_count, total, results
    """
    success_count = 0
    failed_count = 0
    results = []

    for recipient in recipients:
        email = recipient.get("email")
        name = recipient.get("name", "Recipient")

        if not email:
            failed_count += 1
            results.append({
                "email": email,
                "status": "Failed",
                "error": "Missing email address",
                "message_id": None,
            })
            continue

        result = send_email(
            to_email=email,
            to_name=name,
            subject=subject,
            html_content=html_content,
            plain_text=plain_text,
            attachments=attachments,
        )

        if result["status"] == "Succeeded":
            success_count += 1
        else:
            failed_count += 1

        results.append({
            "email": email,
            "status": result["status"],
            "error": result["error"],
            "message_id": result["message_id"],
        })

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total": len(recipients),
        "results": results,
    }


def send_survey_emails(
    access_links: List[dict],
    survey_name: str,
    survey_type: str,
) -> dict:
    """
    Send survey access links to recipients.

    Args:
        access_links: List of dicts with keys: recipient_name, recipient_email, access_token
        survey_name: Name of the survey
        survey_type: Type of survey

    Returns:
        dict with keys: success_count, failed_count, total, errors
    """
    success_count = 0
    failed_count = 0
    errors = []

    for link in access_links:
        recipient_name = link.get("recipient_name", "Recipient")
        recipient_email = link.get("recipient_email")
        token = link.get("access_token")

        if not recipient_email or not token:
            failed_count += 1
            errors.append(f"Missing email or token for {recipient_name}")
            continue

        # Build survey URL
        base_url = os.getenv("SURVEY_BASE_URL", "http://localhost:5173")
        survey_url = f"{base_url}/survey/{token}"

        # Email template
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #c8102e;">We value your feedback</h2>
                    <p>Dear {recipient_name},</p>
                    <p>You have been invited to participate in a <strong>{survey_type}</strong> survey.</p>
                    <p><strong>Survey:</strong> {survey_name}</p>
                    <div style="margin: 30px 0;">
                        <a href="{survey_url}" style="background-color: #c8102e; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">
                            Take Survey
                        </a>
                    </div>
                    <p>Or copy and paste this link:</p>
                    <p style="word-break: break-all;"><a href="{survey_url}">{survey_url}</a></p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                    <p style="font-size: 12px; color: #999;">Your responses are confidential and will only be used to improve our services.</p>
                    <p style="font-size: 12px; color: #999;">SurveyCore © 2026</p>
                </div>
            </body>
        </html>
        """

        subject = f"Your {survey_type} Survey - {survey_name}"

        result = send_email(
            to_email=recipient_email,
            to_name=recipient_name,
            subject=subject,
            html_content=html_content,
        )

        if result["status"] == "Succeeded":
            success_count += 1
        else:
            failed_count += 1
            errors.append(f"Error sending to {recipient_email}: {result['error']}")

    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "errors": errors,
        "total": len(access_links),
    }
