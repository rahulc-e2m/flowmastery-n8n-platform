"""Email service for sending invitations"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from app.config import settings
from app.models.invitation import Invitation


async def send_invitation_email(invitation: Invitation) -> bool:
    """Send invitation email to user"""
    # Create invitation link (needed for both email and fallback)
    invitation_link = f"{settings.FRONTEND_URL}/accept-invitation?token={invitation.token}"
    
    if not settings.SMTP_HOST:
        print(f"📧 Email not configured. Invitation link: {invitation_link}")
        return True
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = settings.FROM_EMAIL
        msg['To'] = invitation.email
        msg['Subject'] = f"Welcome to FlowMastery - Your {invitation.role.title()} Account Invitation"
        
        # Get inviter name (admin who sent the invitation)
        inviter_name = "FlowMastery Team"  # Default fallback
        if hasattr(invitation, 'invited_by_admin') and invitation.invited_by_admin:
            if hasattr(invitation.invited_by_admin, 'first_name') and invitation.invited_by_admin.first_name:
                inviter_name = f"{invitation.invited_by_admin.first_name}"
                if hasattr(invitation.invited_by_admin, 'last_name') and invitation.invited_by_admin.last_name:
                    inviter_name += f" {invitation.invited_by_admin.last_name}"
            elif hasattr(invitation.invited_by_admin, 'email') and invitation.invited_by_admin.email:
                inviter_name = invitation.invited_by_admin.email
        
        # Set workspace name
        workspace_name = "FlowMastery Platform"
        
        # Simple FlowMastery email template with inline CSS
        body = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #374151; margin: 0; padding: 40px 20px; background-color: #f0f4ff;">
    <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 12px; padding: 40px; box-shadow: 0 4px 20px rgba(102, 126, 234, 0.1);">
        
        <!-- Header -->
        <div style="text-align: center; margin-bottom: 32px;">
            <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 12px; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center;">
                <span style="color: white; font-size: 24px;">⚡</span>
            </div>
            <h1 style="margin: 0; font-size: 24px; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">FlowMastery</h1>
            <p style="margin: 4px 0 0; color: #6b7280; font-size: 14px;">Workflow Analytics Platform</p>
        </div>

        <!-- Content -->
        <div style="text-align: center;">
            <h2 style="font-size: 28px; color: #1f2937; margin: 0 0 16px;">You're Invited! 🎉</h2>
            <p style="font-size: 16px; color: #4b5563; margin: 0 0 24px; line-height: 1.6;">
                <strong>{inviter_name}</strong> has invited you to join <strong>{workspace_name}</strong> as a team member.
            </p>

            <!-- Role Card -->
            <div style="background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%); border-radius: 8px; padding: 20px; margin: 24px 0; border: 1px solid #a5b4fc;">
                <p style="margin: 0 0 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #4c51bf; font-weight: 600;">You're invited as a</p>
                <p style="margin: 0; font-size: 20px; font-weight: 700; color: #3730a3; text-transform: capitalize;">{invitation_role}</p>
            </div>

            <!-- CTA Button -->
            <a href="{invitation_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 16px 32px; border-radius: 8px; font-weight: 600; margin: 24px 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                🚀 Accept Invitation
            </a>

            <!-- Link Fallback -->
            <p style="font-size: 14px; color: #6b7280; margin: 16px 0;">
                Can't click the button? <a href="{invitation_link}" style="color: #667eea;">Use this link</a>
            </p>

            <!-- Expiry Warning -->
            <div style="background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 12px; margin: 24px 0; font-size: 14px; color: #92400e;">
                ⚠️ This invitation expires on <strong>{expiry_date}</strong>
            </div>
        </div>

        <!-- Footer -->
        <div style="text-align: center; padding-top: 32px; border-top: 1px solid #e5e7eb; margin-top: 32px;">
            <p style="font-size: 14px; color: #6b7280; margin: 0 0 16px;">If you have questions, please contact our support team.</p>
            <p style="font-size: 12px; color: #9ca3af; margin: 0;">© 2024 FlowMastery, Inc. • Workflow Analytics Platform</p>
        </div>
    </div>
</body>
</html>
        """.format(
            inviter_name=inviter_name,
            workspace_name=workspace_name,
            invitation_link=invitation_link,
            invitation_role=invitation.role.title(),
            expiry_date=invitation.expiry_date.strftime('%B %d, %Y')
        )
        
        msg.attach(MIMEText(body, 'html'))
        
        # Send email using context manager for proper cleanup
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            
            server.send_message(msg)
        
        print(f"✅ Invitation email sent to {invitation.email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send invitation email to {invitation.email}: {str(e)}")
        print(f"🔍 SMTP Config - Host: {settings.SMTP_HOST}, Port: {settings.SMTP_PORT}, Username: {settings.SMTP_USERNAME}")
        # In development, still show the link
        print(f"📧 Invitation link: {invitation_link}")
        return False