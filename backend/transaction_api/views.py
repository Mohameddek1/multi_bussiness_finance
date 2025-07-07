from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Sum, Q, Count
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, date
from business_api.models import Business, UserBusinessRole
from .models import Transaction, TransactionCategory, AuditLog, InterBusinessTransaction, InterBusinessBalance, SharedExpense, RepaymentSchedule
from .serializers import (
    TransactionSerializer,
    TransactionListSerializer,
    TransactionCategorySerializer,
    TransactionSummarySerializer,
    AuditLogSerializer,
    TransactionFilterSerializer,
    InterBusinessTransactionSerializer,
    InterBusinessTransactionListSerializer,
    RepaymentScheduleSerializer,
    InterBusinessBalanceSerializer,
    SharedExpenseSerializer,
    CashFlowSummarySerializer,
    RepaymentSerializer
)
from .permissions import (
    HasBusinessAccess,
    CanManageTransactions,
    StaffCanOnlyAddIncome,
    CanManageCategories,
    log_user_action
)


class TransactionCategoryListCreateView(generics.ListCreateAPIView):
    """
    List categories for a business or create new category
    """
    serializer_class = TransactionCategorySerializer
    permission_classes = [IsAuthenticated, HasBusinessAccess, CanManageCategories]
    
    def get_queryset(self):
        business_id = self.kwargs['business_id']
        return TransactionCategory.objects.filter(
            business_id=business_id,
            is_active=True
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['business_id'] = self.kwargs['business_id']
        return context
    
    def perform_create(self, serializer):
        category = serializer.save()
        # Log the action
        log_user_action(
            user=self.request.user,
            business=category.business,
            action='create',
            entity_type='category',
            entity_id=category.id,
            details={'name': category.name, 'type': category.type}
        )


class TransactionCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a category
    """
    serializer_class = TransactionCategorySerializer
    permission_classes = [IsAuthenticated, HasBusinessAccess, CanManageCategories]
    
    def get_queryset(self):
        business_id = self.kwargs['business_id']
        return TransactionCategory.objects.filter(business_id=business_id)


class TransactionListCreateView(generics.ListCreateAPIView):
    """
    List transactions for a business or create new transaction
    """
    permission_classes = [IsAuthenticated, HasBusinessAccess, CanManageTransactions, StaffCanOnlyAddIncome]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return TransactionListSerializer
        return TransactionSerializer
    
    def get_queryset(self):
        business_id = self.kwargs['business_id']
        queryset = Transaction.objects.filter(
            business_id=business_id,
            is_deleted=False
        ).select_related('category', 'created_by')
        
        # Apply filters from query parameters
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        """
        Apply filtering based on query parameters
        """
        # Date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        # Transaction type filtering
        transaction_type = self.request.query_params.get('type')
        if transaction_type in ['income', 'expense']:
            queryset = queryset.filter(type=transaction_type)
            
        # Category filtering
        category_id = self.request.query_params.get('category_id')
        if category_id:
            try:
                queryset = queryset.filter(category_id=int(category_id))
            except ValueError:
                pass
                
        # Amount range filtering
        min_amount = self.request.query_params.get('min_amount')
        max_amount = self.request.query_params.get('max_amount')
        
        if min_amount:
            try:
                queryset = queryset.filter(amount__gte=Decimal(min_amount))
            except (ValueError, TypeError):
                pass
                
        if max_amount:
            try:
                queryset = queryset.filter(amount__lte=Decimal(max_amount))
            except (ValueError, TypeError):
                pass
        
        return queryset
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['business_id'] = self.kwargs['business_id']
        return context
    
    def perform_create(self, serializer):
        transaction = serializer.save()
        # Log the action
        log_user_action(
            user=self.request.user,
            business=transaction.business,
            action='create',
            entity_type='transaction',
            entity_id=transaction.id,
            details={
                'type': transaction.type,
                'amount': str(transaction.amount),
                'category': transaction.category.name
            }
        )


class TransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or soft delete a transaction
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated, HasBusinessAccess, CanManageTransactions, StaffCanOnlyAddIncome]
    
    def get_queryset(self):
        business_id = self.kwargs['business_id']
        return Transaction.objects.filter(
            business_id=business_id,
            is_deleted=False
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['business_id'] = self.kwargs['business_id']
        return context
    
    def destroy(self, request, *args, **kwargs):
        """
        Soft delete transaction instead of permanent deletion
        """
        instance = self.get_object()
        
        # Perform soft delete
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.deleted_by = request.user
        instance.save()
        
        # Log the action
        log_user_action(
            user=request.user,
            business=instance.business,
            action='delete',
            entity_type='transaction',
            entity_id=instance.id,
            details={
                'type': instance.type,
                'amount': str(instance.amount),
                'description': instance.description
            }
        )
        
        # Return custom response
        return Response({
            'detail': 'Transaction deleted successfully',
            'deleted_transaction': {
                'id': instance.id,
                'type': instance.type,
                'amount': str(instance.amount),
                'description': instance.description,
                'deleted_at': instance.deleted_at,
                'deleted_by': instance.deleted_by.username
            }
        }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBusinessAccess])
def get_transaction_summary(request, business_id):
    """
    Get financial summary for a business
    """
    # Get date range from query params or default to current month
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date:
        today = date.today()
        start_date = today.replace(day=1)  # First day of current month
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get transactions in the date range
    transactions = Transaction.objects.filter(
        business_id=business_id,
        is_deleted=False,
        date__range=[start_date, end_date]
    )
    
    # Calculate totals
    income_total = transactions.filter(type='income').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    expense_total = transactions.filter(type='expense').aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    net_amount = income_total - expense_total
    
    # Get breakdown by category
    income_by_category = {}
    expense_by_category = {}
    
    income_breakdown = transactions.filter(type='income').values(
        'category__name'
    ).annotate(total=Sum('amount'))
    
    for item in income_breakdown:
        income_by_category[item['category__name']] = str(item['total'])
    
    expense_breakdown = transactions.filter(type='expense').values(
        'category__name'
    ).annotate(total=Sum('amount'))
    
    for item in expense_breakdown:
        expense_by_category[item['category__name']] = str(item['total'])
    
    summary_data = {
        'total_income': income_total,
        'total_expenses': expense_total,
        'net_amount': net_amount,
        'transaction_count': transactions.count(),
        'period_start': start_date,
        'period_end': end_date,
        'income_by_category': income_by_category,
        'expenses_by_category': expense_by_category
    }
    
    serializer = TransactionSummarySerializer(summary_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBusinessAccess])
def get_business_audit_log(request, business_id):
    """
    Get audit log for a specific business
    """
    # Only owners and admins can view audit logs
    user_role = UserBusinessRole.objects.get(
        user=request.user,
        business_id=business_id
    )
    
    if user_role.role not in ['owner', 'admin']:
        return Response(
            {'error': 'You do not have permission to view audit logs'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    audit_logs = AuditLog.objects.filter(business_id=business_id)[:50]  # Last 50 entries
    serializer = AuditLogSerializer(audit_logs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, HasBusinessAccess])
def create_default_categories(request, business_id):
    """
    Create default categories for a new business
    """
    user_role = UserBusinessRole.objects.get(
        user=request.user,
        business_id=business_id
    )
    
    if user_role.role not in ['owner', 'admin']:
        return Response(
            {'error': 'You do not have permission to create categories'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    default_categories = [
        {'name': 'Sales Revenue', 'type': 'income', 'description': 'Revenue from sales'},
        {'name': 'Service Revenue', 'type': 'income', 'description': 'Revenue from services'},
        {'name': 'Rent', 'type': 'expense', 'description': 'Office or store rent'},
        {'name': 'Utilities', 'type': 'expense', 'description': 'Electricity, water, internet'},
        {'name': 'Supplies', 'type': 'expense', 'description': 'Office or business supplies'},
        {'name': 'Marketing', 'type': 'expense', 'description': 'Advertising and marketing costs'},
        {'name': 'Miscellaneous', 'type': 'both', 'description': 'Other income or expenses'},
    ]
    
    created_categories = []
    for cat_data in default_categories:
        category, created = TransactionCategory.objects.get_or_create(
            business_id=business_id,
            name=cat_data['name'],
            defaults={
                'type': cat_data['type'],
                'description': cat_data['description'],
                'created_by': request.user
            }
        )
        if created:
            created_categories.append(category)
    
    return Response({
        'message': f'Created {len(created_categories)} default categories',
        'categories': TransactionCategorySerializer(created_categories, many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, HasBusinessAccess])
def export_transactions(request, business_id):
    """
    Export transactions as CSV (placeholder for now)
    """
    # This is a placeholder - you can implement CSV export logic here
    return Response({
        'message': 'CSV export functionality coming soon',
        'download_url': f'/api/businesses/{business_id}/transactions/export.csv'
    })

# ==============================================
# INTER-BUSINESS TRANSACTION VIEWS
# ==============================================

class InterBusinessTransactionListCreateView(generics.ListCreateAPIView):
    """
    Create and list inter-business transactions (loans, transfers, etc.)
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return InterBusinessTransactionListSerializer
        return InterBusinessTransactionSerializer
    
    def get_queryset(self):
        # Only show transactions for businesses owned by current user
        user_businesses = Business.objects.filter(
            user_roles__user=self.request.user
        ).values_list('id', flat=True)
        
        queryset = InterBusinessTransaction.objects.filter(
            from_business_id__in=user_businesses,
            to_business_id__in=user_businesses,
            is_deleted=False
        ).select_related('from_business', 'to_business', 'created_by')
        
        return self._apply_filters(queryset)
    
    def _apply_filters(self, queryset):
        """Apply filtering based on query parameters"""
        # Filter by transaction type
        transaction_type = self.request.query_params.get('type')
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        # Filter by business
        from_business = self.request.query_params.get('from_business')
        if from_business:
            queryset = queryset.filter(from_business_id=from_business)
            
        to_business = self.request.query_params.get('to_business')
        if to_business:
            queryset = queryset.filter(to_business_id=to_business)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
                
        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        return queryset
    
    def perform_create(self, serializer):
        inter_transaction = serializer.save()
        
        # Update inter-business balance
        self._update_balance(inter_transaction)
        
        # Create regular transactions in both businesses
        self._create_linked_transactions(inter_transaction)
        
        # Log the action
        log_user_action(
            user=self.request.user,
            business=inter_transaction.from_business,
            action='create',
            entity_type='inter_business_transaction',
            entity_id=inter_transaction.id,
            details={
                'type': inter_transaction.transaction_type,
                'amount': str(inter_transaction.amount),
                'to_business': inter_transaction.to_business.name,
                'purpose': inter_transaction.purpose
            }
        )
    
    def _update_balance(self, inter_transaction):
        """Update the balance between two businesses"""
        business_a = inter_transaction.from_business
        business_b = inter_transaction.to_business
        
        # Ensure consistent ordering (lower ID first)
        if business_a.id > business_b.id:
            business_a, business_b = business_b, business_a
            amount_change = inter_transaction.amount
        else:
            amount_change = -inter_transaction.amount
        
        balance, created = InterBusinessBalance.objects.get_or_create(
            business_a=business_a,
            business_b=business_b,
            defaults={'net_balance': amount_change}
        )
        
        if not created:
            balance.net_balance += amount_change
            balance.save()
    
    def _create_linked_transactions(self, inter_transaction):
        """Create corresponding transactions in both businesses"""
        # Create expense in sending business
        Transaction.objects.create(
            business=inter_transaction.from_business,
            category=self._get_or_create_inter_category(inter_transaction.from_business, 'expense'),
            type='expense',
            amount=inter_transaction.amount,
            date=inter_transaction.date,
            description=f"Transfer to {inter_transaction.to_business.name}: {inter_transaction.purpose}",
            reference_number=f"IBT-{inter_transaction.id}",
            created_by=inter_transaction.created_by
        )
        
        # Create income in receiving business
        Transaction.objects.create(
            business=inter_transaction.to_business,
            category=self._get_or_create_inter_category(inter_transaction.to_business, 'income'),
            type='income',
            amount=inter_transaction.amount,
            date=inter_transaction.date,
            description=f"Transfer from {inter_transaction.from_business.name}: {inter_transaction.purpose}",
            reference_number=f"IBT-{inter_transaction.id}",
            created_by=inter_transaction.created_by
        )
    
    def _get_or_create_inter_category(self, business, category_type):
        """Get or create category for inter-business transactions"""
        category_name = "Inter-Business Transfer"
        category, created = TransactionCategory.objects.get_or_create(
            business=business,
            name=category_name,
            defaults={
                'type': 'both',
                'description': 'Transfers between owned businesses',
                'created_by': self.request.user
            }
        )
        return category


class InterBusinessTransactionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete an inter-business transaction
    """
    serializer_class = InterBusinessTransactionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_businesses = Business.objects.filter(
            user_roles__user=self.request.user
        ).values_list('id', flat=True)
        
        return InterBusinessTransaction.objects.filter(
            from_business_id__in=user_businesses,
            to_business_id__in=user_businesses,
            is_deleted=False
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_business_cash_flow(request, business_id):
    """
    Get comprehensive cash flow summary for a business
    """
    # Verify user has access to this business
    try:
        UserBusinessRole.objects.get(user=request.user, business_id=business_id)
    except UserBusinessRole.DoesNotExist:
        return Response(
            {'error': 'Access denied to this business'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    business = get_object_or_404(Business, id=business_id)
    
    # Get date range
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if not start_date:
        start_date = date.today().replace(day=1)  # First day of current month
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
    if not end_date:
        end_date = date.today()
    else:
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Calculate inter-business flows
    money_received = InterBusinessTransaction.objects.filter(
        to_business_id=business_id,
        date__range=[start_date, end_date],
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    money_sent = InterBusinessTransaction.objects.filter(
        from_business_id=business_id,
        date__range=[start_date, end_date],
        is_deleted=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Calculate outstanding balances
    balances_a = InterBusinessBalance.objects.filter(business_a_id=business_id)
    balances_b = InterBusinessBalance.objects.filter(business_b_id=business_id)
    
    total_owed_to_others = Decimal('0.00')
    total_owed_by_others = Decimal('0.00')
    
    for balance in balances_a:
        if balance.net_balance > 0:
            total_owed_to_others += balance.net_balance
        else:
            total_owed_by_others += abs(balance.net_balance)
    
    for balance in balances_b:
        if balance.net_balance < 0:
            total_owed_to_others += abs(balance.net_balance)
        else:
            total_owed_by_others += balance.net_balance
    
    # Count active loans and pending repayments
    active_loans_given = InterBusinessTransaction.objects.filter(
        from_business_id=business_id,
        transaction_type='loan',
        status__in=['pending', 'partially_paid'],
        is_deleted=False
    ).count()
    
    active_loans_received = InterBusinessTransaction.objects.filter(
        to_business_id=business_id,
        transaction_type='loan',
        status__in=['pending', 'partially_paid'],
        is_deleted=False
    ).count()
    
    pending_repayments = RepaymentSchedule.objects.filter(
        inter_transaction__to_business_id=business_id,
        is_paid=False,
        due_date__lte=date.today()
    ).count()
    
    cash_flow_data = {
        'business_id': business_id,
        'business_name': business.name,
        'money_received': money_received,
        'money_sent': money_sent,
        'net_inter_business_flow': money_received - money_sent,
        'total_owed_to_others': total_owed_to_others,
        'total_owed_by_others': total_owed_by_others,
        'net_balance': total_owed_by_others - total_owed_to_others,
        'active_loans_given': active_loans_given,
        'active_loans_received': active_loans_received,
        'pending_repayments': pending_repayments
    }
    
    serializer = CashFlowSummarySerializer(cash_flow_data)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_inter_business_balances(request):
    """
    Get all inter-business balances for user's businesses
    """
    user_businesses = Business.objects.filter(
        user_roles__user=request.user
    ).values_list('id', flat=True)
    
    balances = InterBusinessBalance.objects.filter(
        business_a_id__in=user_businesses,
        business_b_id__in=user_businesses
    ).exclude(net_balance=0)
    
    serializer = InterBusinessBalanceSerializer(balances, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_repayment(request):
    """
    Record a repayment for an inter-business loan
    """
    serializer = RepaymentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        inter_transaction = InterBusinessTransaction.objects.get(
            id=data['inter_transaction_id'],
            is_deleted=False
        )
    except InterBusinessTransaction.DoesNotExist:
        return Response(
            {'error': 'Transaction not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Verify user has access
    user_businesses = Business.objects.filter(
        user_roles__user=request.user
    ).values_list('id', flat=True)
    
    if (inter_transaction.from_business_id not in user_businesses or 
        inter_transaction.to_business_id not in user_businesses):
        return Response(
            {'error': 'Access denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Update the payment amount
    payment_amount = data['amount']
    remaining = inter_transaction.amount - inter_transaction.amount_paid
    
    if payment_amount > remaining:
        return Response(
            {'error': f'Payment amount ({payment_amount}) exceeds remaining balance ({remaining})'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    inter_transaction.amount_paid += payment_amount
    inter_transaction.save()
    
    # Update balance between businesses
    business_a = inter_transaction.from_business
    business_b = inter_transaction.to_business
    
    if business_a.id > business_b.id:
        business_a, business_b = business_b, business_a
        balance_change = -payment_amount
    else:
        balance_change = payment_amount
    
    try:
        balance = InterBusinessBalance.objects.get(
            business_a=business_a,
            business_b=business_b
        )
        balance.net_balance += balance_change
        balance.save()
    except InterBusinessBalance.DoesNotExist:
        pass
    
    # Create transaction records
    # Expense in paying business
    Transaction.objects.create(
        business=inter_transaction.to_business,
        category=TransactionCategory.objects.filter(
            business=inter_transaction.to_business,
            name="Inter-Business Transfer"
        ).first(),
        type='expense',
        amount=payment_amount,
        date=data['payment_date'],
        description=f"Repayment to {inter_transaction.from_business.name}",
        reference_number=f"REP-{inter_transaction.id}",
        created_by=request.user
    )
    
    # Income in receiving business
    Transaction.objects.create(
        business=inter_transaction.from_business,
        category=TransactionCategory.objects.filter(
            business=inter_transaction.from_business,
            name="Inter-Business Transfer"
        ).first(),
        type='income',
        amount=payment_amount,
        date=data['payment_date'],
        description=f"Repayment from {inter_transaction.to_business.name}",
        reference_number=f"REP-{inter_transaction.id}",
        created_by=request.user
    )
    
    return Response({
        'message': 'Repayment recorded successfully',
        'transaction_id': inter_transaction.id,
        'amount_paid': payment_amount,
        'remaining_balance': inter_transaction.remaining_balance,
        'status': inter_transaction.status
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_overdue_payments(request):
    """
    Get all overdue payments for user's businesses
    """
    user_businesses = Business.objects.filter(
        user_roles__user=request.user
    ).values_list('id', flat=True)
    
    overdue_transactions = InterBusinessTransaction.objects.filter(
        Q(from_business_id__in=user_businesses) | Q(to_business_id__in=user_businesses),
        transaction_type='loan',
        status__in=['pending', 'partially_paid'],
        due_date__lt=date.today(),
        is_deleted=False
    )
    
    serializer = InterBusinessTransactionListSerializer(overdue_transactions, many=True)
    return Response(serializer.data)
