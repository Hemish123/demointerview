from django.contrib import admin
from core.models import (
    InterviewSession,
    InterviewTurn,
    UploadedDocument,
    InterviewExport
)


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "session_type",
        "candidate_name",
        "candidate_email",
        "candidate_phone",
        "company",
        "designation",
        "finished",
        "created_at",
    )
    list_filter = ("session_type", "finished")
    search_fields = ("company", "designation", "role_label", "candidate_name", "candidate_email")


@admin.register(InterviewTurn)
class InterviewTurnAdmin(admin.ModelAdmin):
    list_display = (
        "session",  
        "question_index",
        "created_at",
    )
    list_filter = ("session",)


@admin.register(UploadedDocument)
class UploadedDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "original_name",
        "uploaded_at",
    )


@admin.register(InterviewExport)
class InterviewExportAdmin(admin.ModelAdmin):
    list_display = (
        "session",
        "format",
        "created_at",
    )
