from django.apps import AppConfig


class TransactionApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'transaction_api'
    verbose_name = 'Transaction Management'
