import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
sys.path.insert(0, r'c:\Users\Dell\OneDrive\Desktop\team4\3')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# List all users
users = User.objects.all()
print("Users in DB:")
for u in users:
    print(f"  - {u.username} (has profile: {hasattr(u, 'profile')})")
    try:
        p = u.profile
        print(f"    user_type: '{p.user_type}', skills: '{p.skills}', bio: '{p.bio[:50] if p.bio else 'None'}'")
    except Exception as e:
        print(f"    Profile error: {e}")

# Login and test profile page
c = Client()
if users.exists():
    first_user = users.first()
    c.force_login(first_user)
    
    # Try viewing another user's profile
    other_user = users.exclude(id=first_user.id).first()
    if other_user:
        target = other_user.username
    else:
        target = first_user.username
    
    print(f"\nTesting profile page for: {target}")
    response = c.get(f'/profile/{target}/')
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        content = response.content.decode()
        print(f"Contains 'role-badge': {'role-badge' in content}")
        print(f"Contains 'info-section': {'info-section' in content}")
        print(f"Contains 'Skills': {'Skills' in content}")
        print(f"Contains 'Student': {'Student' in content}")
        print(f"Contains 'Alumni': {'Alumni' in content}")
    else:
        print(f"Response content: {response.content.decode()[:500]}")
