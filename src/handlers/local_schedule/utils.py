from datetime import datetime, timedelta

def get_monday_date():
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())

    reference_date = datetime(2025, 11, 10)
    delta_weeks = (monday - reference_date).days // 7
    monday_pair = reference_date + timedelta(weeks=(delta_weeks // 2) * 2)
    return monday_pair

print(get_monday_date())