from django.urls import path
from .views import (
    TransactionCategoryListCreateView,
    TransactionCategoryDetailView,
    TransactionListCreateView,
    TransactionDetailView,
    get_transaction_summary,
    get_business_audit_log,
    create_default_categories,
    export_transactions,
    InterBusinessTransactionListCreateView,
    InterBusinessTransactionDetailView,
    get_business_cash_flow,
    get_inter_business_balances,
    make_repayment,
    get_overdue_payments
)

urlpatterns = [
    # Transaction Category Management
    path('businesses/<int:business_id>/categories/', 
         TransactionCategoryListCreateView.as_view(), 
         name='category-list-create'),
    path('businesses/<int:business_id>/categories/<int:pk>/', 
         TransactionCategoryDetailView.as_view(), 
         name='category-detail'),
    path('businesses/<int:business_id>/categories/create-defaults/', 
         create_default_categories, 
         name='create-default-categories'),
    
    # Transaction Management
    path('businesses/<int:business_id>/transactions/', 
         TransactionListCreateView.as_view(), 
         name='transaction-list-create'),
    path('businesses/<int:business_id>/transactions/<int:pk>/', 
         TransactionDetailView.as_view(), 
         name='transaction-detail'),
    
    # Analytics and Reports
    path('businesses/<int:business_id>/summary/', 
         get_transaction_summary, 
         name='transaction-summary'),
    path('businesses/<int:business_id>/audit-log/', 
         get_business_audit_log, 
         name='business-audit-log'),
    path('businesses/<int:business_id>/export/', 
         export_transactions, 
         name='export-transactions'),

    # Inter-Business Transaction Management
    path('inter-business-transactions/', 
         InterBusinessTransactionListCreateView.as_view(), 
         name='inter-business-list-create'),
    path('inter-business-transactions/<int:pk>/', 
         InterBusinessTransactionDetailView.as_view(), 
         name='inter-business-detail'),

    # Cash Flow and Balances
    path('businesses/<int:business_id>/cash-flow/', 
         get_business_cash_flow, 
         name='business-cash-flow'),
    path('inter-business-balances/', 
         get_inter_business_balances, 
         name='inter-business-balances'),

    # Repayment and Overdue Payments
    path('repayments/', 
         make_repayment, 
         name='make-repayment'),
    path('overdue-payments/', 
         get_overdue_payments, 
         name='overdue-payments'),
]
