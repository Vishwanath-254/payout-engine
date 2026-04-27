# Payout Engine Explainer

## 1. Ledger
Balance is stored in paise as integer.
Credits and debits are stored as transactions.
Balance = sum(credits) - sum(debits).

## 2. Lock (Concurrency)
I used select_for_update() inside transaction.atomic().

This ensures that when two payout requests happen simultaneously,
only one transaction can modify the balance at a time.

## 3. Idempotency
Each payout request includes an Idempotency-Key.

Before creating a payout:
- I check if the key already exists
- If yes, I return the existing payout

This prevents duplicate payouts.

## 4. State Machine
Payout states:
pending → processing → completed OR failed

Invalid transitions are blocked in logic.

## 5. AI Audit
AI initially suggested checking balance without database locking,
which could cause race conditions.

I fixed it using:
- transaction.atomic()
- select_for_update()

This ensures correct concurrency handling.