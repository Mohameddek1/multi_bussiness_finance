from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Business, UserBusinessRole


class BusinessSerializer(serializers.ModelSerializer):
    """
    Serializer for Business model
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    
    class Meta:
        model = Business
        fields = [
            'id', 'name', 'description', 'owner', 'owner_username', 'owner_email',
            'currency', 'fiscal_year_start', 'default_language',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'owner_username', 'owner_email', 'created_at', 'updated_at']
        
    def validate_name(self, value):
        """
        Validate business name is unique for the current user
        """
        user = self.context['request'].user
        if Business.objects.filter(owner=user, name=value).exists():
            raise serializers.ValidationError("You already have a business with this name.")
        return value
        
    def create(self, validated_data):
        """
        Create business and assign owner from request user
        """
        validated_data['owner'] = self.context['request'].user
        business = Business.objects.create(**validated_data)
        
        # Automatically create owner role for the user
        UserBusinessRole.objects.create(
            user=business.owner,
            business=business,
            role='owner',
            assigned_by=business.owner
        )
        
        return business


class BusinessListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing businesses
    """
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Business
        fields = [
            'id', 'name', 'description', 'currency', 'fiscal_year_start',
            'owner_username', 'user_role', 'created_at'
        ]
        
    def get_user_role(self, obj):
        """
        Get the current user's role in this business
        """
        user = self.context['request'].user
        try:
            role = UserBusinessRole.objects.get(user=user, business=obj)
            return role.role
        except UserBusinessRole.DoesNotExist:
            return None


class UserBusinessRoleSerializer(serializers.ModelSerializer):
    """
    Serializer for UserBusinessRole model
    """
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    assigned_by_username = serializers.CharField(source='assigned_by.username', read_only=True)
    
    class Meta:
        model = UserBusinessRole
        fields = [
            'id', 'user', 'username', 'user_email', 'business', 'business_name',
            'role', 'assigned_at', 'assigned_by', 'assigned_by_username'
        ]
        read_only_fields = ['id', 'assigned_at', 'assigned_by', 'username', 'user_email', 'business_name', 'assigned_by_username']
        
    def validate(self, attrs):
        """
        Validate role assignment
        """
        user = attrs.get('user')
        business = attrs.get('business')
        request_user = self.context['request'].user
        
        # Check if the request user has permission to assign roles (must be owner or admin)
        try:
            request_user_role = UserBusinessRole.objects.get(user=request_user, business=business)
            if request_user_role.role not in ['owner', 'admin']:
                raise serializers.ValidationError("You don't have permission to assign roles in this business.")
        except UserBusinessRole.DoesNotExist:
            raise serializers.ValidationError("You don't have access to this business.")
            
        # Check if user already has a role in this business
        if UserBusinessRole.objects.filter(user=user, business=business).exists():
            raise serializers.ValidationError("User already has a role in this business.")
            
        return attrs
        
    def create(self, validated_data):
        """
        Create role assignment
        """
        validated_data['assigned_by'] = self.context['request'].user
        return super().create(validated_data)


class AssignUserToBusiness(serializers.Serializer):
    """
    Serializer for assigning a user to a business by email
    """
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=UserBusinessRole.ROLE_CHOICES)
    
    def validate_email(self, value):
        """
        Validate that user with this email exists
        """
        try:
            user = User.objects.get(email=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email address.")
            
    def validate(self, attrs):
        """
        Validate assignment
        """
        email = attrs.get('email')
        user = User.objects.get(email=email)
        business_id = self.context['business_id']
        business = Business.objects.get(id=business_id)
        
        # Check if user already has access to this business
        if UserBusinessRole.objects.filter(user=user, business=business).exists():
            raise serializers.ValidationError("User already has access to this business.")
            
        attrs['user'] = user
        attrs['business'] = business
        return attrs
