from django.urls import path
from . import views

app_name = 'advisor'

urlpatterns = [
    path('', views.home, name='chat_home'),
    path('home/', views.home, name='home'),
    path('chat/', views.chat_page, name='chat_page'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/directory/', views.directory_api, name='directory_api'),
    path('api/referrals/', views.directory_api, name='referrals_api'),
    path('api/knowledge-base/', views.knowledge_base_api, name='knowledge_base_api'),
    path('api/admin/knowledge-base/', views.admin_update_knowledge_api, name='admin_update_knowledge_api'),
    path('api/log-stat/', views.log_stat_api, name='log_stat_api'),
]
