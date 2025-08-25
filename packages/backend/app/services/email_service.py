"""Email service for sending invitations"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings
from app.models.invitation import Invitation


async def send_invitation_email(invitation: Invitation) -> bool:
    """Send invitation email to user"""
    if not settings.SMTP_HOST:
        print(f"📧 Email not configured. Invitation link: {settings.FRONTEND_URL}/accept-invitation?token={invitation.token}")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = invitation.email
        msg['Subject'] = f"Invitation to join FlowMastery as {invitation.role}"
        
        # Create invitation link
        invitation_link = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"
        
        # Email body
        body = f"""
        <html>
        <body>
            <h2>You've been invited to join FlowMastery!</h2>
            <p>You have been invited to join FlowMastery as a <strong>{invitation.role}</strong>.</p>
            <p>Click the link below to accept your invitation and set up your account:</p>
            <p><a href="{invitation_link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Accept Invitation</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{invitation_link}</p>
            <p>This invitation will expire on {invitation.expiry_date.strftime('%Y-%m-%d %H:%M:%S')} UTC.</p>
            <p>If you didn't expect this invitation, you can safely ignore this email.</p>
            <br>
            <p>Best regards,<br>The FlowMastery Team</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        if settings.SMTP_USE_TLS:
            server.starttls()
        
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Invitation email sent to {invitation.email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send invitation email to {invitation.email}: {e}")
        # In development, still show the link
        print(f"📧 Invitation link: {invitation_link}")
        return False