from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    USER_TYPE_CHOICES = (
        ('student', 'Student'),
        ('alumni', 'Alumni'),
        ('mentor', 'Mentor'),
        ('admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='student')
    assessment_marks = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated skills")
    profile_picture = models.ImageField(upload_to='profile_pics', blank=True, null=True)
    
    # Career/Internship Info
    government_internships = models.TextField(blank=True, help_text="Details of government internships")
    private_internships_jobs = models.TextField(blank=True, help_text="Details of private internships and jobs")
    
    def __str__(self):
        return f'{self.user.username} Profile'

class SuccessStory(models.Model):
    alumni = models.ForeignKey(Profile, on_delete=models.CASCADE, limit_choices_to={'user_type': 'alumni'})
    title = models.CharField(max_length=200)
    story = models.TextField()
    graduation_year = models.IntegerField()
    image = models.ImageField(upload_to='success_stories', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Opportunity(models.Model):
    OPPORTUNITY_TYPE_CHOICES = (
        ('internship', 'Internship'),
        ('job', 'Job'),
    )
    CATEGORY_CHOICES = (
        ('govt', 'Government'),
        ('private', 'Private'),
    )
    STIPEND_CHOICES = (
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
    )
    DOMAIN_CHOICES = (
        ('software', 'Software'),
        ('hardware', 'Hardware'),
        ('other', 'Other'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    type = models.CharField(max_length=20, choices=OPPORTUNITY_TYPE_CHOICES)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='private')
    stipend_type = models.CharField(max_length=10, choices=STIPEND_CHOICES, default='paid', blank=True)
    domain = models.CharField(max_length=10, choices=DOMAIN_CHOICES, default='software')
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    min_assessment_score = models.IntegerField(default=25)

    def __str__(self):
        return f"{self.title} at {self.company}"

class Application(models.Model):
    STATUS_CHOICES = (
        ('applied', 'Applied'),
        ('interview', 'Interview Scheduled'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='applied')
    applied_at = models.DateTimeField(auto_now_add=True)
    interview_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.opportunity.title}"

class Connection(models.Model):
    user = models.ForeignKey(User, related_name='connections', on_delete=models.CASCADE)
    connected_user = models.ForeignKey(User, related_name='connected_to', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} connected with {self.connected_user.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

class TeaTimeSession(models.Model):
    STATUS_CHOICES = (
        ('scheduled', 'Scheduled'),
        ('live', 'Live Now'),
        ('completed', 'Completed'),
    )
    host = models.ForeignKey(User, related_name='hosted_sessions', on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date_time = models.DateTimeField()
    meeting_link = models.URLField(blank=True, help_text="Link to join the meeting (internal or external)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    participants = models.ManyToManyField(User, related_name='joined_sessions', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic} hosted by {self.host.username}"

class CommunityPost(models.Model):
    CATEGORY_CHOICES = (
        ('certificate', 'Certificate 📜'),
        ('academic', 'Academic Result 🎓'),
        ('project', 'Project Showcase 💻'),
        ('general', 'General Update 📢'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='community_images', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='general')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.category}"

class MentorRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    student = models.ForeignKey(User, related_name='mentor_requests', on_delete=models.CASCADE)
    mentor = models.ForeignKey(User, related_name='mentoring_sessions', on_delete=models.CASCADE)
    message = models.TextField(help_text="Reason for seeking mentorship")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request: {self.student.username} to {self.mentor.username} ({self.status})"

class ChatMessage(models.Model):
    request = models.ForeignKey(MentorRequest, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} at {self.timestamp}"

class AuditLog(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    target = models.CharField(max_length=255, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.username} - {self.action} - {self.timestamp}"
