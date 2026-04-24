from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Notebook, Page, ShareLink
from .permissions import IsNotebookOwner, IsPageOwner
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    NotebookSerializer,
    NotebookListSerializer,
    PageSerializer,
    SharedPageSerializer,
)


# ── Auth ─────────────────────────────────────────────────────────────────────

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    refresh = RefreshToken.for_user(user)
    return Response(
        {
            "user": UserSerializer(user).data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request):
    return Response(UserSerializer(request.user).data)


# ── Notebooks ─────────────────────────────────────────────────────────────────

class NotebookListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "GET":
            return NotebookListSerializer
        return NotebookSerializer

    def get_queryset(self):
        return Notebook.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class NotebookDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = NotebookSerializer
    permission_classes = [IsAuthenticated, IsNotebookOwner]

    def get_queryset(self):
        return Notebook.objects.filter(user=self.request.user)


# ── Pages ─────────────────────────────────────────────────────────────────────

class PageListCreateView(generics.ListCreateAPIView):
    serializer_class = PageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        notebook = get_object_or_404(Notebook, pk=self.kwargs["notebook_pk"], user=self.request.user)
        return notebook.pages.all()

    def perform_create(self, serializer):
        notebook = get_object_or_404(Notebook, pk=self.kwargs["notebook_pk"], user=self.request.user)
        max_order = notebook.pages.count()
        serializer.save(notebook=notebook, order=max_order)


class PageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PageSerializer
    permission_classes = [IsAuthenticated, IsPageOwner]

    def get_queryset(self):
        return Page.objects.filter(notebook__user=self.request.user)


# ── Share ─────────────────────────────────────────────────────────────────────

@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def page_share(request, pk):
    page = get_object_or_404(Page, pk=pk, notebook__user=request.user)

    if request.method == "POST":
        link, _ = ShareLink.objects.get_or_create(page=page, is_active=True)
        return Response({"token": str(link.token)}, status=status.HTTP_200_OK)

    # DELETE — revoke all active links
    ShareLink.objects.filter(page=page, is_active=True).update(is_active=False)
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([AllowAny])
def shared_page(request, token):
    link = get_object_or_404(ShareLink, token=token, is_active=True)
    serializer = SharedPageSerializer(link.page)
    return Response(serializer.data)
