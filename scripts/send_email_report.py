# send_email_report.py

"""Placeholder script to email the generated PDF report.

The script expects the following environment variables to be set:
- EMAIL_HOST: SMTP server (e.g., smtp.gmail.com)
- EMAIL_PORT: SMTP port (e.g., 587)
- EMAIL_USER: Username/email address
- EMAIL_PASS: Password or app-specific token
- RECIPIENT_EMAIL: Destination email address

It attaches the `reports/analysis_report.pdf` file and sends it.
"""

import os
import smtplib
from email.message import EmailMessage

def send_email_report(pdf_path: str = "reports/analysis_report.pdf"):
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT", "587"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    recipient = os.getenv("RECIPIENT_EMAIL")

    if not all([host, user, password, recipient]):
        raise EnvironmentError("Missing required email configuration environment variables.")

    msg = EmailMessage()
    msg["Subject"] = "Bluestocks Mutual Funds Analysis Report"
    msg["From"] = user
    msg["To"] = recipient
    msg.set_content("Please find the attached analysis report PDF.")

    # Attach PDF
    with open(pdf_path, "rb") as f:
        pdf_data = f.read()
    msg.add_attachment(pdf_data, maintype="application", subtype="pdf", filename=os.path.basename(pdf_path))

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(user, password)
        server.send_message(msg)

if __name__ == "__main__":
    send_email_report()
