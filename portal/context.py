from django.db.models import Sum
from django.utils import timezone

from core.models import Conversation, Ticket

NAV = [
    ("المتابعة", [
        ("overview", "/", "نظرة عامة", "home"),
        ("students", "/students", "الطلبة", "students"),
        ("providers", "/providers", "الشركات", "building"),
        ("groups", "/groups", "المجموعات", "groups"),
        ("instructors", "/instructors", "المحاضرين", "user"),
    ]),
    ("التشغيل اليومي", [
        ("attendance", "/attendance", "الحضور", "calendar"),
        ("inbox", "/inbox", "صندوق الواتساب", "whatsapp"),
        ("tickets", "/tickets", "الشكاوى والطلبات", "kanban"),
        ("projects", "/projects", "مشاريع التخرج", "project"),
        ("alerts", "/alerts", "محتاج تدخّل", "alert"),
    ]),
    ("البيانات والإعدادات", [
        ("forms", "/forms", "الفورمز", "clipboard"),
        ("imports", "/imports", "استيراد الإكسل", "upload"),
        ("audit", "/audit", "سجل العمليات", "shield"),
        ("settings", "/settings", "الإعدادات والتكاملات", "gear"),
    ]),
]


def shell(request):
    if request.path.startswith("/login") or not request.session.get("user"):
        return {}
    first = request.path.strip("/").split("/")[0] or "overview"
    open_tickets = [t for t in Ticket.objects.exclude(status="resolved").only("created_at", "priority", "resolved_at")]
    return {
        "NAV": NAV,
        "active": first,
        "user_name": request.session.get("user"),
        "badge_inbox": Conversation.objects.aggregate(s=Sum("unread"))["s"] or 0,
        "badge_breached": sum(t.breached for t in open_tickets),
        "now": timezone.localtime(),
    }
