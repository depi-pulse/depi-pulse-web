"""Fill the database with FAKE data shaped like DEPI round 5.

Every name, national ID, phone and e-mail here is generated. No real personal data is used.
Run:  python manage.py seed_demo          (wipes the demo tables first)
"""
import hashlib
import hmac
import random
import secrets
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import (
    Applicant, AttendanceRule, AuditLog, Conversation, FormSubmission, Governorate, Group, ImportBatch,
    Instructor, Lecture, Message, Provider, ProjectAssessment, ProjectTeam, Ticket, Track,
)

R = random.Random(2026)
NOW = timezone.now()

GOVS = [
    ("CAI", "القاهرة", 9), ("GIZ", "الجيزة", 7), ("ALX", "الإسكندرية", 6), ("QLY", "القليوبية", 4), ("DKH", "الدقهلية", 4),
    ("SHR", "الشرقية", 4), ("GHR", "الغربية", 3), ("MNF", "المنوفية", 3), ("BHR", "البحيرة", 3), ("KFS", "كفر الشيخ", 2),
    ("DMT", "دمياط", 1), ("PTS", "بورسعيد", 1), ("ISM", "الإسماعيلية", 1), ("SUZ", "السويس", 1), ("FYM", "الفيوم", 2),
    ("BNS", "بني سويف", 2), ("MNY", "المنيا", 3), ("AST", "أسيوط", 3), ("SHG", "سوهاج", 3), ("QNA", "قنا", 2),
    ("LXR", "الأقصر", 1), ("ASN", "أسوان", 1), ("RSD", "البحر الأحمر", 1), ("WAD", "الوادي الجديد", 1), ("MTR", "مطروح", 1),
    ("NSN", "شمال سيناء", 1), ("SSN", "جنوب سيناء", 1), ("ONL", "أونلاين", 8),
]
TRACKS = [
    ("SWD", "تطوير البرمجيات", "Software Development", "#2f4fb5", 27,
     ["Full stack .NET Web Developer", "React Frontend Web Developer", "Cross Platform Mobile App Developer", "Software Tester", "Python Full Stack Developer"]),
    ("AIS", "الذكاء الاصطناعي وعلوم البيانات", "AI & Data Science", "#7b57c9", 21,
     ["Data Scientist", "Microsoft Machine Learning Engineer", "AWS Machine Learning Engineer", "AI Automation Workflow with N8N Professional", "Agentic AI and Generative AI System Developer"]),
    ("DAT", "تحليل البيانات", "Data Analytics", "#0f9aa0", 17, ["Junior Data Analyst", "Professional Data Analyst", "Microsoft Data Engineer"]),
    ("DRT", "التسويق والفنون الرقمية", "Digital Marketing & Art", "#c8553d", 14, ["UI & UX Web Designer", "Digital Marketing Specialist", "Graphic Designer", "Motion Graphics Designer"]),
    ("ISS", "البنية التحتية والأمن", "Infrastructure & Security", "#2e8b57", 10,
     ["Cyber Security Incident Response Analyst", "Vulnerability Analyst and Penetration Tester", "DevOps Engineer", "AWS Security Cloud Computing"]),
    ("ERP", "الإدارة وERP", "Management & ERP", "#c08a2a", 6, ["Odoo ERP Consultant", "SAP Business One Consultant"]),
    ("IND", "مسار الصناعة", "DEPI Industry", "#5e6a82", 3, ["Industrial Automation Specialist"]),
    ("GAM", "صناعة الألعاب الرقمية", "Digital Game Creation", "#c9577e", 2, ["Unity Game Developer"]),
]
TECH = ["YAT", "YTH", "NHA", "GLB", "AMT", "CLS", "LRN", "NXT", "ITC", "AST", "HRV", "NTI", "EUI"]
ENGLISH = [("BRL", "Berlitz"), ("SYE", "SYE"), ("OTO", "OTO")]
SOFT = [("LDG", "Leading 365"), ("HRF", "ElHarefa"), ("NVA", "Nova"), ("NVM", "Nova Mind"), ("FRY", "Freelance Yard"), ("ICR", "iCareer")]
CONSORTIA = [("CLH", "Leading 365 + ElHarefa"), ("CFI", "Freelance Yard + iCareer")]
COLORS = ["#2f55d4", "#7b57c9", "#0f9aa0", "#c8553d", "#2e8b57", "#c08a2a", "#5e6a82", "#c9577e", "#1f3fae", "#a26d17", "#13254a", "#b8432f", "#1e8a5a"]

MALE = [("محمد", "Mohamed"), ("أحمد", "Ahmed"), ("محمود", "Mahmoud"), ("مصطفى", "Mostafa"), ("عمر", "Omar"), ("يوسف", "Youssef"), ("كريم", "Karim"),
        ("علي", "Ali"), ("حسن", "Hassan"), ("خالد", "Khaled"), ("إبراهيم", "Ibrahim"), ("عبدالرحمن", "Abdelrahman"), ("زياد", "Ziad"), ("مروان", "Marwan"),
        ("سيف", "Seif"), ("آدم", "Adam"), ("طارق", "Tarek"), ("هشام", "Hesham"), ("إسلام", "Eslam"), ("بلال", "Belal")]
FEMALE = [("مريم", "Mariam"), ("سارة", "Sara"), ("نور", "Nour"), ("آية", "Aya"), ("هبة", "Heba"), ("منة", "Menna"), ("رنا", "Rana"), ("دينا", "Dina"),
          ("ياسمين", "Yasmin"), ("سلمى", "Salma"), ("فاطمة", "Fatma"), ("ندى", "Nada"), ("روان", "Rawan"), ("ملك", "Malak"), ("جنى", "Jana"),
          ("هاجر", "Hagar"), ("شهد", "Shahd"), ("بسمة", "Basma"), ("إسراء", "Esraa"), ("رحمة", "Rahma")]
FAMILY = [("السيد", "Elsayed"), ("عبدالله", "Abdallah"), ("حسين", "Hussein"), ("فتحي", "Fathy"), ("سليمان", "Soliman"), ("عادل", "Adel"), ("رمضان", "Ramadan"),
          ("الشافعي", "Elshafei"), ("منصور", "Mansour"), ("جمال", "Gamal"), ("صبري", "Sabry"), ("عثمان", "Osman"), ("نصار", "Nassar"), ("زكي", "Zaki"),
          ("الشربيني", "Elsherbiny"), ("حمدي", "Hamdy"), ("فرج", "Farag"), ("كامل", "Kamel"), ("سالم", "Salem"), ("البنا", "Elbanna")]
UNIS = ["جامعة القاهرة", "جامعة عين شمس", "جامعة الإسكندرية", "جامعة المنصورة", "جامعة أسيوط", "جامعة حلوان", "جامعة الزقازيق", "جامعة طنطا",
        "جامعة بنها", "جامعة المنوفية", "جامعة سوهاج", "الجامعة الأمريكية", "جامعة النيل", "جامعة مصر للعلوم والتكنولوجيا"]

ALPHA = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def luhn32(body):
    factor, total = 2, 0
    for ch in reversed(body):
        addend = factor * ALPHA.index(ch)
        factor = 1 if factor == 2 else 2
        total += addend // 32 + addend % 32
    return ALPHA[(32 - total % 32) % 32]


def instructor_code(nid, key):
    """Same algorithm as the Ministry generator (demo key generated per run and never stored)."""
    v = int.from_bytes(hmac.new(key, nid.encode(), hashlib.sha256).digest()[:5], "big")
    token = "".join(ALPHA[(v >> s) & 31] for s in range(35, -1, -5))
    body = nid[-4:] + token
    return f"DEPI-{nid[-4:]}-{token[:4]}-{token[4:]}-{luhn32(body)}"


def person(female=None):
    female = R.random() < 0.45 if female is None else female
    first = R.choice(FEMALE if female else MALE)
    father, grand = R.choice(MALE), R.choice(FAMILY)
    return f"{first[0]} {father[0]} {grand[0]}", f"{first[1]} {father[1]} {grand[1]}", female


def fake_nid(female):
    y = R.randint(97, 99) if R.random() < .4 else R.randint(0, 5)
    century = "2" if y > 50 else "3"
    gov = R.choice(["01", "02", "12", "13", "14", "16", "21", "25", "26"])
    serial = R.randint(100, 999)
    gender_digit = R.choice("02468" if female else "13579")
    return f"{century}{y:02d}{R.randint(1, 12):02d}{R.randint(1, 28):02d}{gov}{serial}{gender_digit}{R.randint(0, 9)}"


def phone():
    return R.choice(["010", "011", "012", "015"]) + f"{R.randint(0, 99999999):08d}"


def ago(**kw):
    return NOW - timedelta(**kw)


class Command(BaseCommand):
    help = "Fill the prototype database with fake data shaped like DEPI round 5."

    @transaction.atomic
    def handle(self, *args, **opts):
        for m in (Message, Ticket, Conversation, ProjectAssessment, ProjectTeam, FormSubmission, Lecture, Applicant, Group,
                  Instructor, Provider, Track, Governorate, ImportBatch, AuditLog, AttendanceRule):
            m.objects.all().delete()
        AttendanceRule.objects.create()

        govs = {c: Governorate.objects.create(code=c, name_ar=n) for c, n, _ in GOVS}
        gov_w = [w for *_, w in GOVS]
        tracks = {c: Track.objects.create(code=c, name_ar=a, name_en=e, color=col) for c, a, e, col, *_ in TRACKS}
        profiles = {c: p for c, *_, p in TRACKS}

        provs = {}
        for i, c in enumerate(TECH):
            provs[c] = Provider.objects.create(code=c, name=c, kind="technical", color=COLORS[i % len(COLORS)],
                                               rating=round(R.uniform(3.6, 4.8), 1), whatsapp_number=phone())
        for c, n in ENGLISH:
            provs[c] = Provider.objects.create(code=c, name=n, kind="english", color="#0f9aa0", rating=round(R.uniform(3.8, 4.7), 1), whatsapp_number=phone())
        for c, n in SOFT:
            provs[c] = Provider.objects.create(code=c, name=n, kind="soft", color="#c08a2a", rating=round(R.uniform(3.7, 4.7), 1), whatsapp_number=phone())
        for c, n in CONSORTIA:
            provs[c] = Provider.objects.create(code=c, name=n, kind="consortium", color="#a26d17", rating=round(R.uniform(3.8, 4.6), 1))
        for code in ("NTI", "EUI"):
            provs[code].teams_status = "consented"
            provs[code].save()
        provs["AST"].teams_status = "failing"
        provs["AST"].save()

        # ---- instructors (1,416; 27 with an invalid ID -> no code, needs review)
        key = secrets.token_bytes(32)
        ins_objs, ins_meta = [], []
        field_mix = [("Technical", 675), ("English", 222), ("Soft Skills", 163), ("Coaching", 107), ("Soft Skills + Freelance", 67),
                     ("Soft Skills + Freelance + Coaching", 62), ("Freelance + Coaching", 51), ("Freelance", 51), ("Soft Skills + Coaching", 18)]
        fields = [f for f, k in field_mix for _ in range(k)]
        bad = set(R.sample(range(len(fields)), 27))
        used_codes = set()
        for i, f in enumerate(fields):
            ar, en, female = person()
            nid = fake_nid(female)
            if i in bad:
                nid = nid[:R.choice([9, 13])] if R.random() < .7 else nid + "1"
                code, review, note = None, True, "الرقم القومي مش صحيح، والكود هيطلع أول ما يتصلح"
            else:
                code = instructor_code(nid, key)
                if code in used_codes:
                    continue
                used_codes.add(code)
                review = R.random() < .02
                note = "الرقم القومي اتاخد من ملف المجموعات، محتاج تأكيد من الشركة" if review else ""
            slug = en.split()[0].lower()
            ins_objs.append(Instructor(
                code=code, name_ar=ar, name_en=en, national_id=nid, email=f"{slug}.{i}@example.com", phone=phone(), fields=f,
                approval="partial" if (f == "Technical" and R.random() < .18) else "approved", needs_review=review, review_note=note,
                cv_link=f"https://drive.example.com/cv/{i}", video_link=f"https://drive.example.com/video/{i}",
                id_photo_link=f"https://drive.example.com/id/{i}", late_count=R.choices([0, 0, 0, 1, 2, 3, 4], k=1)[0],
                rating=round(R.uniform(3.4, 5.0), 1), from_form=R.random() < .12))
            ins_meta.append(f)
        Instructor.objects.bulk_create(ins_objs, batch_size=1000)
        instructors = list(Instructor.objects.order_by("id"))
        tech_ins = [x for x in instructors if "Technical" in x.fields]
        eng_ins = [x for x in instructors if "English" in x.fields]
        soft_ins = [x for x in instructors if "Technical" not in x.fields and "English" not in x.fields]
        through = Instructor.providers.through
        links = []
        for x in tech_ins:
            for p in R.sample(TECH, 2 if R.random() < .12 else 1):
                links.append(through(instructor_id=x.id, provider_id=provs[p].id))
        for x in eng_ins:
            links.append(through(instructor_id=x.id, provider_id=provs[R.choice(ENGLISH)[0]].id))
        for x in soft_ins:
            for p in R.sample([c for c, _ in SOFT], 2 if R.random() < .2 else 1):
                links.append(through(instructor_id=x.id, provider_id=provs[p].id))
        through.objects.bulk_create(links, ignore_conflicts=True)
        ttrough = Instructor.tracks.through
        ttrough.objects.bulk_create([ttrough(instructor_id=x.id, track_id=tracks[R.choice(list(tracks))].id) for x in tech_ins], ignore_conflicts=True)

        # ---- groups (573)
        track_w = [t[4] for t in TRACKS]
        groups, serial = [], {}
        slots = ["السبت والإثنين ١٠ص–١ م", "الأحد والثلاثاء ٦–٩ م", "الإثنين والأربعاء ٢–٥ م", "السبت والثلاثاء ٦–٩ م", "الخميس والجمعة ١٠ص–١ م"]
        for _ in range(573):
            tc = R.choices([t[0] for t in TRACKS], weights=track_w)[0]
            pn = R.randint(1, len(profiles[tc]))
            gc = R.choices([g[0] for g in GOVS], weights=gov_w)[0]
            aud = "G" if R.random() < .3 else "S"
            k = (gc, tc, pn, aud)
            serial[k] = serial.get(k, 0) + 1
            code = f"{gc}5_{tc}{pn}_{aud}{serial[k]}"
            tech = provs[R.choice(TECH)]
            soft = provs[R.choice(["CLH", "HRF", "NVM", "CFI", "YTH"])]
            groups.append(Group(
                code=code, track=tracks[tc], profile=profiles[tc][pn - 1], governorate=govs[gc], audience=aud,
                mode="online" if gc == "ONL" else "physical", provider=tech, soft_provider=soft,
                english_provider=provs[R.choice(["BRL", "SYE", "OTO"])], technical_instructor=R.choice(tech_ins),
                soft_instructor=R.choice(soft_ins), english_instructor=R.choice(eng_ins) if R.random() > .02 else None,
                capacity=R.choice([25, 25, 25, 30]), schedule=R.choice(slots), teams_link_ok=R.random() > .03))
        Group.objects.bulk_create(groups)
        groups = list(Group.objects.select_related("track", "governorate"))
        by_track = {}
        for g in groups:
            by_track.setdefault(g.track.code, []).append(g)

        # ---- applicants (48,932) with round-5 status mix
        mix = [("accepted", 13013), ("rejected", 34097), ("postponed", 1614), ("withdrawn", 161), ("under_review", 32), ("dropout", 8), ("banned", 7)]
        statuses = [s for s, k in mix for _ in range(k)]
        R.shuffle(statuses)
        start = ago(days=150)
        apps = []
        fill = {g.id: 0 for g in groups}
        targets = {g.id: max(8, min(g.capacity, int(R.gauss(g.capacity * .9, 3)))) for g in groups}
        for g in R.sample(groups, 18):
            targets[g.id] = g.capacity + R.randint(1, 3)  # a few oversized groups (real data has them)
        for i, st in enumerate(statuses):
            ar, en, female = person()
            tc = R.choices([t[0] for t in TRACKS], weights=track_w)[0]
            gc = R.choices([g[0] for g in GOVS if g[0] != "ONL"], weights=[g[2] for g in GOVS if g[0] != "ONL"])[0]
            grp = None
            lectures = present = partial = absent = excused = late = 0
            if st in ("accepted", "dropout", "withdrawn"):
                cands = by_track[tc]
                grp = R.choice(cands)
                for _ in range(25):
                    if fill[grp.id] < targets[grp.id]:
                        break
                    grp = R.choice(cands)
                fill[grp.id] += 1
                lectures = 24
                profile = R.random()
                p_abs = .01 if profile < .78 else .045 if profile < .93 else .11 if profile < .985 else .26
                for _ in range(lectures):
                    r = R.random()
                    if r < p_abs:
                        absent += 1
                    elif r < p_abs * 1.6:
                        partial += 1
                    elif r < p_abs * 1.8:
                        excused += 1
                    else:
                        present += 1
                        late += R.random() < .05
            slug = en.split()[0].lower()
            apps.append(Applicant(
                name_ar=ar, name_en=en, national_id=fake_nid(female), email=f"{slug}{i}@example.com", phone=phone(),
                gender="f" if female else "m", governorate=govs[gc], track=tracks[tc], status=st, is_graduate=R.random() < .35,
                university=R.choice(UNIS), registered_at=start + timedelta(minutes=R.randint(0, 60 * 24 * 40)), group=grp,
                lectures=lectures, present=present, partial=partial, absent=absent, excused=excused, late=late))
        Applicant.objects.bulk_create(apps, batch_size=4000)

        # ---- lectures: last 2 weeks for every group (3 components x 2 weeks)
        lec = []
        sizes = dict(fill)
        for g in groups:
            for week in (1, 0):
                for comp, ins in (("technical", g.technical_instructor), ("soft", g.soft_instructor), ("english", g.english_instructor)):
                    when = (NOW - timedelta(days=7 * week + R.randint(0, 6))).replace(hour=R.choice([10, 14, 18]), minute=0, second=0, microsecond=0)
                    if when > NOW:
                        when -= timedelta(days=7)
                    late_min = R.choices([0, 3, 7, 12, 18, 35], weights=[60, 14, 10, 8, 5, 1.2])[0]
                    status = "not_held" if late_min >= 30 else "held"
                    if R.random() < .01:
                        status = "cancelled"
                    n = sizes[g.id]
                    a = int(n * R.uniform(.02, .12))
                    p = int(n * R.uniform(.02, .08))
                    lec.append(Lecture(
                        group=g, component=comp, instructor=ins, starts_at=when, duration_min=180, instructor_late_min=late_min,
                        actual_duration_min=180 - late_min - R.choice([0, 0, 0, 10, 25]), status=status,
                        has_report=status == "cancelled" or R.random() > .04, present=max(0, n - a - p), partial=p, absent=a,
                        unmatched=R.choices([0, 0, 0, 1, 2], k=1)[0]))
        Lecture.objects.bulk_create(lec, batch_size=2000)

        self._inbox(provs, groups)
        self._projects(groups, provs, by_track)
        self._forms_imports(provs)
        self.stdout.write(self.style.SUCCESS(
            f"Demo data ready: {len(apps):,} applicants, {len(groups)} groups, {len(instructors):,} instructors, {len(lec):,} lectures."))

    # ------------------------------------------------------------------ WhatsApp inbox + tickets
    def _inbox(self, provs, groups):
        threads = [
            ("wavz", None, "Wavz — فريق المتابعة", [
                ("in", "صباح الخير، مجموعة {g} المحاضر مدخلش المحاضرة النهاردة لحد دلوقتي والطلبة مستنيين من نص ساعة", "incident", "urgent", "المحاضر متأخر أكتر من ٣٠ دقيقة عن المحاضرة", "Ticket"),
                ("out", "تمام، تم إبلاغ الشركة وهيتم عمل محاضرة تعويضية خلال ٧ أيام. هنبعتلكم الميعاد.", "", "", "", ""),
                ("in", "شكرًا. كمان فيه ٣ طلبة في نفس المجموعة بيقولوا إن إيميلهم مش بيدخل Teams", "complaint", "high", "مشكلة دخول طلبة على Teams بالإيميل المسجل", "Ticket"),
            ]),
            ("wavz", None, "Wavz — الدعم الميداني", [
                ("in", "معمل الإسكندرية التكييف واقف والمحاضرة بكرة الساعة ١٠ الصبح", "complaint", "high", "مشكلة في المكان (تكييف) قبل محاضرة حضوري", "Ticket"),
                ("in", "ممكن نعرف حالة الشكوى بتاعة المعمل؟", "question", "low", "استعلام عن حالة شكوى", "Status"),
            ]),
            ("provider", "YAT", "YAT — منسق التدريب", [
                ("in", "محتاجين لينك فورم المحاضرين علشان نضيف محاضرين جداد", "request", "medium", "طلب لينك فورم المحاضرين", "Form"),
                ("out", "أهلًا بحضرتك، ده لينك فورم المحاضرين: https://forms.example.com/instructors", "", "", "", ""),
            ]),
            ("provider", "NHA", "NHA — شؤون المتدربين", [
                ("in", "عايزين نعرف ميعاد مناقشة مشاريع التخرج ونبعت التقييمات إزاي", "question", "medium", "استفسار عن مناقشة وتقييم مشاريع التخرج", "Form"),
            ]),
            ("provider", "BRL", "Berlitz — English Team", [
                ("in", "We need to reschedule the English lecture for group {g} next Monday", "request", "medium", "طلب تغيير ميعاد محاضرة إنجليزي", "Ticket"),
            ]),
            ("provider", "LDG", "Leading 365 — Soft Skills", [
                ("in", "اقتراح: نزود ورشة عن العمل الحر في آخر شهرين لكل المجموعات", "suggestion", "low", "اقتراح ورشة عمل حر", "Ticket"),
            ]),
            ("provider", "AST", "AST — IT", [
                ("in", "مش قادرين نوافق على صلاحية قراءة تقارير Teams، بيطلع خطأ في الموافقة", "incident", "high", "مشكلة في ربط Teams بالموقع (Consent)", "Ticket"),
            ]),
            ("provider", "CLS", "CLS — منسق", [
                ("in", "تم رفع تقييمات مشاريع التخرج لمجموعتين، ممكن تأكيد؟", "question", "low", "تأكيد استلام تقييمات", "Status"),
            ]),
        ]
        extra_prov = ["GLB", "AMT", "LRN", "NXT", "ITC", "HRV", "NTI", "OTO", "SYE", "NVM", "HRF", "FRY"]
        texts = [
            ("طالب في مجموعة {g} بيشتكي إن المحاضر بيقفل الكاميرا وبيشرح بسرعة", "complaint", "medium", "شكوى من أسلوب شرح محاضر", "Ticket"),
            ("فيه طالبين عايزين ينقلوا لمجموعة أونلاين بسبب السفر", "request", "low", "طلب نقل طلبة لمجموعة أونلاين", "Ticket"),
            ("تقرير الحضور بتاع محاضرة امبارح مش ظاهر عندنا، هل وصلكم؟", "question", "medium", "استفسار عن تقرير حضور ناقص", "Status"),
            ("محتاجين لينك فورم مشروع التخرج للتيم ليدرز", "request", "low", "طلب لينك فورم مشروع التخرج", "Form"),
            ("المعمل فيه ٥ أجهزة واقفة ومحتاجين بديل قبل الخميس", "incident", "urgent", "أجهزة معمل واقفة قبل محاضرة", "Ticket"),
        ]
        for c in extra_prov:
            t = R.choice(texts)
            threads.append(("provider", c, f"{c} — منسق التدريب", [("in",) + t]))

        tk_n = 124
        for kind, pcode, name, msgs in threads:
            g = R.choice(groups)
            hours_ago = R.choice([0.3, 1, 2, 5, 9, 20, 30, 50])
            first = ago(hours=hours_ago + len(msgs))
            conv = Conversation.objects.create(
                sender_kind=kind, provider=provs.get(pcode), display_name=name, phone=phone(),
                last_inbound_at=first, last_message_at=first, unread=0)
            t = first
            last_in = first
            for direction, text, typ, prio, summary, intent in msgs:
                t += timedelta(minutes=R.randint(4, 50))
                body = text.format(g=g.code)
                Message.objects.create(conversation=conv, direction=direction, text=body, created_at=t, ai_type=typ, ai_priority=prio,
                                       ai_summary=summary, ai_intent=intent, delivery="read" if direction == "out" else "read")
                if direction == "in":
                    last_in = t
                    conv.unread += 1
                    if intent in ("Form", "Status"):
                        t += timedelta(seconds=20)
                        reply = ("أهلًا بحضرتك 👋 ده اللينك المطلوب: https://forms.example.com/" + ("graduation" if "تخرج" in body else "instructors")) if intent == "Form" \
                            else f"أهلًا بحضرتك، الشكوى رقم TKT-2026-{tk_n - 1:06d} حالتها: قيد التنفيذ."
                        Message.objects.create(conversation=conv, direction="out", text=reply, created_at=t, auto_reply=True, delivery="read")
                    if intent == "Ticket":
                        Ticket.objects.create(code=f"TKT-2026-{tk_n:06d}", conversation=conv, type=typ, category=summary[:40], priority=prio,
                                              status=R.choice(["new", "new", "in_progress", "waiting"]), title=summary, summary=body,
                                              group=g, created_at=t)
                        tk_n += 1
                else:
                    conv.unread = 0
            conv.last_inbound_at, conv.last_message_at = last_in, t
            conv.save()

        # older tickets (history for kanban + analytics)
        cats = [("complaint", "شكوى من محاضر"), ("complaint", "مشكلة في المكان"), ("request", "طلب نقل مجموعة"), ("question", "استفسار عن الجدول"),
                ("incident", "انقطاع Teams"), ("suggestion", "اقتراح محتوى"), ("complaint", "تأخير بداية المحاضرة"), ("request", "طلب شهادة حضور")]
        for i in range(110):
            typ, cat = R.choice(cats)
            prio = R.choices(["critical", "urgent", "high", "medium", "low"], weights=[2, 8, 25, 40, 25])[0]
            created = ago(days=R.uniform(0.2, 56))
            status = R.choices(["new", "in_progress", "waiting", "resolved"], weights=[8, 12, 6, 74])[0]
            hours = Ticket.SLA_HOURS[prio]
            resolved = created + timedelta(hours=R.uniform(.2, 1.4) * hours) if status == "resolved" else None
            if resolved and resolved > NOW:
                resolved = NOW
            Ticket.objects.create(code=f"TKT-2026-{tk_n:06d}", type=typ, category=cat, priority=prio, status=status,
                                  title=f"{cat} — {R.choice(groups).code}", summary="رسالة واتساب من Wavz متصنفة أوتوماتيك.",
                                  group=R.choice(groups), created_at=created, resolved_at=resolved)
            tk_n += 1

    # ------------------------------------------------------------------ graduation projects
    def _projects(self, groups, provs, by_track):
        ideas = ["منصة حجز عيادات", "نظام إدارة مخازن", "تطبيق توصيل طلبات", "داشبورد مبيعات بالذكاء الاصطناعي", "شات بوت خدمة عملاء",
                 "نظام حضور بالتعرف على الوجه", "متجر إلكتروني للحرف اليدوية", "تحليل بيانات المرور", "لعبة تعليمية للأطفال", "منصة تطوع",
                 "كشف الاحتيال في المدفوعات", "نظام إدارة مدارس", "تطبيق لياقة بدنية", "تحليل مشاعر التعليقات", "حماية شبكة شركة صغيرة"]
        teams = []
        for i, g in enumerate(R.sample(groups, 120)):
            for k in range(2 if R.random() < .55 else 1):
                ar, en, _ = person()
                teams.append(ProjectTeam(group=g, name=f"فريق {k + 1}", idea=R.choice(ideas), leader_name=ar,
                                         leader_email=f"{en.split()[0].lower()}.tl{i}{k}@example.com", members=R.randint(4, 7),
                                         github=f"https://github.com/depi-demo/team-{i}-{k}", registered_at=ago(days=R.randint(3, 25))))
        teams = teams[:241]
        ProjectTeam.objects.bulk_create(teams)
        assessed = []
        for t in ProjectTeam.objects.select_related("group__provider").order_by("?")[:158]:
            assessed.append(ProjectAssessment(team=t, presentation_demo=R.randint(55, 70), final_submission=R.randint(18, 30),
                                              recording_link=f"https://drive.example.com/rec/{t.id}", assessed_by=t.group.provider,
                                              submitted_at=ago(days=R.randint(0, 9))))
        ProjectAssessment.objects.bulk_create(assessed)

    # ------------------------------------------------------------------ form responses, imports, audit
    def _forms_imports(self, provs):
        subs, n = [], 1
        for _ in range(46):
            ar, en, _ = person()
            p = provs[R.choice(TECH + ["BRL", "LDG", "NVM", "FRY"])]
            st = R.choices(["applied", "review", "rejected", "duplicate"], weights=[78, 10, 6, 6])[0]
            issue = {"review": "الرقم القومي اتسجل قبل كده بإيميل مختلف", "rejected": "لينك الفيديو مش شغال",
                     "duplicate": "نفس الرقم القومي اتبعت مرتين"}.get(st, "")
            subs.append(FormSubmission(kind="instructors", response_id=f"R-{n:05d}", submitted_by=ar, provider=p,
                                       summary=f"{en} · {R.choice(['Technical', 'Soft Skills', 'English', 'Coaching'])}", status=st, issue=issue,
                                       submitted_at=ago(hours=R.randint(1, 400))))
            n += 1
        for t in ProjectTeam.objects.select_related("group__provider")[:60]:
            subs.append(FormSubmission(kind="graduation", response_id=f"R-{n:05d}", submitted_by=t.leader_name, provider=t.group.provider,
                                       summary=f"{t.group.code} · {t.idea} · {t.members} أعضاء", status="applied", submitted_at=t.registered_at))
            n += 1
        for a in ProjectAssessment.objects.select_related("team__group", "assessed_by")[:50]:
            subs.append(FormSubmission(kind="assessment", response_id=f"R-{n:05d}", submitted_by=f"محاضر {a.assessed_by.code}",
                                       provider=a.assessed_by, summary=f"{a.team.group.code} · الإجمالي {a.total}", status="applied",
                                       submitted_at=a.submitted_at))
            n += 1
        FormSubmission.objects.bulk_create(subs)

        ImportBatch.objects.bulk_create([
            ImportBatch(file_name="DepiData_2026-10-29.xlsx", kind="المتقدمين", rows=48932, inserted=63, updated=412, unchanged=48457, issues=41, created_at=ago(days=2, hours=3)),
            ImportBatch(file_name="Group_DB.xlsx", kind="المجموعات", rows=573, inserted=0, updated=6, unchanged=567, issues=13, created_at=ago(days=6)),
            ImportBatch(file_name="Schedule_data.xlsx", kind="المواعيد", rows=1571, inserted=2, updated=11, unchanged=1558, issues=3, created_at=ago(days=6)),
            ImportBatch(file_name="ID_with_Instructor_Codes.xlsx", kind="المحاضرين", rows=1416, inserted=1416, updated=0, unchanged=0, issues=27, created_at=ago(days=1)),
            ImportBatch(file_name="Final Project TLs.xlsx", kind="فرق مشاريع التخرج", rows=1367, inserted=241, updated=0, unchanged=0, issues=0, created_at=ago(days=9)),
        ])
        acts = [("تسجيل دخول", "الحساب", "دخول بحساب Microsoft"), ("كشف بيانات شخصية", "طالب", "عرض الرقم القومي كامل"),
                ("رد على واتساب", "محادثة", "رد من صندوق الواتساب"), ("تغيير حالة", "شكوى", "من جديدة إلى قيد التنفيذ"),
                ("استيراد", "ملف إكسل", "رفع ملف المتقدمين"), ("تصدير", "تقرير", "تصدير قايمة المعرضين للخطر"), ("إرسال لينك فورم", "محادثة", "فورم المحاضرين")]
        AuditLog.objects.bulk_create([AuditLog(at=ago(minutes=R.randint(3, 60 * 24 * 10)), action=a, entity=e, detail=d)
                                      for a, e, d in (R.choice(acts) for _ in range(60))])
