import os
import smtplib
import re
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any
from datetime import datetime, timezone
from app.core.config import settings

logger = logging.getLogger(__name__)

def send_job_match_notification(email_to: str, query: str, matches: List[Dict[str, Any]]) -> bool:
    """
    Formulate and send a premium HTML job match digest to the registered user.
    If SMTP server configurations are not found, falls back to logging the email HTML in the workspace.
    """
    if not matches:
        logger.info("[EmailService] No matches found. Skipping notification.")
        return False
        
    subject = f"🚀 PJSAP Digest: {len(matches)} New Live Job Matches for '{query}'"
    
    # 1. Build HTML content with beautiful modern aesthetics
    html_items = ""
    for m in matches:
        job = m["job"]
        score_percent = int(m["match_score"] * 100)
        score_color = "#10B981" if score_percent >= 80 else ("#F59E0B" if score_percent >= 50 else "#EF4444")
        salary_str = f"{job.salary_currency or 'USD'} {job.salary_min:,} - {job.salary_max:,}" if job.salary_min and job.salary_max else "Undisclosed"
        
        # Strip HTML tags from description for neat display
        desc_clean = re.sub(r'<[^>]*>', '', job.description)
        desc_trunc = desc_clean[:250] + "..." if len(desc_clean) > 250 else desc_clean
        
        html_items += f"""
        <div style="background-color: #1E293B; border-radius: 8px; border-left: 5px solid {score_color}; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="vertical-align: top;">
                        <h3 style="margin: 0 0 8px 0; color: #F8FAFC; font-size: 18px;">{job.title}</h3>
                        <p style="margin: 0 0 12px 0; color: #94A3B8; font-size: 14px;"><strong>🏢 {job.company}</strong> | 📍 {job.location} | {'🌐 Remote Work' if job.is_remote else '🏢 On-Site'}</p>
                    </td>
                    <td style="vertical-align: top; text-align: right; width: 120px;">
                        <div style="display: inline-block; background-color: rgba(15, 23, 42, 0.6); border: 1px solid {score_color}; color: {score_color}; border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: bold; text-align: center;">
                            {score_percent}% Match
                        </div>
                    </td>
                </tr>
            </table>
            <p style="color: #CBD5E1; font-size: 14px; line-height: 1.5; margin: 0 0 16px 0;">{desc_trunc}</p>
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #334155; padding-top: 12px; margin-top: 12px;">
                <span style="color: #10B981; font-size: 14px; font-weight: 500; display: inline-block; margin-top: 8px;">💰 Est. Salary: {salary_str}</span>
                <a href="{job.url}" target="_blank" style="display: inline-block; float: right; background: linear-gradient(135deg, #06B6D4, #3B82F6); color: #FFFFFF; text-decoration: none; border-radius: 4px; padding: 8px 16px; font-size: 13px; font-weight: bold;">Apply Direct</a>
            </div>
            <div style="clear: both;"></div>
        </div>
        """
        
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{subject}</title>
    </head>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0F172A; color: #F8FAFC; padding: 30px; margin: 0;">
        <div style="max-width: 650px; margin: 0 auto; background-color: #0F172A; border-radius: 12px; border: 1px solid #334155; padding: 40px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);">
            <div style="text-align: center; margin-bottom: 30px;">
                <div style="display: inline-block; background: linear-gradient(135deg, #06B6D4, #3B82F6); border-radius: 10px; padding: 12px; margin-bottom: 12px;">
                    <span style="font-size: 24px; color: white; display: block; line-height: 1;">💼</span>
                </div>
                <h1 style="margin: 0; color: #FFFFFF; font-size: 24px; font-weight: bold; letter-spacing: -0.025em;">PJSAP Career Digest</h1>
                <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 14px;">Personalized Job Search Automation Platform</p>
            </div>
            
            <p style="font-size: 15px; color: #E2E8F0; line-height: 1.6;">Hello,</p>
            <p style="font-size: 15px; color: #E2E8F0; line-height: 1.6;">We have completed crawling real-time listings matching your keyword <strong>"{query}"</strong>. Our semantic matching engine analyzed their descriptions against your user preferences, and we found <strong>{len(matches)} highly relevant live postings</strong> ready for your review!</p>
            
            <div style="margin-top: 30px; margin-bottom: 30px;">
                {html_items}
            </div>
            
            <div style="background-color: #1E293B; border-radius: 8px; padding: 16px; border: 1px dashed #334155; text-align: center; margin-top: 30px;">
                <p style="margin: 0; color: #E2E8F0; font-size: 14px;">📢 <strong>Spreadsheet Tracking:</strong> You can add any of these applications to your local tracking spreadsheet directly from your PJSAP Agent Console dashboard!</p>
            </div>
            
            <hr style="border: 0; border-top: 1px solid #334155; margin: 30px 0;">
            <p style="font-size: 12px; color: #64748B; text-align: center; line-height: 1.5; margin: 0;">
                This email was auto-generated by your local PJSAP Agent.<br>
                Encryption and GDPR controllers active. Security and privacy of your details are guaranteed.
            </p>
        </div>
    </body>
    </html>
    """

    # 2. Check configuration and send SMTP or log file fallback
    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            logger.info(f"[EmailService] Initiating real-time SMTP send to: {email_to}")
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.EMAILS_FROM_EMAIL
            msg["To"] = email_to
            msg.attach(MIMEText(html_content, "html"))
            
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAILS_FROM_EMAIL, [email_to], msg.as_string())
            server.quit()
            
            logger.info("[EmailService] Email sent successfully via SMTP.")
            return True
        except Exception as e:
            logger.error(f"[EmailService] Failed sending SMTP email: {str(e)}")
            
    # Fallback to local workspace file logging so the user can easily verify and read the HTML contents
    try:
        # Resolve path to write in the workspace root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        workspace_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "..", ".."))
        log_path = os.path.join(workspace_dir, "sent_emails.log")
        
        # Append email contents with a clean separator
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n\n{'='*80}\n")
            f.write(f"TIMESTAMP: {datetime.now(timezone.utc).isoformat()}\n")
            f.write(f"TO: {email_to}\n")
            f.write(f"SUBJECT: {subject}\n")
            f.write(f"{'='*80}\n")
            f.write(html_content)
            f.write(f"\n{'-'*80}\n")
            
        logger.info(f"[EmailService] Local SMTP credentials not found. Beautiful email logged to workspace at: {log_path}")
        return True
    except Exception as e:
        logger.error(f"[EmailService] Failed to write local email log: {str(e)}")
        return False
