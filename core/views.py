from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import transaction

from .models import Merchant, BankAccount, LedgerEntry, Payout, IdempotencyKey
from .utils import get_balance
from .tasks import process_payout


@api_view(['POST'])
def create_payout(request):
    # 👉 get merchant (temporary)
    merchant = Merchant.objects.first()

    if not merchant:
        return Response({"error": "No merchant found"}, status=400)

    # 👉 idempotency key
    key = request.headers.get('Idempotency-Key')
    if not key:
        return Response({"error": "Idempotency-Key required"}, status=400)

    # 👉 check duplicate request
    existing = IdempotencyKey.objects.filter(
        merchant=merchant,
        key=key
    ).first()

    if existing:
        return Response(existing.response)

    # 👉 input validation
    try:
        amount = int(request.data.get('amount_paise'))
        bank_account_id = int(request.data.get('bank_account_id'))
    except:
        return Response({"error": "Invalid input"}, status=400)

    # 👉 validate bank account
    try:
        bank_account = BankAccount.objects.get(
            id=bank_account_id,
            merchant=merchant
        )
    except BankAccount.DoesNotExist:
        return Response({"error": "Invalid bank account"}, status=400)

    # 🔒 atomic transaction
    with transaction.atomic():

        # 🔥 lock merchant row
        merchant_locked = Merchant.objects.select_for_update().get(id=merchant.id)

        # 💰 check balance
        balance = get_balance(merchant_locked)

        if balance < amount:
            return Response({"error": "Insufficient balance"}, status=400)

        # 🧾 create payout
        payout = Payout.objects.create(
            merchant=merchant,
            amount_paise=amount,
            bank_account=bank_account,
            status='pending'
        )

        # 💸 deduct balance
        LedgerEntry.objects.create(
            merchant=merchant,
            amount_paise=-amount,
            reference=f"payout:{payout.id}"
        )

        response_data = {
            "payout_id": payout.id,
            "status": payout.status
        }

        # 🔐 save idempotency
        IdempotencyKey.objects.create(
            merchant=merchant,
            key=key,
            response=response_data
        )

    # 🚀 VERY IMPORTANT (OUTSIDE TRANSACTION)
    print("🔥 SENDING TASK:", payout.id)
    process_payout.delay(payout.id)

    return Response(response_data)