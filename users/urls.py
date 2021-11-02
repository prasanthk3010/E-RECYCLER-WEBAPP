from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('',views.home,name="home"),
    
    path('register/',views.register,name="register"),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html',redirect_authenticated_user=True) ,name= 'login'),
    path('verification/', views.VerificationSlots ,name= 'verify'),
    path('verification/amazon/', views.AImageVerify ,name= 'amazon-verify'),
    path('verification/flipcart/', views.FImageVerify ,name= 'flipcart-verify'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='users/password_reset.html') ,name= 'password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='users/password_reset_done.html') ,name= 'password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='users/password_reset_confirm.html') ,name= 'password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='users/password_reset_complete.html') ,name= 'password_reset_complete'),
    path('logout/', views.user_logout, name= 'logout'),
    
]
