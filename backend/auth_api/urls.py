from django.urls import path
from .views import RegisterView, UserView, LoginView, LogoutView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),  # Use custom login view
    path('logout/', LogoutView.as_view(), name='logout'),  # Add logout endpoint
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user/', UserView.as_view(), name='user'),
]