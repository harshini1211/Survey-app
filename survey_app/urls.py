# survey_app/urls.py

from django.urls import path
from django.views.generic import RedirectView
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('creator/dashboard/', views.creator_dashboard, name='creator_dashboard'),
    path('creator/create_survey/', views.create_survey, name='create_survey'),
    path('creator/edit_survey/<int:survey_id>/', views.edit_survey, name='edit_survey'),
    path('creator/publish_survey/<int:survey_id>/', views.publish_survey, name='publish_survey'),
    path('creator/close_survey/<int:survey_id>/', views.close_survey, name='close_survey'),
    path('creator/view_results/<int:survey_id>/', views.view_results, name='view_results'),
    path('taker/dashboard/', views.taker_dashboard, name='taker_dashboard'),
    path('taker/take_survey/<int:survey_id>/', views.take_survey, name='take_survey'),
    path('taker/survey_completed/', views.survey_completed, name='survey_completed'),
    path('creator/delete_question/<int:question_id>/', views.delete_question, name='delete_question'),
    path('creator/edit_survey/<int:survey_id>/edit_question/<int:question_id>/', views.edit_question, name='edit_question'),
    path('creator/edit_survey/<int:survey_id>/delete_question/<int:question_id>/', views.delete_question, name='delete_question'),
    path('creator/edit_survey/<int:survey_id>/add_question/', views.add_question, name='add_question'),
    path('survey/<int:survey_id>/publish/', views.publish_survey, name='publish_survey'),
    path('survey/<int:survey_id>/question/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('survey/<int:survey_id>/republish/', views.republish_survey, name='republish_survey'),
    path('survey/<int:survey_id>/results/', views.view_survey_results, name='view_survey_results'),
    path('survey/<int:survey_id>/take/', views.take_survey, name='take_survey'),


    path(
        'survey/<int:survey_id>/question/<int:question_id>/option/<int:option_id>/delete/',
        views.delete_option,
        name='delete_option'
    ),
    path('', RedirectView.as_view(url='login/')),  # Redirect root to login
]
