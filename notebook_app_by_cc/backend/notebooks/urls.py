from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path("auth/register/", views.register, name="register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", views.me, name="me"),

    # Notebooks
    path("notebooks/", views.NotebookListCreateView.as_view(), name="notebook-list"),
    path("notebooks/<int:pk>/", views.NotebookDetailView.as_view(), name="notebook-detail"),

    # Pages (nested under notebook)
    path("notebooks/<int:notebook_pk>/pages/", views.PageListCreateView.as_view(), name="page-list"),

    # Pages (standalone)
    path("pages/<int:pk>/", views.PageDetailView.as_view(), name="page-detail"),
    path("pages/<int:pk>/share/", views.page_share, name="page-share"),

    # Public shared page
    path("shared/<uuid:token>/", views.shared_page, name="shared-page"),
]
