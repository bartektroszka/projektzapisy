from django import template
from django.contrib.auth.models import User

from ..users import is_theses_board_member
from ..models import get_num_ungraded_for_emp


register = template.Library()


@register.simple_tag
def num_ungraded_theses(user: User):
    """
    Return the number of ungraded theses if the user is a theses board member.
    Returns 0 otherwise, since in that case the template won't show the number.
    """
    if not user.is_authenticated:
        return 0
    # this trycatch is a fix for dumb tests such as apps.users.tests.test_admin.AdminTestCase
    # which don't create user instances properly, resulting in weird
    # cases where the logged in user is neither a student nor an employee
    # (wrap_user throws in this case)
    try:
        if not is_theses_board_member(user):
            return 0
        return get_num_ungraded_for_emp(user)
    except ValueError:
        return 0
