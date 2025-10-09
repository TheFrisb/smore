from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.models import User
import stripe


class Command(BaseCommand):
    help = "Delete all Stripe customers that have no associated User record."

    def handle(self, *args, **options):
        # Configure Stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Step 1️⃣ — Get all valid Stripe customer IDs from your DB
        existing_customer_ids = set(
            User.objects.exclude(stripe_customer_id__isnull=True)
            .exclude(stripe_customer_id__exact="")
            .values_list("stripe_customer_id", flat=True)
        )

        self.stdout.write(
            self.style.NOTICE(
                f"Found {len(existing_customer_ids)} Stripe customer IDs linked to users."
            )
        )

        # Step 2️⃣ — Iterate through Stripe customers and delete orphans
        deleted_count = 0
        checked_count = 0
        starting_after = None

        while True:
            customers = stripe.Customer.list(limit=100, starting_after=starting_after)

            # Handle both object and dict-style responses
            customer_data = (
                customers.get("data") if isinstance(customers, dict) else customers.data
            )
            has_more = (
                customers.get("has_more")
                if isinstance(customers, dict)
                else customers.has_more
            )

            if not customer_data:
                break

            for customer in customer_data:
                checked_count += 1
                cust_id = customer["id"] if isinstance(customer, dict) else customer.id

                if cust_id not in existing_customer_ids:
                    self.stdout.write(f"🗑️ Deleting orphan Stripe customer: {cust_id}")
                    try:
                        stripe.Customer.delete(cust_id)
                        deleted_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️ Failed to delete {cust_id}: {e}")
                        )

            # Pagination
            if has_more:
                last_id = (
                    customer_data[-1]["id"]
                    if isinstance(customer_data[-1], dict)
                    else customer_data[-1].id
                )
                starting_after = last_id
            else:
                break

        # Step 3️⃣ — Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"✅ Done. Checked {checked_count} customers, deleted {deleted_count} orphaned ones."
            )
        )
