# import json
# import os
# import sys
# import time

# BASE_DIR = os.path.dirname(
#     os.path.dirname(
#         os.path.dirname(os.path.abspath(__file__))
#     )
# )

# if BASE_DIR not in sys.path:
#     sys.path.insert(0, BASE_DIR)


# from core.services.session_store import create_session
# from core.services.role_orchestrator import get_next_question
# from core.services import stt, tts
# from core.services import exporter


# # -------------------------------------------------
# # BASE PATH
# # -------------------------------------------------

# MASTER_FILE = os.path.join(BASE_DIR, "core", "data", "master_roles.json")


# # -------------------------------------------------
# # MASTER HELPERS
# # -------------------------------------------------

# def load_master_roles():
#     with open(MASTER_FILE, "r", encoding="utf-8") as f:
#         return json.load(f)


# def list_domains_from_master(master):
#     return [d for d in master["domains"] if d.get("active")]


# def list_roles_from_master(master, domain_id):

#     for d in master["domains"]:
#         if d["id"] == domain_id:
#             return [r for r in d["roles"] if r.get("active")]

#     return []


# # =====================================================
# # 🔵 NEW — COMMON INTERVIEW RUNNER (manual + auto JD)
# # =====================================================
# def run_interview(session):

#     print("\n🎙️ VOICE AI INTERVIEW ENGINE (LLM Screening Mode)\n")

#     # ------------------------------------------
#     # AUTO MODE CHECK
#     # ------------------------------------------

#     auto_mode = False

#     if len(sys.argv) > 1 and sys.argv[1] == "--auto":
#         auto_mode = True

#     # ------------------------------------------
#     # AUTO JD INGEST MODE
#     # ------------------------------------------

#     if auto_mode:

#         from core.services.auto_ingest import ingest_document

#         print("\n📂 AUTO JD MODE ENABLED")

#         jd_path = input("\nEnter JD file path: ").strip()

#         if not os.path.exists(jd_path):
#             print("❌ File not found:", jd_path)
#             return

#         session = ingest_document(jd_path)

#         print("\n==============================")
#         print("🎧 Interview started")
#         print("==============================\n")

#     # ------------------------------------------
#     # MANUAL MODE (OLD FLOW)
#     # ------------------------------------------

#     else:

#         master = load_master_roles()

#         domains = list_domains_from_master(master)

#         print("Available Domains:")
#         for idx, d in enumerate(domains, 1):
#             print(f"{idx}. {d['label']}")

#         d_idx = int(input("\nSelect Domain: ")) - 1
#         selected_domain = domains[d_idx]

#         roles = list_roles_from_master(master, selected_domain["id"])

#         print("\nAvailable Roles:")
#         for idx, r in enumerate(roles, 1):
#             print(f"{idx}. {r['label']}")

#         r_idx = int(input("\nSelect Role: ")) - 1
#         selected_role = roles[r_idx]

#         session = create_session(
#             company="JMS TechNova",
#             role_label=selected_role["label"],
#             designation=selected_role["id"],
#         )

#         print("\n==============================")
#         print("🎧 Interview started")
#         print("==============================\n")

#     # ------------------------------------------
#     # INTERVIEW LOOP (UNCHANGED)
#     # ------------------------------------------

#     while True:

#         q = get_next_question(session)

#         print("\n🤖:", q["text"])
#         tts.speak(q["text"])

#         if q["id"] == "end":
#             break

#         print("\n🎙️ Listening...")
#         answer = stt.listen()

#         print("👤:", answer)

#         session.last_answer = answer
#         session.answers[q["id"]] = answer

#         time.sleep(0.6)

#     # ------------------------------------------
#     # EXPORT
#     # ------------------------------------------

#     print("\n\n✅ INTERVIEW COMPLETE")

#     print("\n📄 Do you want to export this interview?")
#     print("1. PDF")
#     print("2. Word (.docx)")
#     print("3. JSON")
#     print("4. CSV")
#     print("5. Skip")

#     choice = input("\nSelect option: ").strip()

#     export_dir = os.path.join(BASE_DIR, "exports")
#     os.makedirs(export_dir, exist_ok=True)

#     if choice in {"1", "2", "3", "4"}:

#         fmt_map = {
#             "1": "pdf",
#             "2": "docx",
#             "3": "json",
#             "4": "csv",
#         }

#         fmt = fmt_map[choice]

#         filepath = exporter.export_interview(
#             session=session,
#             output_dir=export_dir,
#             format=fmt,
#         )

#         print(f"\n📁 Interview exported successfully:")
#         print(filepath)

#     else:
#         print("\n📌 Export skipped.")



# # =====================================================
# # MANUAL TERMINAL ENTRY
# # =====================================================

# def main():

#     print("\n🎙️ VOICE AI INTERVIEW ENGINE (LLM Screening Mode)\n")

#     master = load_master_roles()

#     # ---------- SELECT DOMAIN ----------
#     domains = list_domains_from_master(master)

#     print("Available Domains:")
#     for idx, d in enumerate(domains, 1):
#         print(f"{idx}. {d['label']}")

#     d_idx = int(input("\nSelect Domain: ")) - 1
#     selected_domain = domains[d_idx]

#     # ---------- SELECT ROLE ----------
#     roles = list_roles_from_master(master, selected_domain["id"])

#     print("\nAvailable Roles:")
#     for idx, r in enumerate(roles, 1):
#         print(f"{idx}. {r['label']}")

#     r_idx = int(input("\nSelect Role: ")) - 1
#     selected_role = roles[r_idx]

#     # ---------- CREATE SESSION ----------
#     session = create_session(
#         company="JMS TechNova",
#         role_label=selected_role["label"],
#         designation=selected_role["id"],
#     )

#     # ---------- RUN INTERVIEW ----------
#     run_interview(session)


# if __name__ == "__main__":
#     main()

































import json
import os
import sys
import time
import argparse

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


from urllib.parse import urlparse, unquote
import tkinter as tk
from tkinter import filedialog


from core.services.session_store import create_session
from core.services.role_orchestrator import get_next_question
from core.services import stt, tts, exporter

# AUTO INGEST
from core.services.auto_ingest import ingest_document


MASTER_FILE = os.path.join(BASE_DIR, "core", "data", "master_roles.json")


# -------------------------------------------------
# MASTER HELPERS
# -------------------------------------------------

def load_master_roles():
    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def list_domains_from_master(master):
    return [d for d in master["domains"] if d.get("active")]


def list_roles_from_master(master, domain_id):
    for d in master["domains"]:
        if d["id"] == domain_id:
            return [r for r in d["roles"] if r.get("active")]
    return []


# -------------------------------------------------
# INTERVIEW LOOP
# -------------------------------------------------

def run_interview(session):

    print("\n==============================")
    print("🎧 Interview started")
    print("==============================\n")

    while True:

        q = get_next_question(session)

        print("\n🤖:", q["text"])
        tts.speak(q["text"])

        if q["id"] == "end":
            break

        print("\n🎙️ Listening...")
        answer = stt.listen()

        print("👤:", answer)

        session.last_answer = answer
        session.answers[q["id"]] = answer

        time.sleep(0.6)

    # ---------------- EXPORT ----------------

    print("\n\n✅ INTERVIEW COMPLETE")

    print("\n📄 Do you want to export this interview?")
    print("1. PDF")
    print("2. Word (.docx)")
    print("3. JSON")
    print("4. CSV")
    print("5. Skip")

    choice = input("\nSelect option: ").strip()

    export_dir = os.path.join(BASE_DIR, "exports")
    os.makedirs(export_dir, exist_ok=True)

    if choice in {"1", "2", "3", "4"}:

        fmt_map = {
            "1": "pdf",
            "2": "docx",
            "3": "json",
            "4": "csv",
        }

        fmt = fmt_map[choice]

        filepath = exporter.export_interview(
            session=session,
            output_dir=export_dir,
            format=fmt,
        )

        print("\n📁 Interview exported successfully:")
        print(filepath)

    else:
        print("\n📌 Export skipped.")


# -------------------------------------------------
# MAIN
# -------------------------------------------------

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--auto", action="store_true", help="Auto JD mode")

    args = parser.parse_args()

    print("\n🎙️ VOICE AI INTERVIEW ENGINE (LLM Screening Mode)\n")

    # =====================================================
    # AUTO MODE
    # =====================================================

    if args.auto:

        print("\n📂 AUTO JD MODE ENABLED\n")

        # -------- FILE PICKER --------
        root = tk.Tk()
        root.withdraw()

        jd_path = filedialog.askopenfilename(
            title="Select JD File",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("Word files", "*.docx"),
                ("Text files", "*.txt"),
            ],
        )

        if not jd_path:
            print("❌ No file selected.")
            return

        # -------- URI FIX --------
        if jd_path.startswith("file:///"):
            parsed = urlparse(jd_path)
            jd_path = unquote(parsed.path.lstrip("/"))

        print("📄 Selected file:", jd_path)

        if not os.path.exists(jd_path):
            print("❌ File not found:", jd_path)
            return

        session = ingest_document(jd_path)

        run_interview(session)
        return


    # =====================================================
    # NORMAL MODE
    # =====================================================

    master = load_master_roles()

    domains = list_domains_from_master(master)

    print("Available Domains:")
    for idx, d in enumerate(domains, 1):
        print(f"{idx}. {d['label']}")

    d_idx = int(input("\nSelect Domain: ")) - 1
    selected_domain = domains[d_idx]

    roles = list_roles_from_master(master, selected_domain["id"])

    print("\nAvailable Roles:")
    for idx, r in enumerate(roles, 1):
        print(f"{idx}. {r['label']}")

    r_idx = int(input("\nSelect Role: ")) - 1
    selected_role = roles[r_idx]

    session = create_session(
        company="JMS TechNova",
        role_label=selected_role["label"],
        designation=selected_role["id"],
    )

    run_interview(session)


if __name__ == "__main__":
    main()
