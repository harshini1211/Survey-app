from django.db import models
from django.contrib.auth.models import User

# UserProfile model to extend User with a role
class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('creator', 'Survey Creator'),
        ('taker', 'Survey Taker'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return self.user.username

class Survey(models.Model):
    STATE_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('republished', 'Republished'),
    )
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField()
    state = models.CharField(max_length=11, choices=STATE_CHOICES, default='draft')  # Update max_length to 11
    published_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name



# Question model
class Question(models.Model):
    QUESTION_TYPES = (
        ('radio', 'Single Choice'),
        ('checkbox', 'Multiple Choice'),
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=10, choices=QUESTION_TYPES)

    def __str__(self):
        return self.text

# Option model
class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    text = models.CharField(max_length=200)

    def __str__(self):
        return self.text

# Response model
class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    taker = models.ForeignKey(User, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(Option)

    def __str__(self):
        return f"{self.question.text} - {self.response.taker.username}"
