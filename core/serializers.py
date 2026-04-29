from rest_framework import serializers


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
