# Seed Data

Python script that populates the SQL Server database with initial curriculum data.

## What it seeds

| Entity            | Count |
|-------------------|-------|
| Courses           | 2 (English B1, Tiếng Anh A1) |
| Units             | 2 per course → 4 total |
| Lessons           | 6 per unit → 24 total |
| Exercises         | None (not implemented) |
| Users             | 3 (1 admin + 2 learners) |
| UserLessonProgress| 6 sample completions |

### Lesson types per unit
Each unit has 4 × `new knowledge`, 1 × `review`, 1 × `test`.

### Seeded users (all use password `abc123`)

| Username | Email            | Role  | CEFR | XP  | Streak |
|----------|------------------|-------|------|-----|--------|
| admin    | admin@elp.local  | Admin | —    | 0   | 0      |
| alice    | alice@elp.local  | User  | B1   | 340 | 5      |
| bob      | bob@elp.local    | User  | A1   | 80  | 2      |

### Sample progress
- **alice**: lessons 1–4 of *English Unit 1* (scores 100, 95, 90, 85)
- **bob**: lessons 1–2 of *Tiếng Anh Unit 1* (scores 100, 90)

## Running via Docker (recommended)

From the **project root** (where `docker-compose.yml` lives):

```bash
# Start everything (SQL Server, backend, client, seeder)
docker compose up

# Or run only the seeder against an already-running SQL Server
docker compose run --rm seeder
```

The seeder waits for SQL Server to be healthy before inserting data.  
It is **idempotent** — running it multiple times is safe.

## Running locally

```bash
cd seed_data
pip install -r requirements.txt
SERVER_PATH=../server \
DATABASE_URL="mssql+pyodbc://sa:YourStrong!Passw0rd@localhost:1433/EnglishLearning?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes" \
python seed.py
```
