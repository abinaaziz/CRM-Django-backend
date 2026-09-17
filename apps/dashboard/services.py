from django.contrib.auth import get_user_model
from django.db.models import Count, DecimalField, Q, Sum, Value
from django.db.models.functions import Coalesce, TruncMonth, TruncQuarter, TruncYear
from django.utils import timezone

from apps.leads.models import Lead
from apps.deals.models import Deal


User = get_user_model()


CLOSED_STAGES = [
    "Closed Won",
    "Closed Lost",
]


ACTIVE_STAGES = [
    "Contract Sent",
    "Appointment Scheduled",
    "Presentation Scheduled",
    "Qualified to Buy",
    "Decision Maker Bought In",
]


def get_dashboard_summary():

    total_leads = Lead.objects.count()

    active_deals = Deal.objects.filter(
        deal_stage__in=ACTIVE_STAGES
    ).count()

    closed_deals = Deal.objects.filter(
        deal_stage__in=CLOSED_STAGES
    ).count()

    today = timezone.localdate()

    monthly_revenue = Deal.objects.filter(
        deal_stage="Closed Won",
        close_date__year=today.year,
        close_date__month=today.month,
        close_date__lte=today,
    ).aggregate(
        total=Sum("amount")
    )["total"] or 0

    return {
        "total_leads": total_leads,
        "active_deals": active_deals,
        "closed_deals": closed_deals,
        "monthly_revenue": monthly_revenue,
    }


def get_conversion_data():

    # Contact starts from the Lead table
    contact_count = Lead.objects.count()

    # Remaining conversion stages come from the Deal table
    qualified_lead_count = Deal.objects.filter(
        deal_stage="Qualified to Buy"
    ).count()

    proposal_sent_count = Deal.objects.filter(
        deal_stage="Contract Sent"
    ).count()

    negotiation_count = Deal.objects.filter(
        deal_stage="Decision Maker Bought In"
    ).count()

    closed_won_count = Deal.objects.filter(
        deal_stage="Closed Won"
    ).count()

    closed_lost_count = Deal.objects.filter(
        deal_stage="Closed Lost"
    ).count()

    return {
        "contact": {
            "count": contact_count,
            "percentage": 100 if contact_count > 0 else 0,
        },

        "qualified_lead": {
            "count": qualified_lead_count,
            "percentage": round(
                (qualified_lead_count / contact_count) * 100
            ) if contact_count else 0,
        },

        "proposal_sent": {
            "count": proposal_sent_count,
            "percentage": round(
                (proposal_sent_count / contact_count) * 100
            ) if contact_count else 0,
        },

        "negotiation": {
            "count": negotiation_count,
            "percentage": round(
                (negotiation_count / contact_count) * 100
            ) if contact_count else 0,
        },

        "closed_won": {
            "count": closed_won_count,
            "percentage": round(
                (closed_won_count / contact_count) * 100
            ) if contact_count else 0,
        },

        "closed_lost": {
            "count": closed_lost_count,
            "percentage": round(
                (closed_lost_count / contact_count) * 100
            ) if contact_count else 0,
        },
    }


def get_sales_report(period="Monthly"):

    today = timezone.localdate()

    deals = Deal.objects.filter(
        deal_stage="Closed Won"
    )

    if period == "Monthly":

        deals = deals.filter(
            close_date__year=today.year
        ).annotate(
            period=TruncMonth("close_date")
        )

        sales = (
            deals
            .values("period")
            .annotate(
                revenue=Sum("amount")
            )
            .order_by("period")
        )

        sales_by_month = {
            item["period"].month: item["revenue"]
            for item in sales
        }

        months = [
            "Jan",
            "Feb",
            "Mar",
            "Apr",
            "May",
            "Jun",
            "Jul",
            "Aug",
            "Sep",
            "Oct",
            "Nov",
            "Dec",
        ]

        return [
            {
                "month": month_name,
                "revenue": sales_by_month.get(
                    month_number,
                    0
                ),
            }
            for month_number, month_name in enumerate(
                months,
                start=1
            )
        ]

    elif period == "Quarterly":

        deals = deals.filter(
            close_date__year=today.year
        ).annotate(
            period=TruncQuarter("close_date")
        )

        sales = (
            deals
            .values("period")
            .annotate(
                revenue=Sum("amount")
            )
            .order_by("period")
        )

        sales_by_quarter = {
            item["period"].quarter: item["revenue"]
            for item in sales
        }

        return [
            {
                "month": f"Q{quarter}",
                "revenue": sales_by_quarter.get(
                    quarter,
                    0
                ),
            }
            for quarter in range(1, 5)
        ]

    elif period == "Yearly":

        deals = deals.annotate(
            period=TruncYear("close_date")
        )

        sales = (
            deals
            .values("period")
            .annotate(
                revenue=Sum("amount")
            )
            .order_by("period")
        )

        return [
            {
                "month": item["period"].year,
                "revenue": item["revenue"],
            }
            for item in sales
        ]

    return []


def get_team_performance():

    team_performance = (
        User.objects
        .filter(
            owned_deals__isnull=False
        )
        .annotate(
            active_deals=Count(
                "owned_deals",
                filter=Q(
                    owned_deals__deal_stage__in=ACTIVE_STAGES
                ),
                distinct=True,
            ),

            closed_deals=Count(
                "owned_deals",
                filter=Q(
                    owned_deals__deal_stage__in=CLOSED_STAGES
                ),
                distinct=True,
            ),

            revenue=Coalesce(
                Sum(
                    "owned_deals__amount",
                    filter=Q(
                        owned_deals__deal_stage="Closed Won"
                    ),
                ),
                Value(0),
                output_field=DecimalField(
                    max_digits=12,
                    decimal_places=2,
                ),
            ),
        )
        .order_by("-revenue")
    )

    for employee in team_performance:
        employee.revenue_change = "0%"

    return team_performance