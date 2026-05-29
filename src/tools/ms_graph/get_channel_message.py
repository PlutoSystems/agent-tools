import sys
import json
import re
import requests
from typing import Any
from tools.ms_graph.auth import auth_headers, GRAPH_BASE

SCOPES = ["https://graph.microsoft.com/ChannelMessage.Read.All"]


def _strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _format_attachment(att: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    info: dict[str, Any] = {
        "id": att.get("id", ""),
        "contentType": att.get("contentType", ""),
        "name": att.get("name", ""),
        "contentUrl": att.get("contentUrl", ""),
    }

    if att.get("contentType") == "reference" and att.get("contentUrl"):
        drive_url = (
            f"{GRAPH_BASE}/shares/u!{_encode_sharing_url(att['contentUrl'])}/driveItem"
        )
        resp = requests.get(drive_url, headers=headers)
        if resp.ok:
            item = resp.json()
            info["size"] = item.get("size")
            info["mimeType"] = item.get("file", {}).get("mimeType", "")
            info["downloadUrl"] = item.get("@microsoft.graph.downloadUrl", "")
            info["webUrl"] = item.get("webUrl", "")

    return info


def _encode_sharing_url(url: str) -> str:
    import base64

    encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
    return encoded


def _format_message(msg: dict[str, Any]) -> dict[str, Any]:
    body = msg.get("body", {})
    body_text = body.get("content", "")
    if body.get("contentType") == "html":
        body_text = _strip_html(body_text)

    sender = msg.get("from", {})
    user = sender.get("user", {}) if sender else {}

    return {
        "id": msg["id"],
        "sender": user.get("displayName", "Unknown"),
        "createdDateTime": msg.get("createdDateTime", ""),
        "body": body_text,
    }


def get_channel_message(team_id: str, channel_id: str, message_id: str) -> str:
    headers = auth_headers(SCOPES)
    base = f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages/{message_id}"

    resp = requests.get(base, headers=headers)
    if not resp.ok:
        return f"Error fetching message: {resp.status_code} {resp.text}"

    msg = resp.json()
    body = msg.get("body", {})
    body_text = body.get("content", "")
    if body.get("contentType") == "html":
        body_text = _strip_html(body_text)

    sender = msg.get("from", {})
    user = sender.get("user", {}) if sender else {}

    attachments = [
        _format_attachment(att, headers) for att in msg.get("attachments", [])
    ]

    # Fetch replies
    replies: list[dict[str, Any]] = []
    replies_url: str | None = f"{base}/replies?$top=50"
    while replies_url:
        resp = requests.get(replies_url, headers=headers)
        if not resp.ok:
            break
        data = resp.json()
        for reply in data.get("value", []):
            if reply.get("messageType") != "message":
                continue
            r = _format_message(reply)
            r["attachments"] = [
                _format_attachment(a, headers) for a in reply.get("attachments", [])
            ]
            replies.append(r)
        replies_url = data.get("@odata.nextLink")

    result: dict[str, Any] = {
        "id": msg["id"],
        "subject": msg.get("subject", "") or "",
        "sender": user.get("displayName", "Unknown"),
        "createdDateTime": msg.get("createdDateTime", ""),
        "body": body_text,
        "attachments": attachments,
        "replyCount": len(replies),
        "replies": replies,
    }

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(
            "Usage: python get_channel_message.py <TEAM_ID> <CHANNEL_ID> <MESSAGE_ID>"
        )
        sys.exit(1)
    print(get_channel_message(sys.argv[1], sys.argv[2], sys.argv[3]))
