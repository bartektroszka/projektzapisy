"""This module defines high-level thesis-related permissions
checks used when deserializing a received thesis object and performing actions.
"""
from apps.users.models import Employee, BaseUser

from .models import Thesis, ThesisStatus
from .users import ThesisUserType, get_user_type, is_theses_board_member, is_admin


def is_thesis_staff(user: BaseUser) -> bool:
    """Determine whether the user should be considered a "staff member" in the theses system"""
    return is_admin(user) or is_theses_board_member(user)


def can_add_thesis(user: BaseUser) -> bool:
    """Is the given user permitted to add new thesis objects?"""
    user_type = get_user_type(user)
    return user_type != ThesisUserType.student


def is_owner_of_thesis(user: BaseUser, thesis: Thesis) -> bool:
    """Is the specified user the advisor of the specified thesis?"""
    return thesis.advisor == user


def can_modify_thesis(user: BaseUser, thesis: Thesis) -> bool:
    """Is the specified user permitted to make any changes to the specified thesis?"""
    if thesis.is_archived():
        return is_admin(user)
    return is_thesis_staff(user) or is_owner_of_thesis(user, thesis)


def can_change_title(user: BaseUser, thesis: Thesis) -> bool:
    """Is the specified user permitted to change the title of the specified thesis?"""
    allowed_statuses = [ThesisStatus.being_evaluated, ThesisStatus.returned_for_corrections]
    return (
        is_thesis_staff(user) or
        is_owner_of_thesis(user, thesis) and ThesisStatus(thesis.status) in allowed_statuses
    )


def can_set_status(user: BaseUser, status: ThesisStatus) -> bool:
    """Can a user of the specified type set the specified status for a new thesis?"""
    return is_thesis_staff(user) or status == ThesisStatus.being_evaluated


def can_change_status(user: BaseUser) -> bool:
    """Can a user of the specified type modify an existing thesis' status?"""
    return is_thesis_staff(user)


def can_set_advisor(user: BaseUser, advisor: Employee) -> bool:
    """Is the specified user permitted to set the given advisor (may be None)?"""
    return is_thesis_staff(user) or user == advisor