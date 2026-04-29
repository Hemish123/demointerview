# core/services/master_registry.py

import json
import os
import re

TEMP_MASTER = "core/data/temp_master.json"
DATASET_ROOT = "core/data/domains/temp_ingested"


def _slug(text):

    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def register_temp_roles(role_data, datasets):

    """
    role_data:
      {
        domain: "...",
        roles: [{"label": "..."}]
      }

    datasets:
      { role_id: dataset_path }
    """

    os.makedirs(DATASET_ROOT, exist_ok=True)

    domain_id = _slug(role_data["domain"])

    blob = {
        "id": domain_id,
        "label": role_data["domain"],
        "active": True,
        "roles": [],
    }

    for r in role_data["roles"]:

        rid = _slug(r["label"])

        blob["roles"].append({
            "id": rid,
            "label": r["label"],
            "dataset": datasets[rid],
            "experience": r.get("level"),
            "active": True,
        })

    with open(TEMP_MASTER, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "temp",
                "source": "auto_ingest",
                "domains": [blob],
            },
            f,
            indent=2,
        )

    return TEMP_MASTER
