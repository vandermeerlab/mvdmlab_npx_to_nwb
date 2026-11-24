from datetime import datetime

def get_age(dob, session_date):
    """Calculate the age of the subject in weeks based on the date of birth and session date.
    
    Parameters
    ----------
    dob : str
        The date of birth in the format 'MM/DD/YYYY'.
    session_date : str
        The session date in the format 'YYYY-MM-DD'.
    
    Returns
    -------
    str
        The age in days, formatted as 'P{days}D'.
    """
    dob_date = datetime.strptime(dob, '%m/%d/%Y')
    session_date_obj = datetime.strptime(session_date, '%Y-%m-%d')
    age_in_days = (session_date_obj - dob_date).days
    return f"P{age_in_days}D"