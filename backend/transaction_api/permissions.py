from rest_framework.permissions import BasePermission
from business_api.models import UserBusinessRole
from django.shortcuts import get_object_or_404


class HasBusinessAccess(BasePermission):
    """
    Permission to check if user has access to a specific business
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        business_id = view.kwargs.get('business_id') or view.kwargs.get('pk')
        if not business_id:
            return False
            
        # Check if user has any role in this business
        return UserBusinessRole.objects.filter(
            user=request.user,
            business_id=business_id
        ).exists()


class CanManageTransactions(BasePermission):
    """
    Permission for transaction management based on user role
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        business_id = view.kwargs.get('business_id')
        if not business_id:
            return False
            
        try:
            user_role = UserBusinessRole.objects.get(
                user=request.user,
                business_id=business_id
            )
            
            # GET requests: All roles can view
            if request.method == 'GET':
                return True
                
            # POST requests (create): All except viewer can create
            if request.method == 'POST':
                return user_role.role != 'viewer'
                
            # PUT/PATCH requests (update): Only owner, admin, accountant
            if request.method in ['PUT', 'PATCH']:
                return user_role.role in ['owner', 'admin', 'accountant']
                
            # DELETE requests: Only owner and admin
            if request.method == 'DELETE':
                return user_role.role in ['owner', 'admin']
                
            return False
            
        except UserBusinessRole.DoesNotExist:
            return False


class StaffCanOnlyAddIncome(BasePermission):
    """
    Staff members can only add income transactions, not expenses
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        business_id = view.kwargs.get('business_id')
        if not business_id:
            return False
            
        try:
            user_role = UserBusinessRole.objects.get(
                user=request.user,
                business_id=business_id
            )
            
            # Only apply this restriction to staff/employee roles
            if user_role.role in ['employee']:
                # For POST requests, check if they're trying to add expense
                if request.method == 'POST':
                    transaction_type = request.data.get('type')
                    if transaction_type == 'expense':
                        return False
                        
                # For PUT/PATCH requests, check if they're trying to change to expense
                if request.method in ['PUT', 'PATCH']:
                    transaction_type = request.data.get('type')
                    if transaction_type == 'expense':
                        return False
                        
            return True
            
        except UserBusinessRole.DoesNotExist:
            return False


class CanManageCategories(BasePermission):
    """
    Permission for category management - only owner and admin
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        business_id = view.kwargs.get('business_id')
        if not business_id:
            return False
            
        try:
            user_role = UserBusinessRole.objects.get(
                user=request.user,
                business_id=business_id
            )
            
            # GET requests: All roles can view categories
            if request.method == 'GET':
                return True
                
            # Create, Update, Delete: Only owner and admin
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                return user_role.role in ['owner', 'admin']
                
            return False
            
        except UserBusinessRole.DoesNotExist:
            return False


def get_user_role_in_business(user, business_id):
    """
    Helper function to get user's role in a business
    """
    try:
        user_role = UserBusinessRole.objects.get(user=user, business_id=business_id)
        return user_role.role
    except UserBusinessRole.DoesNotExist:
        return None


def can_user_access_business(user, business_id):
    """
    Helper function to check if user can access a business
    """
    return UserBusinessRole.objects.filter(
        user=user,
        business_id=business_id
    ).exists()


def log_user_action(user, business, action, entity_type, entity_id, details=None, ip_address=None):
    """
    Helper function to log user actions for audit trail
    """
    from .models import AuditLog
    
    AuditLog.objects.create(
        user=user,
        business=business,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=ip_address
    )
