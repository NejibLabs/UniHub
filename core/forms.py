import json
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile,Specialty,Resource,ToDo,NewsPost,Faculty,ContactMessage,years_for_specialty
User=get_user_model()


class SpecialtyCycleFormMixin:
    def configure_specialty_year_fields(self):
        specialties=Specialty.objects.all()
        self.fields["specialty"].queryset=specialties
        self.fields["specialty"].widget.attrs["data-year-counts"] = json.dumps({
            str(specialty.pk): len(years_for_specialty(specialty))
            for specialty in specialties
        })

    def clean(self):
        cleaned_data=super().clean()
        specialty=cleaned_data.get("specialty")
        current_year=cleaned_data.get("current_year")
        if specialty and current_year and current_year not in years_for_specialty(specialty):
            self.add_error("current_year","Select a year available for the chosen program cycle.")
        return cleaned_data


class RegisterForm(UserCreationForm):
    email=forms.EmailField(required=True)
    first_name=forms.CharField(max_length=150,required=False)
    last_name=forms.CharField(max_length=150,required=False)
    class Meta(UserCreationForm.Meta):
        model=User
        fields=("username","first_name","last_name","email")
    def clean_email(self):
        value=self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=value).exists(): raise forms.ValidationError("An account with this email already exists.")
        return value
class StudentProfileForm(SpecialtyCycleFormMixin,forms.ModelForm):
    faculty=forms.ModelChoiceField(queryset=Faculty.objects.all(),required=True)
    avatar=forms.ImageField(label="Profile picture",required=False,widget=forms.FileInput)

    class Meta:
        model=UserProfile
        fields=("specialty","current_year","avatar")
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.order_fields(("avatar","faculty","specialty","current_year"))
        self.fields["avatar"].widget.attrs["class"]="student-setup-avatar-input"
        self.configure_specialty_year_fields()
        specialties=Specialty.objects.select_related("faculty").all()
        specialties_by_faculty={}
        for specialty in specialties:
            specialties_by_faculty.setdefault(str(specialty.faculty_id),[]).append({
                "id":specialty.pk,
                "name":specialty.name,
            })
        self.fields["faculty"].widget.attrs["data-specialties"] = json.dumps(specialties_by_faculty)
        faculty_value=self.data.get(self.add_prefix("faculty")) if self.is_bound else self.initial.get("faculty")
        if not faculty_value and self.instance.specialty_id:
            faculty_value=self.instance.specialty.faculty_id
        if hasattr(faculty_value,"pk"):
            faculty_value=faculty_value.pk
        try:
            faculty_id=int(faculty_value)
        except (TypeError,ValueError):
            faculty_id=None
        if faculty_id is not None:
            self.fields["faculty"].initial=faculty_id
            self.fields["specialty"].queryset=specialties.filter(faculty_id=faculty_id)
        else:
            self.fields["specialty"].widget.attrs["disabled"]="disabled"
class ProfileForm(forms.ModelForm):
    first_name=forms.CharField(max_length=150,required=False)
    last_name=forms.CharField(max_length=150,required=False)
    email=forms.EmailField()
    class Meta:
        model=UserProfile
        fields=("bio",)
    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs); self.user=user
        if user:
            self.fields["first_name"].initial=user.first_name; self.fields["last_name"].initial=user.last_name; self.fields["email"].initial=user.email
    def clean_email(self):
        value=self.cleaned_data["email"].strip().lower()
        if self.user and User.objects.filter(email__iexact=value).exclude(pk=self.user.pk).exists(): raise forms.ValidationError("That email address is already in use.")
        return value
    def save(self,commit=True):
        obj=super().save(commit=False)
        if self.user:
            self.user.first_name=self.cleaned_data["first_name"]; self.user.last_name=self.cleaned_data["last_name"]; self.user.email=self.cleaned_data["email"]
            if commit: self.user.save()
        if commit: obj.save()
        return obj
class ContactMessageForm(forms.ModelForm):
    class Meta:
        model=ContactMessage
        fields=("category","message")
        widgets={"message":forms.Textarea(attrs={"rows":6,"placeholder":"Tell us how we can help..."})}
    def __init__(self,*args,user,**kwargs):
        super().__init__(*args,**kwargs)
        self.user=user
    def save(self,commit=True):
        obj=super().save(commit=False)
        obj.user=self.user
        obj.username=self.user.get_username()
        obj.contact_name=self.user.get_full_name()
        obj.email=self.user.email
        if commit: obj.save()
        return obj
class ResourceForm(forms.ModelForm):
    class Meta:
        model=Resource
        fields=("title","category","description","url")
        widgets={"description":forms.Textarea(attrs={"rows":3})}
class ToDoForm(forms.ModelForm):
    class Meta:
        model=ToDo
        fields=("title","description","due_date","assigned_to")
        widgets={"description":forms.Textarea(attrs={"rows":3}),"due_date":forms.DateInput(attrs={"type":"date"})}

class NewsPostForm(forms.ModelForm):
    faculty=forms.ModelChoiceField(queryset=Faculty.objects.all(),label="University / Faculty")
    class Meta:
        model=NewsPost
        fields=("faculty","content","image","link_url")
        widgets={"content":forms.Textarea(attrs={"rows":4,"placeholder":"Share a faculty update, announcement, or reminder…"}),"link_url":forms.URLInput(attrs={"placeholder":"https://example.com"})}

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields["content"].required = True
        self.fields["image"].required = False
        self.fields["link_url"].required = False
