from django.db.models.signals import post_save, pre_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, Application, Notification


# Store the original status before saving
_application_status_cache = {}


@receiver(pre_save, sender=Application)
def store_application_status(sender, instance, **kwargs):
    """Store the original status before the save"""
    if instance.pk:
        try:
            old_instance = Application.objects.get(pk=instance.pk)
            _application_status_cache[instance.pk] = old_instance.status
        except Application.DoesNotExist:
            _application_status_cache[instance.pk] = None
    else:
        _application_status_cache[instance.pk] = None


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile when a new User is created"""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure a Profile exists for every User after save."""
    Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=Application)
def application_status_changed(sender, instance, created, **kwargs):
    """Create notifications when application status changes"""
    
    # If this is a new application, notify the employer (company)
    if created:
        # Notify employer that a new application has been received
        Notification.objects.create(
            recipient=instance.job.posted_by,
            application=instance,
            notification_type='application_received',
            title=f'New Application for {instance.job.title}',
            message=f'{instance.student.first_name or instance.student.username} has applied for the position of {instance.job.title}.'
        )
    else:
        # Check if status has changed
        old_status = _application_status_cache.get(instance.pk)
        new_status = instance.status
        
        # Only create notification if status actually changed
        if old_status != new_status and old_status is not None:
            # Map status to notification type and messages
            status_map = {
                'reviewed': {
                    'type': 'application_reviewed',
                    'title': f'Your application is under review',
                    'message': f'Your application for {instance.job.title} at {instance.job.company.name} is now under review.'
                },
                'interview': {
                    'type': 'application_interview',
                    'title': f'Interview invitation for {instance.job.title}',
                    'message': f'Congratulations! You have been invited for an interview for {instance.job.title} at {instance.job.company.name}.'
                },
                'accepted': {
                    'type': 'application_accepted',
                    'title': f'Job offer for {instance.job.title}',
                    'message': f'Congratulations! Your application for {instance.job.title} at {instance.job.company.name} has been accepted!'
                },
                'rejected': {
                    'type': 'application_rejected',
                    'title': f'Application update for {instance.job.title}',
                    'message': f'Unfortunately, your application for {instance.job.title} at {instance.job.company.name} was not selected at this time. Please keep trying!'
                }
            }
            
            if new_status in status_map:
                status_info = status_map[new_status]
                # Notify student about status change
                Notification.objects.create(
                    recipient=instance.student,
                    application=instance,
                    notification_type=status_info['type'],
                    title=status_info['title'],
                    message=status_info['message']
                )
        
        # Clean up cache
        if instance.pk in _application_status_cache:
            del _application_status_cache[instance.pk]