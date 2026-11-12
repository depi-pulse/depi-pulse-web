"""DEPI Pulse portal views (server-rendered Django + HTMX).

Reads use annotations/aggregates in the database and always paginate lists.
"""
import random
from collections import Counter
from datetime import timedelta

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, F, Q, Sum
from django.db.models.functions import TruncWeek
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.models import (
    Applicant, AttendanceRule, AuditLog, Conversation, FormSubmission, Governorate, Group, ImportBatch, Instructor,
    Lecture, Message, Provider, ProjectAssessment, ProjectTeam, Ticket, Track,
)

TEMPLATES = [
    ("ticket_status", "تحديث حالة شكوى", "أهلًا {{1}}، حالة الشكوى رقم {{2}} اتغيرت إلى: {{3}}."),
    ("form_link", "لينك فورم", "أهلًا {{1}}، ده لينك {{2}}: {{3}}"),
    ("form_reminder", "تذكير بفورم", "تذكير: لسه مستنيين {{1}} الخاص بمجموعة {{2}}."),
    ("missing_report", "تقرير حضور ناقص", "محاضرة {{1}} يوم {{2}} مفيش ليها تقرير حضور على Teams."),
    ("announcement", "إعلان عام", "إعلان من وزارة الاتصالات: {{1}}"),
]
FORM_LINKS = {
    "instructors": ("فورم المحاضرين", "https://forms.example.com/instructors"),
    "graduation": ("فورم مشروع التخرج", "https://forms.example.com/graduation"),
    "assessment": ("فورم تقييم المشروع", "https://forms.example.com/assessment"),
}


def audit(action, entity, detail):
    AuditLog.objects.create(at=timezone.now(), action=action, entity=entity, detail=detail)


def is_htmx(request):
    return request.headers.get("HX-Request") == "true"


# ---------------------------------------------------------------- login
def login(request):
    if request.method == "POST":
        request.session["user"] = "المستخدم"
        audit("تسجيل دخول", "الحساب", "دخول بحساب Microsoft بتاع الوزارة")
        return redirect("/")
    return render(request, "portal/login.html")


def logout(request):
    request.session.flush()
    return redirect("/login")


# ---------------------------------------------------------------- overview
def overview(request):
    a = Applicant.objects
    total = a.count()
    by_status = dict(a.values_list("status").annotate(c=Count("id")))
    accepted = by_status.get("accepted", 0)
    groups = Group.objects.annotate(n_students=Count("students", filter=Q(students__status="accepted")))
    sizes = [(g.n_students, g.capacity) for g in groups]
    week_ago = timezone.now() - timedelta(days=7)
    open_t = Ticket.objects.exclude(status="resolved")
    breached = sum(t.breached for t in open_t)
    lectures = Lecture.objects.filter(starts_at__gte=week_ago)
    lec_tot = lectures.aggregate(p=Sum("present"), q=Sum("partial"), a=Sum("absent"))
    att_rate = round(100 * ((lec_tot["p"] or 0) + .5 * (lec_tot["q"] or 0)) / max(1, sum(v or 0 for v in lec_tot.values())))
    at_risk = sum(1 for s in a.filter(status="accepted").only("lectures", "absent", "partial", "excused") if s.absence_rate >= 10)

    kpis = [
        ("المتقدمين", total, "", "/students?status=", "كل اللي سجلوا في الراوند ٥"),
        ("المقبولين", accepted, "", "/students?status=accepted", f"نسبة القبول {round(100 * accepted / total)}٪"),
        ("المجموعات", len(sizes), "", "/groups", f"{sum(1 for e, c in sizes if e > c)} مجموعة أكبر من طاقتها"),
        ("متوسط الامتلاء", round(100 * sum(e for e, _ in sizes) / max(1, sum(c for _, c in sizes))), "٪", "/groups", "من السعة الكلية"),
        ("نسبة الحضور (آخر ٧ أيام)", att_rate, "٪", "/attendance", f"{lectures.count()} محاضرة"),
        ("طلبة معرضين للخطر", at_risk, "", "/students?risk=1", "غياب ١٠٪ أو أكتر"),
        ("شكاوى مفتوحة", open_t.count(), "", "/tickets", f"{breached} عدّت وقت الـ SLA"),
        ("رسايل واتساب جديدة", Conversation.objects.aggregate(s=Sum("unread"))["s"] or 0, "", "/inbox", "مستنية رد من الموقع"),
    ]
    funnel = [(Applicant.Status(s).label, by_status.get(s, 0)) for s in ["accepted", "rejected", "postponed", "withdrawn", "under_review", "dropout", "banned"]]
    tracks = list(Track.objects.annotate(apps=Count("applicants"), acc=Count("applicants", filter=Q(applicants__status="accepted"))).order_by("-apps"))
    govs = list(Governorate.objects.exclude(code="ONL").annotate(apps=Count("applicants")).order_by("-apps")[:12])
    reg = list(a.annotate(w=TruncWeek("registered_at")).values("w").annotate(c=Count("id")).order_by("w"))
    tk = list(Ticket.objects.annotate(w=TruncWeek("created_at")).values("w").annotate(c=Count("id")).order_by("w"))[-8:]
    providers = list(Provider.objects.filter(kind="technical").annotate(
        n_groups=Count("groups", distinct=True), students=Count("groups__students", filter=Q(groups__students__status="accepted"))).order_by("-students"))
    alerts = _alerts()
    charts = {
        "funnel": {"type": "bar", "labels": [f[0] for f in funnel], "values": [f[1] for f in funnel], "horizontal": True},
        "tracks": {"type": "stack", "labels": [t.name_ar for t in tracks], "series": [
            {"name": "مقبولين", "values": [t.acc for t in tracks]}, {"name": "باقي المتقدمين", "values": [t.apps - t.acc for t in tracks]}],
            "colors": [t.color for t in tracks]},
        "govs": {"type": "bar", "labels": [g.name_ar for g in govs], "values": [g.apps for g in govs]},
        "reg": {"type": "line", "labels": [r["w"].strftime("%d/%m") for r in reg], "values": [r["c"] for r in reg]},
        "tk": {"type": "line", "labels": [r["w"].strftime("%d/%m") for r in tk], "values": [r["c"] for r in tk]},
    }
    return render(request, "portal/overview.html", {
        "kpis": kpis, "charts": charts, "providers": providers[:8], "alerts": alerts[:5], "total": total, "accepted": accepted,
        "top_track": tracks[0] if tracks else None, "feeds": _feeds(),
    })


def _feeds():
    now = timezone.now()
    last_imp = ImportBatch.objects.first()
    last_msg = Message.objects.filter(direction="in").order_by("-created_at").first()
    last_form = FormSubmission.objects.first()
    return [
        ("إكسل البوابة", last_imp.created_at if last_imp else now, "upload"),
        ("واتساب (n8n)", last_msg.created_at if last_msg else now, "whatsapp"),
        ("الفورمز", last_form.submitted_at if last_form else now, "clipboard"),
        ("حضور Teams", now - timedelta(minutes=17), "calendar"),
    ]


def _alerts():
    groups = Group.objects.annotate(n=Count("students", filter=Q(students__status="accepted")))
    over = groups.filter(n__gt=F("capacity")).count()
    small = groups.filter(n__lt=15).count()
    breached = sum(t.breached for t in Ticket.objects.exclude(status="resolved"))
    risk = sum(1 for s in Applicant.objects.filter(status="accepted").only("lectures", "absent", "partial", "excused") if s.absence_rate >= 20)
    late = Instructor.objects.filter(late_count__gte=3).count()
    no_report = Lecture.objects.filter(has_report=False).count()
    not_held = Lecture.objects.filter(status="not_held").count()
    review = Instructor.objects.filter(needs_review=True).count()
    teams = Provider.objects.exclude(teams_status="active").exclude(kind="consortium").count()
    rows = [
        ("crit", "شكاوى عدّت وقت الـ SLA", breached, "/tickets", "clock"),
        ("crit", "محاضرات متعملتش (تأخير ٣٠ دقيقة أو أكتر) ومحتاجة تعويض", not_held, "/attendance?status=not_held", "alert"),
        ("warn", "طلبة غيابهم ٢٠٪ أو أكتر (إنذار تاني)", risk, "/students?risk=2", "students"),
        ("warn", "محاضرات خلصت من غير تقرير حضور", no_report, "/attendance?report=0", "file"),
        ("warn", "مجموعات أكبر من طاقتها", over, "/groups?status=over", "groups"),
        ("warn", "شركات ربط Teams بتاعها مش شغال", teams, "/settings#teams", "plug"),
        ("info", "محاضرين اتأخروا ٣ مرات أو أكتر", late, "/instructors?late=1", "user"),
        ("info", "محاضرين محتاجين مراجعة رقم قومي", review, "/instructors?review=1", "shield"),
        ("info", "مجموعات أقل من ١٥ طالب", small, "/groups?status=small", "groups"),
    ]
    return [r for r in rows if r[2]]


def alerts(request):
    rows = _alerts()
    counts = Counter(r[0] for r in rows)
    return render(request, "portal/alerts.html", {"rows": rows, "counts": counts})


# ---------------------------------------------------------------- students
def students(request):
    qs = Applicant.objects.select_related("group", "track", "governorate")
    q, status, track, risk = request.GET.get("q", "").strip(), request.GET.get("status", "accepted"), request.GET.get("track", ""), request.GET.get("risk", "")
    if q:
        qs = qs.filter(Q(name_ar__icontains=q) | Q(name_en__icontains=q) | Q(national_id=q) | Q(group__code__icontains=q))
    if status:
        qs = qs.filter(status=status)
    if track:
        qs = qs.filter(track__code=track)
    if risk:
        lvl = 10 if risk == "1" else 20
        # absence = (absent + partial/2) / (lectures - excused)
        qs = qs.filter(lectures__gt=0).annotate(score=(F("absent") * 2 + F("partial")) * 100 - (F("lectures") - F("excused")) * 2 * lvl).filter(score__gte=0)
    page = Paginator(qs.order_by("name_ar"), 25).get_page(request.GET.get("page"))
    ctx = {"page": page, "q": q, "status": status, "track": track, "risk": risk, "tracks": Track.objects.all(),
           "statuses": Applicant.Status.choices, "total": qs.count()}
    if is_htmx(request):
        return render(request, "portal/partials/students_table.html", ctx)
    return render(request, "portal/students.html", ctx)


def student_detail(request, pk):
    s = get_object_or_404(Applicant.objects.select_related("group__provider", "group__track", "track", "governorate"), pk=pk)
    rule = AttendanceRule.objects.first()
    tickets = Ticket.objects.filter(group=s.group)[:5] if s.group else []
    team = ProjectTeam.objects.filter(group=s.group).select_related("assessment").first() if s.group else None
    rng = random.Random(s.pk)
    timeline = [rng.choices(["present", "partial", "absent", "excused"], weights=[s.present, s.partial, s.absent, s.excused or 0.01])[0]
                for _ in range(s.lectures)]
    return render(request, "portal/student.html", {"s": s, "rule": rule, "tickets": tickets, "team": team, "timeline": timeline})


@require_POST
def reveal(request, kind, pk):
    """Reveal one personal-data field. Every reveal is written to the audit log."""
    obj = get_object_or_404(Applicant if kind == "student" else Instructor, pk=pk)
    field = request.POST.get("field", "national_id")
    if field not in ("national_id", "phone", "email"):
        return HttpResponse(status=400)
    audit("كشف بيانات شخصية", "طالب" if kind == "student" else "محاضر", f"{field} · #{pk}")
    return HttpResponse(f'<span class="masked revealed" dir="ltr">{getattr(obj, field)}</span>')


# ---------------------------------------------------------------- providers
def providers(request):
    kind = request.GET.get("kind", "technical")
    qs = Provider.objects.filter(kind=kind).annotate(
        n_groups=Count("groups", distinct=True), n_instructors=Count("instructors", distinct=True))
    return render(request, "portal/providers.html", {"providers": qs, "kind": kind, "kinds": Provider.Kind.choices})


def provider_detail(request, code):
    p = get_object_or_404(Provider, code=code)
    groups = Group.objects.filter(Q(provider=p) | Q(soft_provider=p) | Q(english_provider=p)).select_related("track", "governorate").annotate(
        n_students=Count("students", filter=Q(students__status="accepted")))
    lectures = Lecture.objects.filter(group__in=groups)
    late = lectures.filter(instructor_late_min__gt=10).count()
    no_report = lectures.filter(has_report=False).count()
    by_track = Counter(g.track.name_ar for g in groups)
    return render(request, "portal/provider.html", {
        "p": p, "groups": groups[:60], "n_groups": groups.count(), "students": sum(g.n_students for g in groups),
        "instructors": p.instructors.all()[:30], "n_instructors": p.instructors.count(), "late": late, "no_report": no_report,
        "lec_count": lectures.count(), "chart": {"type": "bar", "labels": list(by_track), "values": list(by_track.values()), "horizontal": True},
        "teams": ProjectTeam.objects.filter(group__provider=p).count(),
    })


# ---------------------------------------------------------------- groups
def groups(request):
    qs = Group.objects.select_related("track", "governorate", "provider").annotate(n_students=Count("students", filter=Q(students__status="accepted"))).order_by("code")
    q, track, status = request.GET.get("q", "").strip(), request.GET.get("track", ""), request.GET.get("status", "")
    if q:
        qs = qs.filter(code__icontains=q)
    if track:
        qs = qs.filter(track__code=track)
    if status == "over":
        qs = qs.filter(n_students__gt=F("capacity"))
    elif status == "small":
        qs = qs.filter(n_students__lt=15)
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    ctx = {"page": page, "q": q, "track": track, "status": status, "tracks": Track.objects.all(), "total": qs.count()}
    if is_htmx(request):
        return render(request, "portal/partials/groups_table.html", ctx)
    return render(request, "portal/groups.html", ctx)


def group_detail(request, code):
    g = get_object_or_404(Group.objects.select_related("track", "governorate", "provider", "soft_provider", "english_provider",
                                                       "technical_instructor", "soft_instructor", "english_instructor"), code=code)
    studs = g.students.filter(status="accepted").order_by("name_ar")
    lectures = g.lecture_set.select_related("instructor")
    teams = g.teams.select_related("assessment")
    return render(request, "portal/group.html", {"g": g, "students": studs, "n": studs.count(), "lectures": lectures, "teams": teams,
                                                 "d": g.decoded})


# ---------------------------------------------------------------- instructors
def instructors(request):
    qs = Instructor.objects.prefetch_related("providers")
    q, field, review, late = request.GET.get("q", "").strip(), request.GET.get("field", ""), request.GET.get("review", ""), request.GET.get("late", "")
    if q:
        qs = qs.filter(Q(name_ar__icontains=q) | Q(name_en__icontains=q) | Q(code__icontains=q))
    if field:
        qs = qs.filter(fields__icontains=field)
    if review:
        qs = qs.filter(needs_review=True)
    if late:
        qs = qs.filter(late_count__gte=3)
    total = Instructor.objects.count()
    stats = {"total": total, "coded": Instructor.objects.exclude(code=None).count(), "review": Instructor.objects.filter(needs_review=True).count(),
             "partial": Instructor.objects.filter(approval="partial").count(), "form": Instructor.objects.filter(from_form=True).count()}
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    ctx = {"page": page, "q": q, "field": field, "review": review, "late": late, "stats": stats, "count": qs.count(),
           "fields": ["Technical", "English", "Soft Skills", "Freelance", "Coaching"]}
    if is_htmx(request):
        return render(request, "portal/partials/instructors_table.html", ctx)
    return render(request, "portal/instructors.html", ctx)


def instructor_detail(request, pk):
    i = get_object_or_404(Instructor.objects.prefetch_related("providers", "tracks"), pk=pk)
    gs = Group.objects.filter(Q(technical_instructor=i) | Q(soft_instructor=i) | Q(english_instructor=i)).select_related("track")
    lectures = i.lectures.select_related("group")[:20]
    agg = i.lectures.aggregate(n=Count("id"), late=Count("id", filter=Q(instructor_late_min__gt=10)), avg=Avg("instructor_late_min"))
    return render(request, "portal/instructor.html", {"i": i, "groups": gs, "lectures": lectures, "agg": agg})


# ---------------------------------------------------------------- attendance
def attendance(request):
    qs = Lecture.objects.select_related("group", "instructor")
    status, report, comp = request.GET.get("status", ""), request.GET.get("report", ""), request.GET.get("component", "")
    if status:
        qs = qs.filter(status=status)
    if report == "0":
        qs = qs.filter(has_report=False, status__in=["held", "not_held"])
    if comp:
        qs = qs.filter(component=comp)
    allq = Lecture.objects.all()
    t = allq.aggregate(p=Sum("present"), q=Sum("partial"), a=Sum("absent"), u=Sum("unmatched"))
    stats = {
        "lectures": allq.count(), "rate": round(100 * (t["p"] + .5 * t["q"]) / max(1, t["p"] + t["q"] + t["a"])),
        "late": allq.filter(instructor_late_min__gt=10).count(), "not_held": allq.filter(status="not_held").count(),
        "no_report": allq.filter(has_report=False).exclude(status="cancelled").count(), "unmatched": t["u"],
    }
    by_day = list(allq.values("starts_at__date").annotate(p=Sum("present"), q=Sum("partial"), a=Sum("absent")).order_by("starts_at__date"))
    chart = {"type": "line", "labels": [d["starts_at__date"].strftime("%d/%m") for d in by_day],
             "values": [round(100 * (d["p"] + .5 * d["q"]) / max(1, d["p"] + d["q"] + d["a"])) for d in by_day], "unit": "٪", "min": 70}
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    return render(request, "portal/attendance.html", {"page": page, "stats": stats, "rule": AttendanceRule.objects.first(), "chart": chart,
                                                      "status": status, "report": report, "comp": comp,
                                                      "providers": Provider.objects.exclude(kind="consortium")})


def lecture_detail(request, pk):
    lec = get_object_or_404(Lecture.objects.select_related("group", "instructor"), pk=pk)
    rule = AttendanceRule.objects.first()
    rng = random.Random(lec.pk)
    rows = []
    for s in lec.group.students.filter(status="accepted").order_by("name_ar"):
        r = rng.random()
        if r < lec.absent / max(1, lec.present + lec.partial + lec.absent):
            minutes, join = rng.choice([0, 0, 30, 60]), None
        else:
            join = rng.choice([0, 0, 0, 2, 5, 9, 18, 26])
            minutes = lec.actual_duration_min - join - rng.choice([0, 0, 0, 10, 40])
        pct_ = round(100 * minutes / lec.duration_min)
        st = "present" if pct_ >= rule.present_min_percent else "partial" if pct_ >= rule.partial_min_percent else "absent"
        rows.append({"s": s, "minutes": max(0, minutes), "pct": max(0, pct_), "status": st, "late": join is not None and join > rule.late_after_minutes,
                     "join": join, "seg": [(join or 0) / lec.duration_min * 100, max(0, minutes) / lec.duration_min * 100]})
    labels = {"present": "حاضر", "partial": "حضور جزئي", "absent": "غائب"}
    return render(request, "portal/lecture.html", {"lec": lec, "rows": rows, "rule": rule, "labels": labels})


# ---------------------------------------------------------------- WhatsApp inbox
def inbox(request, pk=None):
    convs = Conversation.objects.select_related("provider")
    current = get_object_or_404(convs, pk=pk) if pk else convs.first()
    if current and current.unread:
        current.unread = 0
        current.save(update_fields=["unread"])
    msgs = current.messages.all() if current else []
    return render(request, "portal/inbox.html", {"convs": convs, "c": current, "msgs": msgs, "templates": TEMPLATES, "forms": FORM_LINKS,
                                                 "tickets": current.tickets.all() if current else []})


@require_POST
def inbox_send(request, pk):
    """Reply from the portal. The real system writes an outbox row; n8n sends it with the WhatsApp Send node."""
    c = get_object_or_404(Conversation, pk=pk)
    text, tpl, form = request.POST.get("text", "").strip(), request.POST.get("template", ""), request.POST.get("form", "")
    if form in FORM_LINKS:
        name, url = FORM_LINKS[form]
        text = f"أهلًا بحضرتك، ده لينك {name}: {url}" if c.window_open else f"أهلًا، ده لينك {name}: {url}"
        tpl = "" if c.window_open else "form_link"
    elif tpl:
        text = dict((k, b) for k, _, b in TEMPLATES).get(tpl, "")
    if not text:
        return HttpResponse(status=204)
    if not c.window_open and not tpl:
        return render(request, "portal/partials/window_closed.html", {"c": c}, status=200)
    now = timezone.now()
    m = Message.objects.create(conversation=c, direction="out", text=text, created_at=now, template=tpl, delivery="sent")
    c.last_message_at = now
    c.save(update_fields=["last_message_at"])
    audit("رد على واتساب", "محادثة", f"{c.display_name}{' · قالب ' + tpl if tpl else ''}")
    return render(request, "portal/partials/message.html", {"m": m, "fresh": True})


# ---------------------------------------------------------------- tickets
def tickets(request):
    cols = []
    base = Ticket.objects.select_related("group", "conversation")
    for key, label in Ticket.Status.choices:
        items = base.filter(status=key)
        if key == "resolved":
            items = items.order_by("-resolved_at")[:12]
        cols.append((key, label, list(items[:40]), base.filter(status=key).count()))
    allt = list(Ticket.objects.all())
    by_type = Counter(Ticket.Type(t.type).label for t in allt)
    resolved = [t for t in allt if t.resolved_at]
    within = sum(1 for t in resolved if not t.breached)
    stats = {"open": sum(1 for t in allt if t.status != "resolved"), "breached": sum(1 for t in allt if t.status != "resolved" and t.breached),
             "sla": round(100 * within / max(1, len(resolved))), "total": len(allt)}
    chart = {"type": "pie", "labels": list(by_type), "values": list(by_type.values())}
    return render(request, "portal/tickets.html", {"cols": cols, "stats": stats, "chart": chart})


def ticket_detail(request, code):
    t = get_object_or_404(Ticket.objects.select_related("group", "conversation"), code=code)
    msgs = t.conversation.messages.all() if t.conversation else []
    return render(request, "portal/ticket.html", {"t": t, "msgs": msgs, "statuses": Ticket.Status.choices})


@require_POST
def ticket_status(request, code):
    t = get_object_or_404(Ticket, code=code)
    new = request.POST.get("status")
    if new in Ticket.Status.values:
        old = t.get_status_display()
        t.status = new
        t.resolved_at = timezone.now() if new == "resolved" else None
        t.save()
        audit("تغيير حالة", "شكوى", f"{t.code}: من {old} إلى {t.get_status_display()}")
        messages.success(request, f"حالة {t.code} بقت «{t.get_status_display()}»، والرد هيتبعت لصاحب الشكوى على الواتساب.")
    return redirect(request.POST.get("next") or f"/tickets/{code}")


# ---------------------------------------------------------------- graduation projects
def projects(request):
    teams = ProjectTeam.objects.select_related("group__track", "group__provider", "assessment")
    track = request.GET.get("track", "")
    if track:
        teams = teams.filter(group__track__code=track)
    ass = ProjectAssessment.objects.all()
    agg = ass.aggregate(p=Avg("presentation_demo"), f=Avg("final_submission"))
    totals = [float(a.total) for a in ass]
    bins = Counter(min(9, int(t // 10)) for t in totals)
    chart = {"type": "bar", "labels": [f"{b * 10}–{b * 10 + 9}" for b in range(5, 10)], "values": [bins.get(b, 0) for b in range(5, 10)]}
    stats = {"teams": ProjectTeam.objects.count(), "members": ProjectTeam.objects.aggregate(s=Sum("members"))["s"] or 0,
             "assessed": ass.count(), "avg": round(sum(totals) / max(1, len(totals)), 1), "p": agg["p"] or 0, "f": agg["f"] or 0}
    page = Paginator(teams, 30).get_page(request.GET.get("page"))
    return render(request, "portal/projects.html", {"page": page, "stats": stats, "chart": chart, "tracks": Track.objects.all(), "track": track})


# ---------------------------------------------------------------- forms, imports, audit, settings
def forms(request):
    kind = request.GET.get("kind", "instructors")
    subs = FormSubmission.objects.filter(kind=kind).select_related("provider")
    counts = {k: FormSubmission.objects.filter(kind=k).count() for k, _ in FormSubmission.Kind.choices}
    issues = FormSubmission.objects.filter(kind=kind).exclude(status="applied").count()
    columns = {
        "instructors": ["Full Name (Ar)", "Full Name (En)", "Email", "National ID", "Company", "Field(s)", "Profiles", "Tracks", "Phone Number", "CV Link", "Video Link", "ID photo Link"],
        "graduation": ["Team Group", "Team Leader Name", "Number of Team Members", "Students Name", "Students Email", "Mobile Number", "Project GitHub Link"],
        "assessment": ["Team Group", "Presentation & Demo", "Final Submission & Delivery", "Total (المجموع أوتوماتيك)", "Project discussion recording"],
    }
    who = {"instructors": "المحاضرين والشركات", "graduation": "قائد فريق مشروع التخرج", "assessment": "المحاضرين والشركات"}
    return render(request, "portal/forms.html", {"subs": subs[:40], "kind": kind, "kinds": FormSubmission.Kind.choices, "counts": counts,
                                                 "links": FORM_LINKS, "columns": columns[kind], "who": who[kind], "issues": issues})


def imports(request):
    preview = None
    if request.method == "POST":
        f = request.FILES.get("file")
        if not f or not f.name.lower().endswith((".xlsx", ".xls")):
            messages.error(request, "ارفع ملف إكسل (.xlsx) من بوابة DEPI.")
        else:
            rng = random.Random(f.size)
            rows = rng.randint(800, 49000)
            preview = {"name": f.name, "size": f.size, "rows": rows, "new": rng.randint(10, 90), "upd": rng.randint(50, 400),
                       "issues": rng.randint(0, 40)}
            preview["same"] = rows - preview["new"] - preview["upd"]
            if request.POST.get("confirm"):
                ImportBatch.objects.create(file_name=f.name, kind="المتقدمين", rows=rows, inserted=preview["new"], updated=preview["upd"],
                                           unchanged=preview["same"], issues=preview["issues"], created_at=timezone.now())
                audit("استيراد", "ملف إكسل", f.name)
                messages.success(request, f"الملف {f.name} اتسجل. (في النموذج الأولي الأرقام تجريبية)")
                return redirect("/imports")
    return render(request, "portal/imports.html", {"batches": ImportBatch.objects.all(), "preview": preview})


def audit_log(request):
    page = Paginator(AuditLog.objects.all(), 30).get_page(request.GET.get("page"))
    return render(request, "portal/audit.html", {"page": page})


def settings_page(request):
    return render(request, "portal/settings.html", {
        "rule": AttendanceRule.objects.first(),
        "sla": [("حرجة", "ساعة"), ("عاجلة", "٤ ساعات"), ("عالية", "٢٤ ساعة"), ("متوسطة", "٣ أيام"), ("منخفضة", "أسبوع")],
        "providers": Provider.objects.exclude(kind="consortium"), "templates": TEMPLATES,
    })
