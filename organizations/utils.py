from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import calendar
from django.utils.translation import gettext as _
from datetime import datetime
from collections import defaultdict
from calendar import HTMLCalendar
from teams.models import TeamMember, ATHLETE, AttendanceRecord

def paginateAthletes(request, athletes, results):
    page = request.GET.get('page')
    paginator = Paginator(athletes, results)

    try:
        athletes = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        athletes = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        athletes = paginator.page(page)

    leftIndex = (int(page) - 4)
    if leftIndex < 1:
        leftIndex = 1

    rightIndex = (int(page) + 5)
    if rightIndex > paginator.num_pages:
        rightIndex = paginator.num_pages + 1

    custom_range = range(leftIndex, rightIndex)

    return custom_range, athletes

def paginateTeams(request, teams, results):
    page = request.GET.get('page')
    paginator = Paginator(teams, results)

    try:
        teams = paginator.page(page)
    except PageNotAnInteger:
        page = 1
        teams = paginator.page(page)
    except EmptyPage:
        page = paginator.num_pages
        teams = paginator.page(page)

    leftIndex = (int(page) - 4)
    if leftIndex < 1:
        leftIndex = 1

    rightIndex = (int(page) + 5)
    if rightIndex > paginator.num_pages:
        rightIndex = paginator.num_pages + 1

    custom_range = range(leftIndex, rightIndex)

    return custom_range, teams


def searchAthlete(request, teams_in_org):
    search_query = request.GET.get('search_query', '')
    team_search_query = request.GET.get('team_search_query', '')
    gender = request.GET.get('gender', '')
    birth_year = request.GET.get('birth_year', '')

    # Fetch distinct athletes with ordering
    athletes = TeamMember.objects.filter(
        teamID__in=teams_in_org, 
        role=ATHLETE,
        is_active=True,
    ).distinct('profileID').order_by('profileID', 'id').select_related('profileID')

    # Apply search criteria
    query = Q()
    if search_query:
        query &= Q(profileID__name__icontains=search_query)
    if team_search_query:
        query &= Q(teamID__teamName__icontains=team_search_query)
    if gender:
        query &= Q(profileID__gender_type=gender)
    if birth_year:
        query &= Q(profileID__birth_date__year=birth_year)

    athletes = athletes.filter(query) if query else athletes

    # Fetch teams for each athlete
    athlete_ids = athletes.values_list('profileID', flat=True)
    team_memberships = TeamMember.objects.filter(profileID__in=athlete_ids, is_active=True,).select_related('teamID')

    # Manually map teams to athletes
    teams_per_athlete = {athlete_id: [] for athlete_id in athlete_ids}
    for membership in team_memberships:
        teams_per_athlete[membership.profileID_id].append(membership.teamID)

    # Add the teams to athlete objects
    for athlete in athletes:
        athlete.teams = teams_per_athlete.get(athlete.profileID_id, [])

    return athletes, search_query

def searchTeams(request, teams_in_org):
    search_query = request.GET.get('search_query', '')

    if search_query:
        teams = teams_in_org.filter(teamName__icontains=search_query).order_by('teamName')
    else:
        teams = teams_in_org

    return teams, search_query

class AthleteCalendar(HTMLCalendar):
    def __init__(self, year=None, month=None, athleteProfile=None, team_ids=None, org=None):
        self.year = year
        self.month = month
        self.athleteProfile = athleteProfile
        self.team_ids = team_ids
        self.org = org
        super(AthleteCalendar, self).__init__()

    def formatday(self, day, events_by_day):
        events_per_day = events_by_day.get(day, [])
        d = ''
        for record in events_per_day:
            if record.event.type:
                d += f'<li class="event-type{record.event.type}"><strong>{record.event.teamID.teamName.upper()}</strong> | {record.event.get_event_data}  </li>'

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

    def formatweek(self, theweek, teamevents):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, teamevents)
        return f'<tr> {week} </tr>'

    def formatmonth(self, withyear=True):
        events = AttendanceRecord.objects.filter(
            team_member__profileID=self.athleteProfile,
            team__id__in=self.team_ids,
            team__organization=self.org,
            event__start_time__year=self.year,
            event__start_time__month=self.month
        ).prefetch_related('event').order_by('event__start_time')

        events_by_day = defaultdict(list)
        for event in events:
            day = event.event.start_time.day
            events_by_day[day].append(event)

        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, events_by_day)}\n'
        cal += f'</table>\n'
        return cal

    def formatmonthname(self, theyear, themonth, withyear=True):
        if withyear:
            s = '%s %s' % (_(calendar.month_name[themonth]), theyear)
        else:
            s = '%s' % _(calendar.month_name[themonth])
        return '<tr><th colspan="7" class="month">%s</th></tr>' % s

    def formatweekday(self, day):
        return '<th class="%s">%s</th>' % (self.cssclasses[day], _(calendar.day_abbr[day]))

    def formatweekheader(self):
        s = ''.join(self.formatweekday(i) for i in self.iterweekdays())
        return '<tr>%s</tr>' % s