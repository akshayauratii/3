import os
import django
from django.test import Client
from django.urls import reverse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

def verify():
    c = Client()
    try:
        from django.contrib.auth.models import User
        from network.models import Profile
        user = User.objects.get(username='AlumniHost')
        if not hasattr(user, 'profile'):
            print("Creating missing profile for AlumniHost...")
            Profile.objects.create(user=user, user_type='alumni')
    except Exception as e:
        print(f"User setup error: {e}")
        return

    # Login
    logged_in = c.login(username='AlumniHost', password='password123')
    if not logged_in:
        print("Login failed!")
        return

    print("Login successful.")
    
    # Get Tea Time page
    try:
        url = reverse('tea_time')
        print(f"Fetching {url}...")
        response = c.get(url)
        
        if response.status_code == 200:
            print("Page load successful (200 OK).")
            content = response.content.decode('utf-8')
            
            # Checks
            if "Chai Time Sessions" in content:
                print("SUCCESS: Header found.")
            else:
                print("FAILURE: Header NOT found.")

            if "Join Session" in content or "Starts " in content:
                 print("SUCCESS: Session card button found.")
            else:
                 print("FAILURE: Session card button NOT found.")

            # Check for Host New button
            if "Host New" in content:
                 print("SUCCESS: 'Host New' button found.")
            else:
                 print("FAILURE: 'Host New' button NOT found.")

            # Check logic for empty tag error
            if "Invalid block tag" in content:
                print("FAILURE: Template Error detected in content!")
            else:
                print("SUCCESS: No template error message detected.")

        else:
            print(f"Page load failed with status {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    verify()
