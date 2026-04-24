import uuid
from django.db import models
from django.contrib.auth.models import User


class Notebook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notebooks")
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title


class Page(models.Model):
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=255, default="Untitled")
    content = models.JSONField(default=dict)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title


class ShareLink(models.Model):
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="share_links")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Share({self.page.title}, {self.token})"
