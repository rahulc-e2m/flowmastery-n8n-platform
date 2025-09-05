"""Email service for sending invitations"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from app.config import settings
from app.models.invitation import Invitation


class EmailService:
    """Base email service for SMTP operations"""
    
    def __init__(self, smtp_config: Optional[Dict[str, Any]] = None):
        """Initialize EmailService with SMTP configuration"""
        self.smtp_config = smtp_config or {
            'host': settings.SMTP_HOST,
            'port': settings.SMTP_PORT,
            'use_tls': settings.SMTP_USE_TLS,
            'username': settings.SMTP_USERNAME,
            'password': settings.SMTP_PASSWORD,
            'from_email': settings.FROM_EMAIL
        }
    
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured"""
        return bool(self.smtp_config.get('host'))
    
    async def send_email(self, to_email: str, subject: str, body: str, content_type: str = 'html') -> bool:
        """Send email using SMTP"""
        if not self.is_configured():
            print(f"📧 Email not configured. Would send to: {to_email}")
            print(f"📧 Subject: {subject}")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, content_type))
            
            # Send email using context manager for proper cleanup
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                if self.smtp_config['use_tls']:
                    server.starttls()
                
                if self.smtp_config['username'] and self.smtp_config['password']:
                    server.login(self.smtp_config['username'], self.smtp_config['password'])
                
                server.send_message(msg)
            
            print(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            return False


class EmailTemplate(ABC):
    """Abstract base class for email templates"""
    
    @abstractmethod
    def get_subject(self, **kwargs) -> str:
        """Get email subject"""
        pass
    
    @abstractmethod
    def get_body(self, **kwargs) -> str:
        """Get email body"""
        pass


class InvitationEmailTemplate(EmailTemplate):
    """Template for invitation emails"""
    
    def get_subject(self, invitation: Invitation) -> str:
        """Get invitation email subject"""
        return f"Welcome to FlowMastery - Your {invitation.role.title()} Account Invitation"
    
    def get_body(self, invitation: Invitation, invitation_link: str) -> str:
        """Get invitation email body"""
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
        
        return """
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

        <div style="text-align: center;">
            <h2 style="font-size: 28px; color: #1f2937; margin: 0 0 16px;">Welcome to FlowMastery! 🎉</h2>
            <p style="font-size: 16px; color: #4b5563; margin: 0 0 24px; line-height: 1.6;">
                <strong>{inviter_name}</strong> has invited you to join <strong>{workspace_name}</strong> as a <strong>{invitation_role}</strong>.
            </p>

            <!-- Instructions Card -->
            <div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border-radius: 8px; padding: 24px; margin: 24px 0; border: 1px solid #0ea5e9; text-align: left;">
                <h3 style="margin: 0 0 16px; font-size: 18px; color: #0369a1; display: flex; align-items: center;">
                    📋 How to Get Started:
                </h3>
                <ol style="margin: 0; padding-left: 20px; color: #0f172a; line-height: 1.6;">
                    <li style="margin-bottom: 8px;">Click the button below to visit FlowMastery</li>
                    <li style="margin-bottom: 8px;">Explore our platform and features</li>
                    <li style="margin-bottom: 8px;">Scroll down to complete your account setup</li>
                    <li style="margin-bottom: 0;">Start automating your workflows!</li>
                </ol>
            </div>

            <!-- Role Card -->
            <div style="background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%); border-radius: 8px; padding: 20px; margin: 24px 0; border: 1px solid #a5b4fc;">
                <p style="margin: 0 0 8px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #4c51bf; font-weight: 600;">You're invited as a</p>
                <p style="margin: 0; font-size: 20px; font-weight: 700; color: #3730a3; text-transform: capitalize;">{invitation_role}</p>
            </div>

            <!-- CTA Button -->
            <a href="{invitation_link}" style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 16px 32px; border-radius: 8px; font-weight: 600; margin: 24px 0; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);">
                🚀 Explore FlowMastery & Complete Setup
            </a>

            <!-- Link Fallback -->
            <p style="font-size: 14px; color: #6b7280; margin: 16px 0;">
                Can't click the button? <a href="{invitation_link}" style="color: #667eea;">Copy this link: {invitation_link}</a>
            </p>

            <!-- Note about the flow -->
            <div style="background: #f3f4f6; border-radius: 6px; padding: 16px; margin: 24px 0; font-size: 14px; color: #374151; text-align: left;">
                <p style="margin: 0 0 8px; font-weight: 600; color: #1f2937;">💡 What to expect:</p>
                <p style="margin: 0;">The link will take you to our homepage where you can learn more about FlowMastery. You'll then be guided to complete your account setup.</p>
            </div>

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
            expiry_date=invitation.expiry_date.strftime('%B %d, %Y') if invitation.expiry_date else 'Not specified'
        )


class InvitationEmailService:
    """Service for handling invitation emails"""
    
    def __init__(self, email_service: Optional[EmailService] = None, template: Optional[InvitationEmailTemplate] = None):
        """Initialize InvitationEmailService"""
        self.email_service = email_service or EmailService()
        self.template = template or InvitationEmailTemplate()
    
    async def send_invitation_email(self, invitation: Invitation) -> bool:
        """Send invitation email to user"""
        # Create invitation link pointing to homepage with token
        invitation_link = f"{settings.FRONTEND_URL}/?token={invitation.token}"
        
        if not self.email_service.is_configured():
            print(f"📧 Email not configured. Invitation link: {invitation_link}")
            return True
        
        try:
            subject = self.template.get_subject(invitation)
            body = self.template.get_body(invitation, invitation_link)
            
            success = await self.email_service.send_email(
                to_email=invitation.email,
                subject=subject,
                body=body,
                content_type='html'
            )
            
            if success:
                print(f"✅ Invitation email sent to {invitation.email}")
            else:
                # In development, still show the link
                print(f"📧 Invitation link: {invitation_link}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send invitation email to {invitation.email}: {str(e)}")
            # In development, still show the link
            print(f"📧 Invitation link: {invitation_link}")
            return False
