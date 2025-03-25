# templatetags/notification_filters.py
from django import template

register = template.Library()

@register.filter
def filter_by_category(notifications, category):
    return [n for n in notifications if n.category == category]