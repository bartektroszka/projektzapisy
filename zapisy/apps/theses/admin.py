from django.contrib import admin

from . import models
from .forms import ThesisForm


class ThesisAdmin(admin.ModelAdmin):
    autocomplete_fields = ['advisor', 'supporting_advisor']
    form = ThesisForm


admin.site.register(models.Thesis, ThesisAdmin)
