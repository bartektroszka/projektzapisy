# -*- coding:utf-8 -*-

"""
    Preferences models
"""

from django.db import models
from apps.enrollment.courses.models.course import CourseEntity

from apps.users.models import Employee
from apps.offer.proposal.models import Proposal
from apps.offer.preferences.exceptions import *

PREFERENCE_CHOICES = (
    (3, 'Chętnie'),
    (2, 'Być może'),
    (1, 'Raczej nie'),
    (0, 'Nie'),
)

class PreferenceManager(models.Manager):
    """
        Manages preferences
    """
    def get_employees_prefs(self, employee, hidden=None, types=None, query=None):
        """
            Returns employee's preferences.

            hidden - include hidden
            types  - accepted type of the related proposal
            q      - substring of the related proposal's name
        """
        prefs = Preference.objects.filter(
            employee=employee)
        if not hidden:
            prefs = prefs.exclude(hidden=True)
        if types:
            prefs = prefs.filter(proposal__descriptions__type__in=types)
        if query: # TODO: zaawansowane filtrowanie
            prefs = prefs.filter(proposal__name__icontains=query)
        return prefs

    def init_preference(self, employee, course):
        """
            Sets initial values for employee's preferences with regard
            to the given course.
        """
        try:
            Preference.objects.get(employee=employee, proposal=course)
            raise CoursePreferencesAlreadySet
        except Preference.DoesNotExist:
            pref = Preference(
                employee = employee,
                proposal = course,
                hidden   = False,
                lecture  = 0,
                review_lecture = 0,
                tutorial = 0,
                lab      = 0)
            pref.save()
            return pref

class Preference(models.Model):
    """
        A model representing employee's will to give lectures and tutor
        for a course.
    """
    employee   = models.ForeignKey(Employee, verbose_name='pracownik')

    hidden     = models.BooleanField(default=False, 
                                     verbose_name='ukryte')

    proposal   = models.ForeignKey(CourseEntity, verbose_name='propozycja')

    # preferences
    lecture    = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='wykład')
    review_lecture = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='repetytorium')
    tutorial   = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='ćwiczenia')
    lab        = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='pracownia')
    tutorial_lab        = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='ćwiczenio-pracownia')
    seminar        = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='seminarium')
    project        = models.IntegerField(choices=PREFERENCE_CHOICES, null=True, blank=True,
                                     verbose_name='projekt')

    
    class Meta:
        verbose_name = 'preferencja'
        verbose_name_plural = 'preferencje'
    
    def __unicode__(self):
        rep = ''.join([self.employee.user.get_full_name(),
                       ': ',
                       self.proposal.name])
        return rep
    
    def hide(self):
        """
            Hides this preference in a default employee's view.
        """
        self.hidden = True
        self.save()
    
    def unhide(self):
        """
            Unhides this preference in a default employee's view.
        """
        self.hidden = False
        self.save()
    
    def set_preference(self, **kwargs):
        """
            Sets employee's preferences.

            Example usage:
            p.set_preference(lecture=2, tutorial=0)

            Values are restricted with PREFERENCE_CHOICES.
        """
        valid_prefs = ['lecture', 'review_lecture', 'tutorial', 'lab']
        valid_values = dict(PREFERENCE_CHOICES).keys()
        for pref in filter(valid_prefs.__contains__, kwargs.keys()):
            if kwargs[pref] not in valid_values:
                raise UnknownPreferenceValue
            self.__setattr__(pref, kwargs[pref])
        self.save()

    @staticmethod
    def for_employee(employee):
        return Preference.objects\
                    .filter(employee=employee, proposal__in_prefs=True, proposal__status__gte=1)\
                    .select_related('proposal', 'proposal__type', 'employee', 'employee__user')

    @staticmethod
    def make_preferences(employee):
        prefsid = Preference.objects\
                        .filter(employee=employee)\
                        .order_by('proposal__id')\
                        .values_list('proposal__id')

        free = CourseEntity.objects.\
                            exclude(id__in=prefsid).\
                            filter(in_prefs=True, status__gte=1)

        new_preferences = []

        for pref in free:
            new_preferences.append(Preference(employee=employee, proposal=pref))

        Preference.objects.bulk_create(new_preferences)