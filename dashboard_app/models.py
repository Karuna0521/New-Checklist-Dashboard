from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
from django.forms import forms, ModelForm
# from .forms import validate_email_unique
from djongo import models
from django.core.validators import RegexValidator, EmailValidator


# from dashboard_app.forms import QuestionForm


class User(models.Model):
    objects = models.DjongoManager()
    first_name = models.TextField(max_length=10, blank=False)
    last_name = models.TextField(max_length=10, blank=False)
    email = models.CharField(blank=False, max_length=255)
    # email = models.EmailField(blank=False, unique=True, validators=[EmailValidator(message="invalid email")])
    password = models.TextField(max_length=10, blank=False,
                                validators=[
                                    RegexValidator('^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$',
                                                   message="Password "
                                                           "must "
                                                           "contain "
                                                           "at least "
                                                           "one "
                                                           "uppercase letter, one lowercase letter, one digit, one special character and minimum 8 length")])
    role = models.CharField(blank=False, max_length=50, default="user")
    enable = models.BooleanField(blank=False, default=False)


class ChecklistCategory(models.Model):
    checklist_type = models.JSONField(null=True, blank=True, default=[])
    objects = models.DjongoManager()


class QuestionList(models.Model):
    # id = models.IntegerField(primary_key=True)
    category = models.CharField(max_length=500, blank=False)
    question_list = models.JSONField(null=True, blank=True, default=[])
    objects = models.DjongoManager()


class Options(models.Model):
    option_text = models.CharField(max_length=500, blank=False)
    objects = models.DjongoManager()


class AnswerData(models.Model):
    app_name = models.TextField(blank=False)
    md5 = models.TextField(blank=False)
    category = models.CharField(max_length=500, blank=False)
    question_answer = models.JSONField(null=True, blank=True, default={})
    objects = models.DjongoManager()


class App_Info(models.Model):
    app_name = models.TextField(blank=False)
    app_category = models.TextField(blank=False)
    package_name = models.TextField(blank=False)
    main_activity = models.TextField(blank=False)
    app_version = models.TextField(blank=False)
    md5 = models.TextField(blank=False)
    sha256 = models.TextField(blank=False)
    app_url = models.URLField(blank=False)
    tester = models.CharField(blank=False, max_length=255)
    objects = models.DjongoManager()


class Category_Weightage(models.Model):
    app_name = models.TextField(blank=False)
    md5 = models.TextField(blank=False)
    ownership_info = models.IntegerField(blank=False)
    company_related_info = models.IntegerField(blank=False)
    services_security = models.IntegerField(blank=False)
    privacy_policy = models.IntegerField(blank=False)
    data_related_info = models.IntegerField(blank=False)
    insecure_data_storage = models.IntegerField(blank=False)
    cryptography = models.IntegerField(blank=False)
    network_communication = models.IntegerField(blank=False)
    platform_interaction = models.IntegerField(blank=False)
    pgrm = models.IntegerField(blank=False)
    objects = models.DjongoManager()
