from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count,Q
from django.http import HttpResponseForbidden
from django.shortcuts import render,redirect,get_object_or_404
from django.db.models.functions import TruncMonth
from datetime import date,datetime,time
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Faculty,Specialty,Subject,UserProfile,Resource,ToDo,ActivityLog,NewsPost,ContactMessage,years_for_specialty
from .forms import RegisterForm,StudentProfileForm,ProfileForm,ResourceForm,ToDoForm,NewsPostForm,ContactMessageForm

def profile_for(user):
    obj,created=UserProfile.objects.get_or_create(user=user)
    return obj
def log(user,action,details=""):
    ActivityLog.objects.create(user=user if user.is_authenticated else None,action=action,details=details[:300])
def home(request):
    return render(request,"home.html",{
        "subject_count":Subject.objects.count(),
        "resource_count":Resource.objects.filter(is_verified=True).count(),
        "faculty_count":Faculty.objects.count(),
        "specialty_count":Specialty.objects.count(),
        "total_resource_count":Resource.objects.count(),
        "student_count":UserProfile.objects.filter(role="student").count(),
        "subjects":Subject.objects.select_related("specialty")[:3],
        "pending_task_count":ToDo.objects.filter(is_completed=False).count(),
        "pending_tasks":ToDo.objects.filter(is_completed=False).select_related("subject")[:2],
    })
def about(request): return render(request,"about.html")

@login_required
def contact(request):
    form=ContactMessageForm(request.POST or None,user=request.user)
    if request.method=="POST" and form.is_valid():
        form.save()
        messages.success(request,"Your message has been sent to the UniHub team.")
        return redirect("contact")
    return render(request,"contact.html",{"form":form})

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("Only administrators can access this page.")
    total_users=get_user_model().objects.count()
    total_faculties=Faculty.objects.count()
    total_specialties=Specialty.objects.count()
    total_subjects=Subject.objects.count()
    total_resources=Resource.objects.count()
    pending_resources=Resource.objects.filter(is_verified=False).count()
    verified_resources=total_resources-pending_resources
    total_students=UserProfile.objects.filter(role="student").count()
    total_professors=UserProfile.objects.filter(role="professor").count()
    total_representatives=UserProfile.objects.filter(role="representative").count()
    pending_tasks=ToDo.objects.filter(is_completed=False).count()
    completed_tasks=ToDo.objects.filter(is_completed=True).count()
    today=timezone.localdate()
    month_starts=[]
    year,month=today.year,today.month
    for _ in range(6):
        month_starts.append(date(year,month,1))
        month-=1
        if month==0:
            year-=1
            month=12
    month_starts.reverse()
    next_month=today.replace(day=1)
    if next_month.month==12:
        next_month=date(next_month.year+1,1,1)
    else:
        next_month=date(next_month.year,next_month.month+1,1)
    chart_start=timezone.make_aware(datetime.combine(month_starts[0],time.min))
    chart_end=timezone.make_aware(datetime.combine(next_month,time.min))
    current_timezone=timezone.get_current_timezone()

    def counts_by_month(queryset,field):
        rows=(queryset.filter(**{f"{field}__gte":chart_start,f"{field}__lt":chart_end})
            .annotate(month=TruncMonth(field,tzinfo=current_timezone))
            .values("month").annotate(total=Count("pk")))
        return {(row["month"].year,row["month"].month):row["total"] for row in rows}

    user_months=counts_by_month(get_user_model().objects,"date_joined")
    resource_months=counts_by_month(Resource.objects,"created_at")
    chart_x=[50+index*112 for index in range(6)]
    line_max=max(
        [*user_months.values(),*resource_months.values()],
        default=0,
    )
    line_scale=max(line_max,1)
    line_series=[]
    for label,color,monthly_values in (
        ("New users","#6654d9",user_months),
        ("Resources submitted","#36a17c",resource_months),
    ):
        values=[monthly_values.get((month_start.year,month_start.month),0) for month_start in month_starts]
        points=[
            {"x":x,"y":190-round(value*155/line_scale),"value":value,"month":month_start}
            for x,value,month_start in zip(chart_x,values,month_starts)
        ]
        line_series.append({
            "label":label,
            "color":color,
            "points":points,
            "polyline":" ".join(f"{point['x']},{point['y']}" for point in points),
        })
    line_ticks=[
        {"value":round(line_max*index/3),"y":190-round(round(line_max*index/3)*155/line_scale)}
        for index in range(4)
    ]
    bar_metrics=[
        {"label":"Users","short_label":"Users","value":total_users},
        {"label":"Faculties","short_label":"Faculty","value":total_faculties},
        {"label":"Specialties","short_label":"Specialty","value":total_specialties},
        {"label":"Subjects","short_label":"Subject","value":total_subjects},
        {"label":"Verified resources","short_label":"Verified","value":verified_resources},
        {"label":"Awaiting review","short_label":"Pending","value":pending_resources},
    ]
    bar_max=max((metric["value"] for metric in bar_metrics),default=0)
    for index,metric in enumerate(bar_metrics):
        bar_height=round(metric["value"]*145/bar_max) if bar_max else 0
        metric.update({
            "x":55+index*96,
            "y":185-bar_height,
            "height":bar_height,
        })
    return render(request,"admin_dashboard.html",{
        "user_count":total_users,
        "faculty_count":total_faculties,
        "specialty_count":total_specialties,
        "subject_count":total_subjects,
        "resource_count":total_resources,
        "pending_resource_count":pending_resources,
        "student_count":total_students,
        "line_series":line_series,
        "line_ticks":line_ticks,
        "chart_months":month_starts,
        "bar_metrics":bar_metrics,
        "latest_resources":Resource.objects.select_related(
            "subject","subject__specialty","subject__specialty__faculty","submitted_by"
        ).order_by("-created_at")[:20],
        "recent_activity":ActivityLog.objects.select_related("user")[:15],
        "contact_messages":ContactMessage.objects.select_related("user").order_by("-created_at"),
        "contact_message_count":ContactMessage.objects.count(),
    })

def register(request):
    if request.user.is_authenticated: return redirect("dashboard")
    form=RegisterForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        user=form.save()
        UserProfile.objects.create(
            user=user,
            role="student",
        )
        login(request,user); log(user,"Account created")
        messages.success(request,"Your account is ready. Complete your academic profile.")
        return redirect("student_form")
    return render(request,"registration/register.html",{"form":form})

def login_view(request):
    if request.user.is_authenticated: return redirect("dashboard")
    error=""
    if request.method=="POST":
        user=authenticate(request,username=request.POST.get("username","").strip(),password=request.POST.get("password",""))
        if user:
            login(request,user); profile=profile_for(user); profile.refresh_semester(); log(user,"Logged in")
            nxt=request.POST.get("next") or request.GET.get("next")
            if nxt and url_has_allowed_host_and_scheme(nxt,allowed_hosts={request.get_host()},require_https=request.is_secure()): return redirect(nxt)
            return redirect("dashboard")
        error="The username or password you entered is incorrect."
    return render(request,"registration/login.html",{"error":error,"next":request.GET.get("next","")})

@login_required
@require_POST
def logout_view(request):
    log(request.user,"Logged out"); logout(request); return redirect("home")

@login_required
def student_form(request):
    profile=profile_for(request.user); form=StudentProfileForm(request.POST or None,request.FILES or None,instance=profile)
    if request.method=="POST" and form.is_valid():
        form.save(); messages.success(request,"Your academic profile has been saved."); return redirect("dashboard")
    name_parts=[part for part in (request.user.first_name,request.user.last_name) if part]
    initials="".join(part[0] for part in name_parts[:2]) or request.user.username[:2]
    if len(initials)==1 and request.user.username:
        initials+=request.user.username[1:2]
    return render(request,"registration/student_form.html",{"form":form,"avatar_initials":initials.upper()})

@login_required
def dashboard(request):
    p=profile_for(request.user)
    p.refresh_semester()
    semester_number=1 if p.semester=="semester_1" else 2
    subjects=Subject.objects.none()
    if p.specialty_id:
        subjects=Subject.objects.filter(
            specialty__faculty_id=p.specialty.faculty_id,
            specialty_id=p.specialty_id,
            year=p.current_year,
            semester=semester_number,
        ).select_related("specialty","specialty__faculty")
    tasks=ToDo.objects.filter(Q(assigned_to=request.user)|Q(created_by=request.user)).select_related("subject")
    resources=Resource.objects.filter(subject__in=subjects).select_related("subject","subject__specialty","subject__specialty__faculty").order_by("-created_at")
    verified_resource_count=resources.filter(is_verified=True).count()
    return render(request,"academics/student_hub.html",{
        "profile":p,
        "subjects":subjects,
        "tasks":tasks[:10],
        "resources":resources[:5],
        "pending_count":tasks.filter(is_completed=False).distinct().count(),
        "resource_count":verified_resource_count,
    })

@login_required
def specialty_subjects(request):
    profile=profile_for(request.user)
    if not profile.specialty_id:
        messages.warning(request,"Complete your academic profile to view your specialty subjects.")
        return redirect("student_form")

    specialty=profile.specialty
    subjects=Subject.objects.filter(specialty=specialty).order_by("year","semester","name")
    subject_groups=[
        {
            "year":year,
            "semesters":[
                {
                    "number":semester,
                    "subjects":subjects.filter(year=year,semester=semester),
                }
                for semester in (1,2)
            ],
        }
        for year in years_for_specialty(specialty)
    ]
    return render(request,"academics/specialty_subjects.html",{
        "profile":profile,
        "specialty":specialty,
        "subject_groups":subject_groups,
    })

@login_required
def news_feed(request):
    profile=profile_for(request.user)
    is_student=profile.role=="student" and not request.user.is_staff
    if is_student and not profile.specialty_id:
        messages.warning(request,"Complete your academic profile before posting faculty news.")
        return redirect("student_form")

    faculties=Faculty.objects.all().order_by("name")
    selected_faculty_id=request.GET.get("faculty")
    if "faculty" not in request.GET and profile.specialty and profile.specialty.faculty_id:
        selected_faculty_id=str(profile.specialty.faculty_id)
    selected_faculty=faculties.filter(pk=selected_faculty_id).first() if selected_faculty_id else None

    if request.method=="POST":
        form=NewsPostForm(request.POST,request.FILES)
        if is_student:
            form.fields["faculty"].queryset=Faculty.objects.filter(
                pk=profile.specialty.faculty_id,
            )
        if form.is_valid():
            post=form.save(commit=False)
            post.author=request.user
            post.faculty=form.cleaned_data["faculty"]
            post.save()
            log(request.user,"News post published",post.faculty.name)
            messages.success(request,"Your announcement has been published.")
            if post.faculty_id:
                return redirect(f"{request.path}?faculty={post.faculty_id}")
            return redirect("news_feed")
    else:
        form=NewsPostForm(initial={"faculty": selected_faculty_id or (profile.specialty.faculty_id if profile.specialty else None)})
        if is_student:
            form.fields["faculty"].queryset=Faculty.objects.filter(
                pk=profile.specialty.faculty_id,
            )

    posts=NewsPost.objects.select_related("author__profile","faculty").order_by("-created_at")
    if selected_faculty:
        posts=posts.filter(faculty=selected_faculty)

    return render(request,"news/news_feed.html",{
        "faculties":faculties,
        "selected_faculty":selected_faculty,
        "posts":posts,
        "form":form,
        "user_faculty":profile.specialty.faculty if profile.specialty else None,
    })

@login_required
def subject_list(request):
    q=request.GET.get("q","").strip()
    profile=profile_for(request.user)
    spec=request.GET.get("specialty","") if "specialty" in request.GET else str(profile.specialty_id or "")
    subjects=Subject.objects.select_related("specialty","specialty__faculty")
    if q: subjects=subjects.filter(Q(name__icontains=q)|Q(code__icontains=q)|Q(description__icontains=q))
    if spec.isdigit(): subjects=subjects.filter(specialty_id=int(spec))
    return render(request,"academics/subject_list.html",{"subjects":subjects,"specialties":Specialty.objects.select_related("faculty"),"query":q,"selected_specialty":spec})

def subject_vault(request,subject_id):
    subject=get_object_or_404(Subject.objects.select_related("specialty","specialty__faculty"),pk=subject_id)
    resources=subject.resources.select_related("submitted_by","verified_by")
    tasks=subject.tasks.all()
    return render(request,"academics/subject_vault.html",{"subject":subject,"resources":resources,"tasks":tasks})

@login_required
def add_resource(request,subject_id):
    subject=get_object_or_404(Subject,pk=subject_id); form=ResourceForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.subject=subject; obj.submitted_by=request.user; obj.save(); log(request.user,"Resource submitted",obj.title)
        messages.success(request,"Resource submitted for review."); return redirect("subject_vault",subject_id=subject.pk)
    return render(request,"academics/resource_form.html",{"form":form,"subject":subject})

@login_required
@require_POST
def verify_resource(request,resource_id):
    p=profile_for(request.user); obj=get_object_or_404(Resource,pk=resource_id)
    if not (request.user.is_staff or p.role in ("professor","representative")): return HttpResponseForbidden("You do not have permission to verify resources.")
    obj.is_verified=True; obj.verified_by=request.user; obj.save(update_fields=["is_verified","verified_by"]); log(request.user,"Resource verified",obj.title)
    messages.success(request,"Resource verified.")
    next_url=request.POST.get("next","")
    if next_url and url_has_allowed_host_and_scheme(next_url,allowed_hosts={request.get_host()},require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("subject_vault",subject_id=obj.subject_id)

@login_required
def add_task(request,subject_id):
    subject=get_object_or_404(Subject,pk=subject_id); p=profile_for(request.user)
    if not (request.user.is_staff or p.role in ("professor","representative")): return HttpResponseForbidden("Only professors, representatives, or administrators can create shared tasks.")
    form=ToDoForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.subject=subject; obj.created_by=request.user; obj.save(); log(request.user,"Task created",obj.title)
        messages.success(request,"Task created."); return redirect("subject_vault",subject_id=subject.pk)
    return render(request,"academics/task_form.html",{"form":form,"subject":subject})

@login_required
@require_POST
def toggle_task(request,task_id):
    obj=get_object_or_404(ToDo,pk=task_id)
    if obj.assigned_to_id not in (None,request.user.id) and obj.created_by_id!=request.user.id and not request.user.is_staff: return HttpResponseForbidden("You cannot update this task.")
    if obj.assigned_to_id is None and obj.created_by_id!=request.user.id and not request.user.is_staff: return HttpResponseForbidden("Only the task creator can update this unassigned task.")
    obj.is_completed=not obj.is_completed; obj.save(update_fields=["is_completed"]); log(request.user,"Task status changed",obj.title)
    messages.success(request,"Task status updated.")
    nxt=request.POST.get("next","")
    if nxt and url_has_allowed_host_and_scheme(nxt,allowed_hosts={request.get_host()}): return redirect(nxt)
    return redirect("dashboard")

@login_required
def profile(request):
    p=profile_for(request.user)
    p.refresh_semester()
    form=ProfileForm(request.POST or None,instance=p,user=request.user)
    if request.method=="POST" and form.is_valid():
        form.save(); log(request.user,"Profile updated"); messages.success(request,"Your profile has been updated."); return redirect("profile")
    basic_complete=bool(request.user.first_name.strip() and request.user.last_name.strip() and request.user.email.strip())
    academic_complete=bool(p.specialty_id and p.current_year)
    bio_complete=bool(p.bio.strip())
    avatar_complete=bool(p.avatar or p.avatar_url.strip())
    completion_items=[
        {"label":"Basic information","complete":basic_complete},
        {"label":"Academic details","complete":academic_complete},
        {"label":"Bio","complete":bio_complete},
        {"label":"Avatar","complete":avatar_complete},
    ]
    completed_count=sum(item["complete"] for item in completion_items)
    semester_number=1 if p.semester=="semester_1" else 2
    subjects=Subject.objects.none()
    if p.specialty_id:
        subjects=Subject.objects.filter(
            specialty__faculty_id=p.specialty.faculty_id,
            specialty_id=p.specialty_id,
            year=p.current_year,
            semester=semester_number,
        )
    tasks=ToDo.objects.filter(Q(assigned_to=request.user)|Q(created_by=request.user)).distinct()
    return render(request,"profiles/profile.html",{
        "profile_obj":p,
        "form":form,
        "completion_items":completion_items,
        "completion_percentage":round(completed_count*100/len(completion_items)),
        "profile_subject_count":subjects.count(),
        "profile_task_count":tasks.count(),
        "profile_resource_count":Resource.objects.filter(submitted_by=request.user).count(),
        "profile_follower_count":p.followed_by.count(),
        "profile_initials":(request.user.first_name[:1]+request.user.last_name[:1]).upper() or request.user.username[:2].upper(),
    })

@login_required
def search(request):
    q=request.GET.get("q","").strip(); subjects=Subject.objects.none(); resources=Resource.objects.none()
    if q:
        subjects=Subject.objects.filter(Q(name__icontains=q)|Q(code__icontains=q)|Q(description__icontains=q)).select_related("specialty")
        resources=Resource.objects.filter(Q(title__icontains=q)|Q(description__icontains=q),is_verified=True).select_related("subject")
    return render(request,"search.html",{"query":q,"subjects":subjects,"resources":resources})
