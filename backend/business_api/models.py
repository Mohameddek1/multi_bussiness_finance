from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator


class Business(models.Model):
    """
    Business model to represent different businesses a user can manage
    """
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        ('JPY', 'Japanese Yen'),
        ('CAD', 'Canadian Dollar'),
        ('AUD', 'Australian Dollar'),
        ('CHF', 'Swiss Franc'),
        ('CNY', 'Chinese Yuan'),
        ('INR', 'Indian Rupee'),
        ('BRL', 'Brazilian Real'),
    ]
    
    FISCAL_YEAR_CHOICES = [
        (1, 'January'),
        (2, 'February'),
        (3, 'March'),
        (4, 'April'),
        (5, 'May'),
        (6, 'June'),
        (7, 'July'),
        (8, 'August'),
        (9, 'September'),
        (10, 'October'),
        (11, 'November'),
        (12, 'December'),
    ]
    
    name = models.CharField(
        max_length=255, 
        validators=[MinLengthValidator(2)],
        help_text="Business name (minimum 2 characters)"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        help_text="Optional business description"
    )
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='owned_businesses',
        help_text="User who owns this business"
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='USD',
        help_text="Default currency for this business"
    )
    fiscal_year_start = models.PositiveSmallIntegerField(
        choices=FISCAL_YEAR_CHOICES, 
        default=1,
        help_text="Month when fiscal year starts (1=January, 12=December)"
    )
    default_language = models.CharField(
        max_length=10, 
        default='en',
        help_text="Default language code (e.g., 'en', 'es', 'fr')"
    )
    # logo = models.ImageField(
    #     upload_to='business_logos/', 
    #     blank=True, 
    #     null=True,
    #     help_text="Optional business logo"
    # )  # Temporarily disabled - install Pillow to enable
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.owner.username})"


class UserBusinessRole(models.Model):
    """
    Model to assign different roles to users for specific businesses
    This allows multiple users to access the same business with different permissions
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('accountant', 'Accountant'),
        ('employee', 'Employee'),
        ('viewer', 'Viewer'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='business_roles'
    )
    business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE,
        related_name='user_roles'
    )
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES,
        help_text="User's role in this business"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_roles',
        help_text="User who assigned this role"
    )
    
    class Meta:
        unique_together = ('user', 'business')  # One role per user per business
        verbose_name = 'User Business Role'
        verbose_name_plural = 'User Business Roles'
        
    def __str__(self):
        return f"{self.user.username} - {self.business.name} ({self.role})"
