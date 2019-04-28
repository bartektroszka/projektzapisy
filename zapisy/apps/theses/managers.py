"""Defines a custom Theses manager for use by the Rest API,
with prefetching and several common filters
"""
from typing import List

from django.db import models

from django.db.models import Value, When, Case, BooleanField, QuerySet, Q
from django.db.models.functions import Concat, Lower

from apps.users.models import BaseUser
from .enums import (
    ThesisKind, ThesisStatus, ThesisTypeFilter,
    ENGINEERS_KINDS, BACHELORS_KINDS, BACHELORS_OR_ENGINEERS_KINDS,
    ISIM_KINDS, NOT_READY_STATUSES
)
from .users import ThesisUserType, is_student, get_user_type


class APIQueryset(models.QuerySet):
    def theses_filter(
        self, user: BaseUser, thesis_type: ThesisTypeFilter,
        title: str, advisor_name: str, only_mine: bool,
    ) -> QuerySet:
        result = self._thesis_type_filter(thesis_type)
        result = self._user_filter(result, user)
        if only_mine:
            result = self._only_mine_filter(result, user)
        if title:
            result = result.filter(title__icontains=title)
        if advisor_name:
            result = result.filter(_advisor_name__icontains=advisor_name)
        return result

    def filter_available(self: QuerySet) -> QuerySet:
        """Returns only theses that are considered "available" from the specified queryset"""
        return self.exclude(
            status=ThesisStatus.IN_PROGRESS
        ).exclude(_is_archived=True).filter(reserved_until__isnull=True)

    def filter_by_type(self: QuerySet, thesis_type: ThesisTypeFilter) -> QuerySet:
        """Returns only theses matching the specified type filter from the specified queryset"""
        if thesis_type == ThesisTypeFilter.EVERYTHING:
            return self
        elif thesis_type == ThesisTypeFilter.CURRENT:
            return self.exclude(_is_archived=True)
        elif thesis_type == ThesisTypeFilter.ARCHIVED:
            return self.filter(_is_archived=True)
        elif thesis_type == ThesisTypeFilter.MASTERS:
            return self.filter(kind=ThesisKind.MASTERS)
        elif thesis_type == ThesisTypeFilter.ENGINEERS:
            return self.filter(kind__in=ENGINEERS_KINDS)
        elif thesis_type == ThesisTypeFilter.BACHELORS:
            return self.filter(kind__in=BACHELORS_KINDS)
        elif thesis_type == ThesisTypeFilter.BACHELORS_OR_ENGINEERS:
            return self.filter(kind__in=BACHELORS_OR_ENGINEERS_KINDS)
        elif thesis_type == ThesisTypeFilter.ISIM:
            return self.filter(kind__in=ISIM_KINDS)
        elif thesis_type == ThesisTypeFilter.AVAILABLE_MASTERS:
            return self.available_thesis_filter(self.filter(kind=ThesisKind.MASTERS))
        elif thesis_type == ThesisTypeFilter.AVAILABLE_ENGINEERS:
            return self.available_thesis_filter(self.filter(kind__in=ENGINEERS_KINDS))
        elif thesis_type == ThesisTypeFilter.AVAILABLE_BACHELORS:
            return self.available_thesis_filter(self.filter(kind__in=BACHELORS_KINDS))
        elif thesis_type == ThesisTypeFilter.AVAILABLE_BACHELORS_OR_ENGINEERS:
            return self.available_thesis_filter(self.filter(kind__in=BACHELORS_OR_ENGINEERS_KINDS))
        elif thesis_type == ThesisTypeFilter.AVAILABLE_ISIM:
            return self.available_thesis_filter(self.filter(kind__in=ISIM_KINDS))
        # Should never get here
        return self

    def filter_by_user(self: QuerySet, user: BaseUser):
        """Filter the queryset based on special logic depending
        on the type of the user
        """
        # Students should not see theses that are not "ready" yet
        if is_student(user):
            return self.exclude(status__in=NOT_READY_STATUSES)
        return self

    def filter_by_title(self: QuerySet, title: str):
        return self.filter(title__icontains=title)

    def filter_by_advisor(self: QuerySet, advisor: str):
        return self.filter(_advisor_name__icontains=advisor)

    def filter_only_mine(self: QuerySet, user: BaseUser):
        user_type = get_user_type(user)
        if user_type == ThesisUserType.STUDENT:
            return self.filter(students__in=[user])
        return self.filter(Q(advisor=user) | Q(supporting_advisor=user))

    def sort(self: QuerySet, sort_column: str, sort_dir: str) -> QuerySet:
        """Sort the specified queryset first by archived status (unarchived theses first),
        then by the specified column in the specified direction,
        or by newest first if not specified
        """
        db_column = ""
        if sort_column == "advisor":
            db_column = "_advisor_name"
        elif sort_column == "title":
            db_column = "title"

        resulting_ordering = "-modified"
        if db_column:
            orderer = Lower(db_column)
            resulting_ordering = orderer.desc() if sort_dir == "desc" else orderer.asc()

        # We want to first order by archived
        return self.order_by("_is_archived", resulting_ordering)


class APIManager(models.Manager):
    def get_queryset(self):
        """Return theses queryset with the appropriate fields prefetched (see fields_for_prefetching)
        as well as user names annotated for further processing - sorting/filtering
        """
        return APIQueryset(self.model, using=self._db).select_related(
            *APIManager.fields_for_prefetching("advisor"),
            *APIManager.fields_for_prefetching("supporting_advisor"),
        ).prefetch_related(
            "students"
        ).annotate(
            _advisor_name=Concat(
                "advisor__user__first_name", Value(" "), "advisor__user__last_name"
            )
        ).annotate(_is_archived=Case(
            When(status=ThesisStatus.DEFENDED, then=True),
            default=Value(False),
            output_field=BooleanField()
        ))

    @staticmethod
    def fields_for_prefetching(base_field: str) -> List[str]:
        """For all user fields present on the thesis, we need to prefetch
        both our user model and the standard Django user it's linked to,
        since basic user information needed when serializing is defined there.
        """
        return [base_field, f'{base_field}__user']
