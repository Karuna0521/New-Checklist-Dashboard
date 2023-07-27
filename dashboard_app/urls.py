from django.urls import path
from dashboard_app import views
from checklist_dashboard import settings
from django.conf.urls.static import static

urlpatterns = [
    path('login/', views.login, name='login'),
    path('registration/', views.registration, name='registration'),
    path('checklist_category/', views.checklist_category),
    path('collective_checklist/', views.collective_checklist),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage_questions/', views.manage_questions),
    path('manage_users/', views.manage_users),
    path('delete_question/', views.delete_item, name='delete_question'),
    path('update_user/', views.update_user, name='update_user'),
    path('update_options/', views.update_options, name='update_options'),
    path('user_dashboard/', views.user_dashboard, name='user_dashboard'),
    path('user_new_app/', views.user_new_app),
    path('app_category/', views.app_category, name='app_category'),
    path('ownership_info/', views.ownership_info, name='ownership_info'),
    path('company_related_info/', views.company_related_info, name='company_related_info'),
    path('services_and_security/', views.services_and_security, name='services_and_security'),
    path('privacy_policy/', views.privacy_policy, name='privacy_policy'),
    path('data_related_info/', views.data_related_info, name='data_related_info'),
    path('insecure_data_storage/', views.insecure_data_storage, name='insecure_data_storage'),
    path('cryptography/', views.cryptography, name='cryptography'),
    path('network_communication/', views.network_communication, name='network_communication'),
    path('platform_interaction/', views.platform_interaction, name='platform_interaction'),
    path('pgrm/', views.pgrm, name='pgrm'),
    path('user_result/', views.result, name='user_result'),
    path('admin_result/', views.result, name='admin_result'),
    path('view_result/', views.view_result, name='view_result'),
    path('question_upload/', views.question_upload, name='question_upload'),
    path('download_excel/', views.download_excel, name='download_excel'),
]