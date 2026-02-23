from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from .models import SiteVisit

def get_site_stats():
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    stats = {
        'total_visits': SiteVisit.objects.count(),
        'visits_today': SiteVisit.objects.filter(timestamp__gte=today_start).count(),
        'visits_yesterday': SiteVisit.objects.filter(timestamp__gte=yesterday_start, timestamp__lt=today_start).count(),
        'weekly_visits': SiteVisit.objects.filter(timestamp__gte=week_ago).count(),
        'monthly_visits': SiteVisit.objects.filter(timestamp__gte=month_ago).count(),
        'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'new_users_month': User.objects.filter(date_joined__gte=month_ago).count(),
        'recent_visitors': (
            SiteVisit.objects.filter(timestamp__gte=week_ago)
            .select_related('user')
            .values('user__username', 'ip_address', 'timestamp')
            .distinct()
        )
    }

    return stats
