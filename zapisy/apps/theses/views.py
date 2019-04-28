from typing import Optional

from django.db.models import Value
from django.db.models.functions import Concat
from rest_framework import viewsets, permissions, exceptions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import LimitOffsetPagination, PageNumberPagination

from apps.users.models import Student, Employee
from .models import Thesis
from . import serializers
from .drf_permission_classes import ThesisPermissions
from .users import get_theses_board
from .enums import ThesisTypeFilter

"""Names of processing parameters in query strings"""
THESIS_TYPE_FILTER_NAME = "type"
THESIS_TITLE_FILTER_NAME = "title"
THESIS_ADVISOR_FILTER_NAME = "advisor"
ONLY_MINE_THESES_PARAM_NAME = "only_mine"
THESIS_SORT_COLUMN_NAME = "column"
THESIS_SORT_DIR_NAME = "dir"


class ThesesPagination(LimitOffsetPagination):
    default_limit = 30


class ThesesViewSet(viewsets.ModelViewSet):
    # NOTICE if you change this, you might also want to change the permission class
    http_method_names = ["patch", "get", "post", "delete"]
    permission_classes = (ThesisPermissions,)
    serializer_class = serializers.ThesisSerializer
    pagination_class = ThesesPagination

    def get_queryset(self):
        requested_type = ThesesViewSet._parse_thesis_type(
            self.request.query_params.get(THESIS_TYPE_FILTER_NAME, None)
        )
        requested_title = self.request.query_params.get(
            THESIS_TITLE_FILTER_NAME, ""
        ).strip()
        requested_advisor_name = self.request.query_params.get(
            THESIS_ADVISOR_FILTER_NAME, ""
        ).strip()
        requested_only_mine = self.request.query_params.get(
            ONLY_MINE_THESES_PARAM_NAME, "0"
        ) == "1"

        sort_column = self.request.query_params.get(THESIS_SORT_COLUMN_NAME, "")
        sort_dir = self.request.query_params.get(THESIS_SORT_DIR_NAME, "")

        theses = Thesis.rest_objects.get_queryset().filter_by_type(
            requested_type
        ).filter_by_user(self.request.user)

        if requested_only_mine:
            theses = theses.filter_only_mine(self.request.user)
        if requested_title:
            theses = theses.filter_by_title(requested_title)
        if requested_advisor_name:
            theses = theses.filter_by_advisor(requested_advisor_name)

        return theses.sort(sort_column, sort_dir)

    @staticmethod
    def _parse_thesis_type(type_str: Optional[str]):
        try:
            if type_str:
                return ThesisTypeFilter(int(type_str))
            else:
                return ThesisTypeFilter.DEFAULT
        except ValueError:
            raise exceptions.ParseError(f'Unknown filter value {type_str}')


class ThesesBoardViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.ThesesBoardMemberSerializer

    def get_queryset(self):
        return get_theses_board()


class EmployeesViewSet(viewsets.ModelViewSet):
    http_method_names = ["get"]
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.ThesesPersonSerializer

    def get_queryset(self):
        return Employee.objects.select_related("user")


@api_view(http_method_names=["get"])
@permission_classes((permissions.IsAuthenticated,))
def get_current_user(request):
    """Allows the front end to query the current thesis user role"""
    serializer = serializers.CurrentUserSerializer(request.user)
    return Response(serializer.data)


class PersonAutocompletePagination(PageNumberPagination):
    page_size = 15


def build_autocomplete_view_with_queryset(queryset):
    """Given a queryset, build an autocomplete view for use by the frontend"""
    class PersonAutocompleteViewset(viewsets.ModelViewSet):
        http_method_names = ["get"]
        permission_classes = (permissions.IsAuthenticated, )
        serializer_class = serializers.ThesesPersonSerializer
        pagination_class = PersonAutocompletePagination

        def get_queryset(self):
            qs = queryset.objects.select_related(
                "user"
            ).annotate(
                _full_name=Concat(
                    "user__first_name", Value(" "), "user__last_name"
                )
            ).order_by("_full_name")
            name_filter = self.request.query_params.get("filter", "").strip()
            if name_filter:
                qs = qs.filter(_full_name__icontains=name_filter)
            return qs.all()
    return PersonAutocompleteViewset


StudentAutocomplete = build_autocomplete_view_with_queryset(Student)
EmployeeAutocomplete = build_autocomplete_view_with_queryset(Employee)
