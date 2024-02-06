from django import template
from teams.models import AttendanceRecord, COUNTRY_CHOICES, athleteGenderChoice  
from django.utils.translation import gettext as _
from datetime import datetime
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def get_trans_item(dictionary, key):
    value = dictionary.get(key, None)
    if value is None:
        return _("-")  # Apply translation directly within the filter
    return value

@register.filter
def get_gender_value(gender):
    for choice in athleteGenderChoice:
        if choice[0] == gender:
            return choice[1]
    return '' 

@register.filter
def get_country_full_name(country_code):
    for code, name in COUNTRY_CHOICES:
        if code == country_code:
            return name
    return country_code 

@register.filter(name='get_value_from_dict')
def get_value_from_dict(dictionary, key):
    return dictionary.get(key, key)

@register.filter
def get_score_by_member_and_date(dictionary, team_member, date, field):
    nested_dict = dictionary.get(team_member)
    if nested_dict:
        record = nested_dict.get(date)
        if record:
            return getattr(record, field, None)
    return None

@register.filter
def format_duration(duration):
    total_seconds = int(duration.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    milliseconds = duration.microseconds // 1000

    if hours > 0:
        return f"{hours}h {minutes}m {seconds:02d}.{milliseconds:03d}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:02d}.{milliseconds:03d}s"
    else:
        return f"{seconds:02d}.{milliseconds:03d}s"

@register.filter
def format_distance(distance):
    if distance < 0:
        return _("Invalid distance")

    kilometers, meters = divmod(distance, 1000)
    meters, centimeters = divmod(meters, 1)
    centimeters, millimeters = divmod(centimeters * 100, 1)
    millimeters *= 10

    if kilometers >= 1:
        return f"{kilometers:.0f} km {meters:.0f} m"
    elif meters >= 1:
        return f"{meters:.0f} m {centimeters:.0f} cm"
    else:
        return f"{centimeters:.0f} cm {millimeters:.0f} mm"
    
@register.filter   
def get_attendance_label(value):
    label_dict = dict(AttendanceRecord.ATTENDANCE_CHOICES)
    return label_dict.get(value, '')

@register.filter
def get_attendance_count(attendance_data, choice):
    for attendance in attendance_data:
        if attendance['label'] == choice:
            return attendance['count']
    return 0

@register.filter
def widget_type(bound_field):
    return bound_field.field.widget.__class__.__name__


@register.filter(name='split')
def split(value, key):
    """
        Splits the value by the key and returns a list of strings.
    """
    return value.split(key)

@register.filter()
def format_time_duration(duration):
    if duration:
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        milliseconds = duration.microseconds // 1000
        # Format milliseconds to have three digits
        formatted_milliseconds = f"{milliseconds:03d}"[:3]

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}.{formatted_milliseconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}.{formatted_milliseconds}s"
        else:
            return f"{seconds}.{formatted_milliseconds}s"
    return "0.0s"

@register.simple_tag
def current_year():
    return datetime.now().year

