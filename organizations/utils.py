from django.db.models import Q, Prefetch
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from teams.models import TeamMember, ATHLETE

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
        role=ATHLETE
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
    team_memberships = TeamMember.objects.filter(profileID__in=athlete_ids).select_related('teamID')

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

