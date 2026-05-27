import sys
import os
import re
import json
import base64
from typing import Any
from datetime import datetime, timezone

import extract_msg


def sanitize(s: str | None) -> str:
    if not s:
        return ""
    return re.sub(r"[\t\n\r`]", " ", s).strip()


def format_address(name: str | None, email: str | None) -> str:
    name = sanitize(name)
    email = sanitize(email)
    if name and email and name != email:
        return f"{name} <{email}>"
    return email or name or ""


def parse_email(file_path: str) -> dict[str, Any]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext != ".msg":
        raise ValueError("Only .msg email files are supported currently")

    try:
        msg = extract_msg.Message(file_path)
    except Exception as err:
        return {
            "sentOn": int(datetime.now(timezone.utc).timestamp() * 1000),
            "from": "",
            "to": [],
            "cc": [],
            "bcc": [],
            "subject": "(parsing error)",
            "body": f"Failed to parse .msg file: {err}",
            "attachments": [],
        }

    sent_on = msg.date
    if isinstance(sent_on, str):
        try:
            sent_on = datetime.fromisoformat(sent_on)
        except ValueError:
            sent_on = None
    sent_timestamp = (
        int(sent_on.timestamp() * 1000)
        if sent_on
        else int(datetime.now(timezone.utc).timestamp() * 1000)
    )

    sender_name = msg.sender or ""
    sender_email = (
        getattr(msg, "senderSmtpAddress", None)
        or getattr(msg, "headerDict", {}).get("from", "")
        or sender_name
    )
    from_address = format_address(sender_name, sender_email)

    def split_addresses(field: str | None) -> list[str]:
        if not field:
            return []
        return [sanitize(addr) for addr in field.split(";") if addr.strip()]

    to = split_addresses(msg.to)
    cc = split_addresses(msg.cc)
    bcc = split_addresses(msg.bcc)

    subject = sanitize(msg.subject) or ""

    body = (msg.body or "").strip()
    body = re.sub(r"\s*[\r\n]+\s*", "\n\n", body)
    body = re.sub(r"[ \t]+", " ", body)
    body = re.sub(
        r"https?://[^\s]+",
        lambda m: "[LINK]" if len(m.group(0).encode("utf-8")) > 100 else m.group(0),
        body,
    )

    attachments: list[dict[str, Any]] = []
    for attach in msg.attachments:
        if not attach.name:
            continue
        if getattr(attach, "hidden", False):
            continue

        name = attach.name
        ext_part = name.rsplit(".", 1)[-1] if "." in name else ""
        content = attach.data if hasattr(attach, "data") else b""
        attachments.append(
            {
                "name": name,
                "extension": ext_part,
                "size": len(content) if content else 0,
                "mimeType": getattr(attach, "mimetype", "application/octet-stream")
                or "application/octet-stream",
                "content": base64.b64encode(content).decode("utf-8") if content else "",
            }
        )

    msg.close()

    return {
        "sentOn": sent_timestamp,
        "from": from_address,
        "to": to,
        "cc": cc,
        "bcc": bcc,
        "subject": subject,
        "body": body,
        "attachments": attachments,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_email.py <MSG_FILE_PATH>")
        sys.exit(1)

    result = parse_email(sys.argv[1])
    # Print without attachment content for readability
    display = {
        **result,
        "attachments": [
            {k: v for k, v in a.items() if k != "content"}
            for a in result["attachments"]
        ],
    }
    print(json.dumps(display, indent=2, default=str))
