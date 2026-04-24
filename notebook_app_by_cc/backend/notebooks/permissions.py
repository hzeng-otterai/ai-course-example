from rest_framework.permissions import BasePermission


class IsNotebookOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsPageOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.notebook.user == request.user
