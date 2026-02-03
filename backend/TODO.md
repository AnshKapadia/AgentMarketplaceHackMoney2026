 ```
 Files to Create:

  1. app/models/payment.py - Payment transaction model
  # Track all payment transactions
  - id, job_id, payer_id, payee_id
  - amount, currency, status
  - payment_method, transaction_id
  - escrow_status, released_at
  2. app/services/payment_service.py - Core payment logic
  # Main payment operations:
  - create_escrow(job_id, amount) -> hold funds when job created
  - release_payment(job_id) -> release to worker on completion
  - refund_payment(job_id) -> refund client on cancellation
  - process_payment(payment_data) -> integrate with Stripe/PayPal
  3. app/schemas/payment.py - Payment validation schemas
  - PaymentMethodCreate
  - PaymentResponse
  - EscrowStatus
  4. app/api/payments.py - Payment endpoints
  - POST /api/payments/methods - Add payment method
  - GET /api/payments/history - Transaction history
  - POST /api/payments/{id}/refund - Manual refunds

  Files to Modify:

  1. app/services/job_service.py
  # In create_job():
  await payment_service.create_escrow(job.id, job.price_usd)

  # In complete_job():
  await payment_service.release_payment(job.id)

  # In cancel_job():
  await payment_service.refund_payment(job.id)
  2. app/models/job.py
  # Add payment tracking fields:
  payment_status: Mapped[str]  # pending|escrowed|released|refunded
  payment_id: Mapped[str | None]  # Reference to payment record
  3. app/config.py
  # Add payment provider config:
  STRIPE_SECRET_KEY: str
  STRIPE_PUBLISHABLE_KEY: str
  PAYMENT_PROVIDER: str = "stripe"  # or "solana"
  4. requirements.txt
  stripe>=7.0.0  # For traditional payments
  # OR
  solana>=0.30.0  # For blockchain payments
  anchorpy>=0.18.0  # For Solana smart contracts
```
