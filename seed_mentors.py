import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.contrib.auth.models import User
from network.models import Profile

def seed_mentors():
    # Ensure some alumni users exist as mentors
    mentor_data = [
        {'username': 'mentor_arjun', 'email': 'arjun@example.com', 'bio': 'Senior DevOps Engineer at Google.', 'skills': 'AWS, Docker, Kubernetes'},
        {'username': 'mentor_sara', 'email': 'sara@example.com', 'bio': 'Full Stack Developer with a passion for React.', 'skills': 'React, Node.js, GraphQL'},
        {'username': 'mentor_vikram', 'email': 'vikram@example.com', 'bio': 'Data Scientist specialized in NLP.', 'skills': 'Python, PyTorch, Bert'}
    ]

    for data in mentor_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            email=data['email']
        )
        if created:
            user.set_password('mentor123')
            user.save()
            
        profile, p_created = Profile.objects.get_or_create(user=user)
        profile.user_type = 'alumni'
        profile.bio = data['bio']
        profile.skills = data['skills']
        profile.save()

    print("Mentor data seeded successfully!")

if __name__ == '__main__':
    seed_mentors()
