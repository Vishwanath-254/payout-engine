from celery import shared_task

@shared_task
def process_payout(payout_id):
    print("🔥🔥 TASK RECEIVED IN CELERY:", payout_id)