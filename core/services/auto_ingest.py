# core/services/auto_ingest.py
import sys
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from core.services.file_loader import load_document
from core.services.role_detector import detect_domains_and_roles
from core.services.master_registry import register_temp_roles
from core.services.session_store import create_session
from core.services.dataset_builder import build_basic_dataset


def ingest_document(path: str):
    """
    Full ingestion pipeline:
    File → Text → Role Detection → Master Mapping → Session
    """

    print("\n📄 Loading document...")
    text = load_document(path)

    if not text.strip():
        raise RuntimeError("Document contains no readable text")

    print("🤖 Detecting domain and role from document...")

    detected = detect_domains_and_roles(text)

    if not detected:
        raise RuntimeError("Could not detect role from document")

    print("📌 Detected:", detected)

    print("🔎 Matching with master registry...")

    # -------------------------------
    # 🔧 FIX-1: build datasets first
    # -------------------------------

    datasets = {}

    for r in detected["roles"]:
        path = build_basic_dataset(
            detected["domain"],
            r["label"],
        )

        rid = os.path.basename(path).replace(".json", "")
        datasets[rid] = path

    # -------------------------------
    # 🔧 FIX-2: proper registry call
    # -------------------------------

    master_path = register_temp_roles(
        detected,
        datasets,
    )

    if not master_path:
        raise RuntimeError("Detected role not registered into temp master")

    # ---- pick first role for session ----
    first_role = detected["roles"][0]

    session = create_session(
        company="JMS TechNova",
        role_label=first_role["label"],
        designation=first_role["label"],
    )

    return session

if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: python auto_ingest.py <jd_file>")
        sys.exit(1)

    jd_path = sys.argv[1]

    session = ingest_document(jd_path)

    # 🚀 START INTERVIEW
    from core.services.terminal_interviewer import run_interview

    run_interview(session)

