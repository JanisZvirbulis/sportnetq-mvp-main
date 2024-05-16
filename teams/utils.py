from datetime import datetime, timedelta, time
from collections import Counter, defaultdict
from calendar import HTMLCalendar
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.mail import send_mass_mail
from django.db.models import Count
from django.conf import settings
from .models import Event, AttendanceRecord, eventChoice

import calendar, operator

class Calendar(HTMLCalendar):
        def __init__(self, year=None, month=None, pk=None, team=None, orgCalendar=False):
            self.year = year
            self.month = month
            self.pk = pk
            self.team = team
            self.orgCalendar = orgCalendar
            super(Calendar, self).__init__()

    # formats a day as a td
	# filter events by day
        def formatday(self, day, events_by_day):
            events_per_day = events_by_day.get(day, [])
            d = ''
            for event in events_per_day:
                if event.type:
                    if self.orgCalendar:
                        d += f'<li class="event-type{event.type}"> {event.get_event_data} </li>'
                    else:
                        d += f'<li class="event-type{event.type}"> {event.get_html_url} </li>'
            
            # for event in events_per_day:
            #     if event.type:
            #         if event.type == '1':
            #             d += f'<li class="event-type1"> {event.get_html_url} </li>'
            #         if event.type == '2':
            #             d += f'<li class="event-type2"> {event.get_html_url} </li>'
            #         if event.type == '3':
            #             d += f'<li class="event-type3"> {event.get_html_url} </li>'
            #         if event.type == '4':
            #             d += f'<li class="event-type4"> {event.get_html_url} </li>'

            current_date = datetime.now().date()
            current_year, current_month = current_date.year, current_date.month

            is_current_day = day == current_date.day and self.month == current_month and self.year == current_year

            if day != 0:
                if is_current_day:
                    return f"<td class='calendar-current-day'><div class='cell-content'><span class='date'>{day}.</span><ul> {d} </ul></div></td>"
                else:
                    return f"<td><div class='cell-content'><span class='date'>{day}.</span><ul> {d} </ul></div></td>"
            elif is_current_day:
                return f"<td class='calendar-current-day'><div class='cell-content'></div></td>"
            return '<td></td>'

	# formats a week as a tr 
        def formatweek(self, theweek, teamevents):
            week = ''
            for d, weekday in theweek:
                week += self.formatday(d, teamevents)
            return f'<tr> {week} </tr>'

	# formats a month as a table
	# filter events by year and month
        def formatmonth(self, withyear=True):
            # Retrieve all events for the month
            events = self.team.events.filter(
                teamID=self.pk,
                start_time__year=self.year,
                start_time__month=self.month
            ).order_by('start_time')

            # Organize events in a dictionary
            events_by_day = defaultdict(list)
            for event in events:
                day = event.start_time.day
                events_by_day[day].append(event)

            cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
            cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
            cal += f'{self.formatweekheader()}\n'
            for week in self.monthdays2calendar(self.year, self.month):
                cal += f'{self.formatweek(week, events_by_day)}\n'  # Pass the dictionary instead
            cal += f'</table>\n'
            return cal
        
        def formatmonthname(self, theyear, themonth, withyear=True):
            """
            Return a month name as a table row.
            """
            if withyear:
                s = '%s %s' % (_(calendar.month_name[themonth]), theyear)
            else:
                s = '%s' % _(calendar.month_name[themonth])
            return '<tr><th colspan="7" class="month">%s</th></tr>' % s

        def formatweekday(self, day):
            """
            Return a weekday name as a table header.
            """
            return '<th class="%s">%s</th>' % (self.cssclasses[day], _(calendar.day_abbr[day]))

        def formatweekheader(self):
            """
            Return a header for a week as a table row.
            """
            s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
            return '<tr>%s</tr>' % s

def generate_attendance_data(team_attendance):
    attendance_counter = Counter(record.attendance for record in team_attendance)
    return [
        {
            'label': label,
            'count': attendance_counter.get(choice, 0),
        }
        for choice, label in AttendanceRecord.ATTENDANCE_CHOICES
        if choice != AttendanceRecord.EMPTYVALUE
    ]

def generate_event_data(team_events):
    event_counter= Counter(record.type for record in team_events)
    return [
        {
            'label': label,
            'count': event_counter.get(choice, 0),
        }
        for choice, label in eventChoice
    ]

def generate_athlete_evemt_data(athlete_events):
    event_counter= Counter(record.event.type for record in athlete_events)
    return [
        {
            'label': label,
            'count': event_counter.get(choice, 0),
        }
        for choice, label in eventChoice
    ]

def generate_happened_event_data(team_events, team_attendance):
    happened_events_counter = Counter()

    # Get a set of unique event dates for which there are attendance records
    attended_event_dates = set(
        record.event.start_time.date()
        for record in team_attendance
        if record.attendance not in (AttendanceRecord.EMPTYVALUE, AttendanceRecord.NOT_REQUIRED)
    )

    # Count occurred events for each event type
    for event in team_events:
        event_date = event.start_time.date()
        if event_date in attended_event_dates:
            happened_events_counter[event.type] += 1

    return [
        {
            'label': label,
            'count': happened_events_counter.get(choice, 0),
        }
        for choice, label in eventChoice
    ]


def generate_happened_athlete_event_data(team_events, team_attendance):
    happened_events_counter = Counter()

    # Get a set of unique event dates for which there are attendance records
    attended_event_dates = set(
        record.event.start_time.date()
        for record in team_attendance
        if record.attendance not in (AttendanceRecord.EMPTYVALUE, AttendanceRecord.NOT_REQUIRED)
    )

    # Count occurred events for each event type
    for e in team_events:
        event_date = e.event.start_time.date()
        if event_date in attended_event_dates:
            happened_events_counter[e.event.type] += 1

    return [
        {
            'label': label,
            'count': happened_events_counter.get(choice, 0),
        }
        for choice, label in eventChoice # Assuming you have a similar choices tuple in the Event model
    ]

def get_event_type_label(event_type):
    for event_id, event_str in eventChoice:
        if event_id == event_type:
            return event_str
    return _('Unknown Event Type')

def generate_teammember_attendace_data(member_attendace):
    event_counter = Counter(record.event.type for record in member_attendace)
    return [
        {
            'label': label,
            'count': event_counter.get(choice, 0),
        }
        for choice, label in eventChoice
    ]

def get_event_label_from_choice(choice, event_choices):
    return next((label for c, label in event_choices if c == choice), None)


def get_attendance_label_from_choice(choice, attendance_choices):
    return next((label for c, label in attendance_choices if c == choice), None)

def generate_event_subcategories(member_attendance, event_choices, attendance_choices):
    event_subcategories = defaultdict(lambda: defaultdict(int))
    
    for record in member_attendance:
        event_type = get_event_label_from_choice(record.event.type, event_choices)
        attendance = get_attendance_label_from_choice(record.attendance, attendance_choices)
        event_subcategories[event_type][attendance] += 1
    
    # Convert inner defaultdicts to plain dictionaries
    return {event_type: dict(inner_dict) for event_type, inner_dict in event_subcategories.items()}

def transform_event_subcategories(event_subcategories):
    transformed_data = defaultdict(lambda: defaultdict(int))

    for event_type, subcategories in event_subcategories.items():
        for attendance, count in subcategories.items():
            transformed_data[attendance][event_type] = count

    return dict(transformed_data)
# def generate_team_members_data(team, team_season):
#     team_players = team.teammember_set.filter(role='1').prefetch_related('profileID')
#     data = []
#     for player in team_players:
#         member = player.profileID
#         member_attendance_data = []
#         for choice, _ in AttendanceRecord.ATTENDANCE_CHOICES:
#             if choice != AttendanceRecord.EMPTYVALUE:
#                 count = team.attendancerecord_set.filter(
#                     team_member__profileID=member,
#                     event__start_time__range=(
#                         team_season.start_date if team_season else datetime.min,
#                         team_season.end_date if team_season else datetime.max),
#                     attendance=choice).count()
#                 member_attendance_data.append({'choice': choice, 'label': dict(AttendanceRecord.ATTENDANCE_CHOICES)[choice], 'count': count})
#         data.append({'member_data': member, 'attendance_data': member_attendance_data})
#     return data


def generate_team_members_data(team, team_season, sdate, edate):
    team_players = team.teammember_set.filter(role='1', is_active=True).prefetch_related('profileID').order_by('profileID__name')

    # Get the current timezone
    current_timezone = timezone.get_current_timezone()

    # Convert the start_date and end_date to DateTime objects
    if team_season:
        start_datetime = timezone.make_aware(timezone.datetime.combine(team_season.start_date if team_season else datetime.min.date(), time.min), timezone=current_timezone)
        end_datetime = timezone.make_aware(timezone.datetime.combine(team_season.end_date if team_season else datetime.max.date(), time.max), timezone=current_timezone)
    else:
        start_datetime = timezone.make_aware(timezone.datetime.combine(sdate, time.min), timezone=current_timezone)
        end_datetime = timezone.make_aware(timezone.datetime.combine(edate, time.max), timezone=current_timezone)

    # Query attendance records and annotate them
    attendance_records = AttendanceRecord.objects.filter(
        team_member__in=team_players,
        event__start_time__range=(start_datetime, end_datetime),
    ).values('team_member', 'attendance').annotate(count=Count('attendance'))

    # Organize attendance records into a dictionary
    attendance_data_dict = defaultdict(lambda: defaultdict(int))
    for record in attendance_records:
        team_member_id = record['team_member']
        attendance = record['attendance']
        count = record['count']
        attendance_data_dict[team_member_id][attendance] = count

    # Construct the final data
    gender_count = [{'Male': 0,}, {'Female': 0}]
    for player in team_players:
        gender = player.profileID.gender_type
        if gender == '1':
            gender_count[0]['Male'] += 1
        elif gender == '2':
            gender_count[1]['Female'] += 1
            
    data = []
    for player in team_players:
        member = player.profileID
        team_member_id = player.id
        member_attendance_data = []
        for choice, _ in AttendanceRecord.ATTENDANCE_CHOICES:
            if choice != AttendanceRecord.EMPTYVALUE:
                count = attendance_data_dict[team_member_id].get(choice, 0)
                member_attendance_data.append({'choice': choice, 'label': dict(AttendanceRecord.ATTENDANCE_CHOICES)[choice], 'count': count})
        data.append({'member_data': member, 'attendance_data': member_attendance_data, 'member_id': team_member_id})
    
    return data, gender_count

def generate_org_team_members_data(team, start_date, end_date):
    team_players = team.teammember_set.filter(role='1',is_active=True).prefetch_related('profileID').order_by('profileID__name')

    # Get the current timezone
    current_timezone = timezone.get_current_timezone()

    # Convert the start_date and end_date to DateTime objects
  
  
    start_datetime = timezone.make_aware(timezone.datetime.combine(start_date, time.min), timezone=current_timezone)
    end_datetime = timezone.make_aware(timezone.datetime.combine(end_date, time.max), timezone=current_timezone)
    # Query attendance records and annotate them
    attendance_records = AttendanceRecord.objects.filter(
        team_member__in=team_players,
        event__start_time__range=(start_datetime, end_datetime),
    ).values('team_member', 'attendance').annotate(count=Count('attendance'))

    # Organize attendance records into a dictionary
    attendance_data_dict = defaultdict(lambda: defaultdict(int))
    for record in attendance_records:
        team_member_id = record['team_member']
        attendance = record['attendance']
        count = record['count']
        attendance_data_dict[team_member_id][attendance] = count

    # Construct the final data
    data = []
    for player in team_players:
        member = player.profileID
        team_member_id = player.id
        member_attendance_data = []
        for choice, _ in AttendanceRecord.ATTENDANCE_CHOICES:
            if choice != AttendanceRecord.EMPTYVALUE:
                count = attendance_data_dict[team_member_id].get(choice, 0)
                member_attendance_data.append({'choice': choice, 'label': dict(AttendanceRecord.ATTENDANCE_CHOICES)[choice], 'count': count})
        data.append({'member_data': member, 'attendance_data': member_attendance_data, 'member_id': team_member_id})
    
    return data

def generate_table_data(team_members_data):
    table_data = defaultdict(lambda: defaultdict(int))

    for item in team_members_data:
        member_id = item['member_id']

        for attendance in item['attendance_data']:
            choice = attendance['choice']
            count = attendance['count']
            table_data[choice][member_id] = count

    return dict(table_data)

def custom_forbidden(request, message):
    context = {'message': message}
    return render(request, 'custom_forbidden.html', context, status=403)

def custom_token_error(request, message):
    context = {'message': message}
    return render(request, 'custom_token_error.html', context, status=404)

def custom_team_limit_msg(teamlimit):
    if teamlimit == 1:
        return _(f'max team count reached. Based on your organization subscription plan you can create {teamlimit} team ')
    else:
        return _(f'max team count reached. Based on your organization subscription plan you can create {teamlimit} teams ')



def prepare_scores(physical_assessment_scores):
    prepared_scores = []

    for assessment_type, scores in physical_assessment_scores.items():
        best_score_lower = scores[0].physical_assessment.best_score_lower
        op = operator.lt if best_score_lower else operator.gt

        for index, score in enumerate(scores):
            if index == 0 or op(score.score, best_score):
                best_score = score.score
                best_index = index

            is_best = index == best_index
            prepared_scores.append({
                'id': score.id,  # add id here
                'score': score.score,
                'is_best': is_best,
            })
    return prepared_scores

def send_notification_byemail(subject, message, recipient_list):
    from_email = settings.DEFAULT_FROM_EMAIL
    message_tuples = [
        (subject, message, from_email, [recipient]) for recipient in recipient_list
    ]
    send_mass_mail(
        message_tuples,
        fail_silently=False,
    )