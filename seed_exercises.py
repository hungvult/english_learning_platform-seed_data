"""
Seed exercises for Tiếng Anh A1 — Unit 1, Lesson 1
("Xin chào & Tạm biệt" — Basic Greetings, self-introduction, airplane requests)

Covers all 7 exercise types:
  1. COMPLETE_CONVERSATION
  2. COMPLETE_TRANSLATION
  3. ARRANGE_WORDS
  4. PICTURE_MATCH
  5. TYPE_HEAR
  6. LISTEN_FILL
  7. SPEAK_SENTENCE

Run:
    python seed_exercises.py          (local, needs DATABASE_URL env var)
    docker compose run --rm seeder python seed_exercises.py
"""

import json
import os
import sys
import uuid
from typing import Optional

# ── path bootstrap ──────────────────────────────────────────────────────────
SERVER_PATH = os.environ.get("SERVER_PATH", "/app")
sys.path.insert(0, SERVER_PATH)

from sqlmodel import Session, create_engine, select  # noqa: E402
from app.models.exercise import Exercise, ExerciseType  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.unit import Unit  # noqa: E402
from app.models.lesson import Lesson  # noqa: E402

DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, echo=False)

# ── helpers ──────────────────────────────────────────────────────────────────

def get_or_create_exercise_type(session: Session, name: str) -> ExerciseType:
    obj = session.exec(select(ExerciseType).where(ExerciseType.name == name)).first()
    if obj:
        return obj
    obj = ExerciseType(id=uuid.uuid4(), name=name)
    session.add(obj)
    session.flush()
    print(f"  [seed] ExerciseType created: {name}")
    return obj


def find_lesson(session: Session, course_title: str, unit_order: int, lesson_order: int) -> Optional[Lesson]:
    course = session.exec(select(Course).where(Course.title == course_title)).first()
    if not course:
        print(f"  [seed] Course not found: {course_title}")
        return None

    unit = session.exec(
        select(Unit).where(Unit.course_id == course.id, Unit.order_index == unit_order)
    ).first()
    if not unit:
        print(f"  [seed] Unit not found: order={unit_order}")
        return None

    lesson = session.exec(
        select(Lesson).where(Lesson.unit_id == unit.id, Lesson.order_index == lesson_order)
    ).first()
    if not lesson:
        print(f"  [seed] Lesson not found: order={lesson_order}")
        return None

    return lesson


def upsert_exercise(
    session: Session,
    lesson_id: uuid.UUID,
    exercise_type: ExerciseType,
    question_data: dict | None,
    answer_data: dict,
) -> None:
    """Insert exercise only if no exercise of same type already exists for this lesson."""
    existing = session.exec(
        select(Exercise).where(
            Exercise.lesson_id == lesson_id,
            Exercise.exercise_type_id == exercise_type.id,
        )
    ).first()
    if existing:
        existing.question_data = question_data
        existing.answer_data = answer_data
        session.add(existing)
        print(f"    [seed] Exercise updated: {exercise_type.name}")
        return

    ex = Exercise(
        id=uuid.uuid4(),
        lesson_id=lesson_id,
        exercise_type_id=exercise_type.id,
        question_data=question_data,
        answer_data=answer_data,
    )
    session.add(ex)
    print(f"    [seed] Exercise created: {exercise_type.name}")


# ── exercise definitions ─────────────────────────────────────────────────────

EXERCISES = [
    {
        "type": "COMPLETE_CONVERSATION",
        "question_data": {
            "text": "Can I have some water?",
            "options": [
                {"id": "1", "text": "Yes, here you go."},
                {"id": "2", "text": "I am from Vietnam."},
            ],
        },
        "answer_data": {"correct_option_id": "1"},
    },
    {
        "type": "COMPLETE_TRANSLATION",
        "question_data": {
            "source_sentence": "Chào buổi chiều",
            "text_template": "{0}",
        },
        "answer_data": {"correct_words": ["Good afternoon"]},
    },
    {
        "type": "ARRANGE_WORDS",
        "question_data": {
            "tokens": ["chicken", "I", "like"],
        },
        "answer_data": {"correct_sequence": ["I", "like", "chicken"]},
    },
    {
        "type": "PICTURE_MATCH",
        "question_data": {
            "word": "Coffee",
            "options": [
                {"id": "1", "text": "Cà phê", "image_url": "images/coffee.jpg"},
                {"id": "2", "text": "Trà",    "image_url": "images/tea.jpg"},
            ],
        },
        "answer_data": {"correct_option_id": "1"},
    },
    {
        "type": "TYPE_HEAR",
        "question_data": None,
        "answer_data": {"correct_transcription": "Nice to meet you."},
    },
    {
        "type": "LISTEN_FILL",
        "question_data": {
            "text": "apple juice please",
            "word_bank": [
                {"id": "1", "text": "apple"},
                {"id": "2", "text": "juice"},
                {"id": "3", "text": "please"},
                {"id": "4", "text": "car"},
            ],
        },
        "answer_data": {"correct_sequence_ids": ["1", "2", "3"]},
    },
    {
        "type": "SPEAK_SENTENCE",
        "question_data": None,
        "answer_data": {"expected_text": "Hello, how are you?"},
    },
]


# ── main ────────────────────────────────────────────────────────────────────

def run():
    with Session(engine) as session:
        print("[seed-exercises] Resolving lesson: Tiếng Anh → Unit 1 → Lesson 1")
        lesson = find_lesson(session, "Tiếng Anh", 1, 1)
        if not lesson:
            print("[seed-exercises] Target lesson not found. Run the main seed first.")
            sys.exit(1)

        print(f"[seed-exercises] Lesson found: {lesson.title} (id={lesson.id})")

        for ex_def in EXERCISES:
            ex_type = get_or_create_exercise_type(session, ex_def["type"])
            upsert_exercise(
                session,
                lesson.id,
                ex_type,
                ex_def["question_data"],
                ex_def["answer_data"],
            )

        session.commit()
        print("[seed-exercises] Done.")


if __name__ == "__main__":
    run()
