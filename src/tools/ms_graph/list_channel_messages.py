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


def _summarize_attachments(attachments: list[dict[str, Any]]) -> list[dict[str, str]]:
    result = []
    for att in attachments:
        result.append(
            {
                "id": att.get("id", ""),
                "contentType": att.get("contentType", ""),
                "name": att.get("name", ""),
                "contentUrl": att.get("contentUrl", ""),
            }
        )
    return result


def list_channel_messages(team_id: str, channel_id: str, limit: int = 20) -> str:
    headers = auth_headers(SCOPES)
    url = f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages?$top={min(limit, 50)}"

    resp = requests.get(url, headers=headers)
    if not resp.ok:
        return f"Error fetching messages: {resp.status_code} {resp.text}"

    messages: list[dict[str, Any]] = []
    for msg in resp.json().get("value", []):
        if msg.get("messageType") != "message":
            continue

        body = msg.get("body", {})
        body_text = body.get("content", "")
        if body.get("contentType") == "html":
            body_text = _strip_html(body_text)

        preview = body_text[:200] + ("..." if len(body_text) > 200 else "")
        sender = msg.get("from", {})
        user = sender.get("user", {}) if sender else {}
        attachments = msg.get("attachments", [])

        messages.append(
            {
                "id": msg["id"],
                "subject": msg.get("subject", "") or "",
                "sender": user.get("displayName", "Unknown"),
                "createdDateTime": msg.get("createdDateTime", ""),
                "preview": preview,
                "attachmentCount": len(attachments),
                "replyCount": (
                    msg.get("replyCount", 0)
                    if "replyCount" not in msg
                    else msg["replyCount"]
                ),
            }
        )

    return json.dumps({"count": len(messages), "messages": messages}, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python list_channel_messages.py <TEAM_ID> <CHANNEL_ID> [LIMIT]")
        sys.exit(1)
    lim = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    print(list_channel_messages(sys.argv[1], sys.argv[2], lim))
