from django.urls import path, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register("theses", views.ThesesViewSet, base_name="theses")
router.register("theses_board", views.ThesesBoardViewSet, base_name="theses_board")
router.register("theses_employees", views.EmployeesViewSet, base_name="theses_employees")
router.register("theses_ac_students", views.StudentAutocomplete, base_name="theses_ac_students")
router.register("theses_ac_employees", views.EmployeeAutocomplete, base_name="theses_ac_employees")

urlpatterns = [
    path("api/current_user/", views.get_current_user, name="current_user"),
    path("api/", include(router.urls))
]
