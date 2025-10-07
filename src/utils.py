from datetime import datetime, timedelta

def get_monday_date():
    today = datetime.today()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime("%Y-%m-%dT00:00:00.000Z")