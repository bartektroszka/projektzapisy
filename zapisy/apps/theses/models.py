from datetime import datetime

from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from apps.users.models import Employee, Student

from .enums import ThesisKind, ThesisStatus
from .managers import APIManager

MAX_THESIS_TITLE_LEN = 300


class Thesis(models.Model):
    """Represents a thesis in the theses system.

    A Thesis instance can represent a thesis in many different
    configurations (an idea submitted by an employee, a work in progress
    by a student, or a thesis defended years ago). This is accomplished
    through various possible combinations of mainly the 'status' and 'student'
    fields, as described in more detail below.

    A thesis is first added typically by a regular university employee;
    they are then automatically assigned as the advisor.

    Before the thesis can be assigned to a student, the theses board
    must first determine whether it is suitable; this is facilitated by the
    voting logic. If the thesis is accepted as submitted,
    its status is then automatically changed to either 'in progress' if the advisor
    has assigned a student, or 'accepted' otherwise.
    The advisor is then permitted to change its status to 'archived'
    after the student completes and presents it.
    """

    objects = models.Manager()
    rest_objects = APIManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Save the status so that, when saving, we can determine whether or not it changed
        # See https://stackoverflow.com/a/1793323
        self.__original_status = self.status
        # See get_students
        self.__sort_criterion = "{}.id".format(Thesis.students.through._meta.db_table)

    title = models.CharField(max_length=MAX_THESIS_TITLE_LEN, unique=True)
    # the related_name's below are necessary because we have multiple foreign keys pointing
    # to the same model and Django isn't smart enough to generate unique reverse accessors
    advisor = models.ForeignKey(
        Employee, on_delete=models.PROTECT, blank=True, null=True,
        related_name='thesis_advisor'
    )
    supporting_advisor = models.ForeignKey(
        Employee, on_delete=models.PROTECT, blank=True, null=True,
        related_name='thesis_supporting_advisor'
    )
    kind = models.SmallIntegerField(choices=ThesisKind.choices())
    status = models.SmallIntegerField(choices=ThesisStatus.choices())
    # How long the assigned student(s) has/have to complete their work on this thesis
    # Note that this is only a convenience field for the users, the system
    # does not enforce this in any way
    reserved_until = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    students = models.ManyToManyField(Student, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    # A thesis is _modified_ when its status changes
    modified = models.DateTimeField(auto_now_add=True)

    def is_archived(self):
        return self.status == ThesisStatus.DEFENDED

    def has_any_students_assigned(self):
        """Check if this thesis has any students assigned.

        NOTICE: this will query the DB. For processing multiple theses,
        you should annotate each object instead.
        """
        return self.students.all().exists()

    def get_students(self):
        """Get all the students assigned to this thesis in the proper order
        (students.all() doesn't order them properly)
        """
        return self.students.order_by(self.__sort_criterion)

    def set_students(self, students):
        """Given an interable of students, assign them as to this thesis.

        We don't use ManyToManyRelatedManager#set as it doesn't maintain the
        order in which items are specified, which matters to us here
        (the add() with multiple argument has the same problem - we need to execute
        a query per student to ensure they're appended to the end of the table
        in the order we want. In practice this is not a problem as we always have just a few
        students per thesis at most)
        """
        self.students.clear()
        for student in students:
            self.students.add(student)

    def __str__(self) -> str:
        return self.title

    def clean(self):
        """Ensure that the title never contains superfluous whitespace"""
        self.title = self.title.strip()

    def _adjust_status(self):
        """If there is at least one student and the thesis has been accepted,
        we automatically move it to "in progress"; conversely,
        if it was in progress but the students have been removed, go back to accepted
        """
        current_status = ThesisStatus(self.status)
        has_students = self.has_any_students_assigned()
        if current_status == ThesisStatus.ACCEPTED and has_students:
            self.status = ThesisStatus.IN_PROGRESS
        elif current_status == ThesisStatus.IN_PROGRESS and not has_students:
            self.status = ThesisStatus.ACCEPTED
        if self.status != self.__original_status:
            # If the status changed, update modified date
            self.modified = datetime.now()
            self.__original_status = self.status

    def save(self, *args, **kwargs):
        self.full_clean()
        skip = kwargs.pop("skip_status_update", False)
        if self.id and not skip:
            self._adjust_status()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "praca dyplomowa"
        verbose_name_plural = "prace dyplomowe"


@receiver(m2m_changed, sender=Thesis.students.through)
def thesis_students_changed(sender, **kwargs):
    """After the `students` field changes for a thesis,
    we should adjust the status according to the logic defined in
    `Thesis._adjust_status`.

    This has to be done via a signal because m2m relationships are not
    usable until all objects have been saved to the DB and have IDs available
    for use, so doing this in save() would not be enough: for instance,
    a new thesis is created, its save() method runs, no students are yet
    defined, so its status is set to accepted. Only after the save()
    method exits, the students can be defined, but this is not picked up
    by the save method since it's not run again.

    However: we still need to update the status in save() because
    theoretically, this may need to be done even without any changes
    to the `students` field: the advisor may change the status to 'accepted'
    with some students already defined, at which point we should immediately
    move it to 'in progress'
    """
    instance = kwargs["instance"]
    instance._adjust_status()
    instance.save(skip_status_update=True)
