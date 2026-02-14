import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.contrib.auth.models import User
from network.models import TeaTimeSession

def populate():
    # Ensure a host user exists
    host_user, created = User.objects.get_or_create(username='AlumniHost')
    if created:
        host_user.set_password('password123')
        host_user.save()
        print("Created host user 'AlumniHost'")

    sessions = [
        {
            'topic': 'Breaking into AI & ML',
            'description': 'Join us for a deep dive into starting a career in Artificial Intelligence. We will cover necessary skills, project ideas, and industry trends.',
            'date_time': timezone.now() + timedelta(days=1, hours=4),
            'meeting_link': 'https://meet.google.com/abc-defg-hij',
            'status': 'scheduled'
        },
        {
            'topic': 'Resume Review Workshop',
            'description': 'Bring your resume! specialized alumni will screen your resume and give live feedback to help you land that dream job.',
            'date_time': timezone.now() + timedelta(days=3, hours=2),
            'meeting_link': 'https://zoom.us/j/123456789',
            'status': 'scheduled'
        },
        {
            'topic': 'Mental Health in Tech',
            'description': 'A safe space to discuss burnout, imposter syndrome, and maintaining a healthy work-life balance.',
            'date_time': timezone.now() + timedelta(hours=1),
            'meeting_link': 'https://meet.google.com/xyz-uvw-trs',
            'status': 'upcoming' # Note: model choice is 'scheduled', 'live', 'completed'. "upcoming" maps to "scheduled" logically but let's stick to choices.
        }
    ]

    for data in sessions:
        # Fix status to match choices
        if data['status'] == 'upcoming':
            data['status'] = 'scheduled'
            
        session, created = TeaTimeSession.objects.get_or_create(
            topic=data['topic'],
            defaults={
                'host': host_user,
                'description': data['description'],
                'date_time': data['date_time'],
                'meeting_link': data['meeting_link'],
                'status': data['status']
            }
        )
        if created:
            print(f"Created session: {session.topic}")
        else:
            print(f"Session already exists: {session.topic}")

if __name__ == '__main__':
    populate()
