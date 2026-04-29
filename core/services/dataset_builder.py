import json
import os
import re

BASE_DATA = "core/data/domains/temp_ingested"


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def build_basic_dataset(domain, role_label):

    rid = _slug(role_label)

    os.makedirs(BASE_DATA, exist_ok=True)

    path = os.path.join(BASE_DATA, f"{rid}.json")

    dataset = {
        "domain": domain,
        "designation": rid,
        "label": role_label,
        "opening": (
            f"Welcome to the {role_label} interview. "
            "We will begin with a short screening round."
        ),
        "flow_type": "llm_screening",
        "sections": [
            {
                "id": "core_skills",
                "title": "Core Skills",
                "questions": []
            }
        ]
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    return path
