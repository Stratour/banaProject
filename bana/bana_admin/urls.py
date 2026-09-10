from django.urls import path
from . import views

app_name = 'bana_admin'

urlpatterns = [
    path('admin_view', views.admin_view, name='admin_view'),
    path('validate_members', views.validate_members, name='validate_members'),
    path('admin-panel/verify-bvm/<int:profile_id>/', views.verify_bvm_prfl, name='verify_bvm_prfl'),
    path('admin-panel/reject-bvm/<int:profile_id>/', views.reject_bvm_prfl, name='reject_bvm_prfl'),
    path('admin/site-stats/', views.site_stats_view, name='site_stats'),

    path('wxc', views.ValidationListView.as_view(), name='list'),
    path('<int:pk>/validate/', views.ValidateUserView.as_view(), name='validate_user'),
    path('<int:pk>/reject/', views.RejectUserView.as_view(), name='reject_user'),

]
