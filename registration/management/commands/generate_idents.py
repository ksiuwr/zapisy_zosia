# -*- coding: UTF-8 -*-

from django.core.management.base import BaseCommand
from django.utils.encoding import smart_unicode
from registration.models import UserPreferences


class Command(BaseCommand):
    def handle(self, *args, **options):
        preferences = UserPreferences.objects.filter(user__is_active=True)

        for i in range(0, preferences.count(), 2):
            first_name = generate_name(preferences[i])
            second_name = generate_name(preferences[i + 1 if i +1 < preferences.count() else i])
            first_meals = generate_meals(preferences[i])
            second_meals = generate_meals(preferences[i + 1 if i + 1< preferences.count() else i])

            print "\confpin" + smart_unicode(first_name) + "\confpin" + smart_unicode(second_name) + " \confpinrot"\
                  + smart_unicode(first_name) + " \confpinrot" + smart_unicode(second_name) + " \confpinfood" + \
                  smart_unicode(first_meals) + " \confpinfood" + smart_unicode(second_meals)
            print ''


def generate_name(preference):
    return u"{" + smart_unicode(preference.user.get_full_name()) + u"}{ " + smart_unicode(preference.org) + u"}"


def generate_meals(preference):
    result = ''
    if preference.dinner_1:
        result += u'{ Czw - obiad, 20:00-21:30 ('+ str(preference.get_room) + str(is_vegetarian(preference))  +')}'
    else:
        result += u'{}'
    if preference.breakfast_2:
        result += u'{ Pią - śniadanie, 8:00-9:30 ('+ str(preference.get_room) + str(is_vegetarian(preference))  +')}'
    else:
        result += u'{}'
    if preference.dinner_2:
        result += u'{ Pią - obiad, 17:00-19:30 ('+ str(preference.get_room) + str(is_vegetarian(preference))  +')}'
    else:
        result += u'{}'
    if preference.breakfast_3:
        result += u'{ Sob - śniadanie, 8:00-9:30 ('+ str(preference.get_room) + str(is_vegetarian(preference))  +')}'
    else:
        result += u'{}'
    if preference.dinner_3:
        result += u'{ Sob - obiad, 17:00-19:30 ('+ str(preference.get_room) + str(is_vegetarian(preference))  +')}'
    else:
        result += u'{}'
    if preference.breakfast_4:
        result += u'{ Nie - śniadanie, 8:00-9:30 ('+ str(preference.get_room) + str(is_vegetarian(preference)) + ')}'
    else:
        result += u'{}'

    return result


def is_vegetarian(preference):
    if preference.vegetarian:
        return ' W '
    else:
        return '   '