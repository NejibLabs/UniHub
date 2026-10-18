from django.conf import settings
from django.db import models
from django.utils import timezone

SEMESTER_CHOICES = [
    ("semester_1", "Semester 1"),
    ("semester_2", "Semester 2"),
]


def semester_for_date(value):
    if value.month >= 9 or (value.month == 1 and value.day <= 15):
        return "semester_1"
    return "semester_2"


def current_semester():
    return semester_for_date(timezone.localdate())


def years_for_specialty(specialty):
    if specialty and specialty.cycle in ("preparatory", "master"):
        return (1, 2)
    return (1, 2, 3)


class Faculty(models.Model):
    name=models.CharField(max_length=160,unique=True)
    description=models.TextField(blank=True)
    class Meta: ordering=["name"]
    def __str__(self): return self.name

class Specialty(models.Model):
    CYCLE_CHOICES=[
        ("preparatory","Preparatory cycle"),
        ("bachelor","Bachelor"),
        ("master","Master"),
        ("engineering","Engineering cycle"),
    ]
    faculty=models.ForeignKey(Faculty,on_delete=models.CASCADE,related_name="specialties")
    name=models.CharField(max_length=160)
    cycle=models.CharField(max_length=20,choices=CYCLE_CHOICES,default="bachelor")
    class Meta:
        ordering=["name"]
        unique_together=[("faculty","name")]
    def __str__(self): return f"{self.name} — {self.faculty.name}"

class Subject(models.Model):
    specialty=models.ForeignKey(Specialty,on_delete=models.CASCADE,related_name="subjects")
    name=models.CharField(max_length=180)
    code=models.CharField(max_length=40,blank=True)
    description=models.TextField(blank=True)
    professors=models.ManyToManyField(settings.AUTH_USER_MODEL,blank=True,related_name="teaching_subjects")
    year = models.PositiveIntegerField(default=1)

    semester = models.PositiveSmallIntegerField(
        choices=[(1, "Semester 1"), (2, "Semester 2")],
        default=1,
    )
    class Meta: ordering=["name"]
    def __str__(self): return self.name

class UserProfile(models.Model):
    ROLE_CHOICES=[("student","Student"),("professor","Professor"),("representative","Department representative")]
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="profile")
    role=models.CharField(max_length=20,choices=ROLE_CHOICES,default="student")
    semester=models.CharField(max_length=12,choices=SEMESTER_CHOICES,default=current_semester)
    specialty=models.ForeignKey(Specialty,on_delete=models.SET_NULL,null=True,blank=True,related_name="students")
    current_year=models.PositiveSmallIntegerField(choices=[(1,"Year 1"),(2,"Year 2"),(3,"Year 3")],default=1)
    bio=models.TextField(blank=True)
    avatar_url=models.URLField(blank=True)
    avatar=models.ImageField(upload_to="avatars/%Y/%m/%d/",blank=True,null=True)
    follows=models.ManyToManyField("self",symmetrical=False,blank=True,related_name="followed_by")
    created_at=models.DateTimeField(auto_now_add=True)
    def save(self,*args,**kwargs):
        if self._state.adding and self.user_id and self.user.date_joined:
            self.semester=semester_for_date(timezone.localtime(self.user.date_joined).date())
        super().save(*args,**kwargs)
    def refresh_semester(self):
        semester=current_semester()
        if self.semester != semester:
            self.semester=semester
            self.save(update_fields=["semester"])
    def __str__(self): return f"{self.user.username} profile"

class Resource(models.Model):
    CATEGORY_CHOICES=[
        ("exam","Exam"),
        ("notes","Notes"),
        ("other","Other"),
    ]
    subject=models.ForeignKey(Subject,on_delete=models.CASCADE,related_name="resources")
    title=models.CharField(max_length=200)
    author=models.CharField(max_length=200,blank=True)
    category=models.CharField(max_length=12,choices=CATEGORY_CHOICES,default="other")
    description=models.TextField(blank=True)
    url=models.URLField()
    submitted_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="submitted_resources")
    is_verified=models.BooleanField(default=False)
    verified_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name="verified_resources")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-is_verified","-created_at"]
    def __str__(self): return self.title

class ToDo(models.Model):
    subject=models.ForeignKey(Subject,on_delete=models.CASCADE,related_name="tasks")
    title=models.CharField(max_length=200)
    description=models.TextField(blank=True)
    due_date=models.DateField(null=True,blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="created_tasks")
    assigned_to=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,null=True,blank=True,related_name="assigned_tasks")
    is_completed=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["is_completed","due_date","-created_at"]
    @property
    def is_overdue(self): return bool(self.due_date and self.due_date<timezone.localdate() and not self.is_completed)
    def __str__(self): return self.title

class ActivityLog(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    action=models.CharField(max_length=180)
    details=models.CharField(max_length=300,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
    def __str__(self): return self.action

class ContactMessage(models.Model):
    CATEGORY_CHOICES=[
        ("feedback","Feedback"),
        ("alert","Alert / Report"),
        ("complaint","Reclamation / Complaint"),
        ("inquiry","General inquiry"),
    ]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="contact_messages")
    username=models.CharField(max_length=150)
    contact_name=models.CharField(max_length=301,blank=True)
    email=models.EmailField(blank=True)
    category=models.CharField(max_length=20,choices=CATEGORY_CHOICES)
    message=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-created_at"]
        verbose_name="contact message"
        verbose_name_plural="contact messages"
    def __str__(self): return f"{self.get_category_display()} from {self.username}"

class NewsComment(models.Model):
    post=models.ForeignKey("NewsPost",on_delete=models.CASCADE,related_name="comments")
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="news_comments")
    content=models.TextField(max_length=500)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["created_at"]
    def __str__(self): return f"{self.author.username} on {self.post}"

class NewsPost(models.Model):
    faculty=models.ForeignKey(Faculty,on_delete=models.CASCADE,related_name="news_posts")
    author=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="news_posts")
    content=models.TextField()
    image=models.ImageField(upload_to="news/%Y/%m/%d/",blank=True,null=True)
    link_url=models.URLField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta: ordering=["-created_at"]
    @property
    def display_image(self):
        return self.image.url if self.image else ""
    def __str__(self): return f"{self.author.username} · {self.faculty.name}"

class NewsLike(models.Model):
    post=models.ForeignKey(NewsPost,on_delete=models.CASCADE,related_name="likes")
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="news_likes")
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints=[
            models.UniqueConstraint(fields=("post","user"),name="unique_news_like_per_user"),
        ]

    def __str__(self): return f"{self.user.username} likes {self.post}"
