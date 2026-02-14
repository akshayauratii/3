from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
import random
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Profile, SuccessStory, Opportunity, Application, Notification, Connection, TeaTimeSession, CommunityPost, MentorRequest, ChatMessage
from .forms import UserRegistrationForm, ContactForm, ProfileUpdateForm, TeaTimeSessionForm, CommunityPostForm, OpportunityForm
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
# from twilio.rest import Client # Commented out until used or configured

def home(request):
    success_stories = SuccessStory.objects.all().order_by('-created_at')[:3]
    return render(request, 'home.html', {'success_stories': success_stories})

def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        user_type = request.POST.get('user_type', '')
        username = request.POST.get('username', '')
        
        # Handle admin re-registration (existing admin accounts)
        if user_type == 'admin':
            allowed_admins = ['Akshaya', 'Ramya', 'Divya', 'Harini', 'Akanksha']
            allowed_email = 'almamate@gmail.com'
            
            if username and username.lower() in [n.lower() for n in allowed_admins]:
                existing_user = User.objects.filter(username__iexact=username).first()
                if existing_user:
                    # Update existing admin account
                    password = request.POST.get('password', '')
                    email = request.POST.get('email', '')
                    
                    if email.lower() != allowed_email.lower():
                        messages.error(request, f"Admin registration requires the official email: {allowed_email}")
                        return render(request, 'register.html', {'form': form})
                    
                    existing_user.email = email
                    existing_user.set_password(password)
                    existing_user.save()
                    
                    # Ensure profile is admin
                    try:
                        existing_user.profile.user_type = 'admin'
                        existing_user.profile.save()
                    except:
                        from network.models import Profile
                        Profile.objects.create(user=existing_user, user_type='admin')
                    
                    messages.success(request, f'Admin account updated for {existing_user.username}! You can now login.')
                    return redirect('login')
        
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            
            # Create Profile
            # Profile creation is now handled by signals.py
            # We can update the user_type here if needed
            user.profile.user_type = form.cleaned_data['user_type']
            user.profile.save()
            
            messages.success(request, f'Account created for {user.username}! You can now login.')
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Additional Admin Authorization Check
            try:
                is_admin_type = user.profile.user_type == 'admin'
            except:
                is_admin_type = False
                
            if is_admin_type:
                allowed_admins = ['Akshaya', 'Ramya', 'Divya', 'Harini', 'Akanksha']
                allowed_email = 'almamate@gmail.com'
                is_authorized = (
                    user.username.lower() in [name.lower() for name in allowed_admins] and 
                    user.email.lower() == allowed_email.lower()
                )
                if not is_authorized and not user.is_superuser:
                    from django.contrib.auth import logout
                    logout(request)
                    messages.error(request, "This account is not authorized for Admin access. Please contact support.")
                    return redirect('login')

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    # Fetch Applications
    my_applications = Application.objects.filter(user=request.user)
    
    applied_internships = my_applications.filter(
        opportunity__type='internship', 
        status='applied'
    )
    upcoming_interviews = my_applications.filter(
        status='interview',
        interview_date__isnull=False
    ).order_by('interview_date')
    
    # Fetch Sidebar Data
    connections = Connection.objects.filter(user=request.user)
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    
    # Skills list
    skills_list = [s.strip() for s in profile.skills.split(',')] if profile.skills else []

    govt_internships = Opportunity.objects.filter(type='internship', category='govt').exclude(title='Marketing Intern').order_by('-created_at')
    private_internships = Opportunity.objects.filter(type='internship', category='private').exclude(title='Marketing Intern').order_by('-created_at')
    govt_jobs = Opportunity.objects.filter(type='job', category='govt').exclude(title='Marketing Intern').order_by('-created_at')
    private_jobs = Opportunity.objects.filter(type='job', category='private').exclude(title='Marketing Intern').order_by('-created_at')
    
    context = {
        'profile': profile,
        'my_skills': skills_list,
        'my_connections': connections,
        'notifications': notifications,
        'applied_internships': applied_internships,
        'upcoming_interviews': upcoming_interviews,
        'govt_internships': govt_internships,
        'private_internships': private_internships,
        'govt_jobs': govt_jobs,
        'private_jobs': private_jobs,
    }
    return render(request, 'dashboard.html', context)
    
def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            message_content = form.cleaned_data['message']
            
            # 1. Send Email (Console Backend)
            subject = f"New Contact Message from {name}"
            full_message = f"From: {name} <{email}>\n\nMessage:\n{message_content}"
            
            try:
                send_mail(
                    subject,
                    full_message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['akshayauratii@gmail.com'],
                    fail_silently=False,
                )
                email_sent = True
            except Exception as e:
                email_sent = False
                messages.error(request, f"Error sending email: {e}")

            # 2. Send SMS (Twilio)
            sms_sent = False
            try:
                # Use environment variables or safe checks
                twilio_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
                twilio_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
                
                if twilio_sid and twilio_token and twilio_token != 'your_auth_token_here':
                    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                    message = client.messages.create(
                        body=f"New Message from {name}: {message_content[:100]}...",
                        from_=settings.TWILIO_PHONE_NUMBER,
                        to='+916305465006'
                    )
                    sms_sent = True
                else:
                    # Log that credentials are missing (for dev purpose)
                    print("Twilio credentials not found or are placeholders. SMS skipped.")
            except Exception as e:
                print(f"Twilio SMS Error: {e}")
                # Don't show error to user if SMS fails (optional feature)

            if email_sent:
                msg = 'Message sent to akshayauratii@gmail.com'
                if sms_sent:
                    msg += ' and SMS sent to 6305465006'
                else:
                    msg += ' (SMS skipped - verify Twilio credentials)'
                messages.success(request, f"{msg} successfully!")
                return redirect('contact')
                
    else:
        form = ContactForm()
        
    return render(request, 'contact.html', {'form': form})

def impact_stories(request):
    stories = SuccessStory.objects.all().order_by('-created_at')
    return render(request, 'impact_stories.html', {'stories': stories})

# Resource Data (Moved to global scope for search functionality)
RESOURCES_DATA = {
    'fullstack': {
        'title': 'Full Stack Development',
        'icon': '💻',
        'description': 'Become a versatile developer capable of building end-to-end web applications. Total mastery of both frontend user interfaces and backend server logic.',
        'skills': ['HTML5 & CSS3', 'JavaScript (ES6+)', 'React.js', 'Python & Django', 'PostgreSQL', 'Git & GitHub', 'AWS/Heroku'],
        'roadmap': [
            {'title': 'Phase 1: The Foundations', 'desc': 'Master the building blocks of the web: HTML for structure, CSS for style, and JavaScript for interactivity.'},
            {'title': 'Phase 2: Frontend Frameworks', 'desc': 'Learn React.js to build dynamic, single-page applications. Understand state management and component lifecycle.'},
            {'title': 'Phase 3: Backend & Databases', 'desc': 'Dive into Python and Django. Learn how to create REST APIs, manage users, and interact with SQL databases.'},
            {'title': 'Phase 4: Deployment & DevOps', 'desc': 'Host your applications on the cloud using AWS or Heroku. Learn Docker for containerization.'}
        ],
        'links': [
            {'text': 'Official Django Documentation', 'url': 'https://docs.djangoproject.com/'},
            {'text': 'MDN Web Docs (JavaScript)', 'url': 'https://developer.mozilla.org/'},
            {'text': 'React.js Guide', 'url': 'https://react.dev/'}
        ]
    },
    'datascience': {
        'title': 'Data Science & AI',
        'icon': '📊',
        'description': 'Unlock the power of data. Learn to analyze complex datasets, build machine learning models, and derive actionable insights for businesses.',
        'skills': ['Python', 'Pandas & NumPy', 'Matplotlib/Seaborn', 'Scikit-Learn', 'TensorFlow/PyTorch', 'SQL', 'Statistics'],
        'roadmap': [
            {'title': 'Phase 1: Python & Statistics', 'desc': 'Get comfortable with Python syntax and fundamental statistical concepts (probability, distributions, hypothesis testing).'},
            {'title': 'Phase 2: Data Analysis', 'desc': 'Master Pandas for data manipulation and Matplotlib for visualization. "Clean" data is your fuel.'},
            {'title': 'Phase 3: Machine Learning', 'desc': 'Understand algorithms like Linear Regression, Decision Trees, and Clustering. Use Scikit-Learn.'},
            {'title': 'Phase 4: Deep Learning & AI', 'desc': 'Build neural networks using TensorFlow or PyTorch for image and text processing.'}
        ],
        'links': [
            {'text': 'Kaggle Datasets', 'url': 'https://www.kaggle.com/'},
            {'text': 'Scikit-Learn Docs', 'url': 'https://scikit-learn.org/'},
            {'text': 'Towards Data Science (Medium)', 'url': 'https://towardsdatascience.com/'}
        ]
    },
    'design': {
        'title': 'UI/UX Design',
        'icon': '🎨',
        'description': 'Design digital experiences that are intuitive, accessible, and beautiful. Bridge the gap between human needs and technical feasibility.',
        'skills': ['User Research', 'Wireframing', 'Prototyping', 'Figma', 'Adobe XD', 'Color Theory', 'Typography'],
        'roadmap': [
            {'title': 'Phase 1: Design Fundamentals', 'desc': 'Learn the principles of design: alignment, contrast, hierarchy, and balance. Study color theory.'},
            {'title': 'Phase 2: UX Research', 'desc': 'Understand your user. Conduct interviews, create personas, and map user journeys.'},
            {'title': 'Phase 3: UI & Prototyping', 'desc': 'Master Figma. Create high-fidelity mockups and interactive prototypes to test your ideas.'},
            {'title': 'Phase 4: Handoff & Portfolio', 'desc': 'Learn how to prepare assets for developers and build a stunning portfolio to showcase your work.'}
        ],
        'links': [
            {'text': 'Figma Community', 'url': 'https://www.figma.com/community'},
            {'text': 'Nielsen Norman Group (UX)', 'url': 'https://www.nngroup.com/'},
            {'text': 'Dribbble (Inspiration)', 'url': 'https://dribbble.com/'}
        ]
    },
    'frontend': {
        'title': 'Frontend Development',
        'icon': '⚛️',
        'description': 'Craft stunning, responsive, and interactive user interfaces. Master the art of bringing designs to life in the browser.',
        'skills': ['HTML5 & CSS3', 'JavaScript (ES6+)', 'React.js', 'Vue.js', 'Tailwind CSS', 'Redux', 'Webpack'],
        'roadmap': [
            {'title': 'Phase 1: Web Standards', 'desc': 'Deep dive into semantic HTML, modern CSS layouts (Flexbox/Grid), and responsive design principles.'},
            {'title': 'Phase 2: JavaScript Mastery', 'desc': 'Understand the DOM, async programming, closures, and ES6+ features.'},
            {'title': 'Phase 3: Modern Frameworks', 'desc': 'Pick a framework like React or Vue. Build component-based architectures.'},
            {'title': 'Phase 4: State & Performance', 'desc': 'Manage complex state with Redux/Context. Optimize for Core Web Vitals.'}
        ],
        'links': [
            {'text': 'Frontend Masters', 'url': 'https://frontendmasters.com/'},
            {'text': 'CSS-Tricks', 'url': 'https://css-tricks.com/'},
            {'text': 'React Docs', 'url': 'https://react.dev/'}
        ]
    },
    'backend': {
        'title': 'Backend Development',
        'icon': '⚙️',
        'description': 'Power the web. Build robust APIs, manage databases, and ensure security and scalability for applications.',
        'skills': ['Node.js', 'Python/Django', 'Go', 'PostgreSQL', 'Redis', 'Docker', 'System Design'],
        'roadmap': [
            {'title': 'Phase 1: Server Logic', 'desc': 'Learn a backend language (Node, Python, Go) and build simple RESTful APIs.'},
            {'title': 'Phase 2: Databases', 'desc': 'Master SQL (PostgreSQL) and NoSQL (MongoDB). Understand indexing and normalization.'},
            {'title': 'Phase 3: Authentication & Security', 'desc': 'Implement JWT, OAuth, and protect against OWASP Top 10 vulnerabilities.'},
            {'title': 'Phase 4: Scalability', 'desc': 'Learn caching (Redis), load balancing, and microservices architecture.'}
        ],
        'links': [
            {'text': 'Roadmap.sh (Backend)', 'url': 'https://roadmap.sh/backend'},
            {'text': 'System Design Primer', 'url': 'https://github.com/donnemartin/system-design-primer'},
            {'text': 'Django Rest Framework', 'url': 'https://www.django-rest-framework.org/'}
        ]
    },
    'python': {
        'title': 'Python Mastery',
        'icon': '🐍',
        'description': 'Go beyond the syntax. Master Python for automation, data analysis, web development, and more.',
        'skills': ['Advanced Python', 'AsyncIO', 'Testing (PyTest)', 'Virtual Envs', 'FastAPI', 'Algorithms', 'Scripting'],
        'roadmap': [
            {'title': 'Phase 1: Core Concepts', 'desc': 'Data structures, control flow, functions, and OOP in Python.'},
            {'title': 'Phase 2: Advanced Features', 'desc': 'Decorators, Generators, Context Managers, and Metaprogramming.'},
            {'title': 'Phase 3: Concurrency', 'desc': 'Understand Threading on Multiprocessing, and AsyncIO for high-performance I/O.'},
            {'title': 'Phase 4: Ecosystem', 'desc': 'Package management (Poetry/Pip), Testing, and building distributable packages.'}
        ],
        'links': [
            {'text': 'Real Python', 'url': 'https://realpython.com/'},
            {'text': 'Python Weekly', 'url': 'https://www.pythonweekly.com/'},
            {'text': 'Talk Python To Me', 'url': 'https://talkpython.fm/'}
        ]
    },
    'embedded-systems': {
        'title': 'Embedded Systems',
        'desc': 'Learn to design and program embedded systems using C/C++ and microcontrollers.',
        'icon': 'chip',
        'skills': ['C/C++', 'Microcontrollers', 'RTOS', 'IoT', 'Hardware Interface'],
        'roadmap': [
            {'step': 'C/C++ Programming', 'prob': 'Understanding memory management and pointers'},
            {'step': 'Microcontrollers (Arduino/STM32)', 'prob': 'GPIO, Interrupts, Timers'},
            {'step': 'Communication Protocols', 'prob': 'I2C, SPI, UART'},
            {'step': 'Real-Time Operating Systems', 'prob': 'Task scheduling and resource management'},
            {'step': 'IoT & Connectivity', 'prob': 'Connecting devices to the internet'}
        ]
    }
}

OPEN_SOURCE_DATA = {
    'collaborations': [
        {
            'slug': 'ai-traffic-control',
            'title': 'AI Traffic Control',
            'type': 'Research',
            'participants': 'Google + KIT Students',
            'status': 'Active',
            'details': 'Developing an intelligent traffic management system using computer vision and real-time data from city sensors to reduce urban congestion.'
        },
        {
            'slug': 'smart-irrigation',
            'title': 'Smart Irrigation',
            'type': 'IoT',
            'participants': 'AgriTech Startup + Alumni',
            'status': 'Hiring',
            'details': 'Implementing a precision agriculture platform that optimizes water usage based on soil moisture levels and local weather forecasts.'
        },
        {
            'slug': 'blockchain-voting',
            'title': 'Blockchain Voting',
            'type': 'Web3',
            'participants': 'Govt of India + Open Community',
            'status': 'Planning',
            'details': 'Designing a secure, transparent, and tamper-proof electronic voting system using decentralized ledger technology.'
        },
    ],
    'projects': [
        {
            'slug': 'campus-safety-app',
            'title': 'Campus Safety App',
            'tech': 'Flutter/Firebase',
            'needed': 'UI Designers',
            'details': 'A mobile application designed to enhance student safety on campus with real-time tracking, emergency alerts, and a peer-to-peer safety network.'
        },
        {
            'slug': 'e-waste-recycler',
            'title': 'E-Waste Recycler',
            'tech': 'React/Node',
            'needed': 'Backend Devs',
            'details': 'An online platform to connect residential users with e-waste recycling facilities, facilitating easier disposal and tracking of electronic waste.'
        },
        {
            'slug': 'alumni-connect-bot',
            'title': 'Alumni Connect Bot',
            'tech': 'Python/NLP',
            'needed': 'Data Scientists',
            'details': 'An AI-powered chatbot for the alumni portal that helps students find mentors and resources based on their career goals.'
        },
    ],
    'startups': [
        {
            'slug': 'pixel-ai',
            'name': 'PixelAI',
            'field': 'GenAI',
            'founder': 'Rahul (Alumni 2023)',
            'looking_for': 'Co-founder',
            'details': 'A generative AI startup focusing on creating realistic textures and assets for game developers and 3D artists.'
        },
        {
            'slug': 'green-energy',
            'name': 'GreenEnergy',
            'field': 'Sustainability',
            'founder': 'Priya (Alumni 2021)',
            'looking_for': 'Interns',
            'details': 'Developing affordable solar tracking solutions for residential use, maximizing energy capture throughout the day.'
        },
        {
            'slug': 'medtech-solutions',
            'name': 'MedTech Solutions',
            'field': 'Healthcare',
            'founder': 'Dr. Smit (Industry Partner)',
            'looking_for': 'Developers',
            'details': 'Scaling a remote patient monitoring system that provides real-time health alerts to doctors and family members.'
        },
    ]
}

@login_required
def open_source_detail(request, slug):
    # Search in all categories
    item = None
    for category in OPEN_SOURCE_DATA.values():
        item = next((i for i in category if i.get('slug') == slug), None)
        if item:
            break
            
    if not item:
        return redirect('open_source')
    
    # Normalize 'name' to 'title' for consistent rendering
    if 'name' in item and 'title' not in item:
        item['title'] = item['name']
        
    return render(request, 'open_source_detail.html', {'item': item})

QUIZ_QUESTIONS = [
    {'id': 1, 'question': 'Which of the following is NOT a fundamental data type in Python?', 'options': ['List', 'Float', 'Equation', 'Boolean'], 'correct': 'Equation'},
    {'id': 2, 'question': 'What does HTML stand for?', 'options': ['Hyper Text Markup Language', 'High Tech Modern Language', 'Hyperlink Text Management Language'], 'correct': 'Hyper Text Markup Language'},
    {'id': 3, 'question': 'What is Git used for?', 'options': ['Database Management', 'Version Control', 'Graphic Design'], 'correct': 'Version Control'},
    {'id': 4, 'question': 'Which symbol is used for comments in Python?', 'options': ['//', '#', '/* */'], 'correct': '#'},
    {'id': 5, 'question': 'what is the correct file extension for Python files?', 'options': ['.py', '.pt', '.pyt'], 'correct': '.py'},
    {'id': 6, 'question': 'Which of these is a Python web framework?', 'options': ['React', 'Django', 'Laravel'], 'correct': 'Django'},
    {'id': 7, 'question': 'What does SQL stand for?', 'options': ['Structured Query Language', 'Simple Question Logic', 'System Query List'], 'correct': 'Structured Query Language'},
    {'id': 8, 'question': 'What is the boolean result of 5 > 10?', 'options': ['True', 'False', 'Null'], 'correct': 'False'},
    {'id': 9, 'question': 'Which Company created React.js?', 'options': ['Google', 'Facebook (Meta)', 'Amazon'], 'correct': 'Facebook (Meta)'},
    {'id': 10, 'question': 'What is the default port for Django development server?', 'options': ['3000', '8080', '8000'], 'correct': '8000'},
    {'id': 11, 'question': 'Which of these is a valid Python variable name?', 'options': ['2variable', '_my_var', 'my-var', 'import'], 'correct': '_my_var'},
    {'id': 12, 'question': 'What is the output of 2 ** 3 in Python?', 'options': ['6', '8', '9', '5'], 'correct': '8'},
    {'id': 13, 'question': 'Which CSS property is used to change text color?', 'options': ['text-style', 'color', 'background-color', 'font-color'], 'correct': 'color'},
    {'id': 14, 'question': 'What is the main purpose of CSS?', 'options': ['Logic', 'Styling', 'Data Storage', 'Server Management'], 'correct': 'Styling'},
    {'id': 15, 'question': 'Which HTTP method is typically used to create data?', 'options': ['GET', 'POST', 'PUT', 'DELETE'], 'correct': 'POST'},
    {'id': 16, 'question': 'What does API stand for?', 'options': ['Application Programming Interface', 'Advanced Program Integration', 'Automated Protocol Interface'], 'correct': 'Application Programming Interface'},
    {'id': 17, 'question': 'Which of the following is an Agile framework?', 'options': ['Waterfall', 'Scrum', 'V-Model', 'Spiral'], 'correct': 'Scrum'},
    {'id': 18, 'question': 'What is the purpose of a primary key in a database?', 'options': ['To sort data', 'To uniquely identify records', 'To encrypt data'], 'correct': 'To uniquely identify records'},
    {'id': 19, 'question': 'What is the result of 10 // 3 in Python?', 'options': ['3.33', '3', '4', '1'], 'correct': '3'},
    {'id': 20, 'question': 'Which of these is NOT a browser?', 'options': ['Chrome', 'Firefox', 'Safari', 'Python'], 'correct': 'Python'},
    {'id': 21, 'question': 'What does RAM stand for?', 'options': ['Read Access Memory', 'Random Access Memory', 'Ready Active Memory'], 'correct': 'Random Access Memory'},
    {'id': 22, 'question': 'What is the brain of the computer?', 'options': ['RAM', 'GPU', 'CPU', 'HDD'], 'correct': 'CPU'},
    {'id': 23, 'question': 'Which protocol is used for secure web browsing?', 'options': ['HTTP', 'HTTPS', 'FTP', 'SMTP'], 'correct': 'HTTPS'},
    {'id': 24, 'question': 'What is the binary equivalent of 10 (decimal)?', 'options': ['1010', '1100', '1011', '1001'], 'correct': '1010'},
    {'id': 25, 'question': 'Which language is used for Android development?', 'options': ['Swift', 'Kotlin', 'Go', 'PHP'], 'correct': 'Kotlin'},
    {'id': 26, 'question': 'What is the decimal equivalent of binary 110?', 'options': ['4', '5', '6', '7'], 'correct': '6'},
    {'id': 27, 'question': 'Which data structure follows LIFO?', 'options': ['Queue', 'Stack', 'Linked List', 'Tree'], 'correct': 'Stack'},
    {'id': 28, 'question': 'What is the parent class of all classes in Python 3?', 'options': ['Base', 'None', 'object', 'Root'], 'correct': 'object'},
    {'id': 29, 'question': 'What does DOM stand for?', 'options': ['Data Object Model', 'Document Object Model', 'Digital Operation Management'], 'correct': 'Document Object Model'},
    {'id': 30, 'question': 'Which of these is a NoSQL database?', 'options': ['MySQL', 'PostgreSQL', 'MongoDB', 'SQLite'], 'correct': 'MongoDB'},
    {'id': 31, 'question': 'What is the output of "Hello" + "World" in Python?', 'options': ['Hello World', 'HelloWorld', 'Error', 'Hello+World'], 'correct': 'HelloWorld'},
    {'id': 32, 'question': 'Which tag is used for links in HTML?', 'options': ['<link>', '<href>', '<a>', '<url>'], 'correct': '<a>'},
    {'id': 33, 'question': 'What is the default port for HTTP?', 'options': ['80', '443', '21', '22'], 'correct': '80'},
    {'id': 34, 'question': 'Which of these is used for styling web pages?', 'options': ['HTML', 'JavaScript', 'CSS', 'PHP'], 'correct': 'CSS'},
    {'id': 35, 'question': 'What is the keyword for defining a function in Python?', 'options': ['func', 'function', 'def', 'define'], 'correct': 'def'},
    {'id': 36, 'question': 'What is the output of len([1, 2, 3])?', 'options': ['1', '2', '3', '0'], 'correct': '3'},
    {'id': 37, 'question': 'Which of these is a Python dictionary?', 'options': ['[1, 2]', '(1, 2)', '{"key": "value"}', '{1, 2}'], 'correct': '{"key": "value"}'},
    {'id': 38, 'question': 'What is the slice syntax for the first three items?', 'options': ['[:3]', '[3:]', '[0:2]', '[1:3]'], 'correct': '[:3]'},
    {'id': 40, 'question': 'What is the result of bool("") in Python?', 'options': ['True', 'False', 'None'], 'correct': 'False'}
]

@login_required
def quiz(request):
    # Use first 30 questions in fixed order as per most recent request
    current_questions = QUIZ_QUESTIONS[:30]
    
    if request.method == 'POST':
        score = 0
        points_per_question = 1 # 1 mark each
        
        for q in current_questions:
            user_answer = request.POST.get(f'question_{q["id"]}')
            if user_answer == q['correct']:
                score += points_per_question
        
        # Update user profile
        try:
            profile = request.user.profile
        except Profile.DoesNotExist:
            profile = Profile.objects.create(user=request.user)
            
        profile.assessment_marks = score
        profile.save()
        
        if score >= 25:
            messages.success(request, f'Congratulations! You passed with a score of {score}/30. New opportunities unlocked!')
            CommunityPost.objects.create(
                user=request.user,
                content=f"I just passed the Skill Assessment Quiz with a score of {score}/30! 📜🎓",
                category='certificate'
            )
        else:
            messages.warning(request, f'You scored {score}/30. You need 25 to pass. Please try again.')
            
        return redirect('dashboard')
    
    return render(request, 'quiz.html', {'questions': current_questions})

@login_required
def feedback(request):
    if request.method == 'POST':
        messages.success(request, "Thank you for your feedback! We appreciate your input.")
        return redirect('dashboard')
    return render(request, 'feedback.html')

@login_required
def social_feed(request):
    posts = [
        {'user': 'Alice', 'action': 'completed', 'target': 'Python Mastery Course', 'time': '2h ago', 'avatar': '👩‍💻'},
        {'user': 'Bob', 'action': 'is looking for', 'target': 'Hackathon Teammates', 'time': '5h ago', 'avatar': '👨‍💻'},
        {'user': 'Charlie', 'action': 'started', 'target': 'Internship at TechCorp', 'time': '1d ago', 'avatar': '🚀'},
        {'user': 'David', 'action': 'published', 'target': 'A new project: AI Chatbot', 'time': '2d ago', 'avatar': '🤖'},
    ]
    return render(request, 'social_feed.html', {'posts': posts})

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Dummy data for job notifications if none exist
    if not notifications:
        notifications = [
            {'message': 'New Internship posted: Frontend Developer at TechCorp', 'created_at': 'Today'},
            {'message': 'Your profile was viewed by 5 recruiters', 'created_at': 'Yesterday'},
            {'message': 'Reminder: Python Workshop starts in 2 days', 'created_at': '2 days ago'}
        ]
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def connections_view(request):
    connections = Connection.objects.filter(user=request.user)
    # Dummy posts for connections
    connection_posts = [
        {'user': 'Rahul', 'content': 'Just finished my first React project!', 'time': '1h ago'},
        {'user': 'Priya', 'content': 'Looking for team members for the upcoming Hackathon.', 'time': '3h ago'},
        {'user': 'Amit', 'content': 'Excited to start my internship at Google!', 'time': '1d ago'}
    ]
    return render(request, 'connections.html', {'connections': connections, 'posts': connection_posts})

@login_required
def skills_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)
    if request.method == 'POST':
        new_skill = request.POST.get('skill')
        if new_skill:
            current_skills = profile.skills.split(',') if profile.skills else []
            current_skills = [s.strip() for s in current_skills if s.strip()]
            if new_skill not in current_skills:
                current_skills.append(new_skill)
                profile.skills = ', '.join(current_skills)
                profile.save()
                messages.success(request, f'Skill "{new_skill}" added!')
            else:
                messages.warning(request, f'Skill "{new_skill}" already exists.')
        return redirect('skills')
    
    skills_list = [s.strip() for s in profile.skills.split(',')] if profile.skills else []
    return render(request, 'skills.html', {'skills': skills_list})

@login_required
def applied_jobs_view(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_at')
    return render(request, 'applied_jobs.html', {'applications': applications})

@login_required
def upcoming_events_view(request):
    # Filter applications with an interview date in the future (or simplified check)
    import datetime
    upcoming = Application.objects.filter(user=request.user, interview_date__isnull=False).order_by('interview_date')
    return render(request, 'upcoming_events.html', {'upcoming': upcoming})

@login_required
def tea_time(request):
    sessions = TeaTimeSession.objects.all().order_by('date_time')
    
    query = request.GET.get('q')
    if query:
        sessions = sessions.filter(
            Q(topic__icontains=query) | 
            Q(description__icontains=query)
        )

    return render(request, 'tea_time.html', {'sessions': sessions, 'query': query})

@login_required
def create_chai_time_session(request):
    # Only Admins and Mentors can host sessions
    if request.user.profile.user_type not in ('admin', 'mentor') and not request.user.is_superuser:
        messages.error(request, 'Only Admins and Mentors can host Chai Time sessions.')
        return redirect('tea_time')

    if request.method == 'POST':
        form = TeaTimeSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.host = request.user
            session.save()
            messages.success(request, 'Chai Time Session created successfully!')
            return redirect('tea_time')
    else:
        form = TeaTimeSessionForm()
    return render(request, 'create_tea_session.html', {'form': form})

# Alias for urls.py compatibility
create_tea_session = create_chai_time_session

@login_required
def join_meeting(request, session_id):
    session = get_object_or_404(TeaTimeSession, id=session_id)
    # Add user to participants if not already
    if request.user not in session.participants.all():
        session.participants.add(request.user)
        
    return render(request, 'meeting_room.html', {'session': session})

def knowledge_vault(request):
    query = request.GET.get('q')
    resources = RESOURCES_DATA
    
    if query:
        query = query.lower()
        filtered_resources = {}
        for slug, data in RESOURCES_DATA.items():
            # Search in title, description, or skills
            title = str(data.get('title', '')).lower()
            description = str(data.get('description', '')).lower()
            skills = [str(s).lower() for s in data.get('skills', [])]
            
            if (query in title or 
                query in description or 
                any(query in skill for skill in skills)):
                filtered_resources[slug] = data
        resources = filtered_resources
    
    return render(request, 'knowledge_vault.html', {'resources': resources, 'query': query})

@login_required
def edit_profile(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=request.user)

    if request.method == 'POST':
        # p_form handles bio, profile_picture, skills, internships
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if p_form.is_valid():
            p_form.save()
            messages.success(request, f'Your profile has been updated!')
            return redirect('dashboard')
    else:
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'p_form': p_form
    }
    return render(request, 'edit_profile.html', context)

@login_required
def view_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile = profile_user.profile
    
    # Check if already connected
    is_connected = Connection.objects.filter(
        user=request.user, connected_user=profile_user
    ).exists() or Connection.objects.filter(
        user=profile_user, connected_user=request.user
    ).exists()
    
    # Get user's community posts
    user_posts = CommunityPost.objects.filter(user=profile_user).order_by('-created_at')[:5]
    
    # Count connections
    connection_count = Connection.objects.filter(
        Q(user=profile_user) | Q(connected_user=profile_user)
    ).count()
    
    # Split skills for template
    skills_list = [s.strip() for s in profile.skills.split(',') if s.strip()] if profile.skills else []
    
    context = {
        'profile_user': profile_user,
        'profile': profile,
        'is_connected': is_connected,
        'user_posts': user_posts,
        'connection_count': connection_count,
        'is_own_profile': request.user == profile_user,
        'skills_list': skills_list,
    }
    return render(request, 'view_profile.html', context)

@login_required
def connect_user(request, username):
    if request.method == 'POST':
        target_user = get_object_or_404(User, username=username)
        
        if target_user == request.user:
            return JsonResponse({'error': 'Cannot connect with yourself'}, status=400)
        
        # Check if already connected
        already = Connection.objects.filter(
            user=request.user, connected_user=target_user
        ).exists() or Connection.objects.filter(
            user=target_user, connected_user=request.user
        ).exists()
        
        if not already:
            Connection.objects.create(user=request.user, connected_user=target_user)
            Notification.objects.create(
                user=target_user,
                message=f"🤝 {request.user.username} connected with you!"
            )
            return JsonResponse({'status': 'connected', 'message': 'Connected successfully!'})
        else:
            return JsonResponse({'status': 'already', 'message': 'Already connected'})
    
    return JsonResponse({'error': 'POST required'}, status=405)

def resource_detail(request, slug):
    resource = RESOURCES_DATA.get(slug)
    if not resource:
        return redirect('knowledge_vault')
        
    return render(request, 'resource_detail.html', {'resource': resource})

@login_required
def job_collections(request):
    # Categorize jobs by simple keyword matching or explicit category
    # In a real app, this would likely be a Tag or Sector model
    tech_jobs = Opportunity.objects.filter(description__icontains='developer') | Opportunity.objects.filter(title__icontains='engineer')
    govt_jobs = Opportunity.objects.filter(category='govt')
    marketing_jobs = Opportunity.objects.filter(title__icontains='marketing') | Opportunity.objects.filter(description__icontains='social media')
    other_jobs = Opportunity.objects.exclude(id__in=tech_jobs).exclude(id__in=govt_jobs).exclude(id__in=marketing_jobs)
    
    context = {
        'tech_jobs': tech_jobs.distinct(),
        'govt_jobs': govt_jobs.distinct(),
        'marketing_jobs': marketing_jobs.distinct(),
        'other_jobs': other_jobs.distinct()
    }
    return render(request, 'job_collections.html', context)

@login_required
def ecosystem(request):
    """Entry point for the Brochure/Ecosystem."""
    return render(request, 'ecosystem.html')

@login_required
def open_source(request):
    return render(request, 'open_source.html', {'data': OPEN_SOURCE_DATA})

@login_required
def jobs_home(request):
    """Level 2: Jobs Selection (Private vs Govt)."""
    return render(request, 'jobs_home.html')

@login_required
def internships_home(request):
    """Level 2: Internships Selection (Paid vs Unpaid)."""
    return render(request, 'internships_home.html')

@login_required
def job_list(request, category):
    """
    Level 3: Job Listings.
    category: 'private' or 'govt'
    """
    jobs = Opportunity.objects.filter(type='job', category=category).order_by('-created_at')
    
    query = request.GET.get('q')
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(company__icontains=query)
        )

    context = {
        'category': category,
        'title': f"{category.title()} Jobs",
        'jobs': jobs,
        'query': query
    }
    return render(request, 'job_list.html', context)

@login_required
def internship_list(request, stipend_type):
    """
    Level 3: Internship Listings.
    stipend_type: 'paid' or 'unpaid'
    """
    internships = Opportunity.objects.filter(type='internship', stipend_type=stipend_type).order_by('-created_at')
    
    query = request.GET.get('q')
    if query:
        # Search by Domain (Hardware/Software) or general text
        internships = internships.filter(
            Q(title__icontains=query) | 
            Q(description__icontains=query) |
            Q(domain__icontains=query)
        )
        
        # NOTIFICATION LOGIC (As requested)
        # Notify User
        Notification.objects.create(
            user=request.user,
            message=f"You searched for '{query}' in {stipend_type.title()} Internships."
        )
        # Notify Admin (Superusers)
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"User {request.user.username} searched for '{query}' in {stipend_type} internships."
            )

    context = {
        'stipend_type': stipend_type,
        'title': f"{stipend_type.title()} Internships",
        'internships': internships,
        'query': query
    }
    return render(request, 'internship_list.html', context)

@login_required
def apply_for_opportunity(request, job_id):
    from django.shortcuts import get_object_or_404, redirect
    from network.models import Application
    
    job = get_object_or_404(Opportunity, pk=job_id)

    # Redirect to payment if it's a paid internship
    if job.type == 'internship' and job.stipend_type == 'paid':
        # Check if already applied
        if Application.objects.filter(user=request.user, opportunity=job).exists():
            messages.info(request, "You have already applied for this internship.")
            return redirect('job_detail', job_id=job.id)
        return redirect('internship_payment', job_id=job.id)
    
    if request.method == 'POST':
        # Create application entry
        Application.objects.create(
            user=request.user,
            opportunity=job,
            status='applied'
        )
        return render(request, 'application_success.html', {'job': job})
        
    return redirect('job_detail', job_id=job.id)

@login_required
def internship_payment(request, job_id):
    job = get_object_or_404(Opportunity, pk=job_id)
    
    if request.method == 'POST':
        # Simulate payment success
        from network.models import Application
        Application.objects.create(
            user=request.user,
            opportunity=job,
            status='applied'
        )
        messages.success(request, f"Payment successful! You have applied for {job.title}.")
        return render(request, 'application_success.html', {'job': job})

    return render(request, 'payment_process.html', {'job': job})

@login_required
def job_detail(request, job_id):
    from django.shortcuts import get_object_or_404
    job = get_object_or_404(Opportunity, pk=job_id)
    return render(request, 'job_detail.html', {'job': job})

@login_required
def community_hub(request):
    if request.method == 'POST':
        form = CommunityPostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.save()
            messages.success(request, 'Posted successfully! 🚀')
            return redirect('community_hub')
    else:
        form = CommunityPostForm()
    
    posts = CommunityPost.objects.all().order_by('-created_at')
    
    # Search functionality
    query = request.GET.get('q', '')
    search_users = []
    if query:
        posts = posts.filter(
            Q(content__icontains=query) | 
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query)
        )
        search_users = User.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query)
        ).exclude(id=request.user.id)[:10]
    
    return render(request, 'community_hub.html', {
        'form': form, 
        'posts': posts,
        'query': query,
        'search_users': search_users,
    })

@login_required
def like_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'count': post.likes.count()
    })

@login_required
def create_opportunity(request):
    if request.method == 'POST':
        form = OpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)
            opportunity.posted_by = request.user
            opportunity.save()
            messages.success(request, 'Opportunity posted successfully! 🚀')
            # Redirect to the specific list based on type/category
            type_slug = 'jobs' if opportunity.type == 'job' else 'internships'
            return redirect('opportunity_list', type=type_slug, category=opportunity.category)
    else:
        form = OpportunityForm()
    
    return render(request, 'create_opportunity.html', {'form': form})

# Mentoring System Views
@login_required
@login_required
def mentoring_brochure(request):
    """Display available mentor profiles (Alumni) with skill match %."""
    mentors = Profile.objects.filter(user_type='alumni').exclude(user=request.user)
    
    user_skills_raw = request.user.profile.skills
    user_skills = set(s.strip().lower() for s in user_skills_raw.split(',')) if user_skills_raw else set()
    
    mentor_list = []
    for mentor in mentors:
        m_skills_raw = mentor.skills
        m_skills = [s.strip().lower() for s in m_skills_raw.split(',')] if m_skills_raw else []
        
        match_percentage = 0
        if m_skills:
            common = [s for s in m_skills if s in user_skills]
            match_percentage = int((len(common) / len(m_skills)) * 100)
            
        mentor_list.append({
            'profile': mentor,
            'match_percentage': match_percentage,
            'skills_list': m_skills[:3]
        })
    
    mentor_list.sort(key=lambda x: x['match_percentage'], reverse=True)
    return render(request, 'mentoring_brochure.html', {'mentors': mentor_list})

@login_required
def manage_mentorship_requests(request):
    """Allow mentors to see and accept/reject student requests."""
    if request.user.profile.user_type != 'alumni' and not request.user.is_superuser:
        messages.error(request, "Access denied. Only mentors can manage requests.")
        return redirect('dashboard')
        
    mentor_reqs = MentorRequest.objects.filter(mentor=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        
        ment_req = get_object_or_404(MentorRequest, id=req_id, mentor=request.user)
        
        if action == 'accept':
            ment_req.status = 'accepted'
            ment_req.save()
            Notification.objects.create(
                user=ment_req.student,
                content=f"Your mentorship request to {request.user.username} has been ACCEPTED! 🎓"
            )
            messages.success(request, f"Request from {ment_req.student.username} accepted.")
        elif action == 'reject':
            ment_req.status = 'rejected'
            ment_req.save()
            messages.info(request, f"Request from {ment_req.student.username} rejected.")
            
        return redirect('manage_mentorship_requests')
        
    return render(request, 'manage_requests.html', {'mentor_requests': mentor_reqs})

@login_required
def request_mentor(request, mentor_id):
    """Handle request submission and admin notification."""
    mentor_user = get_object_or_404(User, id=mentor_id)
    
    if request.method == 'POST':
        message = request.POST.get('message')
        from network.models import MentorRequest, Notification
        
        # Create request
        ment_req = MentorRequest.objects.create(
            student=request.user,
            mentor=mentor_user,
            message=message
        )
        
        # Notify Admin
        admins = User.objects.filter(is_superuser=True)
        for admin in admins:
            Notification.objects.create(
                user=admin,
                message=f"New Mentor Request: {request.user.username} wants to connect with {mentor_user.username}."
            )
        
        # Notify Mentor
        Notification.objects.create(
            user=mentor_user,
            message=f"Interaction Request: {request.user.username} wants to clarify doubts with you."
        )

        messages.success(request, f"Request sent to {mentor_user.username}! Admin has been notified.")
        return redirect('mentoring_brochure')
        
    return render(request, 'request_mentor_form.html', {'mentor': mentor_user})

@login_required
def mentor_chat(request, req_id):
    """Display the chat interface for a request."""
    from network.models import MentorRequest, ChatMessage
    ment_req = get_object_or_404(MentorRequest, id=req_id)
    
    # Ensure participant
    if request.user != ment_req.student and request.user != ment_req.mentor and not request.user.is_superuser:
        messages.error(request, "Access denied to this chat.")
        return redirect('dashboard')
        
    messages_list = ment_req.messages.all().order_by('timestamp')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            # Create user's message
            ChatMessage.objects.create(
                request=ment_req,
                sender=request.user,
                content=content
            )

            # AI Mentor Simulation (If student is speaking)
            if request.user == ment_req.student:
                import random
                lower_content = content.lower()
                
                # Contextual Map for "Exact" Answers
                context_responses = {
                    'python': [
                        "Python is excellent for readability. Are you working on its application in Data Science or Web Development (Django/Flask)?",
                        "Make sure to understand list comprehensions and decorators!"
                    ],
                    'javascript': [
                        "JavaScript is the language of the web. Have you tried ES6+ features like arrow functions and destructuring?",
                        "Check out MDN docs for deep dives into JS concepts."
                    ],
                    'django': [
                        "Django's MVT architecture is powerful. Are you using Class Based Views or Function Based Views?",
                        "Don't forget to run migrations after changing models!"
                    ],
                    'java': [
                        "Java is great for enterprise apps. Make sure you understand the 'Object Oriented' principles thoroughly.",
                        "Are you using Spring Boot for your Java project? It's highly demanded in the current market.",
                        "For Java performance, focus on Garbage Collection and Memory Management concepts."
                    ],
                    'resume': [
                        "Your resume should be ATS-friendly. Use a clean single-column layout and include quantifiable results.",
                        "On your resume, highlight your projects with links to GitHub. It proves you can actually build things!",
                        "I can review your resume! Key tip: Match your skills section to the specific job description."
                    ],
                    'interview': [
                        "For technical interviews, practice LeetCode and understand Big O notation. It's almost always asked.",
                        "Behavioral questions are as important as technical ones. Use the START method to answer them.",
                        "Don't forget to research the company's culture before the interview. It shows genuine interest."
                    ],
                    'project': [
                        "Projects are the best way to learn. Try building a CRUD app first, then scale it with real-time features.",
                        "For your project portfolio, focus on solving a real-world problem rather than just following tutorials.",
                        "Make sure your projects are well-documented on GitHub. A good README is a developer's best friend."
                    ]
                }
                
                # Find exact match or falls back to general
                response_text = ""
                for keyword, responses in context_responses.items():
                    if keyword in lower_content:
                        response_text = random.choice(responses)
                        break
                
                if not response_text:
                    if 'internship' in lower_content or 'job' in lower_content:
                        response_text = "Regarding career opportunities, I recommend keeping your Git repo active. Recruiters love seeing consistent contributions!"
                    elif 'error' in lower_content or 'bug' in lower_content or 'help' in lower_content:
                        response_text = "Debugging is a core skill. Try to reproduce the error in an isolated environment first. What does the console log say?"
                    elif 'hi' in lower_content or 'hello' in lower_content:
                        response_text = f"Hello {request.user.username}! I am happy to guide you. How can I assist with your doubts today?"
                    else:
                        ai_responses = [
                            "That's a great question! I suggest focusing on the fundamentals before diving into complex layers.",
                            "I understand your doubt. Most students find this tricky at first. Have you tried a hands-on approach?",
                            "Interesting point! Many industry experts still debate this topic. Always keep the user experience in mind.",
                            "Glad to see your proactive approach! Keep exploring these concepts, they are highly valuable.",
                            "Hello! I am here to help. Could you clarify which part of the implementation you're finding difficult?",
                            "That sounds like a robust strategy for your career. Don't forget to network with other alumni too!"
                        ]
                        response_text = random.choice(ai_responses)

                mentor_name = ment_req.mentor.first_name if ment_req.mentor.first_name else ment_req.mentor.username
                ChatMessage.objects.create(
                    request=ment_req,
                    sender=ment_req.mentor,
                    content=f"[{mentor_name} (AI)]: {response_text}"
                )
                
        return redirect('mentor_chat', req_id=req_id)
        
    return render(request, 'mentor_chat.html', {'req': ment_req, 'chat_messages': messages_list})

# Admin Portal Logic
def admin_required(view_func):
    from functools import wraps
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            return redirect('login')
            
        # Security: Check authorized Admin list (Name + Email)
        allowed_admins = ['Akshaya', 'Ramya', 'Divya', 'Harini', 'Akanksha']
        allowed_email = 'almamate@gmail.com'
        
        is_authorized = (
            request.user.username.lower() in [name.lower() for name in allowed_admins] and 
            request.user.email.lower() == allowed_email.lower()
        )
        
        if not is_authorized and not request.user.is_superuser:
            from django.contrib import messages
            messages.error(request, "Access denied. You are not an authorized administrator.")
            from django.shortcuts import redirect
            return redirect('dashboard')
            
        return view_func(request, *args, **kwargs)
    return _wrapped_view

@admin_required
def admin_dashboard(request):
    """Level 3: Admin Dashboard with detailed stats."""
    from network.models import Profile, MentorRequest, Opportunity, Application, User
    
    stats = {
        'total_students': Profile.objects.filter(user_type='student').count(),
        'total_alumni': Profile.objects.filter(user_type='alumni').count(),
        'total_mentors': Profile.objects.filter(user_type='mentor').count(),
        'total_active_users': User.objects.filter(is_active=True).count(),
        'quiz_participants': Profile.objects.filter(assessment_marks__gt=0).count(),
        'mentor_requests': MentorRequest.objects.count(),
    }
    
    return render(request, 'admin/dashboard.html', {'stats': stats})

@admin_required
def admin_user_management(request):
    from network.models import Profile, AuditLog
    profiles = Profile.objects.all().select_related('user')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        new_role = request.POST.get('new_role')
        target_profile = get_object_or_404(Profile, user_id=user_id)
        old_role = target_profile.user_type
        target_profile.user_type = new_role
        target_profile.save()
        
        # Log action
        AuditLog.objects.create(
            admin=request.user,
            action=f"Changed role of {target_profile.user.username} from {old_role} to {new_role}",
            target=target_profile.user.username
        )
        messages.success(request, f"Role updated for {target_profile.user.username}")
        return redirect('admin_user_management')

    return render(request, 'admin/user_management.html', {'profiles': profiles})

@admin_required
def admin_mentor_requests(request):
    from network.models import MentorRequest, AuditLog
    requests = MentorRequest.objects.all().order_by('-created_at')
    
    if request.method == 'POST':
        req_id = request.POST.get('req_id')
        new_status = request.POST.get('status')
        ment_req = get_object_or_404(MentorRequest, id=req_id)
        ment_req.status = new_status
        ment_req.save()
        
        # Log action
        AuditLog.objects.create(
            admin=request.user,
            action=f"Updated Mentor Request #{req_id} status to {new_status}",
            target=ment_req.student.username
        )
        messages.success(request, "Mentor request updated.")
        return redirect('admin_mentor_requests')

    return render(request, 'admin/mentor_requests.html', {'mentor_requests': requests})

@admin_required
def admin_quiz_participation(request):
    from network.models import Profile
    participants = Profile.objects.filter(assessment_marks__gt=0).order_by('-assessment_marks')
    return render(request, 'admin/quiz_participation.html', {'participants': participants})

@admin_required
def admin_audit_logs(request):
    from network.models import AuditLog
    logs = AuditLog.objects.all().order_by('-timestamp')
    return render(request, 'admin/audit_logs.html', {'logs': logs})

@admin_required
def admin_reports(request):
    return render(request, 'admin/reports.html')

@admin_required
def admin_settings(request):
    return render(request, 'admin/settings.html')

@admin_required
def admin_students_list(request):
    from network.models import Profile
    students = Profile.objects.filter(user_type='student').select_related('user').order_by('-user__date_joined')
    return render(request, 'admin/student_list.html', {'students': students})

@admin_required
def admin_alumni_list(request):
    from network.models import Profile
    alumni = Profile.objects.filter(user_type='alumni').select_related('user').order_by('-user__date_joined')
    return render(request, 'admin/alumni_list.html', {'alumni': alumni})

@admin_required
def admin_mentors_list(request):
    from network.models import Profile
    mentors = Profile.objects.filter(user_type='mentor').select_related('user').order_by('-user__date_joined')
    return render(request, 'admin/mentor_list.html', {'mentors': mentors})

@admin_required
def admin_active_users_list(request):
    from network.models import User
    active_users = User.objects.filter(is_active=True).select_related('profile').order_by('-last_login')
    return render(request, 'admin/active_users_list.html', {'active_users': active_users})

@admin_required
def admin_quiz_stats(request):
    from network.models import Profile
    
    # Summary Stats
    total_attempts = Profile.objects.filter(assessment_marks__gt=0).count()
    below_25 = Profile.objects.filter(assessment_marks__gt=0, assessment_marks__lt=25).count()
    above_25 = Profile.objects.filter(assessment_marks__gte=25).count()
    full_marks = Profile.objects.filter(assessment_marks=30).count()
    
    # Detailed Table
    participants = Profile.objects.filter(assessment_marks__gt=0).select_related('user').order_by('-assessment_marks')
    
    context = {
        'total_attempts': total_attempts,
        'below_25': below_25,
        'above_25': above_25,
        'full_marks': full_marks,
        'participants': participants
    }
    return render(request, 'admin/quiz_stats.html', context)
