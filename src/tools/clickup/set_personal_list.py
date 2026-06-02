import os
import re
import json
from tools.clickup import ROOT

_PERSONAL_CACHE = os.path.join(ROOT, "clickup", "personal_list.json")


def set_personal_list(list_id_or_url: str) -> str:
    match = re.search(r"/li/(\d+)", list_id_or_url)
    if match:
        list_id = match.group(1)
    elif list_id_or_url.strip().isdigit():
        list_id = list_id_or_url.strip()
    else:
        return "Error: Could not parse a list ID. Provide either a numeric list ID or a ClickUp list URL containing /li/<id>."

    os.makedirs(os.path.dirname(_PERSONAL_CACHE), exist_ok=True)
    with open(_PERSONAL_CACHE, "w") as f:
        json.dump({"list_id": list_id}, f, indent=2)

    return f"Personal List ID saved: {list_id}"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("list_id_or_url")
    args = parser.parse_args()
    print(set_personal_list(args.list_id_or_url))
