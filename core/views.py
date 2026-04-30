
import os
import uuid
import json
import threading

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
            candidate_name=data.get("candidate_name"),
        )

        InterviewSession.objects.create(
            id=session.session_id,
            session_type="role",
            company=data["company"],
            role_label=data.get("role_label"),
            designation=data["designation"],
            candidate_name=data.get("candidate_name"),
            candidate_email=data.get("candidate_email"),
            candidate_phone=data.get("candidate_phone"),
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
# ANALYSIS PDF EXPORT HELPER
# =====================================================

def _export_analysis_pdf(session_id, candidate_name, role, transcript, evaluation):
    """Generate a detailed analysis PDF with circular gauges and company logo."""
    import math
    from datetime import datetime
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    )
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.graphics.shapes import Drawing, Circle, Wedge, String, Line
    from reportlab.graphics import renderPDF

    os.makedirs(EXPORT_DIR, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    fname = f"analysis_{session_id}_{ts}.pdf"
    path = os.path.join(EXPORT_DIR, fname)

    styles = getSampleStyleSheet()
    story = []

    # ── LOGO + TITLE HEADER ──
    logo_path = os.path.join(settings.BASE_DIR, "static", "JMS .png")
    header_data = []
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=60, height=60)
        header_data = [[
            logo,
            Paragraph(
                '<b>JMS TechNova</b><br/>'
                '<font size="10" color="#666666">Interview Analysis Report</font>',
                ParagraphStyle(
                    "HeaderTitle",
                    parent=styles["Title"],
                    fontSize=18,
                    leading=22,
                    alignment=0,
                )
            )
        ]]
    else:
        header_data = [[
            "",
            Paragraph(
                '<b>JMS TechNova</b><br/>'
                '<font size="10" color="#666666">Interview Analysis Report</font>',
                styles["Title"]
            )
        ]]

    header_table = Table(header_data, colWidths=[75, 425])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8))

    # ── CANDIDATE INFO ──
    info_style = ParagraphStyle("Info", parent=styles["Normal"], fontSize=10, leading=14)
    date_str = datetime.now().strftime("%B %d, %Y  %I:%M %p")
    story.append(Paragraph(f'<b>Candidate:</b> {candidate_name}', info_style))
    story.append(Paragraph(f'<b>Role:</b> {role}', info_style))
    story.append(Paragraph(f'<b>Date:</b> {date_str}', info_style))
    story.append(Spacer(1, 16))

    # ── SEPARATOR ──
    sep_drawing = Drawing(500, 2)
    sep_drawing.add(Line(0, 1, 500, 1, strokeColor=colors.HexColor("#3f51b5"), strokeWidth=1.5))
    story.append(sep_drawing)
    story.append(Spacer(1, 12))

    # ── CIRCULAR GAUGES ──
    def _gauge_color(val):
        if val >= 70: return colors.HexColor("#2e7d32")   # green
        if val >= 40: return colors.HexColor("#f57c00")   # orange
        return colors.HexColor("#c62828")                  # red

    def _draw_gauge(val, label, size=80):
        """Create a circular gauge Drawing."""
        d = Drawing(size + 20, size + 30)
        cx, cy = (size + 20) / 2, (size + 30) / 2 + 6
        r = size / 2 - 4

        # Background circle (light grey)
        d.add(Circle(cx, cy, r, fillColor=colors.HexColor("#e0e0e0"),
                      strokeColor=colors.HexColor("#bdbdbd"), strokeWidth=0.5))

        # Foreground wedge (score arc)
        if val > 0:
            angle = 360 * (val / 100)
            gauge_color = _gauge_color(val)
            d.add(Wedge(cx, cy, r, 90, 90 - angle,
                        fillColor=gauge_color, strokeColor=None, strokeWidth=0))

        # Inner white circle (donut effect)
        inner_r = r * 0.65
        d.add(Circle(cx, cy, inner_r, fillColor=colors.white,
                      strokeColor=None, strokeWidth=0))

        # Value text
        d.add(String(cx, cy - 5, f"{val}%",
                      fontSize=12, fontName="Helvetica-Bold",
                      fillColor=colors.HexColor("#212121"), textAnchor="middle"))

        # Label below
        d.add(String(cx, 6, label,
                      fontSize=7, fontName="Helvetica-Bold",
                      fillColor=colors.HexColor("#424242"), textAnchor="middle"))

        return d

    overall = evaluation.get("overall_score", 0)
    confidence = evaluation.get("confidence_percent", 0)
    knowledge = evaluation.get("knowledge_percent", 0)
    domain = evaluation.get("domain_percent", 0)
    communication = evaluation.get("communication_percent", 0)

    gauges = [
        _draw_gauge(overall, "Score"),
        _draw_gauge(confidence, "Confidence"),
        _draw_gauge(knowledge, "Knowledge"),
        _draw_gauge(domain, "Domain"),
        _draw_gauge(communication, "Communication"),
    ]

    # Section title
    story.append(Paragraph(
        '<b>Performance Overview</b>',
        ParagraphStyle("GaugeTitle", parent=styles["Heading2"],
                       textColor=colors.HexColor("#1a237e"), fontSize=14)
    ))
    story.append(Spacer(1, 6))

    gauge_table = Table([gauges], colWidths=[100, 100, 100, 100, 100])
    gauge_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(gauge_table)
    story.append(Spacer(1, 16))

    # ── SUMMARY ──
    summary = evaluation.get("summary", "No summary available.")
    story.append(Paragraph('<b>Evaluation Summary</b>',
                           ParagraphStyle("SumTitle", parent=styles["Heading3"],
                                          textColor=colors.HexColor("#1a237e"))))
    story.append(Spacer(1, 4))

    summary_style = ParagraphStyle(
        "SummaryBox", parent=styles["Normal"],
        fontSize=9, leading=13,
        backColor=colors.HexColor("#e8eaf6"),
        borderPadding=10,
        borderColor=colors.HexColor("#3f51b5"),
        borderWidth=1,
        borderRadius=4,
    )
    story.append(Paragraph(summary, summary_style))
    story.append(Spacer(1, 16))

    # ── Q&A TABLE ──
    story.append(Paragraph('<b>Question-by-Question Analysis</b>',
                           ParagraphStyle("QATitle", parent=styles["Heading3"],
                                          textColor=colors.HexColor("#1a237e"))))
    story.append(Spacer(1, 6))

    per_q = evaluation.get("per_question", [])
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=10)

    qa_data = [["#", "Question", "Answer", "Score", "Remark"]]
    for i, t in enumerate(transcript):
        pq = per_q[i] if i < len(per_q) else {}
        score = pq.get("score", "-")
        remark = pq.get("remark", "")
        qa_data.append([
            str(t["index"]),
            Paragraph(t["question"][:200], small),
            Paragraph((t["answer"] or "No answer")[:300], small),
            f"{score}/10",
            Paragraph(remark[:150], small),
        ])

    qa_table = Table(qa_data, colWidths=[22, 145, 165, 38, 130])
    qa_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bdbdbd")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
    ]))
    story.append(qa_table)

    # ── FOOTER ──
    story.append(Spacer(1, 20))
    footer_style = ParagraphStyle("Footer", parent=styles["Normal"],
                                   fontSize=7, textColor=colors.grey, alignment=1)
    story.append(Paragraph(
        f"Generated by JMS TechNova AI Interview System | {date_str}",
        footer_style
    ))

    doc = SimpleDocTemplate(path, pagesize=A4,
                            leftMargin=25*mm, rightMargin=25*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    doc.build(story)

    return path


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

        is_finished = getattr(session, "finished", False)

        # ── POST-INTERVIEW PIPELINE ──
        if is_finished:
            try:
                db_session = InterviewSession.objects.filter(id=session_id).first()
                candidate_email = db_session.candidate_email if db_session else None
                candidate_name = db_session.candidate_name if db_session else "Candidate"
                role_label = db_session.role_label if db_session else "Unknown"

                # 1. Send immediate completion email
                if candidate_email:
                    from core.services.email_service import send_interview_completion_email
                    send_interview_completion_email(candidate_email)
                    print(f"✅ Email 1 (completion) sent to {candidate_email}")

                # 2. Schedule analysis + export + delayed email (5 min)
                def _run_analysis():
                    try:
                        print(f"🔄 Running analysis for session {session_id}...")

                        # Fetch all Q&A turns from DB
                        turns = InterviewTurn.objects.filter(
                            session_id=session_id
                        ).order_by("question_index")

                        turn_data = [
                            {"question": t.question_text, "answer": t.answer_text}
                            for t in turns
                        ]

                        transcript = [
                            {
                                "index": t.question_index,
                                "question": t.question_text,
                                "answer": t.answer_text,
                            }
                            for t in turns
                        ]

                        # Run LLM evaluation
                        from core.services.llm_engine import LLMEngine
                        engine = LLMEngine()
                        evaluation = engine.evaluate_interview(role_label, turn_data)

                        print(f"✅ Evaluation complete — Score: {evaluation.get('overall_score', 0)}/100")

                        # Export analysis PDF to exports folder
                        pdf_path = _export_analysis_pdf(
                            session_id, candidate_name, role_label,
                            transcript, evaluation
                        )
                        print(f"✅ Analysis PDF exported: {pdf_path}")

                        # Save export record to DB
                        InterviewExport.objects.create(
                            session_id=session_id,
                            format="pdf",
                            file=os.path.basename(pdf_path),
                        )

                        # Send detailed analysis email with PDF
                        if candidate_email:
                            from core.services.email_service import send_analysis_email
                            send_analysis_email(
                                to_email=candidate_email,
                                candidate_name=candidate_name,
                                role=role_label,
                                evaluation=evaluation,
                                transcript=transcript,
                                pdf_path=pdf_path,
                            )
                            print(f"✅ Email 2 (analysis) sent to {candidate_email}")

                    except Exception as e:
                        print(f"❌ Analysis pipeline failed: {e}")
                        import traceback
                        traceback.print_exc()

                # Schedule for 5 minutes (300 seconds)
                timer = threading.Timer(300, _run_analysis)
                timer.daemon = True
                timer.start()
                print(f"⏰ Analysis scheduled for 5 minutes from now")

            except Exception as e:
                print(f"❌ Post-interview pipeline error: {e}")

        return Response(
            {
                "question": q,
                "audio": synthesize_to_base64(q["text"]),
                "finished": is_finished,
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


# =====================================================
# API: EVALUATE INTERVIEW
# =====================================================

from core.services.llm_engine import LLMEngine

_eval_llm = LLMEngine()


class EvaluateInterviewAPI(APIView):

    authentication_classes = [CsrfExemptSessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        session_id = request.data.get("session_id")

        if not session_id:
            return Response(
                {"error": "session_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session_id = str(session_id)

        # Fetch DB session
        try:
            db_session = InterviewSession.objects.get(id=session_id)
        except InterviewSession.DoesNotExist:
            return Response(
                {"error": "Session not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Fetch all turns ordered by question_index
        turns = InterviewTurn.objects.filter(
            session_id=session_id
        ).order_by("question_index")

        if not turns.exists():
            return Response(
                {"error": "No interview data found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Build transcript
        transcript = []
        for t in turns:
            transcript.append({
                "question": t.question_text,
                "answer": t.answer_text or "(No response)",
                "index": t.question_index,
            })

        # Get role label
        role_label = db_session.role_label or db_session.designation or "General"

        # Call LLM evaluation
        evaluation = _eval_llm.evaluate_interview(
            role=role_label,
            turns=transcript,
        )

        return Response(
            {
                "candidate_name": db_session.candidate_name or "Unknown",
                "role": role_label,
                "transcript": transcript,
                "evaluation": evaluation,
            },
            status=status.HTTP_200_OK
        )

