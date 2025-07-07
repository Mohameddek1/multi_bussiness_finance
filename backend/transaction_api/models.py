from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
from business_api.models import Business


class TransactionCategory(models.Model):
    """
    Categories for transactions (specific to each business)
    """
    CATEGORY_TYPES = [
        ('income', 'Income Category'),
        ('expense', 'Expense Category'),
        ('both', 'Both Income & Expense'),
    ]
    
    business = models.ForeignKey(
        Business, 
        on_delete=models.CASCADE,
        related_name='categories'
    )
    name = models.CharField(
        max_length=100,
        help_text="Category name (e.g., Sales, Rent, Utilities)"
    )
    type = models.CharField(
        max_length=10,
        choices=CATEGORY_TYPES,
        default='both',
        help_text="Whether this category is for income, expense, or both"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional description of this category"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is currently active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_categories'
    )
    
    class Meta:
        unique_together = ('business', 'name')
        verbose_name = 'Transaction Category'
        verbose_name_plural = 'Transaction Categories'
        ordering = ['name']
        
    def __str__(self):
        return f"{self.business.name} - {self.name} ({self.type})"


class Transaction(models.Model):
    """
    Individual financial transactions for businesses
    """
    TRANSACTION_TYPES = [
        ('income', 'Income'),
        ('expense', 'Expense'),
    ]
    
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    category = models.ForeignKey(
        TransactionCategory,
        on_delete=models.PROTECT,
        related_name='transactions',
        help_text="Transaction category"
    )
    type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES,
        help_text="Whether this is income or expense"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Transaction amount (must be positive)"
    )
    date = models.DateField(
        help_text="Date when transaction occurred"
    )
    description = models.TextField(
        help_text="Description of the transaction"
    )
    reference_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Optional reference number (invoice #, receipt #, etc.)"
    )
    
    # Tracking fields
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_transactions',
        help_text="User who created this transaction"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='updated_transactions',
        help_text="User who last updated this transaction"
    )
    
    # Soft deletion
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag - don't permanently delete transactions"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this transaction was deleted"
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_transactions',
        help_text="User who deleted this transaction"
    )
    
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-date', '-created_at']
        
    def __str__(self):
        return f"{self.business.name} - {self.type} - {self.amount} ({self.date})"
    
    def clean(self):
        """
        Validate that category type matches transaction type
        """
        from django.core.exceptions import ValidationError
        
        if self.category and self.type:
            if self.category.type not in ['both', self.type]:
                raise ValidationError(
                    f"Category '{self.category.name}' cannot be used for {self.type} transactions"
                )


class AuditLog(models.Model):
    """
    Audit trail for tracking changes in the system
    """
    ACTION_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('assign', 'Assigned'),
        ('remove', 'Removed'),
    ]
    
    ENTITY_CHOICES = [
        ('business', 'Business'),
        ('transaction', 'Transaction'),
        ('category', 'Category'),
        ('user_role', 'User Role'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        help_text="User who performed the action"
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Business this action relates to"
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    entity_type = models.CharField(
        max_length=20,
        choices=ENTITY_CHOICES,
        help_text="Type of entity affected"
    )
    entity_id = models.PositiveIntegerField(
        help_text="ID of the affected entity"
    )
    details = models.JSONField(
        default=dict,
        help_text="Additional details about the action"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user} {self.action} {self.entity_type} {self.entity_id} at {self.timestamp}"


class InterBusinessTransaction(models.Model):
    """
    Track money movement between businesses owned by the same user
    Supports: loans, transfers, shared expenses, investments
    """
    TRANSACTION_TYPES = [
        ('loan', 'Loan'),
        ('transfer', 'Transfer'),
        ('shared_expense', 'Shared Expense'),
        ('investment', 'Investment'),
        ('repayment', 'Repayment'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('partially_paid', 'Partially Paid'),
        ('fully_paid', 'Fully Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    from_business = models.ForeignKey(
        Business, 
        related_name='sent_transfers', 
        on_delete=models.CASCADE,
        help_text="Business sending/lending money"
    )
    to_business = models.ForeignKey(
        Business, 
        related_name='received_transfers', 
        on_delete=models.CASCADE,
        help_text="Business receiving money"
    )
    
    # Transaction details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    due_date = models.DateField(null=True, blank=True, help_text="When repayment is due")
    
    # Purpose and categorization
    purpose = models.CharField(max_length=255, help_text="Why this transfer happened")
    category = models.CharField(max_length=100, blank=True, help_text="e.g., equipment, inventory, emergency")
    priority = models.CharField(
        max_length=10, 
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='medium'
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Rich details
    notes = models.TextField(blank=True, help_text="Additional details")
    attachment = models.FileField(upload_to='inter_business_docs/', blank=True, null=True)
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft deletion
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User, 
        related_name='deleted_inter_transactions', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    class Meta:
        ordering = ['-date', '-created_at']
        
    def __str__(self):
        return f"{self.from_business.name} → {self.to_business.name}: {self.amount} ({self.transaction_type})"
    
    @property
    def remaining_balance(self):
        """Calculate how much is still owed"""
        return self.amount - self.amount_paid
    
    @property
    def is_fully_paid(self):
        """Check if loan/transfer is fully repaid"""
        return self.amount_paid >= self.amount
    
    def save(self, *args, **kwargs):
        # Auto-update status based on payment
        if self.amount_paid >= self.amount:
            self.status = 'fully_paid'
        elif self.amount_paid > 0:
            self.status = 'partially_paid'
        
        super().save(*args, **kwargs)


class InterBusinessBalance(models.Model):
    """
    Track net balance between two businesses
    Automatically updated when inter-business transactions occur
    """
    business_a = models.ForeignKey(Business, related_name='balances_as_a', on_delete=models.CASCADE)
    business_b = models.ForeignKey(Business, related_name='balances_as_b', on_delete=models.CASCADE)
    
    # Positive means business_a owes business_b
    # Negative means business_b owes business_a
    net_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['business_a', 'business_b']
        
    def __str__(self):
        if self.net_balance > 0:
            return f"{self.business_a.name} owes {self.business_b.name}: {abs(self.net_balance)}"
        elif self.net_balance < 0:
            return f"{self.business_b.name} owes {self.business_a.name}: {abs(self.net_balance)}"
        else:
            return f"{self.business_a.name} ↔ {self.business_b.name}: Even"


class RepaymentSchedule(models.Model):
    """
    Track scheduled repayments for loans
    """
    inter_transaction = models.ForeignKey(
        InterBusinessTransaction, 
        related_name='repayment_schedule', 
        on_delete=models.CASCADE
    )
    
    installment_number = models.IntegerField()
    due_date = models.DateField()
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    # Late payment tracking
    is_overdue = models.BooleanField(default=False)
    late_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    class Meta:
        ordering = ['due_date']
        
    def __str__(self):
        return f"Payment {self.installment_number} for {self.inter_transaction}"
    
    @property
    def remaining_amount(self):
        return self.amount_due - self.amount_paid


class SharedExpense(models.Model):
    """
    Track expenses shared across multiple businesses
    E.g., shared rent, utilities, marketing campaigns
    """
    name = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Which business paid initially
    paid_by_business = models.ForeignKey(
        Business, 
        related_name='shared_expenses_paid', 
        on_delete=models.CASCADE
    )
    
    # How to split the expense
    SPLIT_METHODS = [
        ('equal', 'Equal Split'),
        ('percentage', 'Percentage Split'),
        ('custom', 'Custom Amounts'),
    ]
    split_method = models.CharField(max_length=20, choices=SPLIT_METHODS, default='equal')
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Shared: {self.name} - {self.total_amount}"


class SharedExpenseSplit(models.Model):
    """
    How much each business owes for a shared expense
    """
    shared_expense = models.ForeignKey(
        SharedExpense, 
        related_name='splits', 
        on_delete=models.CASCADE
    )
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    
    # How much this business should pay
    amount_owed = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    is_settled = models.BooleanField(default=False)
    settled_date = models.DateField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.business.name}: {self.amount_owed} for {self.shared_expense.name}"
    
    @property
    def remaining_amount(self):
        return self.amount_owed - self.amount_paid
