import uuid
from django.db import models


class InterviewSession(models.Model):
    """
    Represents one interview run (JD-based or role-based)
    """

    SESSION_TYPE_CHOICES = (
        ("jd", "JD Based"),
        ("role", "Predefined Role"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    session_type = models.CharField(
        max_length=10,
        choices=SESSION_TYPE_CHOICES
    )

    company = models.CharField(max_length=100, default="JMS TechNova")

    role_label = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    designation = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    finished = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"InterviewSession {self.id}"


class InterviewTurn(models.Model):
    """
    One question-answer turn in an interview
    """

    session = models.ForeignKey(
        InterviewSession,
        related_name="turns",
        on_delete=models.CASCADE
    )

    question_text = models.TextField()
    answer_text = models.TextField(blank=True)

    question_index = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Turn {self.question_index} - {self.session.id}"




class UploadedDocument(models.Model):
    """
    Stores uploaded JD files
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name





class InterviewExport(models.Model):
    """
    Stores exported interview reports
    """

    EXPORT_FORMATS = (
        ("pdf", "PDF"),
        ("docx", "DOCX"),
        ("json", "JSON"),
        ("csv", "CSV"),
    )

    session = models.ForeignKey(
        InterviewSession,
        related_name="exports",
        on_delete=models.CASCADE
    )

    format = models.CharField(max_length=10, choices=EXPORT_FORMATS)

    file = models.FileField(upload_to="exports/")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.session.id} ({self.format})"
