import logging
from collections import defaultdict
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from accounts.models import (
    Referral,
    ReferralEarning,
    User,
)

logger = logging.getLogger(__name__)


class ReferralService:
    """
    Handles awarding referral commissions and building the referral network.
    """

    @transaction.atomic
    def award_commissions_for_invoice(self, user: User, total_amount: Decimal):
        """
        Award referral commissions for a newly paid invoice.
        20% to direct referrer (level=1) if active.
        5% to indirect referrer (level=2) if active.
        """
        logger.info(f"Processing referral commissions for user: {user.username}")

        # 1) Find all referral rows for which 'user' is the referred party.
        #    That might be 1 or 2 rows (or more if your system supports >2 levels).
        referral_rows = Referral.objects.filter(referred=user)

        # 2) Define a small map for level->rate
        level_to_rate = {
            Referral.Level.DIRECT: Decimal("0.20"),  # 20%
            Referral.Level.INDIRECT: Decimal("0.05"),  # 5%
        }

        # 3) Loop through each referral row
        for ref in referral_rows:
            referrer = ref.referrer

            # Skip if not active
            if not referrer.has_active_subscription:
                logger.info(
                    f"User: {referrer.username} does not have an active subscription. Referral level: {ref.level}"
                )
                continue

                # Determine rate from the referral level
            commission_rate = level_to_rate.get(ref.level)
            if not commission_rate:
                # e.g., if level is unexpected or 0
                logger.warning(
                    f"Unknown referral level {ref.level} for {referrer.username} -> {user.username}. Skipping commission."
                )
                continue

            # 4) Create the referral earning
            self._create_referral_earning(
                referral=ref,
                receiver=referrer,
                commission_rate=commission_rate,
                total_amount=total_amount,
            )

    def _create_referral_earning(
        self,
        referral: Referral,
        receiver: User,
        commission_rate: Decimal,
        total_amount: Decimal,
    ):
        """
        Calculate commission, update the receiver's balance, create ReferralEarning.
        """
        commission_amount = total_amount * commission_rate

        # 1) Update referrer's balance
        receiver.balance.balance += commission_amount
        receiver.balance.save()

        # 2) Create a ReferralEarning
        earning = ReferralEarning.objects.create(
            referral=referral, receiver=receiver, amount=commission_amount
        )

        logger.info(
            f"Awarded {commission_amount} ({commission_rate * 100}%) to {receiver.username} "
            f"for referring {referral.referred.username} (level={referral.level})."
        )
        return earning

    def build_network(self, user: User):
        """
        Build a nested structure for exactly two levels:
          - Direct referrals of `user` (level=1)
          - Indirect referrals of `user` (level=2)

        Then nest each indirect referral under whichever of user’s
        direct referrals introduced them (the “middle man”).

        Returns a dict like:
          {
            "first_level": [
              {
                "user": <User>,
                "earnings": <Decimal>,
                "second_level": [
                  {"user": <User>, "earnings": <Decimal>},
                  ...
                ]
              },
              ...
            ],
            "direct_referrals_count": N,
            "indirect_referrals_count": M,
          }
        """

        # 1) Fetch all direct referrals for `user` at level=1
        #    (the “A->B” rows)
        direct_referrals = (
            Referral.objects.filter(referrer=user, level=1)
            .select_related("referred")
            .annotate(total_earnings=Sum("earnings__amount"))
        )

        # 2) Fetch all indirect referrals for `user` at level=2
        #    (the “A->C” rows)
        indirect_referrals = (
            Referral.objects.filter(referrer=user, level=2)
            .select_related("referred")
            .annotate(total_earnings=Sum("earnings__amount"))
        )

        # 3) Build a dictionary to store direct referrals
        #    We'll add "second_level": [] and fill them next.
        direct_map = {}
        for ref in direct_referrals:
            direct_map[ref.referred_id] = {
                "user": ref.referred,
                "earnings": ref.total_earnings or Decimal("0.00"),
                "second_level": [],
            }

        # 4) We want to figure out: for each “A->C(level=2)” row, who is
        #    the middle man “B” that introduced C?
        #    That B must also be one of A’s direct referrals (B is in direct_map).
        #    But how do we find “B->C(level=1)”? That row belongs to B, not A.
        #
        #    So we do a small query to find all “B->C(level=1)” rows for any B
        #    that’s in direct_map. Then we can link “C” to that B.
        #
        #    Example scenario:
        #       A->B (level=1), B->C (level=1 from B’s perspective),
        #       A->C (level=2). We want to nest C under B in the UI.

        # Gather the IDs of all direct referrals of A
        potential_middle_man_ids = list(direct_map.keys())

        # For each “B->C(level=1)” row where B is in potential_middle_man_ids:
        # We only need B->C’s referred_id and referrer_id to see that B introduced C.
        middle_rows = Referral.objects.filter(
            referrer_id__in=potential_middle_man_ids,
            level=1,  # “B->C” from B’s standpoint
        ).values(
            "referrer_id", "referred_id"
        )  # We don’t need the actual row; just IDs

        # Build a map: child_user_id => [list of possible middle-man IDs]
        # Usually there's only one middle-man, but the data structure allows multiples
        child_to_middles = defaultdict(list)
        for row in middle_rows:
            middle_id = row["referrer_id"]  # B
            child_id = row["referred_id"]  # C
            child_to_middles[child_id].append(middle_id)

        # 5) Now place each “A->C(level=2)” child into the second_level list
        #    for its middle-man B (if we find a match).
        for iref in indirect_referrals:
            c_id = iref.referred_id
            data = {
                "user": iref.referred,
                "earnings": iref.total_earnings or Decimal("0.00"),
            }

            # Does C have exactly one middle-man among user’s direct referrals?
            possible_bs = child_to_middles.get(c_id, [])
            if len(possible_bs) == 1:
                b_id = possible_bs[0]
                # Insert into that direct referral’s `second_level` array
                direct_map[b_id]["second_level"].append(data)
            else:
                # If none or >1, we skip or store in an "unmapped" array
                # For simplicity, skip
                pass

        # 6) Build final dictionary
        return {
            "first_level": list(direct_map.values()),
            "direct_referrals_count": len(direct_referrals),
            "indirect_referrals_count": len(indirect_referrals),
            "total_earnings": self.get_two_level_total_earnings(user),
            "referral_counts": self.get_referral_counts(user),
        }

    def get_two_level_total_earnings(self, user):
        # 1) Sum direct referrals (level=1)
        direct_sum = Referral.objects.filter(referrer=user, level=1).aggregate(
            total=Sum("earnings__amount")
        ).get("total") or Decimal("0.00")

        # 2) Sum indirect referrals (level=2)
        indirect_sum = Referral.objects.filter(referrer=user, level=2).aggregate(
            total=Sum("earnings__amount")
        ).get("total") or Decimal("0.00")

        return direct_sum + indirect_sum

    def get_referral_counts(self, user: User) -> dict:
        """
        Returns counts of:
          - total referrals
          - referrals with an active subscription
          - referrals without an active subscription
        for the given user (as the referrer).
        """
        total_referrals = Referral.objects.filter(referrer=user).count()

        total_with_active_subscription = (
            Referral.objects.filter(
                referrer=user, referred__subscriptions__is_active=True
            )
            .distinct()
            .count()
        )

        total_without_active_subscription = (
            total_referrals - total_with_active_subscription
        )

        return {
            "total_referrals": total_referrals,
            "active_subscription_count": total_with_active_subscription,
            "inactive_subscription_count": total_without_active_subscription,
        }
