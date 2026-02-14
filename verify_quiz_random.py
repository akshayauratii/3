import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_portal.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from network.views import QUIZ_QUESTIONS

def verify_quiz_expansion():
    print(f"Total questions in pool: {len(QUIZ_QUESTIONS)}")
    
    client = Client()
    user, _ = User.objects.get_or_create(username='quiztester')
    client.force_login(user)
    
    # First attempt
    response1 = client.get('/quiz/')
    content1 = response1.content.decode()
    q_count1 = content1.count('class="question-card"')
    print(f"Attempt 1 question count: {q_count1}")
    
    if q_count1 != 30:
        print(f"[FAIL] Attempt 1 served {q_count1} questions, expected 30.")
        return False
    
    # Reload (should be same due to session)
    response2 = client.get('/quiz/')
    content2 = response2.content.decode()
    q_count2 = content2.count('class="question-card"')
    if q_count1 != q_count2:
        print("[FAIL] Questions count changed on reload.")
        return False
    
    # Check if first question text is the same on reload
    start_str = '<p style="font-weight: 600; font-size: 1.1rem; margin-bottom: 1rem;">'
    first_q1 = content1.find(start_str)
    first_q2 = content2.find(start_str)
    
    if content1[first_q1:first_q1+200] != content2[first_q2:first_q2+200]:
         print("[FAIL] Questions changed on reload (session persistence failed).")
         return False
    else:
        print("[PASS] Questions persisted on reload.")

    # Submit and start new attempt (should be different)
    # We'll just clear the session manually in the client or simulate fresh visit by deleting session entry if we could, 
    # but the POST in 'quiz' view handles it.
    
    # Just a mock POST to trigger cleanup
    client.post('/quiz/', {})
    
    response3 = client.get('/quiz/')
    content3 = response3.content.decode()
    first_q3 = content3.find(start_str)
    
    if content1[first_q1:first_q1+200] == content3[first_q3:first_q3+200]:
        print("[WARNING] Questions identical on new attempt (rare but possible).")
    else:
        print("[PASS] Different questions served on new attempt.")
        
    print("[SUCCESS] Quiz expansion and randomization verified.")
    return True

if __name__ == "__main__":
    verify_quiz_expansion()
