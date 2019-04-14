from django.contrib import admin

from . import models


class ThesisAdmin(admin.ModelAdmin):
    autocomplete_fields = ['advisor', 'supporting_advisor']


admin.site.register(models.Thesis, ThesisAdmin)
