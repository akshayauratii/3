import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.contrib.auth.models import User
from network.models import Opportunity

def populate():
    # Get a user (host/admin)
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        admin_user = User.objects.first()
    
    # Create Dummy Jobs
    Opportunity.objects.get_or_create(
        title="Senior Software Engineer",
        description="Build scalable web services using Python/Django.",
        type="job",
        category="private",
        company="Tech Giant Corp",
        location="Remote",
        posted_by=admin_user
    )
    
    Opportunity.objects.get_or_create(
        title="IAS Officer Recruitment",
        description="Public service opportunity with high impact.",
        type="job",
        category="govt",
        company="Union Public Service Commission",
        location="India",
        posted_by=admin_user
    )
    
    # Create Dummy Internships
    Opportunity.objects.get_or_create(
        title="Embedded Systems Intern",
        description="Design hardware prototypes and write firmware.",
        type="internship",
        category="private",
        stipend_type="paid",
        domain="hardware",
        company="Robotics Lab",
        location="Bangalore",
        posted_by=admin_user
    )
    
    Opportunity.objects.get_or_create(
        title="Web Development Intern",
        description="Master React and UI/UX design.",
        type="internship",
        category="private",
        stipend_type="unpaid",
        domain="software",
        company="Startup Hub",
        location="Hybrid",
        posted_by=admin_user
    )

    print("Dummy Brochure opportunities populated successfully!")

if __name__ == '__main__':
    populate()
