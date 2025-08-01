from flask import Flask, render_template, request
import smtplib, ssl, json, os, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email_utils import save_mailed_lead
from crawler import crawl_site  # Make sure crawler.py exists with crawl_site()
from datetime import datetime

app = Flask(__name__)

def send_email(to_email, subject, message, your_email, app_password):
    try:
        msg = MIMEMultipart()
        msg["From"] = your_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(your_email, app_password)
            server.sendmail(your_email, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"❌ Error sending email to {to_email}: {e}")
        return False

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send", methods=["POST"])
def send():
    websites = request.form["websites"].split()
    subject_template = request.form["subject"]
    message_template = request.form["message"]
    your_email = request.form["your_email"]
    app_password = request.form["app_password"]

    sent_history = {}
    if os.path.exists("sent_emails.json"):
        with open("sent_emails.json", "r") as f:
            sent_history = json.load(f)

    sent_emails = []

    for site in websites:
        site = site.strip().replace("https://", "").replace("http://", "").strip("/")
        site_url = f"https://{site}"
        print(f"\n🌐 Crawling {site_url} ...")

        emails = crawl_site(site_url)
        print(f"📧 Emails found: {len(emails)}")

        if not emails:
            print("⚠️ No emails found, skipping...")
            continue

        for email in emails:
            key = f"{email}|{subject_template}"
            if key in sent_history:
                print(f"⏭️ Already sent this subject to {email}, skipping.")
                continue

            subject = subject_template.replace("{{email}}", email).replace("{{domain}}", site).replace("{{site}}", site_url)
            message = message_template.replace("{{email}}", email).replace("{{domain}}", site).replace("{{site}}", site_url)

            if send_email(email, subject, message, your_email, app_password):
                print(f"✅ Sent to: {email}")
                sent_emails.append(email)

                save_mailed_lead(
                    name=email.split('@')[0],
                    email=email,
                    website=site,
                    subject=subject_template,
                    status="Sent",
                    date=datetime.now().strftime("%Y-%m-%d")
                )

                sent_history[key] = True

        time.sleep(2)

    with open("sent_emails.json", "w") as f:
        json.dump(sent_history, f, indent=2)

    return render_template("results.html", sent_emails=sent_emails)

if __name__ == "__main__":
    app.run(debug=True)
