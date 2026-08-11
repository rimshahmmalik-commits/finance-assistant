import os
import base64
from email.message import EmailMessage

import requests
import msal

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


# ==================================================
# GMAIL
# ==================================================

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]


def get_gmail_service():
    credentials = None

    token_file = "gmail_token.json"
    credentials_file = "gmail_credentials.json"

    if os.path.exists(token_file):
        credentials = Credentials.from_authorized_user_file(
            token_file,
            GMAIL_SCOPES
        )

    if not credentials or not credentials.valid:

        if (
            credentials
            and credentials.expired
            and credentials.refresh_token
        ):
            credentials.refresh(
                Request()
            )

        else:
            if not os.path.exists(
                credentials_file
            ):
                raise FileNotFoundError(
                    "gmail_credentials.json was not found."
                )

            flow = (
                InstalledAppFlow.from_client_secrets_file(
                    credentials_file,
                    GMAIL_SCOPES
                )
            )

            credentials = flow.run_local_server(
                port=0
            )

        with open(
            token_file,
            "w"
        ) as token:
            token.write(
                credentials.to_json()
            )

    return build(
        "gmail",
        "v1",
        credentials=credentials
    )


def send_gmail(
    recipient,
    subject,
    body
):
    service = get_gmail_service()

    message = EmailMessage()

    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    encoded_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    result = (
        service.users()
        .messages()
        .send(
            userId="me",
            body={
                "raw": encoded_message
            }
        )
        .execute()
    )

    return {
        "success": True,
        "provider": "Gmail",
        "message_id": result.get("id")
    }


# ==================================================
# MICROSOFT / OUTLOOK
# ==================================================

def get_microsoft_access_token():
    client_id = os.getenv(
        "MICROSOFT_CLIENT_ID"
    )

    tenant_id = os.getenv(
        "MICROSOFT_TENANT_ID",
        "common"
    )

    if not client_id:
        raise ValueError(
            "MICROSOFT_CLIENT_ID is missing."
        )

    authority = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}"
    )

    app = msal.PublicClientApplication(
        client_id,
        authority=authority
    )

    scopes = [
        "Mail.Send"
    ]

    accounts = app.get_accounts()

    if accounts:
        result = app.acquire_token_silent(
            scopes,
            account=accounts[0]
        )

        if result and "access_token" in result:
            return result["access_token"]

    flow = app.initiate_device_flow(
        scopes=scopes
    )

    if "user_code" not in flow:
        raise RuntimeError(
            "Could not start Microsoft login."
        )

    print(
        "\nMICROSOFT LOGIN\n"
    )

    print(
        flow["message"]
    )

    result = (
        app.acquire_token_by_device_flow(
            flow
        )
    )

    if "access_token" not in result:
        raise RuntimeError(
            result.get(
                "error_description",
                "Microsoft authentication failed."
            )
        )

    return result["access_token"]


def send_microsoft_email(
    recipient,
    subject,
    body
):
    token = get_microsoft_access_token()

    endpoint = (
        "https://graph.microsoft.com/"
        "v1.0/me/sendMail"
    )

    payload = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "Text",
                "content": body
            },
            "toRecipients": [
                {
                    "emailAddress": {
                        "address": recipient
                    }
                }
            ]
        }
    }

    response = requests.post(
        endpoint,
        headers={
            "Authorization": (
                f"Bearer {token}"
            ),
            "Content-Type": (
                "application/json"
            )
        },
        json=payload,
        timeout=30
    )

    if response.status_code not in [
        200,
        202
    ]:
        raise RuntimeError(
            f"Microsoft email failed: "
            f"{response.text}"
        )

    return {
        "success": True,
        "provider": "Microsoft"
    }


# ==================================================
# UNIVERSAL SENDER
# ==================================================

def send_email(
    provider,
    recipient,
    subject,
    body
):
    provider = (
        provider
        .strip()
        .lower()
    )

    if provider == "gmail":
        return send_gmail(
            recipient,
            subject,
            body
        )

    if provider in [
        "outlook",
        "microsoft",
        "microsoft 365",
        "hotmail"
    ]:
        return send_microsoft_email(
            recipient,
            subject,
            body
        )

    raise ValueError(
        f"Unsupported email provider: "
        f"{provider}"
    )