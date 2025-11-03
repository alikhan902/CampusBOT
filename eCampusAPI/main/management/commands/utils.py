from datetime import date, timedelta

def mondays_between(start_date: date, end_date: date):
    days_until_monday = (7 - start_date.weekday()) % 7
    first_monday = start_date + timedelta(days=days_until_monday)

    mondays = []
    current = first_monday
    while current <= end_date:
        mondays.append(current.strftime("%Y-%m-%dT00:00:00.000Z"))  
        current += timedelta(days=7)

    return mondays

print(mondays_between(date(2025, 9, 1), date(2025, 12, 29)))
