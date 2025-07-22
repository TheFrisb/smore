from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field
from solo.models import SingletonModel


# Create your models here.
class BaseInternalModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseProductModel(BaseInternalModel):
    stripe_product_id = models.CharField(max_length=255)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_price_stripe_id = models.CharField(max_length=255)
    monthly_switzerland_price_stripe_id = models.CharField(max_length=255)

    discounted_monthly_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discounted_monthly_price_stripe_id = models.CharField(
        max_length=255, blank=True, null=True
    )
    discounted_switzerland_monthly_price_stripe_id = models.CharField(
        max_length=255, blank=True, null=True
    )

    yearly_price = models.DecimalField(max_digits=10, decimal_places=2)
    yearly_price_stripe_id = models.CharField(max_length=255)
    yearly_switzerland_price_stripe_id = models.CharField(max_length=255)
    discounted_yearly_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    discounted_yearly_price_stripe_id = models.CharField(
        max_length=255, blank=True, null=True
    )
    discounted_switzerland_yearly_price_stripe_id = models.CharField(max_length=255, blank=True, null=True)
    mobile_product_id = models.CharField(max_length=255, blank=True, null=True)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True
        ordering = ["order"]


class Product(BaseProductModel):
    class Types(models.TextChoices):
        SUBSCRIPTION = "SUBSCRIPTION", _("Subscription")
        ADDON = "ADDON", _("Addon")

    class Names(models.TextChoices):
        SOCCER = "Soccer", _("Soccer")
        BASKETBALL = "Basketball", _("Basketball")
        NFL_NHL = "NFL_NHL", _("NFL, NHL")
        TENNIS = "Tennis", _("Tennis")
        AI_ANALYST = "AI Analyst", _("AI Analyst")

    name = models.CharField(
        max_length=255, choices=Names, default=Names.SOCCER, db_index=True
    )
    type = models.CharField(choices=Types, max_length=255, default=Types.SUBSCRIPTION, db_index=True)
    analysis_per_month = models.CharField(max_length=12, blank=True)
    description = models.TextField(blank=True)

    def get_price_id_for_subscription(self, frequency, use_discounted_prices: bool, is_switzerland):
        if frequency == "monthly":
            if not is_switzerland:
                return (
                    self.discounted_monthly_price_stripe_id
                    if use_discounted_prices
                    else self.monthly_price_stripe_id
                )
            else:
                return (
                    self.discounted_switzerland_monthly_price_stripe_id
                    if use_discounted_prices
                    else self.monthly_switzerland_price_stripe_id
                )

        if not is_switzerland:
            return (
                self.discounted_yearly_price_stripe_id
                if use_discounted_prices
                else self.yearly_price_stripe_id
            )

        return (
            self.discounted_switzerland_yearly_price_stripe_id
            if use_discounted_prices
            else self.yearly_switzerland_price_stripe_id
        )

    def get_price_for_subscription(self, frequency, use_discounted_prices: bool):
        if frequency == "monthly":
            return (
                self.discounted_monthly_price
                if use_discounted_prices
                else self.monthly_price
            )

        return (
            self.discounted_yearly_price if use_discounted_prices else self.yearly_price
        )

    def __str__(self):
        return self.name


class FrequentlyAskedQuestion(BaseInternalModel):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.question

    class Meta:
        ordering = ["order"]


class SiteSettings(BaseInternalModel, SingletonModel):
    customer_withdrawal_request_template_id = models.IntegerField(blank=True, null=True)
    email_confirmation_template_id = models.IntegerField(blank=True, null=True)
    password_reset_template_id = models.IntegerField(blank=True, null=True)
    generic_content_template_id = models.IntegerField(blank=True, null=True)
    notification_email = models.EmailField()

    def __str__(self):
        return "Site Settings"

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"


class ApiSportModel(BaseInternalModel):
    class SportType(models.TextChoices):
        SOCCER = "SOCCER", _("Soccer")
        BASKETBALL = "BASKETBALL", _("Basketball")
        NFL = "NFL", _("NFL")
        NHL = "NHL", _("NHL")
        TEMP_FIX = "TEMP_FIX", _("Temporary Fix")

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    external_id = models.IntegerField(db_index=True)
    type = models.CharField(choices=SportType, max_length=255)

    def __str__(self):
        return f"{self.product.name} - {self.type}"

    class Meta:
        abstract = True
        unique_together = ("external_id", "type",)


class SportCountry(BaseInternalModel):
    name = models.CharField(max_length=255, unique=True)
    code = models.CharField(max_length=255, blank=True)
    logo = models.FileField(upload_to="assets/countries/flags/")

    def __str__(self):
        return self.name


class SportLeague(ApiSportModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    external_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    country = models.ForeignKey(SportCountry, on_delete=models.CASCADE)
    league_type = models.CharField(max_length=255)
    logo = models.FileField(upload_to="assets/leagues/logos/")
    current_season_year = models.IntegerField(
        blank=True, null=True, db_index=True
    )
    api_coverage_data = models.JSONField(null=True, blank=True)
    teams = models.ManyToManyField(
        "SportTeam",
        through='SportLeagueTeam',
        related_name='leagues'
    )

    def __str__(self):
        return self.name


class SportTeam(ApiSportModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    external_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    logo = models.FileField(upload_to="assets/teams/logos/")

    @property
    def leagues_list(self):
        return list(self.leagues.all())

    def __str__(self):
        return f"{self.name}"


class TeamStanding(BaseInternalModel):
    league_team = models.OneToOneField(
        'SportLeagueTeam', on_delete=models.CASCADE, related_name='standings', primary_key=True
    )
    data = models.JSONField(null=True, blank=True)


class SportLeagueTeam(models.Model):
    league = models.ForeignKey(SportLeague, on_delete=models.CASCADE, related_name='league_teams')
    team = models.ForeignKey(SportTeam, on_delete=models.CASCADE, related_name='team_leagues')
    season = models.IntegerField(db_index=True)

    class Meta:
        unique_together = [('league', 'team', 'season')]

    def __str__(self):
        return f"{self.team} in {self.league} ({self.season})"


class SportMatch(ApiSportModel):
    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", _("Scheduled")
        IN_PROGRESS = "IN_PROGRESS", _("In Progress")
        FINISHED = "FINISHED", _("Finished")

    status = models.CharField(
        max_length=12, choices=Status.choices, db_index=True
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    external_id = models.IntegerField(db_index=True)
    league = models.ForeignKey(SportLeague, on_delete=models.CASCADE)
    home_team = models.ForeignKey(
        SportTeam, on_delete=models.CASCADE, related_name="home_team"
    )
    home_team_score = models.CharField(blank=True)
    away_team = models.ForeignKey(
        SportTeam, on_delete=models.CASCADE, related_name="away_team"
    )
    away_team_score = models.CharField(blank=True)
    kickoff_datetime = models.DateTimeField(db_index=True)
    metadata = models.JSONField(null=True, blank=True)

    @property
    def is_live(self):
        # calculate if the match is live (soccer match)
        return (
                self.kickoff_datetime
                <= timezone.now()
                <= (self.kickoff_datetime + timedelta(minutes=105))
        )

    @property
    def league_name(self):
        return self.league.name

    def __str__(self):
        return f"[{self.league.name}] {self.home_team.name} vs {self.away_team.name} ({self.kickoff_datetime})"


class Prediction(BaseInternalModel):
    class Status(models.TextChoices):
        WON = "WON", _("Won")
        LOST = "LOST", _("Lost")
        PENDING = "PENDING", _("Pending")

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    visibility = models.CharField(
        max_length=10, choices=Visibility, default=Visibility.PUBLIC, db_index=True
    )
    match = models.OneToOneField(
        SportMatch, on_delete=models.CASCADE, unique=True, related_name="predictions"
    )
    prediction = models.CharField(max_length=255)
    odds = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=10, choices=Status, default=Status.PENDING, db_index=True
    )
    detailed_analysis = CKEditor5Field(blank=True)

    @property
    def is_sport_prediction(self):
        return self.product.name == Product.Names.SOCCER

    @property
    def result(self):
        return f"{self.match.home_team_score} - {self.match.away_team_score}"

    @property
    def has_detailed_analysis(self):
        return (
                self.detailed_analysis != "" and self.detailed_analysis != "<p>&nbsp;</p>"
        )

    def __str__(self):
        return f"[{self.product.name}] {self.match.home_team.name} vs {self.match.away_team.name} ({self.prediction})"

    class Meta:
        verbose_name = "Prediction"
        verbose_name_plural = "Predictions"


class PickOfTheDay(BaseInternalModel, SingletonModel):
    prediction = models.OneToOneField(
        Prediction, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return f"Pick of the Day: {self.prediction}"


class Ticket(BaseInternalModel):
    class Status(models.TextChoices):
        WON = "WON", _("Won")
        LOST = "LOST", _("Lost")
        PENDING = "PENDING", _("Pending")

    class Visibility(models.TextChoices):
        PUBLIC = "PUBLIC", "Public"
        PRIVATE = "PRIVATE", "Private"

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10, choices=Status, default=Status.PENDING, db_index=True
    )
    visibility = models.CharField(
        max_length=10, choices=Visibility, default=Visibility.PUBLIC, db_index=True
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    label = models.CharField(max_length=255, blank=True)

    @property
    def total_odds(self) -> float:
        """
        Calculate the total odds for all bet lines associated with this instance.

        This property computes the product of the odds of all related bet lines. It
        iterates over all bet line objects connected to the instance and multiplies
        their respective odds to produce the final total odds value.

        @return: The calculated total odds of all related bet lines as a float.
        """
        odds = 1
        for match in self.bet_lines.all():
            odds *= match.odds
        return odds

    def __str__(self):
        # get the first match from the bet lines by date
        first_match = self.bet_lines.order_by("match__kickoff_datetime").first()

        return f"[{self.product.name}] {self.label} ({self.status})"


class BetLine(BaseInternalModel):
    class Status(models.TextChoices):
        WON = "WON", _("Won")
        LOST = "LOST", _("Lost")
        PENDING = "PENDING", _("Pending")

    status = models.CharField(
        max_length=10, choices=Status, default=Status.PENDING, db_index=True
    )
    ticket = models.ForeignKey(
        Ticket, on_delete=models.CASCADE, related_name="bet_lines"
    )
    match = models.ForeignKey(SportMatch, on_delete=models.CASCADE)
    bet = models.CharField(max_length=255)
    bet_type = models.CharField(max_length=255)
    odds = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return (
            f"{self.match.home_team.name} vs {self.match.away_team.name} ({self.bet})"
        )

    class Meta:
        verbose_name = "Bet Line"
        verbose_name_plural = "Bet Lines"
        ordering = ["match__kickoff_datetime"]


class Player(ApiSportModel):
    full_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    birth_place = models.CharField(max_length=255, null=True, blank=True)
    birth_country = models.CharField(max_length=255, null=True, blank=True)
    nationality = models.CharField(max_length=255, null=True, blank=True)
    height = models.CharField(max_length=255, null=True, blank=True)
    weight = models.CharField(max_length=255, null=True, blank=True)
    number = models.CharField(max_length=255, null=True, blank=True)
    position = models.CharField(max_length=255, null=True, blank=True)
    photo = models.FileField(upload_to="assets/players/photos/", null=True, blank=True)
