# -*- coding: utf-8 -*-

from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm

from apps.enrollment.courses.models import *
from apps.enrollment.records.models import Record, STATUS_REMOVED, STATUS_ENROLLED, Queue


class GroupForm(ModelForm):
    class Meta:
        model = Group

    def save(self, commit=True):
        group = super(GroupForm, self).save(commit=False)
        if group.id:
            group.course = Course.objects.select_for_update().get(id=group.course_id)
            old_one = Group.objects.get(id=group.id)
            while old_one.limit < group.limit:
                old_one.limit += 1
                old_one.limit_zamawiane = group.limit_zamawiane
                old_one.limit_zamawiane2012 = group.limit_zamawiane2012
                old_one.save()
                if old_one.queued > 0:
                    Group.do_rearanged(old_one)

                old_one = Group.objects.get(id=group.id)
                group.enrolled         = old_one.enrolled
                group.enrolled_zam     = old_one.enrolled_zam
                group.enrolled_zam2012 = old_one.enrolled_zam2012
                group.queued           = old_one.queued

            Group.do_rearanged(group)


        if commit:
            group.save()

        return group


class GroupInline(admin.TabularInline):
    model = Group
    extra = 0
    raw_id_fields = ("teacher",)
    form = GroupForm

class CourseAdmin(admin.ModelAdmin):
    list_display =('semester',)
    list_filter = ('semester',)
    search_fields = ('entity__name',)
    fieldsets = [
        (None,               {'fields': ['entity'], 'classes': ['long_name']}),
        ('Szczegóły', {'fields': ['records_start', 'records_end', 'numeryczna_l', 'dyskretna_l', 'teachers','semester','english','exam','suggested_for_first_year','slug','web_page'], 'classes': ['collapse']}),
    ]
    inlines = [GroupInline, ]


    def changelist_view(self, request, extra_context=None):

        if not request.GET.has_key('semester__id__exact'):

            q = request.GET.copy()
            semester = Semester.get_current_semester()
            q['semester__id__exact'] = semester.id
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super(CourseAdmin,self).changelist_view(request, extra_context=extra_context)

    def get_object(self, request, object_id):
        """
        Returns an instance matching the primary key provided. ``None``  is
        returned if no match is found (or the object_id failed validation
        against the primary key field).
        """
        queryset = self.queryset(request)
        model = queryset.model
        try:
            object_id = model._meta.pk.to_python(object_id)
            return queryset.select_related('semester').get(pk=object_id)
        except (model.DoesNotExist, ValidationError):
            return None

    def queryset(self, request):
       """
       Filter the objects displayed in the change_list to only
       display those for the currently signed in user.
       """
       qs = super(CourseAdmin, self).queryset(request)
       return qs.select_related('semester', 'type')

class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('number', 'capacity', 'building')
    list_filter = ('building','capacity')

class SemesterAdmin(admin.ModelAdmin):
    list_display = ('get_name', 'visible')
    list_filter = ('visible','year','type')
    fieldsets = [
        (None,               {'fields': ['year','type','visible']}),
        ('Ocena', {'fields': ['is_grade_active']}),
        ('Czas trwania semestru', {'fields': ['semester_beginning','semester_ending']}),
        ('Czas trwania zapisów', {'fields': ['records_opening','records_ects_limit_abolition','records_closing']}),
        ('Czas trwania dezyderat', {'fields': ['desiderata_opening', 'desiderata_closing']}),
    ]
    list_editable = ('visible',)

class CourseInline(admin.TabularInline):
    model = Course

class CourseEntityAdmin(admin.ModelAdmin):
    list_display = ('name', 'shortName', 'owner')
    search_fields = ('name', 'shortName', 'owner__user__first_name', 'owner__user__last_name' )
    fieldsets = [
        (None,               {'fields': ['name','shortName','type','description'], 'classes': ['long_name']}),
        (None,               {'fields': ['owner', 'status', 'semester', 'requirements']}),
        (None,               {'fields': ['english', 'exam', 'deleted']}),
        ('USOS',             {'fields': ['usos_kod'], 'classes': ['collapse']}),

    ]
    list_filter = ('semester', 'owner', 'status', 'type', )

    def queryset(self, request):
       """
       Filter the objects displayed in the change_list to only
       display those for the currently signed in user.
       """
       qs = super(CourseEntityAdmin, self).queryset(request)
       return qs.select_related('owner', 'owner__user', 'type')

class TermInline(admin.TabularInline):
    model = Term
    extra = 0

class RecordInlineForm(ModelForm):
    class Meta:
        model = Record

    def save(self, commit=True):

        record = super(RecordInlineForm, self).save(commit=False)

        if record.id:
            old = Record.objects.get(id=record.id)
            if old.status <> record.status:
                if record.status == STATUS_REMOVED:
                    record.group.remove_from_enrolled_counter(record.student)
                    Group.do_rearanged(record.group)
                elif  record.status == STATUS_ENROLLED:
                    record.group.add_to_enrolled_counter(record.student)
                    Queue.objects.filter(group=record.group, student=record.student, deleted=False).update(deleted=True)
                    record.group.queued = Queue.objects.filter(group=record.group, deleted=False).count()
                    record.group.save()

        else:
            if record.status == STATUS_REMOVED:
                pass
            elif  record.status == STATUS_ENROLLED:
                record.group.add_to_enrolled_counter(record.student)
                Queue.objects.filter(group=record.group, student=record.student, deleted=False).update(deleted=True)
                record.group.queued = Queue.objects.filter(group=record.group, deleted=False).count()
                record.group.save()

        if commit:
            record.save()

        return record


class RecordInline(admin.TabularInline):
    model = Record
    extra = 0
    raw_id_fields = ("student",)
    can_delete = False
    form = RecordInlineForm

class QueuedInlineForm(ModelForm):
    class Meta:
        model = Queue

    def save(self, commit=True):
        queue = super(QueuedInlineForm, self).save(commit=False)


        if queue.id:
            old = Queue.objects.get(id=queue.id)
            if not old.deleted and queue.deleted:
                queue.group.remove_from_queued_counter(queue.student)
            elif old.deleted and not queue.deleted:
                queue.group.add_to_queued_counter(queue.student)
        else:
            if not queue.deleted:
                queue.group.add_to_queued_counter(queue.student)

        if commit:
            queue.save()

        return queue

class QueuedInline(admin.TabularInline):
    model = Queue
    extra = 0
    raw_id_fields = ("student",)

    can_delete = False
    form=QueuedInlineForm

class GroupAdmin(admin.ModelAdmin):
    list_display = ('course', 'teacher','type','limit','limit_zamawiane','limit_zamawiane2012','get_terms_as_string')
    list_filter = ('type', 'course__semester', 'teacher')
    search_fields = ('teacher__user__first_name','teacher__user__last_name','course__name')
    inlines = [
        TermInline,RecordInline, QueuedInline
    ]

    form = GroupForm

    raw_id_fields = ('course', 'teacher')

    def changelist_view(self, request, extra_context=None):

        if not request.GET.has_key('course__semester__id__exact'):

            q = request.GET.copy()
            semester = Semester.get_current_semester()
            q['course__semester__id__exact'] = semester.id
            request.GET = q
            request.META['QUERY_STRING'] = request.GET.urlencode()
        return super(GroupAdmin,self).changelist_view(request, extra_context=extra_context)



    def queryset(self, request):
       """
       Filter the objects displayed in the change_list to only
       display those for the currently signed in user.
       """
       qs = super(GroupAdmin, self).queryset(request)
       return qs.select_related('teacher', 'teacher__user', 'course', 'course__semester', 'course__type').prefetch_related('term')

class TypeAdmin(admin.ModelAdmin):
    list_display = ('name','group','meta_type')
    list_filter = ('group','meta_type')


class TermAdmin(admin.ModelAdmin):

    def show_start(self, obj):
        return obj.start_time.strftime('%H:%M')

    def show_end(self, obj):
        return obj.end_time.strftime('%H:%M')

    fieldsets = [
        (None,               {'fields': ['group']}),
        ('Termin', {'fields': ['dayOfWeek','start_time','end_time']}),
        ('Miejsce', {'fields': ['classrooms',]}),
    ]
    list_filter = ('dayOfWeek', 'classrooms', 'group__course__semester')
    list_display = ('__unicode__','dayOfWeek','show_start','show_end', 'group')
    search_fields = ('group__course__name','group__teacher__user__first_name','group__teacher__user__last_name','dayOfWeek')
    ordering = ('dayOfWeek', 'start_time')
    raw_id_fields = ('group',)
    def queryset(self, request):
       """
       Filter the objects displayed in the change_list to only
       display those for the currently signed in user.
       """
       qs = super(TermAdmin, self).queryset(request)
       return qs.select_related('group', 'group__course', 'group__course__entity', 'group__teacher', 'group__teacher__user').prefetch_related('classrooms')

    def changelist_view(self, request, extra_context=None):
        semester = Semester.get_current_semester()
        if not request.GET.has_key('group__course__semester__id__exact'):
           q = request.GET.copy()
           q['group__course__semester__id__exact'] = semester.id
           request.GET = q
           request.META['QUERY_STRING'] = request.GET.urlencode()
            
        return super(TermAdmin,self).changelist_view(request, extra_context=extra_context)

class StudentOptionsAdmin(admin.ModelAdmin):
    list_display = ('__unicode__','records_opening_bonus_minutes')
    search_fields = ('course__name',)
    search_fields = ('student__matricula','student__user__first_name','student__user__last_name','course__name')


admin.site.register(Course)
admin.site.register(CourseDescription)
admin.site.register(CourseEntity)
admin.site.register(StudentOptions,StudentOptionsAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Classroom, ClassroomAdmin)
admin.site.register(Term, TermAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Type, TypeAdmin)
admin.site.register(PointTypes)
admin.site.register(PointsOfCourseEntities)