# # core/views.py

# import os
# import uuid
# import json

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.parsers import MultiPartParser, FormParser

# from django.shortcuts import render
# from django.http import JsonResponse, FileResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.conf import settings
# from core.services.session_store import get_session
# from core.services import exporter

# from core.services.auto_ingest import ingest_document
# from core.services.terminal_interviewer import get_next_question
# from core.services.tts import synthesize_to_base64

# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# EXPORT_DIR = os.path.join(BASE_DIR, "exports")
# os.makedirs(EXPORT_DIR, exist_ok=True)


# # =====================================================
# # CONFIG
# # =====================================================

# UPLOAD_DIR = os.path.join(settings.BASE_DIR, "uploads")

# SESSIONS = {}   # session_id -> InterviewSession


# # =====================================================
# # PAGE
# # =====================================================

# def index(request):
#     return render(request, "index.html")


# # =====================================================
# # START AUTO JD MODE (ONLY ENTRY)
# # =====================================================

# @csrf_exempt
# def api_start_auto(request):

#     file = request.FILES.get("jd")

#     if not file:
#         return JsonResponse({"error": "No JD uploaded"}, status=400)

#     os.makedirs(UPLOAD_DIR, exist_ok=True)

#     fname = f"{uuid.uuid4()}_{file.name}"
#     path = os.path.join(UPLOAD_DIR, fname)

#     with open(path, "wb+") as f:
#         for c in file.chunks():
#             f.write(c)

#     # AUTO INGEST → creates temp master + session
#     session = ingest_document(path)

#     SESSIONS[session.session_id] = session

#     q = get_next_question(session)

#     return JsonResponse({
#         "session_id": session.session_id,
#         "question": q,
#         "audio": synthesize_to_base64(q["text"]),
#         "finished": False,
#     })


# # =====================================================
# # START PREDEFINED ROLE MODE
# # =====================================================

# @csrf_exempt
# def api_start(request):

#     data = json.loads(request.body)

#     role_id = data.get("designation")
#     role_label = data.get("role_label")

#     if not role_id:
#         return JsonResponse({"error": "No role selected"}, status=400)

#     # create fresh session
#     from core.services.session_store import create_session

#     session = create_session(
#         company=data.get("company", "JMS TechNova"),
#         role_label=role_label,
#         designation=role_id,
#     )

#     SESSIONS[session.session_id] = session

#     q = get_next_question(session)

#     return JsonResponse({
#         "session_id": session.session_id,
#         "question": q,
#         "audio": synthesize_to_base64(q["text"]),
#         "finished": False,
#     })


# # =====================================================
# # ANSWER → NEXT QUESTION
# # =====================================================

# @csrf_exempt
# def api_next(request):

#     data = json.loads(request.body)

#     session_id = data.get("session_id")
#     answer = data.get("answer", "")

#     session = SESSIONS.get(session_id)

#     if not session:
#         return JsonResponse({"error": "Invalid session"}, status=400)

#     session.last_answer = answer

#     q = get_next_question(session)

#     # =====================================================
#     # AUTO PDF GENERATION (ONLY ONCE, SERVER SIDE)
#     # =====================================================
#     if getattr(session, "finished", False) and not getattr(session, "_pdf_generated", False):
#         try:
#             from core.services import exporter

#             exporter.export_interview(
#                 session=session,
#                 output_dir="exports",
#                 format="pdf"
#             )

#             # prevent duplicate generation
#             session._pdf_generated = True

#             print(f"✅ Auto PDF generated for session {session.session_id}")

#         except Exception as e:
#             print("❌ AUTO PDF EXPORT FAILED:", e)

#     return JsonResponse({
#         "question": q,
#         "audio": synthesize_to_base64(q["text"]),
#         "finished": getattr(session, "finished", False),
#     })


# # =====================================================
# # PREDEFINED ROLE SUPPORT (MASTER FILE READER)
# # =====================================================

# MASTER_FILE = os.path.join(
#     settings.BASE_DIR,
#     "core",
#     "data",
#     "master_roles.json"
# )


# def _load_master_file():

#     if not os.path.exists(MASTER_FILE):
#         return {"domains": []}

#     with open(MASTER_FILE, "r", encoding="utf-8") as f:
#         return json.load(f)


# def api_domains(request):

#     master = _load_master_file()

#     return JsonResponse({
#         "domains": [
#             {
#                 "id": d["id"],
#                 "label": d["label"],
#             }
#             for d in master.get("domains", [])
#             if d.get("active")
#         ]
#     })


# def api_roles(request, domain_id):

#     master = _load_master_file()

#     for d in master.get("domains", []):
#         if d["id"] == domain_id:

#             return JsonResponse({
#                 "roles": [
#                     {
#                         "id": r["id"],
#                         "label": r["label"],
#                     }
#                     for r in d.get("roles", [])
#                     if r.get("active")
#                 ]
#             })

#     return JsonResponse({"roles": []})






# @csrf_exempt
# def api_export(request):

#     if request.method != "POST":
#         return JsonResponse({"error": "POST required"}, status=400)

#     try:
#         data = json.loads(request.body)

#         session_id = data.get("session_id")
#         fmt = data.get("format")   # pdf / docx / json / csv

#         if not session_id or not fmt:
#             return JsonResponse({"error": "Missing params"}, status=400)

#         session = get_session(session_id)

#         if not session or not session.finished:
#             return JsonResponse({"error": "Invalid session"}, status=400)

#         filepath = exporter.export_interview(
#             session=session,
#             output_dir=EXPORT_DIR,
#             format=fmt,
#         )

#         filename = os.path.basename(filepath)

#         return JsonResponse({
#             "success": True,
#             "file": filename
#         })

#     except Exception as e:
#         return JsonResponse({"error": str(e)}, status=500)


































import os
import uuid
import json

from django.shortcuts import render
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.authentication import SessionAuthentication


from core.services.auto_ingest import ingest_document
from core.services.role_orchestrator import get_next_question
from core.services.tts import synthesize_to_base64
from core.services.session_store import (
    create_session,
    get_session,
    save_session,
)
from core.services import exporter

from core.models import (
    InterviewSession,
    InterviewTurn,
    UploadedDocument,
    InterviewExport,
)

# =====================================================
# PATHS
# =====================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPORT_DIR = os.path.join(BASE_DIR, "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)

MASTER_FILE = os.path.join(
    settings.BASE_DIR,
    "core",
    "data",
    "master_roles.json"
)

# =====================================================
# PAGE
# =====================================================

def index(request):
    return render(request, "index.html")

# =====================================================
# HELPERS
# =====================================================

def _load_master_file():
    if not os.path.exists(MASTER_FILE):
        return {"domains": []}

    with open(MASTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    


class CsrfExemptSessionAuthentication(SessionAuthentication):
    def enforce_csrf(self, request):
        return  # Skip CSRF check


# =====================================================
# API: DOMAINS
# =====================================================

class DomainsAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]
    """
    GET /api/v1/domains/
    """

    def get(self, request):
        master = _load_master_file()

        domains = [
            {
                "id": d["id"],
                "label": d["label"],
            }
            for d in master.get("domains", [])
            if d.get("active")
        ]

        return Response(
            {"domains": domains},
            status=status.HTTP_200_OK
        )

# =====================================================
# API: ROLES
# =====================================================

class RolesAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]
    """
    GET /api/v1/roles/<domain_id>/
    """

    def get(self, request, domain_id):
        master = _load_master_file()

        for d in master.get("domains", []):
            if d["id"] == domain_id:
                roles = [
                    {
                        "id": r["id"],
                        "label": r["label"],
                    }
                    for r in d.get("roles", [])
                    if r.get("active")
                ]

                return Response(
                    {"roles": roles},
                    status=status.HTTP_200_OK
                )

        return Response(
            {"roles": []},
            status=status.HTTP_200_OK
        )
    




# =====================================================
# API: START INTERVIEW (ROLE MODE)
# =====================================================

from core.serializers import StartInterviewSerializer


class StartInterviewAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = StartInterviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        session = create_session(
            company=data["company"],
            role_label=data.get("role_label"),
            designation=data["designation"],
        )

        InterviewSession.objects.create(
            id=session.session_id,
            session_type="role",
            company=data["company"],
            role_label=data.get("role_label"),
            designation=data["designation"],
            finished=False,
        )

        q = get_next_question(session)
        save_session(session)

        return Response(
            {
                "session_id": session.session_id,
                "question": q,
                "audio": synthesize_to_base64(q["text"]),
                "finished": False,
            },
            status=status.HTTP_200_OK
        )





# =====================================================
# API: START INTERVIEW (JD MODE)
# =====================================================

from core.serializers import StartAutoInterviewSerializer


class StartAutoInterviewAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = StartAutoInterviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        file = serializer.validated_data["jd"]

        doc = UploadedDocument.objects.create(
            original_name=file.name,
            file=file
        )

        session = ingest_document(doc.file.path)

        InterviewSession.objects.create(
            id=session.session_id,
            session_type="jd",
            company="JMS TechNova",
            finished=False,
        )

        q = get_next_question(session)
        save_session(session)

        return Response(
            {
                "session_id": session.session_id,
                "question": q,
                "audio": synthesize_to_base64(q["text"]),
                "finished": False,
            },
            status=status.HTTP_200_OK
        )





# =====================================================
# API: NEXT QUESTION
# =====================================================

from core.serializers import NextQuestionSerializer


class NextQuestionAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = NextQuestionSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data
        session_id = str(data["session_id"])
        answer = data.get("answer", "")

        session = get_session(session_id)

        if not session:
            return Response(
                {"error": "Invalid session"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.last_answer = answer
        q = get_next_question(session)
        save_session(session)

        question_index = InterviewTurn.objects.filter(
            session_id=session_id
        ).count() + 1

        InterviewTurn.objects.create(
            session_id=session_id,
            question_text=q["text"],
            answer_text=answer,
            question_index=question_index,
        )

        return Response(
            {
                "question": q,
                "audio": synthesize_to_base64(q["text"]),
                "finished": getattr(session, "finished", False),
            },
            status=status.HTTP_200_OK
        )



# =====================================================
# API: EXPORT INTERVIEW
# =====================================================

from core.serializers import ExportInterviewSerializer


class ExportInterviewAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ExportInterviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        data = serializer.validated_data

        session = get_session(str(data["session_id"]))

        if not session or not session.finished:
            return Response(
                {"error": "Invalid session"},
                status=status.HTTP_400_BAD_REQUEST
            )

        filepath = exporter.export_interview(
            session=session,
            output_dir=EXPORT_DIR,
            format=data["format"],
        )

        InterviewExport.objects.create(
            session_id=data["session_id"],
            format=data["format"],
            file=os.path.basename(filepath)
        )

        return Response(
            {
                "success": True,
                "file": os.path.basename(filepath)
            },
            status=status.HTTP_200_OK
        )
