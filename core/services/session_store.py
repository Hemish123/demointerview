# core/services/session_store.py

import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import uuid

# =====================================================
# PERSISTENCE CONFIG
# =====================================================

SESSION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_sessions")
os.makedirs(SESSION_DIR, exist_ok=True)

# =====================================================
# IN-MEMORY SESSION REGISTRY (Fallback/Cache)
# =====================================================

_SESSIONS: Dict[str, "InterviewSession"] = {}


# =====================================================
# SESSION STATE OBJECT
# =====================================================

@dataclass
class InterviewSession:

    # -------- identity --------
    session_id: str
    company: str
    role_label: str
    designation: str

    # -------- conversation state --------
    phase: str = "intro"
    finished: bool = False

    candidate_name: Optional[str] = None

    last_answer: Optional[str] = None

    answers: Dict[str, str] = field(default_factory=dict)

    # -------- screening topic loop --------
    topics_asked: List[str] = field(default_factory=list)
    current_topic: Optional[str] = None
    awaiting_experience: bool = False

    # -------- HR block --------
    llm_hr_count: int = 0
    hr_limit: Optional[int] = None


# =====================================================
# PERSISTENCE HELPERS
# =====================================================

def save_session(session: InterviewSession):
    """
    Saves full session state to a JSON file.
    Includes dynamically added attributes.
    """
    filepath = os.path.join(SESSION_DIR, f"{session.session_id}.json")
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session.__dict__, f, indent=4)
    except Exception as e:
        print(f"❌ Error saving session {session.session_id}: {e}")


# =====================================================
# FACTORY
# =====================================================

def create_session(company: str, role_label: str, designation: str):

    session = InterviewSession(
        session_id=str(uuid.uuid4()),
        company=company,
        role_label=role_label,
        designation=designation,
    )

    # ✅ STORE SESSION
    _SESSIONS[session.session_id] = session
    save_session(session)

    return session


# =====================================================
# ACCESSOR (CRITICAL)
# =====================================================

def get_session(session_id: str) -> Optional[InterviewSession]:
    filepath = os.path.join(SESSION_DIR, f"{session_id}.json")
    
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            session = InterviewSession(
                session_id=data.get("session_id", ""),
                company=data.get("company", ""),
                role_label=data.get("role_label", ""),
                designation=data.get("designation", ""),
            )
            # Restore all dynamically added properties
            session.__dict__.update(data)
            _SESSIONS[session_id] = session
            return session
        except Exception as e:
            print(f"❌ Error loading session {session_id}: {e}")
            
    return _SESSIONS.get(session_id)