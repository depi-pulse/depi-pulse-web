"""Template helpers: Arabic digits, masking of personal data, icons, status pills."""
from decimal import Decimal

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

AR = str.maketrans("0123456789,.", "٠١٢٣٤٥٦٧٨٩٬٫")


@register.filter
def ar(value, decimals=0):
    """1234.5 -> ١٬٢٣٤ (or ١٬٢٣٤٫٥ with decimals=1). Strings are translated digit by digit."""
    if value is None or value == "":
        return ""
    if isinstance(value, (int, float, Decimal)):
        d = int(decimals)
        text = f"{float(value):,.{d}f}" if d else f"{round(float(value)):,}"
    else:
        text = str(value)
    return text.translate(AR)


@register.filter
def pct(value, decimals=0):
    return f"{ar(value, decimals)}٪"


@register.filter
def mask(value, kind="id"):
    """Personal data is shown masked by default (security rule). Full value needs an audited reveal."""
    v = str(value or "")
    if kind == "email" and "@" in v:
        name, dom = v.split("@", 1)
        return f"{name[:2]}•••@{dom}"
    if len(v) <= 4:
        return "•" * len(v)
    return v[:1] + "•" * (len(v) - 4) + v[-3:]


@register.filter
def percent_of(part, whole):
    try:
        return round(100 * float(part) / float(whole)) if whole else 0
    except (TypeError, ValueError):
        return 0


@register.filter
def sub(a, b):
    return (a or 0) - (b or 0)


LABELS = {
    "critical": "حرجة", "urgent": "عاجلة", "high": "عالية", "medium": "متوسطة", "low": "منخفضة",
    "incident": "مشكلة عاجلة", "complaint": "شكوى", "request": "طلب", "question": "استفسار", "suggestion": "اقتراح",
    "Ticket": "تذكرة", "Form": "طلب فورم", "Status": "سؤال عن حالة", "Other": "رسالة عامة",
}


@register.filter
def label(value):
    return LABELS.get(value, value)


@register.filter
def get(d, key):
    return d.get(key) if hasattr(d, "get") else None


P = {
    "home": "M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
    "students": "M16 19v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1M9.5 10a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7M21 19v-1a4 4 0 0 0-3-3.9M15.5 3.2a3.5 3.5 0 0 1 0 6.6",
    "building": "M4 21V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v16M16 9h2a2 2 0 0 1 2 2v10M8 7h4M8 11h4M8 15h4M3 21h18",
    "groups": "M4 5h16v4H4zM4 13h7v6H4zM15 13h5v6h-5z",
    "user": "M20 21v-1a5 5 0 0 0-5-5H9a5 5 0 0 0-5 5v1M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8",
    "clipboard": "M9 4h6v3H9zM8 5H6a1 1 0 0 0-1 1v14a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V6a1 1 0 0 0-1-1h-2M9 13l2 2 4-4",
    "chat": "M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.5A8 8 0 1 1 21 12zM8.5 12h.01M12 12h.01M15.5 12h.01",
    "upload": "M12 15V3M7 8l5-5 5 5M4 15v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-4",
    "shield": "M12 3 4 6v6c0 5 3.4 8.3 8 9 4.6-.7 8-4 8-9V6zM9 12l2 2 4-4",
    "plug": "M9 2v6M15 2v6M6 8h12v3a6 6 0 0 1-12 0zM12 17v5",
    "search": "M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16zM21 21l-4.3-4.3",
    "bell": "M6 8a6 6 0 1 1 12 0c0 7 3 8 3 8H3s3-1 3-8M10.3 21a1.9 1.9 0 0 0 3.4 0",
    "moon": "M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z",
    "sun": "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M1 12h2M21 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4",
    "menu": "M3 6h18M3 12h18M3 18h18", "x": "M18 6 6 18M6 6l12 12", "check": "M20 6 9 17l-5-5",
    "download": "M12 3v12M7 10l5 5 5-5M4 21h16", "info": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 16v-4M12 8h.01",
    "alert": "M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0zM12 9v4M12 17h.01",
    "clock": "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM12 6v6l4 2",
    "link": "M10 13a5 5 0 0 0 7.5.5l3-3a5 5 0 0 0-7-7l-1.7 1.7M14 11a5 5 0 0 0-7.5-.5l-3 3a5 5 0 0 0 7 7l1.7-1.7",
    "lock": "M5 11h14v10H5zM8 11V7a4 4 0 0 1 8 0v4",
    "eye": "M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12zM12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
    "calendar": "M3 5h18v16H3zM16 3v4M8 3v4M3 10h18",
    "file": "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h5",
    "send": "M22 2 11 13M22 2l-7 20-4-9-9-4z",
    "whatsapp": "M3 21l1.7-5A9 9 0 1 1 8 19.3zM9 9.5c0 3 2.5 5.5 5.5 5.5l1.2-1.3-1.8-1-1 .8a4 4 0 0 1-2.4-2.4l.8-1-1-1.8z",
    "sparkle": "M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM19 3v4M21 5h-4",
    "logout": "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9",
    "kanban": "M3 3h5v18H3zM10 3h5v12h-5zM17 3h4v8h-4z",
    "db": "M12 8c5 0 9-1.3 9-3s-4-3-9-3-9 1.3-9 3 4 3 9 3zM21 12c0 1.7-4 3-9 3s-9-1.3-9-3M3 5v14c0 1.7 4 3 9 3s9-1.3 9-3V5",
    "star": "M12 2l3.1 6.3 6.9 1-5 4.9 1.2 6.8L12 17.8 5.8 21l1.2-6.8-5-4.9 6.9-1z",
    "gear": "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z",
    "project": "M12 2 2 7l10 5 10-5zM2 17l10 5 10-5M2 12l10 5 10-5",
    "github": "M9 19c-5 1.5-5-2.5-7-3m14 6v-3.9a3.4 3.4 0 0 0-.9-2.6c3.1-.4 6.4-1.5 6.4-6.9A5.4 5.4 0 0 0 20 4.8 5 5 0 0 0 19.9 1S18.7.7 16 2.5a13.4 13.4 0 0 0-7 0C6.3.7 5.1 1 5.1 1A5 5 0 0 0 5 4.8a5.4 5.4 0 0 0-1.5 3.7c0 5.4 3.3 6.5 6.4 6.9a3.4 3.4 0 0 0-.9 2.6V22",
    "play": "M5 3l14 9-14 9z", "plus": "M12 5v14M5 12h14", "filter": "M3 5h18l-7 8v6l-4 2v-8z",
    "chev": "M15 18l-6-6 6-6", "robot": "M12 8V4H8M4 8h16v12H4zM9 13h.01M15 13h.01M9 17h6",
}


@register.simple_tag
def icon(name, cls=""):
    return format_html('<svg class="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
                       'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{}"/></svg>',
                       cls, P.get(name, P["info"]))


TONES = {
    "accepted": "ok", "rejected": "err", "postponed": "wait", "under_review": "info", "withdrawn": "", "dropout": "", "banned": "err",
    "new": "info", "in_progress": "wait", "waiting": "", "resolved": "ok",
    "critical": "err", "urgent": "err", "high": "wait", "medium": "info", "low": "",
    "applied": "ok", "review": "wait", "duplicate": "err",
    "held": "ok", "not_held": "err", "cancelled": "", "makeup": "info",
    "approved": "ok", "partial": "wait",
}


@register.simple_tag
def pill(label, key=""):
    return format_html('<span class="pill {}"><i></i>{}</span>', TONES.get(key, key), label)


@register.simple_tag
def logo(size=34):
    return mark_safe(f'<svg width="{size}" height="{size}" viewBox="0 0 32 32" aria-hidden="true"><path d="M16 3 L16 13 M16 13 C16 19 9 22 5 29 '
                     'M16 13 C16 19 23 22 27 29" fill="none" stroke="#8fa6f2" stroke-width="3" stroke-linecap="round"/>'
                     '<path d="M5 29 H27" stroke="#dda845" stroke-width="3" stroke-linecap="round"/></svg>')
