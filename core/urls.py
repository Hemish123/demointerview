# from django.urls import path
# from core import views

# urlpatterns = [

#     path("", views.index),

#     path("api/domains/", views.api_domains),
#     path("api/roles/<str:domain_id>/", views.api_roles),

#     path("api/start/", views.api_start),
#     path("api/start-auto/", views.api_start_auto),

#     path("api/next/", views.api_next),

#     path("api/tts/", views.api_tts),
# ]



# core/urls.py
# from django.urls import path
# from core import views
# from django.http import HttpResponse

# def favicon(request):
#     return HttpResponse(status=204)

# urlpatterns = [

#     path("", views.index),

#     # predefined dropdown
#     path("api/start/", views.api_start),
#     path("api/domains/", views.api_domains),
#     path("api/roles/<str:domain_id>/", views.api_roles),

#     # JD auto
#     path("api/start-auto/", views.api_start_auto),
#     path("api/next/", views.api_next),
#     path("favicon.ico", favicon),
#     path("api/export/", views.api_export),
# ]



from django.urls import path
from core.views import (
    DomainsAPI,
    RolesAPI,
    StartInterviewAPI,
    StartAutoInterviewAPI,
    NextQuestionAPI,
    ExportInterviewAPI,
    index,
)

urlpatterns = [
    path("", index),

    path("api/v1/domains/", DomainsAPI.as_view()),
    path("api/v1/roles/<str:domain_id>/", RolesAPI.as_view()),

    path("api/v1/start/", StartInterviewAPI.as_view()),
    path("api/v1/start-auto/", StartAutoInterviewAPI.as_view()),
    path("api/v1/next/", NextQuestionAPI.as_view()),
    path("api/v1/export/", ExportInterviewAPI.as_view()),
]
