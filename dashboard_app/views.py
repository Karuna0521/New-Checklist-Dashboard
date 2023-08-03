import tablib
from django.db.models import Q
from django.shortcuts import render, redirect
from mongoengine import ImproperlyConfigured
from django.conf import settings
from checklist_dashboard import settings
from .models import User, QuestionList, Options, AnswerData, App_Info, Category_Weightage, ChecklistCategory
from .forms import RegistrationForm
from .forms import LoginForm, AppInfoForm
import json

import io
import openpyxl
from import_export import resources, fields
from .resources import QuestionListResource
from django.contrib import messages
from tablib import Dataset
from django.http import HttpResponseBadRequest

from django.http import FileResponse

import os
from django.core.signing import Signer

# Create your views here.


def login(request):
    form = LoginForm(request.POST)
    message = ''
    if form.is_valid():
        input_email = form.cleaned_data['email']
        input_password = form.cleaned_data['password']
        users = User.objects.filter(email=input_email).values()
        if len(users) != 0:
            user = users[0]
            if user['password'] == input_password:
                if user['enable']:
                    email_signer = Signer()
                    signed_email = email_signer.sign_object(input_email)
                    if user['role'] == 'user':
                        return redirect('/dashboard_app/collective_checklist?user=' + user['email'])
                    else:
                        return redirect('/dashboard_app/checklist_category?user=' + user['email'])
                message = 'Please contact Admin to enable your account.'
                return render(request, 'login.html', {'form': form, 'message': message})
            message = 'Invalid credentials !!! Please try again.'
            return render(request, 'login.html', {'form': form, 'message': message})
        message = 'User not found with email ' + input_email + '. Please register !'
    return render(request, 'login.html', {'form': form, 'message': message})


def checklist_category(request):
    user = request.GET.get('user')
    message = ''
    old_category_types = []
    if request.method == 'POST':
        new_category = request.POST.get('category_text')
        new_category = new_category.title()
        old_category = list(ChecklistCategory.objects.all())
        local_category_list = []
        for category_obj in old_category:
            old_category_types.append({"checklist_type": category_obj.checklist_type})
            local_category_list.append(category_obj.checklist_type.title())
        if new_category not in local_category_list:
            old_category_types.append({"checklist_type": new_category})
            ChecklistCategory.objects.create(
                checklist_type=new_category
            )
            message = new_category + ' Added Successfully!!'
        else:
            message = new_category + ' Already exists!'
    return render(request, 'checklist_category.html', {'user': user, 'message': message, 'old_category_types': old_category_types})


def collective_checklist(request):
    user = request.GET.get('user')
    checklist_type = request.POST.get('checklist_category')
    if checklist_type == 'mobile_checklist':
        apps_risk_ratings = get_apps_risk_rating_by_user(user)
        return render(request, 'user_dashboard.html', {'user': user, 'apps_risk_ratings': apps_risk_ratings})
    elif checklist_type == 'web_checklist':
        return render(request, 'web_user_dashboard.html', {'user': user})
    return render(request, 'collective_checklist.html', {'user': user})


def registration(request):
    message = ''
    form = RegistrationForm(request.POST)
    if form.is_valid():
        input_email = form.cleaned_data['email']
        users = User.objects.filter(email=input_email).values()

        if len(users) != 0:
            message = 'User with this email already exists.'
            return render(request, 'registration.html', {'form': form, 'message': message})
        else:
            form.save()
            return redirect('/dashboard_app/login')
    return render(request, 'registration.html', {'form': form, 'message': message})


def question_upload(request):
    user = request.GET.get('user')
    print("****----->", request)
    if request.method == 'POST' and request.FILES['myfile']:
        category_name_map = {
            'Ownership Related Information': 'ownership_info',
            'Company Related Information': 'company_related_info',
            'Services and Security': 'services_security',
            'Privacy Policy': 'privacy_policy',
            'Insecure Data Storage': 'insecure_data_storage',
            'Data Related Information': 'data_related_info',
            'Cryptography': 'cryptography',
            'Network Communication': 'network_communication',
            'Platform Interaction': 'platform_interaction',
            'Public Grievance Redressal Mechanism': 'pgrm'
        }
        new_questions = request.FILES['myfile']
        file_ext = request.FILES['myfile'].name.rsplit('.', 1)[1].lower()
        print(file_ext, 'file-->', new_questions)
        if file_ext == 'xlsx':
            dataset = Dataset()
            data_import = dataset.load(new_questions.read(), format='xlsx')
            if data_import:
                for row in data_import:
                    row_category = row[0]
                    que = row[1]
                    questions = [que]
                    print(row_category, 'row-->', questions)
                    if row_category is not None and que is not None:
                        category = category_name_map[row_category]
                        category_wise_question = QuestionList.objects.filter(category=category).values()
                        if len(category_wise_question) != 0:  # category exists in db
                            old_questions = category_wise_question[0]['question_list']
                            questions = [*old_questions,
                                         *questions]  # spreading old questions from db and new question from page
                            questions = list(set(questions))
                            QuestionList.objects.filter(category=category).update(
                                question_list=questions
                            )
                        else:
                            QuestionList.objects.create(
                                category=category,
                                question_list=questions
                            )

                return render(request, 'manage_questions.html',
                              {'import': True, 'message': 'File Imported Successfully..!'})
            else:
                return render(request, 'manage_questions.html',
                              {'import': False, 'message': 'File import failed ! PLease try again.', 'user': user})
        else:
            return render(request, 'manage_questions.html',
                          {'import': True, 'message': 'Please import file with ".xlsx" extension', 'user': user})
    return render(request, 'manage_questions.html', {'user': user})


def download_excel(request):
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'Template.xlsx')
    response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="SampleTemplate.xlsx"'
    return response
    # return render(request, 'manage_questions.html')


def manage_questions(request):
    user = request.GET.get('user')
    if request.method == 'POST':
        new_question = request.POST.get('question_text')
        questions = [new_question]

        category = request.POST.get('category')
        category_wise_question = QuestionList.objects.filter(category=category).values()

        if len(category_wise_question) != 0:  # category exists in db
            old_questions = category_wise_question[0]['question_list']
            questions = [*old_questions, *questions]  # spreading old questions from db and new question from page
            questions = list(set(questions))
            QuestionList.objects.filter(category=category).update(
                question_list=questions
            )
        else:
            QuestionList.objects.create(
                category=category,
                question_list=questions
            )

    questions_list = list(QuestionList.objects.all())
    display_questions = []

    # converting [<QuestionList: QuestionList object (13)>,.....] to [{'category': 'ownership_info', 'question':
    # 'What is reaction?'}, {'category': 'ownership_info', 'question': 'what is karuna'}...]
    for category_question in questions_list:
        for q in category_question.question_list:
            display_questions.append({'category': category_question.category, 'question': q})

    options = list(Options.objects.all())
    options_list = []
    for o in options:
        options_list.append(o.option_text)
    options_list = ','.join(options_list)
    return render(request, 'manage_questions.html',
                  {'display_questions': display_questions, 'options': options_list, 'user': user})


def delete_item(request):
    if request.method == 'POST':
        category_question = request.POST.get('delete_question')
        category = category_question.split('______')[0]
        question = category_question.split('______')[1]
        try:
            item = list(QuestionList.objects.filter(category=category))[0]
            question_list = item.question_list
            question_list.remove(question)
            QuestionList.objects.filter(category=category).update(
                question_list=question_list
            )
            print('The question has been deleted successfully', item)
        except QuestionList.DoesNotExist:
            print('The question does not exist')
    return redirect('/dashboard_app/manage_questions/')


def manage_users(request):
    user = request.GET.get('user')
    user_info = list(User.objects.exclude(role='admin'))
    # users = user_info.exclude(role='user')
    return render(request, 'manage_users.html', {'user_info': user_info, 'user': user})


def update_user(request):
    if request.method == 'POST':
        enabled_users = request.POST.getlist('enable')

        User.objects.filter(email__in=enabled_users).update(enable=True)
        User.objects.filter(role='user').exclude(email__in=enabled_users).update(enable=False)

    return redirect('/dashboard_app/manage_users/')


def update_options(request):
    if request.method == 'POST':
        options_text = request.POST.get('options_text').strip()
        options = options_text.split(',')
        all_options = Options.objects.all()
        all_options.delete()
        for opt in options:
            if len(opt) > 0:
                Options.objects.create(option_text=opt.strip())
    return redirect('/dashboard_app/manage_questions')


def user_new_app(request):
    user = request.GET.get('user')
    return render(request, 'user_new_app.html', {'user': user})


def app_category(request):
    user = request.GET.get('user')
    app_name = request.POST.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        new_app_info = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken'}
        if len(new_app_info) != 0:
            existing_apps = App_Info.objects.filter(Q(md5=new_app_info['md5']) & Q(app_name=new_app_info['app_name']))
            existing_apps.delete()  # to avoid duplicates
            App_Info.objects.create(
                app_name=new_app_info['app_name'],
                app_category=new_app_info['app_category'],
                package_name=new_app_info['package_name'],
                main_activity=new_app_info['main_activity'],
                app_version=new_app_info['app_version'],
                md5=new_app_info['md5'],
                sha256=new_app_info['sha256'],
                app_url=new_app_info['app_url'],
                tester=new_app_info['tester']
            )
    return render(request, 'app_category.html', {'app_name': app_name, 'user': user, 'md5': md5})


def ownership_info(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        category_weightage = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken'}

        if len(category_weightage) != 0:
            existing_app_weightage = Category_Weightage.objects.filter(app_name=app_name)
            existing_app_weightage.delete()  # to avoid duplicates
            Category_Weightage.objects.create(
                app_name=app_name,
                md5=category_weightage['md5'],
                ownership_info=category_weightage['ownership_info'],
                company_related_info=category_weightage['company_related_info'],
                services_security=category_weightage['services_security'],
                privacy_policy=category_weightage['privacy_policy'],
                data_related_info=category_weightage['data_related_info'],
                insecure_data_storage=category_weightage['insecure_data_storage'],
                cryptography=category_weightage['cryptography'],
                network_communication=category_weightage['network_communication'],
                platform_interaction=category_weightage['platform_interaction'],
                pgrm=category_weightage['pgrm']
            )
    category_questions = list(QuestionList.objects.filter(category='ownership_info'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'ownership_info.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def company_related_info(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='ownership_info') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='ownership_info',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='company_related_info'))
    if len(category_questions) != 0:
        questions = category_questions[0].question_list
        options = list(Options.objects.all())
        return render(request, 'company_related_info.html',
                      {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})
    return render(request, 'company_related_info.html', {'app_name': app_name, 'user': user, 'md5': md5})


def services_and_security(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='company_related_info') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='company_related_info',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='services_security'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'services_and_security.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def privacy_policy(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')

    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='services_security') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='services_security',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='privacy_policy'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'privacy_policy.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def data_related_info(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='privacy_policy') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='privacy_policy',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='data_related_info'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'data_related_info.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def insecure_data_storage(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='data_related_info') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='data_related_info',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='insecure_data_storage'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'insecure_data_storage.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def cryptography(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='insecure_data_storage') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='insecure_data_storage',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='cryptography'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'cryptography.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def network_communication(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')

    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='cryptography') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='cryptography',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='network_communication'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'network_communication.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def platform_interaction(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')

    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='network_communication') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='network_communication',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='platform_interaction'))
    questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'platform_interaction.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def pgrm(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='platform_interaction') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            md5=md5,
            category='platform_interaction',
            question_answer=answers
        )
    category_questions = list(QuestionList.objects.filter(category='pgrm'))

    questions = []
    if len(category_questions) > 0:
        questions = category_questions[0].question_list
    options = list(Options.objects.all())
    return render(request, 'pgrm.html',
                  {'questions': questions, 'options': options, 'app_name': app_name, 'user': user, 'md5': md5})


def process_answer(app_name):
    answer_data = list(AnswerData.objects.filter(app_name=app_name))
    app_category_weightage = list(Category_Weightage.objects.filter(app_name=app_name))[0]
    final_count = {}
    options = list(Options.objects.all())
    for opt in options:  # creating
        # {'Pass': 0, 'Fail': 0, 'Not Applicable': 0, 'Unable to Verify': 0}
        final_count[opt.option_text] = 0

    category_wise_risk_rating = {
        "ownership_info": 0,
        "company_related_info": 0,
        "services_security": 0,
        "privacy_policy": 0,
        "data_related_info": 0,
        "insecure_data_storage": 0,
        "cryptography": 0,
        "network_communication": 0,
        "platform_interaction": 0,
        "pgrm": 0
    }

    for category_data in answer_data:  # category_data is object having question answer of app
        category = category_data.category
        weightage = getattr(app_category_weightage, category)  # getting weightage for each category
        category_wise_pass = 0
        category_wise_fail = 0
        for ques_ans in category_data.question_answer:  # ques_ans is actual question
            prev_count = final_count[category_data.question_answer[ques_ans]]
            final_count[category_data.question_answer[ques_ans]] = prev_count + weightage

            if category_data.question_answer[ques_ans] == 'Pass':
                category_wise_pass = category_wise_pass + weightage
            if category_data.question_answer[ques_ans] == 'Fail':
                category_wise_fail = category_wise_fail + weightage

        category_risk_rating = calculate_risk_rating({'Pass': category_wise_pass, 'Fail': category_wise_fail})
        category_wise_risk_rating[category] = category_risk_rating * 10  # converting to %

    risk_rating = calculate_risk_rating(final_count)
    data = {'final_count': final_count, 'risk_rating': risk_rating,
            'category_wise_risk_rating': category_wise_risk_rating}
    return data


def calculate_risk_rating(final_count):
    pass_fail_sum = final_count['Pass'] + final_count['Fail']
    risk_rating = (final_count['Fail'] / pass_fail_sum) * 10
    risk_rating = round(risk_rating, 2)
    return risk_rating


def result(request):
    user = request.GET.get('user')
    app_name = request.GET.get('app_name')
    md5 = request.POST.get('md5')
    if request.method == 'POST':
        answers = {k: v for k, v in request.POST.dict().items() if k != 'csrfmiddlewaretoken' and k != 'md5'}
        existing = AnswerData.objects.filter(Q(category='pgrm') & Q(app_name=app_name))
        existing.delete()
        AnswerData.objects.create(
            app_name=app_name,
            category='pgrm',
            md5=md5,
            question_answer=answers
        )

    app_info = list(App_Info.objects.filter(app_name=app_name))[0]
    data = process_answer(app_name)
    risk_rating = data['risk_rating']
    final_count = data['final_count']
    category_wise_risk_rating = data['category_wise_risk_rating']
    final_count_json = json.dumps(final_count)
    category_wise_risk_rating_json = json.dumps(category_wise_risk_rating)

    return render(request, 'user_result.html', {'app_info': app_info,
                                                'risk_rating': risk_rating,
                                                'final_count': final_count_json,
                                                'category_wise_risk_rating': category_wise_risk_rating_json,
                                                'user': user,
                                                'app_name': app_name})


def view_result(request):
    app_name = request.GET.get('app_name')
    user_email = request.GET.get('user')
    app_info = list(App_Info.objects.filter(app_name=app_name))[0]
    data = process_answer(app_name)
    risk_rating = data['risk_rating']
    final_count = data['final_count']
    category_wise_risk_rating = data['category_wise_risk_rating']
    final_count_json = json.dumps(final_count)
    category_wise_risk_rating_json = json.dumps(category_wise_risk_rating)

    users = User.objects.filter(email=user_email).values()
    if len(users) != 0:
        user = users[0]
        if user['role'] == 'user':
            return render(request, 'user_result.html', {'app_info': app_info,
                                                        'risk_rating': risk_rating,
                                                        'final_count': final_count_json,
                                                        'category_wise_risk_rating': category_wise_risk_rating_json,
                                                        'user': user_email,
                                                        'app_name': app_name})
        else:
            return render(request, 'admin_result.html', {'app_info': app_info,
                                                         'risk_rating': risk_rating,
                                                         'final_count': final_count_json,
                                                         'category_wise_risk_rating': category_wise_risk_rating_json,
                                                         'user': user_email,
                                                         'app_name': app_name})


def admin_dashboard(request):
    user = request.GET.get('user')
    apps_risk_ratings = []
    apps = list(App_Info.objects.all())
    for a in apps:
        name = a.app_name
        tester = a.tester
        answer_data = list(AnswerData.objects.filter(app_name=name))
        if len(answer_data) > 0:
            data = process_answer(name)
            apps_risk_ratings.append({'app_name': name, 'tester': tester, 'risk_rating': data['risk_rating']})
    return render(request, 'admin_dashboard.html', {'apps_risk_ratings': apps_risk_ratings, 'user': user})


def get_apps_risk_rating_by_user(user):
    apps_risk_ratings = []
    apps = list(App_Info.objects.filter(tester=user))
    for a in apps:
        answer_data = list(AnswerData.objects.filter(app_name=a.app_name))
        if len(answer_data) > 0:
            data = process_answer(a.app_name)
            apps_risk_ratings.append({'app_name': a.app_name, 'md5': a.md5, 'risk_rating': data['risk_rating']})
    return apps_risk_ratings


def user_dashboard(request):
    user = request.GET.get('user')
    # checklist_category = request.POST.get('checklist_category')
    apps_risk_ratings = get_apps_risk_rating_by_user(user)
    return render(request, 'user_dashboard.html', {'user': user, 'apps_risk_ratings': apps_risk_ratings})
