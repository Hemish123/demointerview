from rest_framework import serializers
from django.core.validators import RegexValidator


class StartInterviewSerializer(serializers.Serializer):
    designation = serializers.CharField(max_length=100)
    role_label = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    company = serializers.CharField(
        max_length=100,
        default="JMS TechNova"
    )
    candidate_name = serializers.CharField(max_length=30)
    candidate_email = serializers.EmailField(max_length=254)
    candidate_phone = serializers.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\d+$',
                message='Phone number must contain only digits.',
            )
        ]
    )


class StartAutoInterviewSerializer(serializers.Serializer):
    jd = serializers.FileField()



class NextQuestionSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    answer = serializers.CharField(
        required=False,
        allow_blank=True
    )


class ExportInterviewSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    format = serializers.ChoiceField(
        choices=["pdf", "docx", "json", "csv"]
    )
