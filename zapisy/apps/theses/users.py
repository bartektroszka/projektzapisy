"""Defines various utility functions related to operations
on users of the theses system"""

from django.contrib.auth.models import User
from apps.users.models import Employee, BaseUser, is_user_in_group

THESIS_BOARD_GROUP_NAME = "Komisja prac dyplomowych"


def is_theses_board_member(user: User) -> bool:
    """Is the specified user a member of the theses board?"""
    return is_user_in_group(user, THESIS_BOARD_GROUP_NAME)


def is_theses_admin(user: User):
    """Is the specified user an admin the thesis system?
    Currently fereol admins are also automatically thesis admins;
    restricting their permissions in the frontend client wouldn't
    make much sense as they're allowed to do anything in the Django admin
    interface
    """
    return user.is_staff


def is_theses_regular_employee(user: User):
    """Is the specified user a regular university employee?
    Those have permissions to create theses and can be set as advisors,
    but otherwise have no administrative privileges
    """
    return BaseUser.is_employee(user) and not user.is_staff


def get_theses_board():
    """Return all members of the theses board"""
    return Employee.objects.select_related(
        'user'
    ).filter(user__groups__name=THESIS_BOARD_GROUP_NAME)


def get_theses_user_full_name(user: User):
    """Returns the full name of the user for use by the theses system.
    If the user is an Employee, `get_full_name_with_academic_title` will be used;
    otherwise, `get_full_name` will be used.
    """
    if BaseUser.is_employee(user):
        return user.employee.get_full_name_with_academic_title()
    return user.get_full_name()
