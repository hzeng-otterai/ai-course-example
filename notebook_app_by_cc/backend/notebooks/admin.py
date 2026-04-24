from django.contrib import admin
from .models import Notebook, Page, ShareLink

admin.site.register(Notebook)
admin.site.register(Page)
admin.site.register(ShareLink)
