from datetime import date, datetime, timedelta, time, tzinfo
import pytz
import jwt
from workers import Response

# TODO: properly handle secret
JWT_SECRET = 'secret'
JWT_EXPIRY_FORMAT = "%d/%m/%y %H:%M:%S"

def create_jwt_token(user_id, username, expiry_delta=timedelta(weeks=1)):
    return jwt.encode({
        "user_id": user_id,
        "username": username,
        "expiry": (datetime.now() + expiry_delta).strftime(JWT_EXPIRY_FORMAT)
    }, JWT_SECRET, algorithm="HS256")

def decode_jwt_token(jwt_encoded):
    jwt_decoded = jwt.decode(jwt_encoded, JWT_SECRET, algorithms="HS256")
    jwt_decoded["expiry"] = datetime.strptime(jwt_decoded["expiry"], JWT_EXPIRY_FORMAT)
    return jwt_decoded

def logged_in_user(func):
    def wrap(user_id, *args):
        if user_id is None:
            return Response.json([])
        else:
            return func(user_id, *args)
    return wrap

def bradley_terry_simple(comparisons, n_items, max_iter=100):
    """Simple Bradley-Terry implementation"""
    wins = [0.0] * n_items
    games = [0.0] * n_items

    for winner, loser in comparisons:
        wins[winner] += 1
        games[winner] += 1
        games[loser] += 1

    # Iterative MM algorithm
    params = [1.0] * n_items
    for _ in range(max_iter):
        new_params = [w / g for w,g in zip(wins, games)]
        param_sum = sum(new_params)
        params = [p / param_sum for p in new_params]

    return params

def _date_at_num_week(year, month, weekday, num_weeks):
    month_start = date(year=year, month=month, day=1)
    day_diff = weekday - month_start.weekday()
    day_diff += 7 if day_diff < 0 else 0
    first_weekday_of_month = month_start + timedelta(day_diff)
    return first_weekday_of_month + timedelta(weeks=num_weeks - 1)


def get_upcoming_events(pubs, time_span=timedelta(weeks=1)):
    """Find upcoming quizzes within the time span from today"""
    # TODO: deal with timezone - db stores it as local time along with timezone (store in local time instead of UTC because of daylight savings)
    # -- NOTE: get timezone from map API
    upcoming_events = []
    for pub in pubs:
        today = (datetime.now(tz=pytz.timezone(pub.timezone))).date()
        end_date = today + time_span

        next_event_dates = []
        if pub.frequency == 'weekly':
            next_poss_date = today + timedelta(days=pub.day_of_week - today.weekday())
            while next_poss_date <= end_date:
                if next_poss_date >= today:
                    next_event_dates.append(next_poss_date)
                next_poss_date += timedelta(weeks=1)
        else:
            # monthly
            for week_of_month in pub.weeks_of_month.split(","):
                next_poss_year = today.year
                next_poss_month = today.month
                next_poss_date = today
                while True:
                    next_poss_date = _date_at_num_week(
                        next_poss_year,
                        next_poss_month,
                        pub.day_of_week,
                        int(week_of_month)
                    )

                    if next_poss_date > end_date:
                        break

                    if next_poss_date >= today:
                        next_event_dates.append(next_poss_date)

                    next_poss_month += 1
                    if next_poss_month == 13:
                        next_poss_year += 1
                        next_poss_month = 1

        event_time = datetime.strptime(pub.time, "%H:%M").time()
        upcoming_events.extend([
            # TODO: add timezone
            (pub, datetime.combine(event_date, event_time, tzinfo=pytz.timezone(pub.timezone)))
            for event_date in next_event_dates
        ])

    return sorted(upcoming_events, key=lambda e:e[1])
