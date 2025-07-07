from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Business, UserBusinessRole
from .serializers import (
    BusinessSerializer, 
    BusinessListSerializer, 
    UserBusinessRoleSerializer,
    AssignUserToBusiness
)


class BusinessListCreateView(generics.ListCreateAPIView):
    """
    List all businesses for the authenticated user or create a new business
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BusinessListSerializer
        return BusinessSerializer
    
    def get_queryset(self):
        """
        Return businesses where user has any role (owner, admin, etc.)
        """
        user = self.request.user
        business_ids = UserBusinessRole.objects.filter(user=user).values_list('business_id', flat=True)
        return Business.objects.filter(id__in=business_ids)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new business and automatically assign owner role
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        business = serializer.save()
        
        return Response({
            'message': 'Business created successfully',
            'business': BusinessSerializer(business, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)


class BusinessDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a specific business
    """
    serializer_class = BusinessSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Only allow access to businesses where user has a role
        """
        user = self.request.user
        business_ids = UserBusinessRole.objects.filter(user=user).values_list('business_id', flat=True)
        return Business.objects.filter(id__in=business_ids)
    
    def update(self, request, *args, **kwargs):
        """
        Only allow owners and admins to update business details
        """
        business = self.get_object()
        user_role = UserBusinessRole.objects.get(user=request.user, business=business)
        
        if user_role.role not in ['owner', 'admin']:
            return Response({
                'error': 'You do not have permission to edit this business'
            }, status=status.HTTP_403_FORBIDDEN)
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        """
        Only allow owners to delete businesses
        """
        business = self.get_object()
        user_role = UserBusinessRole.objects.get(user=request.user, business=business)
        
        if user_role.role != 'owner':
            return Response({
                'error': 'Only business owners can delete businesses'
            }, status=status.HTTP_403_FORBIDDEN)
            
        return super().destroy(request, *args, **kwargs)


class BusinessUsersView(generics.ListAPIView):
    """
    List all users who have access to a specific business
    """
    serializer_class = UserBusinessRoleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        business_id = self.kwargs['business_id']
        business = get_object_or_404(Business, id=business_id)
        
        # Check if user has access to this business
        user_role = get_object_or_404(UserBusinessRole, user=self.request.user, business=business)
        
        return UserBusinessRole.objects.filter(business=business)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_user_to_business(request, business_id):
    """
    Assign a user to a business by email
    """
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Response({
            'error': 'Business not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if request user has permission to assign roles
    try:
        request_user_role = UserBusinessRole.objects.get(user=request.user, business=business)
        if request_user_role.role not in ['owner', 'admin']:
            return Response({
                'error': 'You do not have permission to assign users to this business'
            }, status=status.HTTP_403_FORBIDDEN)
    except UserBusinessRole.DoesNotExist:
        return Response({
            'error': 'You do not have access to this business'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Validate and create assignment
    serializer = AssignUserToBusiness(
        data=request.data, 
        context={'business_id': business_id, 'request': request}
    )
    
    if serializer.is_valid():
        user = User.objects.get(email=serializer.validated_data['email'])
        role = serializer.validated_data['role']
        
        # Create the role assignment
        user_business_role = UserBusinessRole.objects.create(
            user=user,
            business=business,
            role=role,
            assigned_by=request.user
        )
        
        return Response({
            'message': f'User {user.email} assigned as {role} to {business.name}',
            'assignment': UserBusinessRoleSerializer(user_business_role, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_user_from_business(request, business_id, user_id):
    """
    Remove a user's access from a business
    """
    try:
        business = Business.objects.get(id=business_id)
        user_to_remove = User.objects.get(id=user_id)
    except (Business.DoesNotExist, User.DoesNotExist):
        return Response({
            'error': 'Business or user not found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Check if request user has permission
    try:
        request_user_role = UserBusinessRole.objects.get(user=request.user, business=business)
        if request_user_role.role not in ['owner', 'admin']:
            return Response({
                'error': 'You do not have permission to remove users from this business'
            }, status=status.HTTP_403_FORBIDDEN)
    except UserBusinessRole.DoesNotExist:
        return Response({
            'error': 'You do not have access to this business'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Prevent removing the owner
    try:
        role_to_remove = UserBusinessRole.objects.get(user=user_to_remove, business=business)
        if role_to_remove.role == 'owner':
            return Response({
                'error': 'Cannot remove the business owner'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        role_to_remove.delete()
        return Response({
            'message': f'User {user_to_remove.email} removed from {business.name}'
        }, status=status.HTTP_200_OK)
        
    except UserBusinessRole.DoesNotExist:
        return Response({
            'error': 'User does not have access to this business'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_businesses_summary(request):
    """
    Get a summary of all businesses the user has access to
    """
    user = request.user
    roles = UserBusinessRole.objects.filter(user=user).select_related('business')
    
    businesses_summary = []
    for role in roles:
        businesses_summary.append({
            'id': role.business.id,
            'name': role.business.name,
            'currency': role.business.currency,
            'user_role': role.role,
            'created_at': role.business.created_at,
            'is_owner': role.role == 'owner'
        })
    
    return Response({
        'total_businesses': len(businesses_summary),
        'businesses': businesses_summary
    }, status=status.HTTP_200_OK)
