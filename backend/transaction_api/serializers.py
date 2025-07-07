from rest_framework import serializers
from django.contrib.auth.models import User
from business_api.models import Business, UserBusinessRole
from .models import Transaction, TransactionCategory, AuditLog, InterBusinessTransaction, RepaymentSchedule, InterBusinessBalance, SharedExpense, SharedExpenseSplit
from .permissions import get_user_role_in_business


class TransactionCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for TransactionCategory model
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = TransactionCategory
        fields = [
            'id', 'business', 'name', 'type', 'description', 'is_active',
            'created_at', 'created_by', 'created_by_username'
        ]
        read_only_fields = ['id', 'business', 'created_at', 'created_by', 'created_by_username']
        
    def validate_name(self, value):
        """
        Validate category name is unique within the business
        """
        business_id = self.context.get('business_id')
        if TransactionCategory.objects.filter(business_id=business_id, name=value).exists():
            raise serializers.ValidationError("A category with this name already exists in this business.")
        return value
        
    def create(self, validated_data):
        """
        Create category and assign business and creator
        """
        validated_data['business_id'] = self.context['business_id']
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class TransactionSerializer(serializers.ModelSerializer):
    """
    Full serializer for Transaction model
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'business', 'business_name', 'category', 'category_name',
            'type', 'amount', 'date', 'description', 'reference_number',
            'created_by', 'created_by_username', 'created_at',
            'updated_by', 'updated_by_username', 'updated_at',
            'is_deleted'
        ]
        read_only_fields = [
            'id', 'business', 'business_name', 'category_name',
            'created_by', 'created_by_username', 'created_at',
            'updated_by', 'updated_by_username', 'updated_at',
            'is_deleted'
        ]
        
    def validate_category(self, value):
        """
        Validate that category belongs to the same business
        """
        business_id = self.context.get('business_id')
        if value.business_id != int(business_id):
            raise serializers.ValidationError("Category must belong to the same business.")
        return value
        
    def validate(self, attrs):
        """
        Validate transaction type matches category type
        """
        category = attrs.get('category')
        transaction_type = attrs.get('type')
        
        if category and transaction_type:
            if category.type not in ['both', transaction_type]:
                raise serializers.ValidationError(
                    f"Category '{category.name}' cannot be used for {transaction_type} transactions."
                )
                
        # Check role-based restrictions
        user = self.context['request'].user
        business_id = self.context.get('business_id')
        user_role = get_user_role_in_business(user, business_id)
        
        # Staff can only create income transactions
        if user_role == 'employee' and transaction_type == 'expense':
            raise serializers.ValidationError("Staff members can only add income transactions.")
            
        return attrs
        
    def create(self, validated_data):
        """
        Create transaction and assign business and creator
        """
        validated_data['business_id'] = self.context['business_id']
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
        
    def update(self, instance, validated_data):
        """
        Update transaction and track who updated it
        """
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class TransactionListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for listing transactions
    """
    category_name = serializers.CharField(source='category.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'category_name', 'type', 'amount', 'date',
            'description', 'reference_number', 'created_by_username', 'created_at'
        ]


class TransactionSummarySerializer(serializers.Serializer):
    """
    Serializer for transaction summaries and analytics
    """
    total_income = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_count = serializers.IntegerField()
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    
    # Optional breakdown by category
    income_by_category = serializers.DictField(required=False)
    expenses_by_category = serializers.DictField(required=False)


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model
    """
    username = serializers.CharField(source='user.username', read_only=True)
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'user', 'username', 'business', 'business_name',
            'action', 'entity_type', 'entity_id', 'details',
            'timestamp', 'ip_address'
        ]
        read_only_fields = ['id', 'timestamp']


class TransactionFilterSerializer(serializers.Serializer):
    """
    Serializer for transaction filtering parameters
    """
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    type = serializers.ChoiceField(
        choices=[('income', 'Income'), ('expense', 'Expense')],
        required=False
    )
    category_id = serializers.IntegerField(required=False)
    min_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    max_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    
    def validate(self, attrs):
        """
        Validate date range and amount range
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date.")
            
        min_amount = attrs.get('min_amount')
        max_amount = attrs.get('max_amount')
        
        if min_amount and max_amount and min_amount > max_amount:
            raise serializers.ValidationError("Minimum amount must be less than maximum amount.")
            
        return attrs


class InterBusinessTransactionSerializer(serializers.ModelSerializer):
    from_business_name = serializers.CharField(source='from_business.name', read_only=True)
    to_business_name = serializers.CharField(source='to_business.name', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    is_fully_paid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = InterBusinessTransaction
        fields = [
            'id', 'from_business', 'from_business_name', 'to_business', 'to_business_name',
            'transaction_type', 'amount', 'date', 'due_date', 'purpose', 'category', 
            'priority', 'status', 'amount_paid', 'remaining_balance', 'is_fully_paid',
            'notes', 'attachment', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at', 'amount_paid']
    
    def validate(self, data):
        # Ensure businesses belong to the same user
        if data['from_business'].owner != data['to_business'].owner:
            raise serializers.ValidationError(
                "Can only transfer between businesses you own"
            )
        
        # Prevent self-transfer
        if data['from_business'] == data['to_business']:
            raise serializers.ValidationError(
                "Cannot transfer to the same business"
            )
        
        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class InterBusinessTransactionListSerializer(serializers.ModelSerializer):
    """Simplified serializer for list views"""
    from_business_name = serializers.CharField(source='from_business.name', read_only=True)
    to_business_name = serializers.CharField(source='to_business.name', read_only=True)
    remaining_balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = InterBusinessTransaction
        fields = [
            'id', 'from_business_name', 'to_business_name', 'transaction_type',
            'amount', 'remaining_balance', 'date', 'purpose', 'status', 'priority'
        ]


class RepaymentScheduleSerializer(serializers.ModelSerializer):
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = RepaymentSchedule
        fields = [
            'id', 'installment_number', 'due_date', 'amount_due', 'amount_paid',
            'remaining_amount', 'paid_date', 'is_paid', 'is_overdue', 'late_fee'
        ]


class InterBusinessBalanceSerializer(serializers.ModelSerializer):
    business_a_name = serializers.CharField(source='business_a.name', read_only=True)
    business_b_name = serializers.CharField(source='business_b.name', read_only=True)
    
    class Meta:
        model = InterBusinessBalance
        fields = ['id', 'business_a', 'business_a_name', 'business_b', 'business_b_name', 'net_balance', 'last_updated']


class SharedExpenseSerializer(serializers.ModelSerializer):
    paid_by_business_name = serializers.CharField(source='paid_by_business.name', read_only=True)
    splits = serializers.SerializerMethodField()
    
    class Meta:
        model = SharedExpense
        fields = [
            'id', 'name', 'total_amount', 'expense_date', 'category', 'description',
            'paid_by_business', 'paid_by_business_name', 'split_method', 'splits', 'created_at'
        ]
    
    def get_splits(self, obj):
        splits = obj.splits.all()
        return SharedExpenseSplitSerializer(splits, many=True).data


class SharedExpenseSplitSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source='business.name', read_only=True)
    remaining_amount = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = SharedExpenseSplit
        fields = [
            'id', 'business', 'business_name', 'amount_owed', 'amount_paid',
            'remaining_amount', 'percentage', 'is_settled', 'settled_date'
        ]


class CashFlowSummarySerializer(serializers.Serializer):
    """Serializer for business cash flow summary"""
    business_id = serializers.IntegerField()
    business_name = serializers.CharField()
    
    # Money flowing in from other businesses
    money_received = serializers.DecimalField(max_digits=12, decimal_places=2)
    # Money flowing out to other businesses
    money_sent = serializers.DecimalField(max_digits=12, decimal_places=2)
    # Net flow (positive = more received, negative = more sent)
    net_inter_business_flow = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Outstanding balances
    total_owed_to_others = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_owed_by_others = serializers.DecimalField(max_digits=12, decimal_places=2)
    net_balance = serializers.DecimalField(max_digits=12, decimal_places=2)
    
    # Transaction counts
    active_loans_given = serializers.IntegerField()
    active_loans_received = serializers.IntegerField()
    pending_repayments = serializers.IntegerField()


class RepaymentSerializer(serializers.Serializer):
    """Serializer for making repayments"""
    inter_transaction_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    payment_date = serializers.DateField()
    notes = serializers.CharField(max_length=500, required=False)
