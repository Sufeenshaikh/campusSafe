#for email notifications - smtplib

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
GMAIL_ADDRESS      = os.getenv("GMAIL_ADDRESS")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

def send_sos_email(guardian_email, student_name, latitude, longitude):
    """
    Sends SOS alert email to guardian.
    Returns a tuple: (success: bool, message: str)
    """
    maps_link = f"https://maps.google.com/?q={latitude},{longitude}"

    time_now = datetime.now().strftime("%I:%M %p on %d %B %Y")
    
    # ── BUILD THE EMAIL
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 SOS ALERT — {student_name} needs help!"
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = guardian_email

    # Plain text version — shown in email clients that don't support HTML
    plain_text = f"""
SOS ALERT — URGENT

{student_name} has triggered an emergency SOS alert.

Time: {time_now}

Location: {maps_link}

Please check on them immediately or contact campus security.

Emergency numbers:
Police: 100
Women Helpline: 1090
Campus Security: Contact DAVV admin

This alert was sent automatically by CampusSafe.
    """.strip()

    html_text = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">

        <div style="background-color: #CC0000; padding: 20px; border-radius: 8px 8px 0 0;">
            <h1 style="color: white; margin: 0; font-size: 24px;">
                🚨 SOS ALERT — URGENT
            </h1>
        </div>

        <div style="background-color: #f9f9f9; padding: 24px; border: 1px solid #ddd;">

            <p style="font-size: 18px; color: #333;">
                <strong>{student_name}</strong> has triggered an emergency SOS alert.
            </p>

            <p style="color: #666;">
                <strong>Time:</strong> {time_now}
            </p>

            <div style="margin: 24px 0;">
                <a href="{maps_link}"
                   style="background-color: #CC0000;
                          color: white;
                          padding: 14px 28px;
                          text-decoration: none;
                          border-radius: 6px;
                          font-size: 16px;
                          font-weight: bold;">
                    📍 Open Location on Google Maps
                </a>
            </div>

            <p style="color: #333; margin-top: 24px;">
                Please check on them immediately or contact campus security.
            </p>

            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">

            <p style="color: #666; font-size: 14px;">
                <strong>Emergency Numbers:</strong><br>
                Police: 100<br>
                Women Helpline: 1090<br>
                Campus Security: Contact DAVV admin
            </p>

        </div>

        <div style="background-color: #eee; padding: 12px;
                    border-radius: 0 0 8px 8px; text-align: center;">
            <p style="color: #999; font-size: 12px; margin: 0;">
                Sent automatically by CampusSafe — DAVV Indore
            </p>
        </div>

    </body>
    </html>
    """

    # Attach both versions to the email
    # Email client picks whichever it supports
    msg.attach(MIMEText(plain_text, "plain"))
    msg.attach(MIMEText(html_text,  "html"))

    # ── SEND THE EMAIL ────────────────────────────────────────────────────────
    try:
        # SMTP_SSL = secure connection to Gmail server
        # smtp.gmail.com = Gmail's mail server address
        # 465 = the port number Gmail uses for secure connections
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:

            # Login with Gmail credentials from .env
            server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)

            # Send the email
            server.sendmail(
                from_addr = GMAIL_ADDRESS,
                to_addrs  = guardian_email,
                msg       = msg.as_string()
            )

        return (True, "Email sent successfully")   # email sent successfully

    except smtplib.SMTPAuthenticationError as e:
        # Wrong Gmail address or app password
        error_msg = "Gmail authentication failed. Check GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env"
        print(error_msg)
        return (False, error_msg)

    except smtplib.SMTPException as e:
        # Some other email error
        error_msg = f"SMTP Error: {str(e)}"
        print(error_msg)
        return (False, error_msg)

    except Exception as e:
        # Unexpected error
        error_msg = f"Unexpected error: {str(e)}"
        print(error_msg)
        return (False, error_msg)


# def send_test_email(to_email):
    
#     msg = MIMEText(
#         "CampusSafe email alerts are working correctly. "
#         "This is a test message.",
#         "plain"
#     )
#     msg["Subject"] = "CampusSafe — Test Email"
#     msg["From"]    = GMAIL_ADDRESS
#     msg["To"]      = to_email

#     try:
#         with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
#             server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
#             server.sendmail(GMAIL_ADDRESS, to_email, msg.as_string())
#         return True
#     except Exception as e:
#         print(f"Test email failed: {e}")
#         return False
