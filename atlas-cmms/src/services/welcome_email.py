"""Bilingual welcome email for a person added to AJ CAFM.

Canvas owns the visual layout and accepts plain text only. A blank line starts a
paragraph, and an https link is clickable. The message itself carries both English
and Arabic so the recipient does not depend on a language guess.
"""

from __future__ import annotations

import logging

from ajnkit.email import EmailRefused, send

from src.envs import PUBLIC_URL

logger = logging.getLogger(__name__)

_ROLE_COPY = {
    "administrator": ("Administrator", "مسؤول"),
    "admin": ("Administrator", "مسؤول"),
    "role_super_admin": ("Super administrator", "المسؤول الأعلى"),
    "requester": ("Requester", "مقدّم الطلب"),
    "view_only": ("View only", "اطلاع فقط"),
    "limited_technician": ("Technician", "فنّي"),
    "technician": ("Technician", "فنّي"),
}


def role_copy(role_name: str | None) -> tuple[str, str]:
    key = (role_name or "").strip().lower().replace(" ", "_")
    return _ROLE_COPY.get(key, (role_name or "Member", role_name or "عضو"))


def welcome_message(
    *,
    first_name: str | None,
    role_name: str | None,
    company_name: str | None,
) -> tuple[str, str]:
    """Return the Canvas subject and bilingual plain-text body."""
    name = (first_name or "").strip()
    company = (company_name or "AJ CAFM").strip() or "AJ CAFM"
    role_en, role_ar = role_copy(role_name)
    url = PUBLIC_URL.rstrip("/")
    greeting_en = f"Hello {name}," if name else "Hello,"
    greeting_ar = f"مرحباً {name}،" if name else "مرحباً،"
    subject = "Welcome to AJ CAFM  |  أهلاً بك في نظام إدارة المرافق"
    text = "\n".join(
        [
            greeting_en,
            "",
            f"Your account can now open AJ CAFM for {company}. Sign in with your company account. There is no separate password.",
            "",
            f"Role: {role_en}",
            f"Organisation: {company}",
            "",
            "Open AJ CAFM",
            url,
            "",
            "From here you can:",
            "• Follow work orders from the request through to completion",
            "• Keep assets, locations, and spare parts in one record",
            "• Plan preventive maintenance before equipment fails",
            "• See the work that needs attention today",
            "",
            f"An administrator at {company} added you. If you did not expect this message, you can ignore it. A reply reaches the owner of this application.",
            "",
            "—",
            "",
            greeting_ar,
            "",
            f"يمكن لحسابك الآن فتح نظام AJ CAFM لإدارة المرافق والصيانة لدى {company}. الدخول يتم بحساب المؤسسة، دون كلمة مرور منفصلة.",
            "",
            f"الدور: {role_ar}",
            f"المؤسسة: {company}",
            "",
            "افتح النظام",
            url,
            "",
            "من هنا يمكنك:",
            "• متابعة أوامر العمل من الطلب حتى الإغلاق",
            "• حفظ الأصول والمواقع وقطع الغيار في سجل واحد",
            "• التخطيط للصيانة الوقائية قبل تعطّل المعدات",
            "• رؤية الأعمال التي تحتاج إلى انتباهك اليوم",
            "",
            f"أضافك مسؤول في {company}. إذا لم تكن تتوقع هذه الرسالة، فيمكنك تجاهلها. يصل الرد إلى مالك التطبيق.",
            "",
            "AJ CAFM · Powered by Canvas",
        ]
    )
    return subject, text


def send_welcome(
    email: str,
    *,
    first_name: str | None,
    role_name: str | None,
    company_name: str | None,
) -> bool:
    """Send the welcome message. A refusal is logged and does not undo the account."""
    subject, text = welcome_message(
        first_name=first_name,
        role_name=role_name,
        company_name=company_name,
    )
    try:
        send([email], subject, text)
    except EmailRefused as exc:
        reason = str(exc)
        logger.warning("welcome email was not sent to %s: %s", email, reason)
        if "do not send it again" in reason.lower():
            return True
        return False
    return True
