from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
import uuid
from datetime import datetime

from apps.users.models import Student, Employee
from apps.notifications.datatypes import Notification
from apps.enrollment.courses.models.group import Group
from apps.enrollment.courses.views import course_view
from apps.enrollment.records.models import Record, RecordStatus
from apps.news.models import News
from apps.notifications.api import notify_user, notify_selected_users
from apps.notifications.custom_signals import teacher_changed, student_pulled, student_not_pulled
from apps.notifications.templates import NotificationType


def get_id() -> str:
    return str(uuid.uuid1())


def get_time() -> datetime:
    return datetime.now()


@receiver(student_pulled, sender=Record)
def notify_that_student_was_pulled_from_queue(sender: Record, **kwargs) -> None:
    group = kwargs['instance']
    target = reverse(course_view, args=[group.course.slug])

    notify_user(
        kwargs['user'],
        Notification(
            get_id(), get_time(), NotificationType.PULLED_FROM_QUEUE, {
                'course_name': group.course.name,
                'teacher': group.get_teacher_full_name(),
                'type': group.get_type_display(),
            }, target))


@receiver(student_not_pulled, sender=Record)
def notify_that_student_was_not_pulled_from_queue(sender: Record, **kwargs) -> None:
    group = kwargs['instance']
    target = reverse(course_view, args=[group.course.slug])

    notify_user(
        kwargs['user'],
        Notification(
            get_id(), get_time(), NotificationType.NOT_PULLED_FROM_QUEUE, {
                'course_name': group.course.name,
                'teacher': group.get_teacher_full_name(),
                'type': group.get_type_display(),
                'reason': kwargs['reason']
            }, target))


@receiver(post_save, sender=Group)
def notify_that_group_was_added_in_course(sender: Group, **kwargs) -> None:
    group = kwargs['instance']
    if not kwargs['created']:
        return
    course_groups = Group.objects.filter(course=group.course)
    course_name = group.course.name
    target = reverse(course_view, args=[group.course.slug])

    if group.teacher is not None:
        teacher = group.teacher.user

        notify_user(
            teacher,
            Notification(get_id(), get_time(), NotificationType.ASSIGNED_TO_NEW_GROUP_AS_A_TEACHER,
                         {'course_name': course_name}, target))

    enrolled_or_queued = [RecordStatus.ENROLLED, RecordStatus.QUEUED]
    records = Record.objects.filter(group__in=course_groups,
                                    status__in=enrolled_or_queued).select_related(
                                        'student', 'student__user')
    users = {element.student.user for element in records}
    notify_selected_users(
        users,
        Notification(get_id(), get_time(), NotificationType.ADDED_NEW_GROUP, {
            'course_name': course_name,
            'teacher': group.get_teacher_full_name()
        }, target))


@receiver(teacher_changed, sender=Group)
def notify_that_teacher_was_changed(sender: Group, **kwargs) -> None:
    group = kwargs['instance']

    if group.teacher is not None:
        teacher = group.teacher.user
        course_name = group.course.name
        target = reverse(course_view, args=[group.course.slug])

        notify_user(
            teacher,
            Notification(get_id(), get_time(), NotificationType.ASSIGNED_TO_NEW_GROUP_AS_A_TEACHER,
                         {'course_name': course_name}, target))

    queued_users = User.objects.filter(
        student__record__group=group, student__record__status=RecordStatus.QUEUED)

    enrolled_users = User.objects.filter(
        student__record__group=group, student__record__status=RecordStatus.ENROLLED)

    notify_selected_users(
        queued_users,
        Notification(
            get_id(), get_time(), NotificationType.TEACHER_HAS_BEEN_CHANGED_QUEUED, {
                'course_name': course_name,
                'teacher': group.get_teacher_full_name(),
                'type': group.get_type_display(),
            }, target))

    notify_selected_users(
        enrolled_users,
        Notification(
            get_id(), get_time(), NotificationType.TEACHER_HAS_BEEN_CHANGED_ENROLLED, {
                'course_name': course_name,
                'teacher': teacher.get_full_name(),
                'type': group.get_type_display(),
            }, target))


@receiver(post_save, sender=News)
def notify_that_news_was_added(sender: News, **kwargs) -> None:
    news = kwargs['instance']

    # Do not notify about modified news.
    if not kwargs['created']:
        return

    # Do not notify about hidden news.
    if news.category == '-':
        return

    records = set(Employee.get_actives().select_related('user')) | set(
        Student.objects.filter(status=0).select_related('user'))
    users = [element.user for element in records]
    target = reverse('news-one', args=[news.id])

    notify_selected_users(
        users,
        Notification(get_id(), get_time(), NotificationType.NEWS_HAS_BEEN_ADDED, {
            'title': news.title,
            'contents': news.body
        }, target))
