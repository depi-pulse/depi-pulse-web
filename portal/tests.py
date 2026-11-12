import io

from django.core.management import call_command
from django.test import TestCase

from core.models import Applicant, AuditLog, Conversation, Group, Instructor, Lecture, Ticket


class PagesTest(TestCase):
    """Every page renders, personal data stays masked, and sensitive actions are audited."""

    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", stdout=io.StringIO())

    def setUp(self):
        self.client.post("/login")

    def test_login_required(self):
        self.client.get("/logout")
        self.assertRedirects(self.client.get("/students"), "/login", fetch_redirect_response=False)

    def test_all_pages_render(self):
        s = Applicant.objects.filter(status="accepted").first()
        urls = ["/", "/alerts", "/students", f"/students/{s.pk}", "/providers", "/providers/YAT", "/groups",
                f"/groups/{Group.objects.first().code}", "/instructors", f"/instructors/{Instructor.objects.first().pk}",
                "/attendance", f"/attendance/{Lecture.objects.first().pk}", "/inbox", "/tickets",
                f"/tickets/{Ticket.objects.first().code}", "/projects", "/forms", "/imports", "/audit", "/settings"]
        for u in urls:
            with self.subTest(u=u):
                self.assertEqual(self.client.get(u).status_code, 200)

    def test_national_id_is_masked(self):
        s = Applicant.objects.filter(status="accepted").first()
        html = self.client.get(f"/students/{s.pk}").content.decode()
        self.assertNotIn(s.national_id, html)

    def test_reveal_is_audited(self):
        s = Applicant.objects.first()
        r = self.client.post(f"/reveal/student/{s.pk}", {"field": "national_id"})
        self.assertContains(r, s.national_id)
        self.assertTrue(AuditLog.objects.filter(action="كشف بيانات شخصية").exists())

    def test_instructor_codes_valid(self):
        from core.management.commands.seed_demo import luhn32
        for code in Instructor.objects.exclude(code=None).values_list("code", flat=True)[:200]:
            body = code[5:9] + code[10:14] + code[15:19]
            self.assertEqual(code[-1], luhn32(body))

    def test_reply_from_portal(self):
        c = next(x for x in Conversation.objects.all() if x.window_open)
        r = self.client.post(f"/inbox/{c.pk}/send", {"text": "تمام"})
        self.assertContains(r, "bubble out")
