"""
Push Notification Utility
Handles sending push notifications via Expo Push Notification Service
"""
from .models import PushToken
import logging

logger = logging.getLogger(__name__)


def send_push_notification(user, title, message, data=None):
    """
    Send push notification to a specific user
    
    Args:
        user: User object
        title: Notification title
        message: Notification body
        data: Optional dict of extra data
    
    Returns:
        dict with success status and counts
    """
    # Get user's push tokens
    tokens = PushToken.objects.filter(user=user, is_active=True)
    
    if not tokens.exists():
        logger.info(f"No push tokens for user {user.username}")
        return {'success': False, 'reason': 'no_tokens'}
    
    try:
        from exponent_server_sdk import (
            DeviceNotRegisteredError,
            PushClient,
            PushMessage,
            PushServerError,
            PushTicketError,
        )
        
        push_client = PushClient()
        messages = []
        
        for token in tokens:
            try:
                messages.append(PushMessage(
                    to=token.token,
                    title=title,
                    body=message,
                    data=data or {},
                    sound='default',
                    priority='high',
                ))
            except Exception as e:
                logger.error(f"Error preparing message for token {token.id}: {e}")
        
        if not messages:
            return {'success': False, 'reason': 'no_valid_tokens'}
        
        # Send messages
        success_count = 0
        failure_count = 0
        
        try:
            tickets = push_client.publish_multiple(messages)
            
            for ticket in tickets:
                if ticket.is_success():
                    success_count += 1
                else:
                    failure_count += 1
                    logger.error(f"Push ticket error: {ticket.message}")
        
        except PushServerError as e:
            logger.error(f"Push server error: {e}")
            failure_count = len(messages)
        except Exception as e:
            logger.error(f"Unexpected error sending push: {e}")
            failure_count = len(messages)
        
        return {
            'success': success_count > 0,
            'sent': len(messages),
            'success_count': success_count,
            'failure_count': failure_count,
        }
    
    except ImportError:
        # Expo SDK not installed
        logger.warning("exponent_server_sdk not installed. Skipping push notification.")
        return {'success': False, 'reason': 'sdk_not_installed'}


def send_verification_approved_notification(provider_profile):
    """
    Send notification when provider verification is approved
    
    Args:
        provider_profile: ProviderProfile object
    
    Returns:
        dict with success status
    """
    return send_push_notification(
        user=provider_profile.user,
        title="✅ Verification Approved!",
        message="Congratulations! Your account is now verified. You can start adding services.",
        data={
            'type': 'verification_approved',
            'provider_id': provider_profile.id,
        }
    )


def send_trial_expiry_warning(provider_profile, days_left):
    """
    Send notification when trial is expiring soon
    
    Args:
        provider_profile: ProviderProfile object
        days_left: Number of days until trial expires
    
    Returns:
        dict with success status
    """
    return send_push_notification(
        user=provider_profile.user,
        title=f"⏰ Trial Ending in {days_left} Days",
        message=f"Your free trial expires in {days_left} days. Upgrade now to keep your services active!",
        data={
            'type': 'trial_expiry',
            'days_left': days_left,
        }
    )


def send_service_viewed_notification(provider, service):
    """
    Send notification when someone views provider's service
    
    Args:
        provider: User object (provider)
        service: ProviderService object
    
    Returns:
        dict with success status
    """
    return send_push_notification(
        user=provider,
        title="👀 Someone Viewed Your Service!",
        message=f"A potential client just viewed your {service.name}",
        data={
            'type': 'service_view',
            'service_id': service.id,
        }
    )


def send_broadcast_notification(title, message, target_providers):
    """
    Send broadcast notification to multiple providers
    
    Args:
        title: Notification title
        message: Notification body
        target_providers: QuerySet of ProviderProfile objects
    
    Returns:
        dict with success status and counts
    """
    try:
        from exponent_server_sdk import (
            PushClient,
            PushMessage,
            PushServerError,
        )
        
        # Get all push tokens for target providers
        provider_user_ids = target_providers.values_list('user_id', flat=True)
        push_tokens = PushToken.objects.filter(
            user_id__in=provider_user_ids,
            is_active=True
        )
        
        if not push_tokens.exists():
            logger.info("No push tokens found for target providers")
            return {'success': False, 'reason': 'no_tokens', 'sent': 0}
        
        push_client = PushClient()
        messages = []
        
        for token in push_tokens:
            try:
                messages.append(PushMessage(
                    to=token.token,
                    title=title,
                    body=message,
                    data={'type': 'broadcast'},
                    sound='default',
                    priority='high',
                ))
            except Exception as e:
                logger.error(f"Error preparing message for token {token.id}: {e}")
        
        if not messages:
            return {'success': False, 'reason': 'no_valid_tokens', 'sent': 0}
        
        # Send messages in chunks
        success_count = 0
        failure_count = 0
        chunk_size = 100
        
        for i in range(0, len(messages), chunk_size):
            chunk = messages[i:i + chunk_size]
            try:
                tickets = push_client.publish_multiple(chunk)
                
                for ticket in tickets:
                    if ticket.is_success():
                        success_count += 1
                    else:
                        failure_count += 1
                        logger.error(f"Push ticket error: {ticket.message}")
            
            except PushServerError as e:
                logger.error(f"Push server error: {e}")
                failure_count += len(chunk)
            except Exception as e:
                logger.error(f"Unexpected error sending push: {e}")
                failure_count += len(chunk)
        
        return {
            'success': success_count > 0,
            'sent': len(messages),
            'success_count': success_count,
            'failure_count': failure_count,
        }
    
    except ImportError:
        # Expo SDK not installed
        logger.warning("exponent_server_sdk not installed. Skipping broadcast.")
        return {'success': False, 'reason': 'sdk_not_installed', 'sent': 0}
