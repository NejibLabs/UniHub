from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from datetime import date,datetime,timedelta
from unittest.mock import patch
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
import os
import struct
import tempfile
import zlib
from .forms import RegisterForm,StudentProfileForm
from .models import Faculty,Specialty,Subject,UserProfile,Resource,ToDo,NewsPost,NewsLike,semester_for_date,years_for_specialty
class UniHubTests(TestCase):
 def setUp(self):
    f=Faculty.objects.create(name="Engineering"); s=Specialty.objects.create(faculty=f,name="Ecological Informatics"); self.subject=Subject.objects.create(specialty=s,name="Hydrology",code="HYD101")
    self.preparatory=Specialty.objects.create(faculty=f,name="Preparatory Program",cycle="preparatory")
    self.master=Specialty.objects.create(faculty=f,name="Master Program",cycle="master")
    self.student=User.objects.create_user(username="student",password="StrongPass123!"); UserProfile.objects.create(user=self.student,specialty=s)
    self.prof=User.objects.create_user(username="prof",password="StrongPass123!"); UserProfile.objects.create(user=self.prof,role="professor")
 def test_home_public(self):
    response=self.client.get(reverse("home"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'class="hero-video" autoplay loop muted playsinline',html=False)
    self.assertContains(response,'src="/static/img/tunisian_flag_waving_loop_h264.mp4"')
 def test_news_about_card_states_student_life_scope(self):
    self.client.force_login(self.student)
    response=self.client.get(reverse("news_feed"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,"UniHub News is for student life: posts must not be about political, religious, or personal matters.")
 def test_contact_page_requires_authentication(self):
    response=self.client.get(reverse("contact"))
    self.assertRedirects(response,f"{reverse('login')}?next={reverse('contact')}")
 def test_contact_message_saves_category_message_and_account_details(self):
    self.client.force_login(self.student)
    response=self.client.post(reverse("contact"),{
        "category":"feedback",
        "message":"Please add a calendar view.",
    })
    self.assertRedirects(response,reverse("contact"))
    from .models import ContactMessage
    contact_message=ContactMessage.objects.get()
    self.assertEqual(contact_message.user,self.student)
    self.assertEqual(contact_message.username,self.student.username)
    self.assertEqual(contact_message.email,self.student.email)
    self.assertEqual(contact_message.category,"feedback")
    self.assertEqual(contact_message.message,"Please add a calendar view.")
 def test_contact_form_shows_account_details_and_categories(self):
    self.client.force_login(self.student)
    response=self.client.get(reverse("contact"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'<body class="contact-body">',html=False)
    self.assertContains(response,"css/contact.css")
    self.assertContains(response,'src="/static/img/Contact%20message%20plane.png"')
    self.assertContains(response,'alt="Purple glass paper plane representing a message sent to the UniHub team"')
    self.assertContains(response,self.student.username)
    self.assertContains(response,self.student.email)
    self.assertContains(response,"Feedback")
    self.assertContains(response,"Alert / Report")
    self.assertContains(response,"Reclamation / Complaint")
    self.assertContains(response,"General inquiry")
 def test_contact_messages_are_available_to_staff_in_admin(self):
    from .models import ContactMessage
    contact_message=ContactMessage.objects.create(
        user=self.student,
        username=self.student.username,
        email=self.student.email,
        category="alert",
        message="A broken link needs attention.",
    )
    self.client.force_login(self.student)
    restricted_response=self.client.get(reverse("admin:core_contactmessage_changelist"))
    self.assertEqual(restricted_response.status_code,302)
    admin=User.objects.create_superuser(username="contactadmin",email="contactadmin@example.com",password="StrongContactAdmin!123")
    self.client.force_login(admin)
    response=self.client.get(reverse("admin:core_contactmessage_changelist"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,self.student.username)
    self.assertContains(response,"A broken link needs attention.")
    detail_response=self.client.get(reverse("admin:core_contactmessage_change",args=[contact_message.pk]))
    self.assertEqual(detail_response.status_code,200)
    self.assertContains(detail_response,"A broken link needs attention.")
 def test_about_page_shows_hero_mockup(self):
    response=self.client.get(reverse("about"))
    self.assertEqual(response.status_code,200)
    self.assertIn('<body class="about-body">',response.content.decode())
    self.assertContains(response,'src="/static/img/Logo%20%C3%A9ducatif%20U.png"')
    self.assertContains(response,'background:linear-gradient(115deg,#fbfaffc9,#fbfaff80)')
    self.assertContains(response,"developed by a fellow student")
    self.assertContains(response,"no religious, political, or other unrelated purpose or affiliation")
    self.assertContains(response,"Made to support the everyday student journey.")
    self.assertContains(response,"Your academic space, step by step.")
    self.assertContains(response,"A connected campus community")
 def test_about_page_introduces_founder_and_uses_provided_portrait(self):
    response=self.client.get(reverse("about"))

    self.assertEqual(response.status_code,200)
    self.assertContains(response,'src="/static/img/mohamed-nejib-ben-hmida.png"')
    self.assertContains(response,'alt="Portrait of Mohamed Nejib Ben Hmida"')
    self.assertContains(response,"Third-year Ecological Engineering student")
    self.assertContains(response,"Bachelor’s degree in Big Data and Data Analysis")
    self.assertContains(response,"I created UniHub to make that experience a little easier")
 def test_register_page_shows_welcome_mockup(self):
    response=self.client.get(reverse("register"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'class="auth-welcome-image" src="/static/img/UniHub%20Student%20Platform%20Hero%20Mockup.png"')
    self.assertNotContains(response,'name="faculty"')
    self.assertNotContains(response,'name="specialty"')
    self.assertNotContains(response,'name="current_year"')
    self.assertNotContains(response,'name="avatar"')
 def test_academic_setup_page_offers_faculty_specialty_year_and_picture(self):
    self.client.force_login(self.student)
    response=self.client.get(reverse("student_form"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'url("/static/img/student-setup-pastel-campus.png")')
    self.assertContains(response,'src="/static/img/Logo%20%C3%A9ducatif%20U.png"')
    self.assertContains(response,'enctype="multipart/form-data"')
    self.assertContains(response,'aria-label="Profile initials">ST</span>')
    self.assertContains(response,'aria-controls="id_avatar">Change</button>')
    self.assertNotContains(response,'Profile picture</label>')
    self.assertNotContains(response,'Currently:')
    self.assertNotContains(response,'Clear</label>')
    self.assertLess(response.content.decode().index('id="id_avatar"'),response.content.decode().index('name="faculty"'))
    for field in ("faculty","specialty","current_year","avatar"):
        self.assertContains(response,f'name="{field}"')
 def test_academic_setup_prefills_saved_faculty_specialty_and_year(self):
    self.student.profile.current_year=2
    self.student.profile.save(update_fields=["current_year"])
    self.client.force_login(self.student)

    response=self.client.get(reverse("student_form"))

    self.assertEqual(response.status_code,200)
    self.assertEqual(response.context["form"]["faculty"].value(),self.subject.specialty.faculty_id)
    self.assertEqual(response.context["form"]["specialty"].value(),self.subject.specialty_id)
    self.assertEqual(response.context["form"]["current_year"].value(),2)
 def test_registration_saves_uploaded_profile_avatar(self):
    def png_chunk(kind,data):
        payload=kind+data
        return struct.pack(">I",len(data))+payload+struct.pack(">I",zlib.crc32(payload)&0xffffffff)

    image_data=(
        b"\x89PNG\r\n\x1a\n"
        +png_chunk(b"IHDR",struct.pack(">IIBBBBB",1,1,8,2,0,0,0))
        +png_chunk(b"IDAT",zlib.compress(b"\x00\xff\x00\x00"))
        +png_chunk(b"IEND",b"")
    )
    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            response=self.client.post(reverse("register"),{
                "username":"avatarstudent",
                "email":"avatarstudent@example.com",
                "password1":"Turtle!River49",
                "password2":"Turtle!River49",
            })
            self.assertRedirects(response,reverse("student_form"))
            user=User.objects.get(username="avatarstudent")
            self.assertFalse(user.profile.avatar)
            response=self.client.post(reverse("student_form"),{
                "faculty":str(self.subject.specialty.faculty_id),
                "specialty":str(self.subject.specialty_id),
                "current_year":"1",
                "avatar":SimpleUploadedFile("avatar.png",image_data,content_type="image/png"),
            },follow=True)
            self.assertRedirects(response,reverse("dashboard"))
            self.assertContains(response,'<dialog class="messages-modal"')
            self.assertContains(response,"Your academic profile has been saved.")
            self.assertContains(response,'class="message-close" type="button">Close</button>')
            user.profile.refresh_from_db()
            self.assertTrue(os.path.isfile(user.profile.avatar.path))
            setup_response=self.client.get(reverse("student_form"))
            self.assertContains(setup_response,f'src="{user.profile.avatar.url}"')
            self.assertContains(setup_response,'aria-controls="id_avatar">Change</button>')
            profile_response=self.client.get(reverse("profile"))
            self.assertContains(profile_response,f'src="{user.profile.avatar.url}"')
 def test_home_dashboard_preview_shows_live_platform_counts(self):
    Resource.objects.create(
        subject=self.subject,
        title="Home page resource",
        url="https://example.com/resource",
        submitted_by=self.student,
        is_verified=True,
    )
    pending_task=ToDo.objects.create(
        subject=self.subject,
        title="Review hydrology notes",
        created_by=self.student,
    )
    response=self.client.get(reverse("home"))
    self.assertEqual(response.context["faculty_count"],1)
    self.assertEqual(response.context["specialty_count"],3)
    self.assertEqual(response.context["total_resource_count"],1)
    self.assertEqual(response.context["student_count"],1)
    self.assertEqual(response.context["subject_count"],1)
    self.assertEqual(response.context["resource_count"],1)
    self.assertContains(response,"<b>1</b><small>Students</small>",html=True)
    self.assertContains(response,'<span class="hub-stat-label">Students</span><b>1</b>',html=True)
    self.assertContains(response,'<span class="hub-stat-label">Faculties</span><b>1</b>',html=True)
    self.assertNotContains(response,"Pending tasks")
    self.assertEqual(response.context["pending_task_count"],1)
    self.assertEqual(response.context["pending_tasks"][0],pending_task)
    self.assertContains(response,"Your academic overview")
    self.assertContains(response,"Review hydrology notes")
 def test_search_page_has_its_own_campus_background_styles(self):
    response=self.client.get(reverse("search"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'<body class="search-body">',html=False)
    self.assertContains(response,"css/search.css")
 def test_news_feed_filters_faculties_and_shows_empty_state(self):
    business=Faculty.objects.create(name="Business")
    engineering_post=NewsPost.objects.create(
        faculty=self.subject.specialty.faculty,
        author=self.prof,
        content="Engineering announcement",
    )
    business_post=NewsPost.objects.create(
        faculty=business,
        author=self.prof,
        content="Business announcement",
    )
    self.client.force_login(self.student)

    default_response=self.client.get(reverse("news_feed"))
    self.assertEqual(default_response.status_code,200)
    self.assertContains(default_response,engineering_post.content)
    self.assertNotContains(default_response,business_post.content)
    self.assertContains(default_response,self.prof.profile.get_role_display())

    faculty_response=self.client.get(
        reverse("news_feed"),
        {"faculty":business.pk},
    )
    self.assertContains(faculty_response,business_post.content)
    self.assertNotContains(faculty_response,engineering_post.content)
    self.assertContains(faculty_response,f'value="{business.pk}" selected')

    all_faculties_response=self.client.get(reverse("news_feed"),{"faculty":""})
    self.assertContains(all_faculties_response,engineering_post.content)
    self.assertContains(all_faculties_response,business_post.content)

    empty_faculty=Faculty.objects.create(name="Arts")
    empty_response=self.client.get(
        reverse("news_feed"),
        {"faculty":empty_faculty.pk},
    )
    self.assertContains(empty_response,"No announcements yet")
 def test_news_post_publish_validation_and_clickable_link(self):
    self.client.force_login(self.student)
    response=self.client.post(reverse("news_feed"),{
        "faculty":self.subject.specialty.faculty_id,
        "content":"Department seminar next week.\nMore details soon.",
        "link_url":"https://example.com/seminar",
    })
    self.assertRedirects(
        response,
        f"{reverse('news_feed')}?faculty={self.subject.specialty.faculty_id}",
    )
    post=NewsPost.objects.get(content__startswith="Department seminar")
    self.assertEqual(post.author,self.student)
    self.assertEqual(post.faculty,self.subject.specialty.faculty)
    self.assertEqual(post.link_url,"https://example.com/seminar")
    feed_response=self.client.get(reverse("news_feed"),{"faculty":post.faculty_id})
    self.assertContains(feed_response,f'href="{post.link_url}"')
    self.assertContains(feed_response,"<span>Link</span>")
    self.assertNotContains(feed_response,"<img class=\"post-image\"")
    self.assertContains(feed_response,"Department seminar next week.<br>")
    self.assertLess(
        feed_response.content.index(b'class="post-content"'),
        feed_response.content.index(b'class="post-link"'),
    )

    invalid_response=self.client.post(reverse("news_feed"),{
        "faculty":self.subject.specialty.faculty_id,
        "content":"",
        "link_url":"not-a-valid-url",
    })
    self.assertEqual(invalid_response.status_code,200)
    self.assertIn("content",invalid_response.context["form"].errors)
    self.assertIn("link_url",invalid_response.context["form"].errors)
    self.assertNotContains(invalid_response,"Image URL (optional)")
    self.assertEqual(NewsPost.objects.count(),1)

 def test_news_post_comments_can_be_added_and_displayed(self):
    self.client.force_login(self.student)
    post=NewsPost.objects.create(
        faculty=self.subject.specialty.faculty,
        author=self.prof,
        content="Class update for today.",
    )

    response=self.client.post(reverse("news_feed"),{
        "comment_submit":"1",
        "post_id":post.pk,
        "content":"Thanks for the update.",
    },follow=True)

    self.assertRedirects(response,f"{reverse('news_feed')}?faculty={self.subject.specialty.faculty_id}")
    self.assertEqual(post.comments.count(),1)
    self.assertContains(response,"Thanks for the update.")
    self.assertContains(response,"1 comment")
 def test_news_post_can_be_liked_and_unliked(self):
    self.client.force_login(self.student)
    post=NewsPost.objects.create(
        faculty=self.subject.specialty.faculty,
        author=self.prof,
        content="Class update for today.",
    )

    liked_response=self.client.post(reverse("news_feed"),{
        "like_submit":"1",
        "post_id":post.pk,
    })
    self.assertRedirects(
        liked_response,
        f"{reverse('news_feed')}?faculty={post.faculty_id}",
    )
    self.assertEqual(NewsLike.objects.filter(post=post,user=self.student).count(),1)

    feed_response=self.client.get(reverse("news_feed"))
    displayed_post=feed_response.context["posts"].get(pk=post.pk)
    self.assertEqual(displayed_post.like_count,1)
    self.assertTrue(displayed_post.liked_by_user)
    self.assertContains(feed_response,"Liked")
    self.assertContains(feed_response,'aria-pressed="true"')

    unliked_response=self.client.post(reverse("news_feed"),{
        "like_submit":"1",
        "post_id":post.pk,
    })
    self.assertRedirects(
        unliked_response,
        f"{reverse('news_feed')}?faculty={post.faculty_id}",
    )
    self.assertFalse(NewsLike.objects.filter(post=post,user=self.student).exists())

    feed_response=self.client.get(reverse("news_feed"))
    displayed_post=feed_response.context["posts"].get(pk=post.pk)
    self.assertEqual(displayed_post.like_count,0)
    self.assertFalse(displayed_post.liked_by_user)
    self.assertContains(feed_response,"Like")
 def test_student_news_post_is_limited_to_their_faculty(self):
    other_faculty=Faculty.objects.create(name="Business")
    self.client.force_login(self.student)

    response=self.client.get(reverse("news_feed"))
    self.assertEqual(
        list(response.context["form"].fields["faculty"].queryset),
        [self.subject.specialty.faculty],
    )

    response=self.client.post(reverse("news_feed"),{
        "faculty":other_faculty.pk,
        "content":"Cross-faculty announcement",
    })
    self.assertEqual(response.status_code,200)
    self.assertIn("faculty",response.context["form"].errors)
    self.assertFalse(
        NewsPost.objects.filter(content="Cross-faculty announcement").exists(),
    )
 def test_student_without_specialty_is_redirected_to_profile_completion(self):
    self.student.profile.specialty=None
    self.student.profile.save(update_fields=["specialty"])
    self.client.force_login(self.student)

    response=self.client.get(reverse("news_feed"),follow=True)

    self.assertRedirects(response,reverse("student_form"))
    self.assertContains(response,"Complete your academic profile")
 def test_news_uploaded_image_is_saved_and_rendered(self):
    def png_chunk(kind,data):
        payload=kind+data
        return struct.pack(">I",len(data))+payload+struct.pack(">I",zlib.crc32(payload)&0xffffffff)

    image_data=(
        b"\x89PNG\r\n\x1a\n"
        +png_chunk(b"IHDR",struct.pack(">IIBBBBB",1,1,8,2,0,0,0))
        +png_chunk(b"IDAT",zlib.compress(b"\x00\xff\x00\x00"))
        +png_chunk(b"IEND",b"")
    )
    self.client.force_login(self.student)
    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            response=self.client.post(reverse("news_feed"),{
                "faculty":self.subject.specialty.faculty_id,
                "content":"Photo announcement",
                "image":SimpleUploadedFile(
                    "campus.png",
                    image_data,
                    content_type="image/png",
                ),
            })
            self.assertEqual(response.status_code,302)
            post=NewsPost.objects.get(content="Photo announcement")
            self.assertTrue(os.path.isfile(post.image.path))
            self.assertEqual(post.display_image,post.image.url)
            feed_response=self.client.get(
                reverse("news_feed"),
                {"faculty":post.faculty_id},
            )
            self.assertContains(feed_response,f'src="{post.image.url}"')
 def test_guests_can_browse_subject_resources_and_tasks(self):
    resource=Resource.objects.create(
        subject=self.subject,
        title="Guest-visible notes",
        url="https://example.com/notes",
        submitted_by=self.student,
    )
    assigned_task=ToDo.objects.create(
        subject=self.subject,
        title="Guest-visible assigned task",
        created_by=self.prof,
        assigned_to=self.student,
    )
    ToDo.objects.create(
        subject=self.subject,
        title="Guest-visible shared task",
        created_by=self.prof,
    )

    response=self.client.get(reverse("subject_vault",args=[self.subject.pk]))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,resource.title)
    self.assertContains(response,assigned_task.title)
    self.assertContains(response,"Guest-visible shared task")
    self.assertNotContains(response,"Add resource")
    self.assertNotContains(response,"Add task")
 def test_dashboard_requires_login(self): self.assertEqual(self.client.get(reverse("dashboard")).status_code,302)
 def test_dashboard_uses_faculty_name_as_university(self):
    self.client.force_login(self.student)
    dashboard_response=self.client.get(reverse("dashboard"))
    self.assertContains(dashboard_response,'class="identity-label"')
    self.assertContains(dashboard_response,"FACULTY")
    self.assertContains(dashboard_response,"Engineering")
    self.assertContains(dashboard_response,"Ecological Informatics")
 def test_dashboard_shows_university_not_set_without_faculty(self):
    self.student.profile.specialty=None
    self.student.profile.save(update_fields=["specialty"])
    self.client.force_login(self.student)
    response=self.client.get(reverse("dashboard"))
    self.assertContains(response,"University not set")
    self.assertContains(response,f"Year {self.student.profile.current_year}")
    self.assertContains(response,self.student.profile.get_semester_display())
    self.assertContains(response,"Complete your academic profile")
 def test_dashboard_counts_all_verified_resources_and_pending_tasks(self):
    for index in range(7):
        Resource.objects.create(
            subject=self.subject,
            title=f"Verified study resource {index}",
            url=f"https://example.com/resource-{index}",
            submitted_by=self.student,
            is_verified=True,
        )
    Resource.objects.create(
        subject=self.subject,
        title="Resource awaiting review",
        url="https://example.com/review",
        submitted_by=self.student,
        created_at=timezone.now()+timedelta(days=1),
    )
    ToDo.objects.create(
        subject=self.subject,
        title="Assigned pending task",
        created_by=self.prof,
        assigned_to=self.student,
    )
    ToDo.objects.create(
        subject=self.subject,
        title="Student-created pending task",
        created_by=self.student,
    )
    ToDo.objects.create(
        subject=self.subject,
        title="Completed task",
        created_by=self.prof,
        assigned_to=self.student,
        is_completed=True,
    )
    self.client.force_login(self.student)

    response=self.client.get(reverse("dashboard"))

    self.assertEqual(response.status_code,200)
    self.assertEqual(response.context["subjects"].count(),1)
    self.assertEqual(response.context["pending_count"],2)
    self.assertEqual(response.context["resource_count"],7)
    self.assertEqual(len(response.context["resources"]),5)
    self.assertContains(response,"Resource awaiting review")
 def test_profile_renders_real_completion_and_statistics(self):
    self.client.force_login(self.student)
    response=self.client.get(reverse("profile"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'<body class="profile-body">',html=False)
    self.assertContains(response,"css/profile.css")
    self.assertEqual(response.context["completion_percentage"],25)
    self.assertEqual(response.context["profile_subject_count"],1)
    self.assertEqual(response.context["profile_task_count"],0)
    self.assertEqual(response.context["profile_resource_count"],0)
    self.assertContains(response,"STUDENT SPACE")
    self.assertContains(response,'class="profile-avatar-edit" href="/student-form/">Edit</a>')
    self.assertNotContains(response,'name="avatar"')
    self.assertNotContains(response,'name="avatar_url"')
 def test_profile_saves_existing_editable_fields(self):
    self.client.force_login(self.student)
    response=self.client.post(reverse("profile"),{
        "first_name":"Ada",
        "last_name":"Lovelace",
        "email":"ada@example.com",
        "bio":"Engineering student",
    })
    self.assertRedirects(response,reverse("profile"))
    self.student.refresh_from_db()
    self.student.profile.refresh_from_db()
    self.assertEqual(self.student.first_name,"Ada")
    self.assertEqual(self.student.last_name,"Lovelace")
    self.assertEqual(self.student.email,"ada@example.com")
    self.assertEqual(self.student.profile.bio,"Engineering student")
 def test_existing_profile_picture_completes_avatar_progress(self):
    self.client.force_login(self.student)
    with tempfile.TemporaryDirectory() as media_root:
        with override_settings(MEDIA_ROOT=media_root):
            profile=self.student.profile
            profile.avatar.save(
                "profile.png",
                SimpleUploadedFile("profile.png",b"profile image",content_type="image/png"),
                save=True,
            )
            profile_response=self.client.get(reverse("profile"))
            self.assertEqual(profile_response.context["completion_items"][3]["complete"],True)
            self.assertContains(profile_response,f'src="{profile.avatar.url}"')
 def test_profile_validation_errors_and_missing_academics_render(self):
    self.client.force_login(self.student)
    profile=self.student.profile
    profile.specialty=None
    profile.avatar_url=""
    profile.save(update_fields=["specialty","avatar_url"])
    response=self.client.post(reverse("profile"),{
        "first_name":"",
        "last_name":"",
        "email":"not-an-email",
        "bio":"",
        "avatar_url":"",
    })
    self.assertEqual(response.status_code,200)
    self.assertIn("email",response.context["form"].errors)
    self.assertFalse(response.context["completion_items"][1]["complete"])
    self.assertContains(response,"Academic specialty not set")
    self.assertNotContains(response,"<img")
 def test_admin_dashboard_is_staff_only(self):
    response=self.client.get(reverse("admin_dashboard"))
    self.assertEqual(response.status_code,302)
    self.client.force_login(self.student)
    self.assertEqual(self.client.get(reverse("admin_dashboard")).status_code,403)
 def test_admin_dashboard_reviews_latest_resources(self):
    older=Resource.objects.create(
        subject=self.subject,
        title="Older notes",
        url="https://example.com/older",
        submitted_by=self.student,
    )
    Resource.objects.filter(pk=older.pk).update(created_at=timezone.now()-timedelta(days=1))
    latest=Resource.objects.create(
        subject=self.subject,
        title="Latest exam",
        category="exam",
        url="https://example.com/latest",
        submitted_by=self.student,
    )
    admin=User.objects.create_superuser(username="admin",email="admin@example.com",password="Admin!Pass12345")
    self.client.force_login(admin)
    response=self.client.get(reverse("admin_dashboard"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,'<body class="admin-dashboard-body">',html=False)
    self.assertContains(response,"css/admin-dashboard.css")
    self.assertContains(response,"Latest exam")
    self.assertContains(response,"Older notes")
    self.assertContains(response,"University charts")
    self.assertContains(response,"New users")
    self.assertContains(response,"Resources submitted")
    self.assertLess(
        response.content.index(b"Platform activity"),
        response.content.index(b"Latest resource submissions"),
    )
    self.assertEqual(response.context["student_count"],1)
    self.assertEqual(response.context["bar_metrics"][1]["value"],1)
    self.assertLess(
        response.content.index(b"Latest exam"),
        response.content.index(b"Older notes"),
    )
    verified_response=self.client.post(
        reverse("verify_resource",args=[latest.pk]),
        {"next":reverse("admin_dashboard")},
    )
    self.assertRedirects(verified_response,reverse("admin_dashboard"))
    latest.refresh_from_db()
    self.assertTrue(latest.is_verified)
 def test_admin_dashboard_charts_plot_real_monthly_records(self):
    current_month=timezone.localdate().replace(day=1)
    last_month=(current_month-timedelta(days=1)).replace(day=1)
    two_months_ago=(last_month-timedelta(days=1)).replace(day=1)
    joined=User.objects.create_user(username="chartuser",email="chartuser@example.com",password="StrongChartUser!123")
    User.objects.filter(pk=joined.pk).update(
        date_joined=timezone.make_aware(datetime.combine(last_month,datetime.min.time()))
    )
    resource=Resource.objects.create(
        subject=self.subject,
        title="Charted resource",
        url="https://example.com/charted",
        submitted_by=self.student,
    )
    Resource.objects.filter(pk=resource.pk).update(
        created_at=timezone.make_aware(datetime.combine(two_months_ago,datetime.min.time()))
    )
    admin=User.objects.create_superuser(username="chartadmin",email="chartadmin@example.com",password="StrongChartAdmin!123")
    self.client.force_login(admin)
    response=self.client.get(reverse("admin_dashboard"))
    self.assertEqual(response.status_code,200)
    user_series=response.context["line_series"][0]
    resource_series=response.context["line_series"][1]
    self.assertEqual(
        next(point["value"] for point in user_series["points"] if point["month"].month==last_month.month and point["month"].year==last_month.year),
        1,
    )
    self.assertEqual(
        next(point["value"] for point in resource_series["points"] if point["month"].month==two_months_ago.month and point["month"].year==two_months_ago.year),
        1,
    )
    self.assertEqual(response.context["bar_metrics"][0]["value"],User.objects.count())
    self.assertContains(response,"Monthly platform activity")
    self.assertContains(response,"Current platform totals")
    self.assertContains(response,"<polyline",html=False)
    self.assertContains(response,"<rect",html=False)
 def test_admin_dashboard_displays_all_contact_messages_to_staff(self):
    from .models import ContactMessage
    ContactMessage.objects.create(
        user=self.student,
        username=self.student.username,
        contact_name="Student Sender",
        email=self.student.email,
        category="feedback",
        message="Please improve the subject search.",
    )
    ContactMessage.objects.create(
        user=self.student,
        username=self.student.username,
        email=self.student.email,
        category="alert",
        message="The resource link is broken.",
    )
    admin=User.objects.create_user(username="dashboardstaff",email="staff@example.com",password="StrongDashboardStaff!123",is_staff=True)
    self.client.force_login(admin)
    response=self.client.get(reverse("admin_dashboard"))
    self.assertEqual(response.status_code,200)
    self.assertContains(response,"Student Sender")
    self.assertContains(response,"Please improve the subject search.")
    self.assertContains(response,"The resource link is broken.")
    self.assertEqual(response.context["contact_messages"].count(),2)
 def test_dashboard_shows_only_current_specialty_year_and_semester(self):
    for index in range(1,12):
        Subject.objects.create(
            specialty=self.student.profile.specialty,
            name=f"Matching subject {index}",
            year=1,
            semester=1,
        )
    second_year=Subject.objects.create(
        specialty=self.student.profile.specialty,
        name="Second year",
        year=2,
        semester=1,
    )
    second_semester=Subject.objects.create(
        specialty=self.student.profile.specialty,
        name="Second semester",
        year=1,
        semester=2,
    )
    other_specialty=Subject.objects.create(
        specialty=self.preparatory,
        name="Other specialty",
        year=1,
        semester=1,
    )
    other_faculty=Faculty.objects.create(name="Business")
    other_faculty_specialty=Specialty.objects.create(faculty=other_faculty,name="Accounting")
    other_faculty_subject=Subject.objects.create(
        specialty=other_faculty_specialty,
        name="Other faculty",
        year=1,
        semester=1,
    )
    Resource.objects.create(
        subject=self.subject,
        title="Relevant resource",
        url="https://example.com/relevant",
        submitted_by=self.student,
        is_verified=True,
    )
    Resource.objects.create(
        subject=other_specialty,
        title="Irrelevant resource",
        url="https://example.com/irrelevant",
        submitted_by=self.student,
        is_verified=True,
    )
    self.client.force_login(self.student)
    with patch("core.models.timezone.localdate",return_value=date(2026,10,10)):
        first_semester_response=self.client.get(reverse("dashboard"))
    self.assertContains(first_semester_response,"Hydrology")
    self.assertContains(first_semester_response,"Matching subject 11")
    self.assertEqual(len(first_semester_response.context["subjects"]),12)
    self.assertNotContains(first_semester_response,second_year.name)
    self.assertNotContains(first_semester_response,second_semester.name)
    self.assertNotContains(first_semester_response,other_specialty.name)
    self.assertNotContains(first_semester_response,other_faculty_subject.name)
    self.assertContains(first_semester_response,"Relevant resource")
    self.assertNotContains(first_semester_response,"Irrelevant resource")
    with patch("core.models.timezone.localdate",return_value=date(2027,3,1)):
        second_semester_response=self.client.get(reverse("dashboard"))
    self.assertContains(second_semester_response,second_semester.name)
    self.assertNotContains(second_semester_response,"Hydrology")
 def test_specialty_page_groups_all_specialty_subjects_by_year_and_semester(self):
    second_semester=Subject.objects.create(
        specialty=self.student.profile.specialty,
        name="Semester Two Subject",
        code="SEM202",
        description="Second semester subject description",
        year=1,
        semester=2,
    )
    third_year=Subject.objects.create(
        specialty=self.student.profile.specialty,
        name="Third Year Subject",
        year=3,
        semester=1,
    )
    Subject.objects.create(
        specialty=self.preparatory,
        name="Unrelated specialty subject",
        year=1,
        semester=1,
    )
    self.client.force_login(self.student)

    response=self.client.get(reverse("specialty_subjects"))

    self.assertEqual(response.status_code,200)
    self.assertContains(response,"Ecological Informatics")
    self.assertContains(response,"Semester Two Subject")
    self.assertContains(response,"Third Year Subject")
    self.assertNotContains(response,"Unrelated specialty subject")
    self.assertContains(response,reverse("subject_vault",args=[second_semester.pk]))
    self.assertEqual(len(response.context["subject_groups"]),3)
    self.assertEqual(
        list(response.context["subject_groups"][0]["semesters"][1]["subjects"]),
        [second_semester],
    )
    self.assertEqual(
        list(response.context["subject_groups"][2]["semesters"][0]["subjects"]),
        [third_year],
    )

 def test_dashboard_specialty_links_to_specialty_subjects_page(self):
    self.client.force_login(self.student)

    response=self.client.get(reverse("dashboard"))

    self.assertContains(response,reverse("specialty_subjects"))

 def test_specialty_subjects_page_requires_academic_profile(self):
    student_without_specialty=User.objects.create_user(username="no-specialty",password="test-password")
    UserProfile.objects.create(user=student_without_specialty)
    self.client.force_login(student_without_specialty)

    response=self.client.get(reverse("specialty_subjects"))

    self.assertRedirects(response,reverse("student_form"))

 def test_student_cannot_verify(self):
    r=Resource.objects.create(subject=self.subject,title="Notes",url="https://example.com",submitted_by=self.student)
    self.client.login(username="student",password="StrongPass123!")
    self.assertEqual(self.client.post(reverse("verify_resource",args=[r.pk])).status_code,403)
 def test_professor_can_verify(self):
    r=Resource.objects.create(subject=self.subject,title="Notes",url="https://example.com",submitted_by=self.student)
    self.client.login(username="prof",password="StrongPass123!")
    self.assertEqual(self.client.post(reverse("verify_resource",args=[r.pk])).status_code,302); r.refresh_from_db(); self.assertTrue(r.is_verified)
 def test_task_toggle_requires_login(self):
    t=ToDo.objects.create(subject=self.subject,title="Read",created_by=self.student,assigned_to=self.student)
    self.assertEqual(self.client.post(reverse("toggle_task",args=[t.pk])).status_code,302)
    t.refresh_from_db()
    self.assertFalse(t.is_completed)
 def test_resource_category_is_saved_and_displayed(self):
    self.client.force_login(self.student)
    response=self.client.post(
        reverse("add_resource",args=[self.subject.pk]),
        {
            "title":"Practice exam",
            "category":"exam",
            "description":"Past paper",
            "url":"https://example.com/exam",
        },
    )
    self.assertEqual(response.status_code,302)
    resource=Resource.objects.get(title="Practice exam")
    self.assertEqual(resource.category,"exam")
    self.assertContains(self.client.get(reverse("subject_vault",args=[self.subject.pk])),"Exam")
 def test_semester_date_ranges(self):
    for day in (date(2026,9,1),date(2026,12,31),date(2027,1,15)):
        with self.subTest(day=day): self.assertEqual(semester_for_date(day),"semester_1")
    for day in (date(2026,8,31),date(2027,1,16),date(2027,8,31)):
        with self.subTest(day=day): self.assertEqual(semester_for_date(day),"semester_2")
 def test_profile_uses_account_creation_date(self):
    created=date(2026,2,1)
    self.student.date_joined=timezone.make_aware(datetime.combine(created,datetime.min.time()))
    self.student.save(update_fields=["date_joined"])
    UserProfile.objects.filter(user=self.student).delete()
    profile=UserProfile.objects.create(user=self.student)
    self.assertEqual(profile.semester,"semester_2")
 def test_successful_login_refreshes_semester(self):
    self.student.set_password("semester-test-password")
    self.student.save()
    profile=self.student.profile
    profile.semester="semester_1"
    profile.save(update_fields=["semester"])
    with patch("core.models.timezone.localdate",return_value=date(2026,3,1)):
        response=self.client.post(reverse("login"),{"username":"student","password":"semester-test-password"})
    self.assertEqual(response.status_code,302)
    profile.refresh_from_db()
    self.assertEqual(profile.semester,"semester_2")
 def test_years_depend_on_specialty_cycle(self):
    self.assertEqual(years_for_specialty(self.preparatory),(1,2))
    self.assertEqual(years_for_specialty(self.master),(1,2))
    self.assertEqual(years_for_specialty(self.subject.specialty),(1,2,3))
 def test_registration_rejects_year_three_for_preparatory_cycle(self):
    form=StudentProfileForm(data={
        "faculty":str(self.preparatory.faculty_id),
        "specialty":str(self.preparatory.pk),
        "current_year":"3",
    })
    self.assertFalse(form.is_valid())
    self.assertIn("current_year",form.errors)
 def test_academic_profile_requires_faculty_before_specialty(self):
    form=StudentProfileForm(data={
        "specialty":str(self.preparatory.pk),
        "current_year":"2",
    })
    self.assertFalse(form.is_valid())
    self.assertIn("faculty",form.errors)
 def test_registration_rejects_specialty_from_another_faculty(self):
    other_faculty=Faculty.objects.create(name="Business")
    other_specialty=Specialty.objects.create(faculty=other_faculty,name="Accounting")
    form=StudentProfileForm(data={
        "faculty":str(self.preparatory.faculty_id),
        "specialty":str(other_specialty.pk),
        "current_year":"2",
    })
    self.assertFalse(form.is_valid())
    self.assertIn("specialty",form.errors)
 def test_registration_saves_selected_specialty_and_year(self):
    response=self.client.post(reverse("register"),{
        "username":"year2student",
        "email":"year2@example.com",
        "password1":"Turtle!River49",
        "password2":"Turtle!River49",
    })
    self.assertRedirects(response,reverse("student_form"))
    profile=UserProfile.objects.get(user__username="year2student")
    self.assertIsNone(profile.specialty)
    self.assertEqual(profile.current_year,1)
    setup_response=self.client.post(reverse("student_form"),{
        "faculty":str(self.preparatory.faculty_id),
        "specialty":str(self.preparatory.pk),
        "current_year":"2",
    })
    self.assertRedirects(setup_response,reverse("dashboard"))
    profile.refresh_from_db()
    self.assertEqual(profile.specialty,self.preparatory)
    self.assertEqual(profile.current_year,2)
