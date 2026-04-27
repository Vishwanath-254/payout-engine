from django.db.models import Sum
from .models import LedgerEntry

def get_balance(merchant):
    result = LedgerEntry.objects.filter(merchant=merchant)\
        .aggregate(balance=Sum('amount_paise'))
    
    return result['balance'] or 0