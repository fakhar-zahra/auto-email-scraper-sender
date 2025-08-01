import csv
import os

MAILED_LEADS_FILE = 'mailed_leads.csv'

def save_mailed_lead(name, email, website, subject, status, date):
    """
    Save the emailed lead info to mailed_leads.csv
    """
    email = email.strip().lower()
    name = name.strip()
    website = website.strip()
    subject = subject.strip()
    status = status.strip()
    date = date.strip()

    file_exists = os.path.isfile(MAILED_LEADS_FILE)

    with open(MAILED_LEADS_FILE, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Name", "Email", "Website", "Subject", "Status", "Date_Sent"])
        writer.writerow([name, email, website, subject, status, date])

def already_mailed(email):
    """
    Check if the email is already in mailed_leads.csv
    """
    email = email.strip().lower()

    if not os.path.isfile(MAILED_LEADS_FILE):
        return False

    with open(MAILED_LEADS_FILE, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        return any(row['Email'].strip().lower() == email for row in reader)
