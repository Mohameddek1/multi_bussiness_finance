from django.urls import path
from .views import (
    BusinessListCreateView,
    BusinessDetailView,
    BusinessUsersView,
    assign_user_to_business,
    remove_user_from_business,
    get_user_businesses_summary
)

urlpatterns = [
    # Business CRUD operations
    path('businesses/', BusinessListCreateView.as_view(), name='business-list-create'),
    path('businesses/<int:pk>/', BusinessDetailView.as_view(), name='business-detail'),
    
    # Business user management
    path('businesses/<int:business_id>/users/', BusinessUsersView.as_view(), name='business-users'),
    path('businesses/<int:business_id>/assign-user/', assign_user_to_business, name='assign-user-to-business'),
    path('businesses/<int:business_id>/remove-user/<int:user_id>/', remove_user_from_business, name='remove-user-from-business'),
    
    # User business summary
    path('my-businesses/', get_user_businesses_summary, name='user-businesses-summary'),
]
