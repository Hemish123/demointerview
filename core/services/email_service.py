from django.core.mail import send_mail, EmailMessage
from django.conf import settings


def send_interview_completion_email(to_email):
    """Email 1: Sent immediately after interview finishes."""

    subject = "🎉 Interview Completed – JMS TechNova"

    message = """
Hi,

Thank you for completing your interview with JMS TechNova.

We are currently analyzing your performance.
You will receive a detailed report with your scores and feedback within a few minutes.

Best regards,
JMS TechNova Interview Team
"""

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [to_email],
        fail_silently=False,
    )


def send_analysis_email(to_email, candidate_name, role, evaluation, transcript, pdf_path=None):
    """
    Email 2: Sent 5 minutes after interview.
    Sends ONLY the PDF attachment — no body content.
    """

    subject = f"📊 Interview Analysis Report – {role} | JMS TechNova"

    body = (
        f"Hi {candidate_name},\n\n"
        f"Please find attached your detailed Interview Analysis Report "
        f"for the {role} position at JMS TechNova.\n\n"
        f"Best regards,\n"
        f"JMS TechNova Interview Team"
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )

    # Attach PDF
    if pdf_path:
        try:
            import os
            if os.path.exists(pdf_path):
                email.attach_file(pdf_path)
        except Exception as e:
            print(f"⚠️ Could not attach PDF: {e}")

    email.send(fail_silently=False)