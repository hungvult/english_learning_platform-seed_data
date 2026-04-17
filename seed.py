"""
Seed script for English Learning Platform.

Courses            : 2  (English B1 CEFR, Tiếng Anh A1 CEFR)
Units              : 2 per course  → 4 total
Lessons            : 6 per unit   → 24 total
Exercises          : empty (not implemented)
Users              : 1 admin + 2 regular learners
UserLessonProgress : sample completions for the regular users

Default password for all seeded users: abc123

Run via Docker:  docker compose run --rm seeder
Run locally  :   python seed.py
"""

import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta

import bcrypt

# ---------------------------------------------------------------------------
# Retry helper — SQL Server container may not be ready immediately
# ---------------------------------------------------------------------------
MAX_RETRIES = 15
RETRY_DELAY = 5  # seconds


def wait_for_db(engine):
    from sqlalchemy import text
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"[seed] Database ready after {attempt} attempt(s).")
            return
        except Exception as exc:
            print(f"[seed] Attempt {attempt}/{MAX_RETRIES} — DB not ready: {exc}")
            if attempt == MAX_RETRIES:
                print("[seed] Giving up. Is SQL Server running?")
                sys.exit(1)
            time.sleep(RETRY_DELAY)


# ---------------------------------------------------------------------------
# Bootstrap path so we can reuse server models.
# Inside the backend image (elp-backend:dev) the app lives at /app,
# so `from app.models import ...` resolves to /app/app/models/.
# ---------------------------------------------------------------------------
SERVER_PATH = os.environ.get("SERVER_PATH", "/app")
sys.path.insert(0, SERVER_PATH)

from sqlmodel import SQLModel, Session, create_engine, select  # noqa: E402
from app.models import (  # noqa: E402
    Course, Unit, LessonForm, Lesson, User, UserLessonProgress
)

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, echo=False)

# ---------------------------------------------------------------------------
# Wait for SQL Server, then create / migrate tables
# ---------------------------------------------------------------------------
wait_for_db(engine)
print("[seed] Creating tables (if they don't exist)...")
SQLModel.metadata.create_all(engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
DEFAULT_PASSWORD = "abc123"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def upsert_lesson_form(session: Session, name: str) -> LessonForm:
    obj = session.exec(select(LessonForm).where(LessonForm.name == name)).first()
    if obj:
        return obj
    obj = LessonForm(id=uuid.uuid4(), name=name)
    session.add(obj)
    session.flush()
    return obj


def upsert_course(session: Session, title: str, level: str) -> Course:
    obj = session.exec(select(Course).where(Course.title == title)).first()
    if obj:
        return obj
    obj = Course(id=uuid.uuid4(), title=title, expected_cefr_level=level)
    session.add(obj)
    session.flush()
    return obj


def upsert_user(
    session: Session,
    *,
    username: str,
    email: str,
    is_admin: bool = False,
    cefr_level,
    total_xp: int = 0,
    hearts: int = 5,
    gems: int = 0,
    current_streak: int = 0,
    active_course_id=None,
) -> User:
    obj = session.exec(select(User).where(User.email == email)).first()
    if obj:
        if active_course_id is not None and obj.active_course_id != active_course_id:
            obj.active_course_id = active_course_id
            session.add(obj)
            session.flush()
        print(f"  [seed]  User exists: {email}")
        return obj
    obj = User(
        id=uuid.uuid4(),
        username=username,
        email=email,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        is_admin=is_admin,
        cefr_level=cefr_level,
        total_xp=total_xp,
        hearts=hearts,
        gems=gems,
        current_streak=current_streak,
        active_course_id=active_course_id,
        last_activity_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    session.add(obj)
    session.flush()
    print(f"  [seed]  User created: {email} {'(admin)' if is_admin else ''}")
    return obj


def upsert_progress(
    session: Session,
    *,
    user: User,
    lesson: Lesson,
    score: int,
    mistakes: int,
    days_ago: int = 0,
) -> None:
    existing = session.exec(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id == lesson.id,
        )
    ).first()
    if existing:
        return
    progress = UserLessonProgress(
        user_id=user.id,
        lesson_id=lesson.id,
        score=score,
        mistakes=mistakes,
        completed_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )
    session.add(progress)


# ---------------------------------------------------------------------------
# Seed data definition
# ---------------------------------------------------------------------------
COURSES = [
    {
        "title": "English",
        "level": "B1",
        "units": [
            {
                "title": "Unit 1 - Everyday Conversations",
                "order": 1,
                "lessons": [
                    ("Greetings & Introductions",   "new knowledge", 1),
                    ("Asking for Directions",        "new knowledge", 2),
                    ("At the Restaurant",            "new knowledge", 3),
                    ("Shopping Vocabulary",          "new knowledge", 4),
                    ("Review: Conversations",        "review",        5),
                    ("Test: Conversations",          "test",          6),
                ],
            },
            {
                "title": "Unit 2 - Work & Daily Life",
                "order": 2,
                "lessons": [
                    ("Office Vocabulary",            "new knowledge", 1),
                    ("Talking About Jobs",           "new knowledge", 2),
                    ("Daily Routines",               "new knowledge", 3),
                    ("Describing People",            "new knowledge", 4),
                    ("Review: Work & Daily Life",    "review",        5),
                    ("Test: Work & Daily Life",      "test",          6),
                ],
            },
        ],
    },
    {
        "title": "Tiếng Anh",
        "level": "A1",
        "units": [
            {
                "title": "Bai 1 - Chao hoi co ban",
                "order": 1,
                "lessons": [
                    ("Xin chao & Tam biet",         "new knowledge", 1),
                    ("Gioi thieu ban than",          "new knowledge", 2),
                    ("So dem 1-20",                  "new knowledge", 3),
                    ("Mau sac & Hinh dang",          "new knowledge", 4),
                    ("On tap: Chao hoi",             "review",        5),
                    ("Kiem tra: Chao hoi",           "test",          6),
                ],
            },
            {
                "title": "Bai 2 - Gia dinh & Ban be",
                "order": 2,
                "lessons": [
                    ("Thanh vien gia dinh",          "new knowledge", 1),
                    ("Tinh tu mo ta",                "new knowledge", 2),
                    ("Do vat trong nha",             "new knowledge", 3),
                    ("Dong vat & Thien nhien",       "new knowledge", 4),
                    ("On tap: Gia dinh",             "review",        5),
                    ("Kiem tra: Gia dinh",           "test",          6),
                ],
            },
        ],
    },
    {
        "title": "Sample 1",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 2",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 3",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 4",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 5",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 6",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 7",
        "level": "A1",
        "units": [],
    },
    {
        "title": "Sample 8",
        "level": "A1",
        "units": [],
    },
]

LESSON_FORM_NAMES = ["new knowledge", "review", "test"]

# ---------------------------------------------------------------------------
# Users to seed
# ---------------------------------------------------------------------------
USERS = [
    {
        "username": "admin",
        "email": "admin@elp.local",
        "is_admin": True,
        "cefr_level": None,
        "total_xp": 0,
        "hearts": 5,
        "gems": 0,
        "current_streak": 0,
    },
    {
        "username": "alice",
        "email": "alice@elp.local",
        "is_admin": False,
        "cefr_level": "B1",
        "total_xp": 340,
        "hearts": 4,
        "gems": 20,
        "current_streak": 5,
    },
    {
        "username": "bob",
        "email": "bob@elp.local",
        "is_admin": False,
        "cefr_level": "A1",
        "total_xp": 80,
        "hearts": 3,
        "gems": 5,
        "current_streak": 2,
    },
]


# ---------------------------------------------------------------------------
# Run seed
# ---------------------------------------------------------------------------
def run():
    with Session(engine) as session:

        # -- Lesson forms (reference data) -----------------------------------
        print("[seed] Upserting lesson forms...")
        forms = {name: upsert_lesson_form(session, name) for name in LESSON_FORM_NAMES}

        # -- Courses, units, lessons -----------------------------------------
        # Flat map: (course_title, unit_order, lesson_order) -> Lesson
        lesson_map: dict = {}

        for course_def in COURSES:
            course = upsert_course(session, course_def["title"], course_def["level"])
            print(f"[seed] Course: {course.title} ({course.expected_cefr_level})")

            for unit_def in course_def["units"]:
                existing_unit = session.exec(
                    select(Unit).where(
                        Unit.course_id == course.id,
                        Unit.title == unit_def["title"],
                    )
                ).first()

                if existing_unit:
                    unit = existing_unit
                    print(f"  [seed]  Unit exists: {unit.title}")
                else:
                    unit = Unit(
                        id=uuid.uuid4(),
                        course_id=course.id,
                        title=unit_def["title"],
                        order_index=unit_def["order"],
                    )
                    session.add(unit)
                    session.flush()
                    print(f"  [seed]  Unit created: {unit.title}")

                for lesson_title, form_name, order in unit_def["lessons"]:
                    existing_lesson = session.exec(
                        select(Lesson).where(
                            Lesson.unit_id == unit.id,
                            Lesson.title == lesson_title,
                        )
                    ).first()

                    if existing_lesson:
                        lesson = existing_lesson
                        print(f"    [seed]   Lesson exists: {lesson_title}")
                    else:
                        lesson = Lesson(
                            id=uuid.uuid4(),
                            unit_id=unit.id,
                            lesson_form_id=forms[form_name].id,
                            title=lesson_title,
                            order_index=order,
                        )
                        session.add(lesson)
                        session.flush()
                        print(f"    [seed]   Lesson created: {lesson_title}")

                    lesson_map[(course_def["title"], unit_def["order"], order)] = lesson

        # -- Users -----------------------------------------------------------
        print("[seed] Upserting users...")
        seeded_users: dict = {}
        for u in USERS:
            user = upsert_user(session, **u)
            seeded_users[u["username"]] = user

        # Ensure explicit active course (attending course) is set for learners
        if "alice" in seeded_users:
            english_course = session.exec(
                select(Course).where(Course.title == "English")
            ).first()
            if english_course and seeded_users["alice"].active_course_id != english_course.id:
                seeded_users["alice"].active_course_id = english_course.id
                session.add(seeded_users["alice"])

        if "bob" in seeded_users:
            tieng_anh_course = session.exec(
                select(Course).where(Course.title == "Tieng Anh")
            ).first()
            if tieng_anh_course and seeded_users["bob"].active_course_id != tieng_anh_course.id:
                seeded_users["bob"].active_course_id = tieng_anh_course.id
                session.add(seeded_users["bob"])

        # -- User lesson progress --------------------------------------------
        # alice: completed first 4 lessons of English Unit 1 (B1)
        print("[seed] Upserting user lesson progress...")
        alice = seeded_users["alice"]
        for lesson_order in range(1, 5):
            lesson = lesson_map.get(("English", 1, lesson_order))
            if lesson:
                upsert_progress(
                    session,
                    user=alice,
                    lesson=lesson,
                    score=100 - (lesson_order - 1) * 5,   # 100, 95, 90, 85
                    mistakes=lesson_order - 1,             # 0, 1, 2, 3
                    days_ago=4 - lesson_order,
                )

        # bob: completed first 2 lessons of Tieng Anh Unit 1 (A1)
        bob = seeded_users["bob"]
        for lesson_order in range(1, 3):
            lesson = lesson_map.get(("Tieng Anh", 1, lesson_order))
            if lesson:
                upsert_progress(
                    session,
                    user=bob,
                    lesson=lesson,
                    score=100 - (lesson_order - 1) * 10,  # 100, 90
                    mistakes=lesson_order,                 # 1, 2
                    days_ago=2 - lesson_order,
                )

        session.commit()
        print("[seed] Done.")


if __name__ == "__main__":
    run()
