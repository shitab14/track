import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.db.seed import seed_database
from app.models import (
    Company,
    Team,
    User,
    TeamMembership,
    Measurable,
    Score,
    Rock,
    Milestone,
    Issue,
    Todo,
    Meeting,
    MeetingAttendee,
    MeetingRating,
)

@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_seeding_and_idempotency(memory_db):
    # 1. Run seeder first time
    seed_database(memory_db)

    # Verify counts match seed.json
    assert memory_db.query(Company).count() == 1
    assert memory_db.query(Team).count() == 3
    assert memory_db.query(User).count() == 9
    assert memory_db.query(TeamMembership).count() == 11
    assert memory_db.query(Measurable).count() == 7
    assert memory_db.query(Score).count() == 83
    assert memory_db.query(Rock).count() == 7
    assert memory_db.query(Milestone).count() == 12
    assert memory_db.query(Issue).count() == 9
    assert memory_db.query(Todo).count() == 20
    assert memory_db.query(Meeting).count() == 2
    assert memory_db.query(MeetingAttendee).count() == 10
    assert memory_db.query(MeetingRating).count() == 7

    # Specific entity assertions
    u1 = memory_db.query(User).filter_by(id="u1").first()
    assert u1.name == "Avery Admin"
    assert u1.role == "admin"

    m1 = memory_db.query(Measurable).filter_by(id="m1").first()
    assert m1.name == "New deals closed"
    assert len(m1.scores) == 12

    r1 = memory_db.query(Rock).filter_by(id="r1").first()
    assert len(r1.milestones) == 3

    # 2. Re-run seeder on same database to verify idempotency
    seed_database(memory_db)

    assert memory_db.query(Company).count() == 1
    assert memory_db.query(Team).count() == 3
    assert memory_db.query(User).count() == 9
    assert memory_db.query(Score).count() == 83
    assert memory_db.query(Issue).count() == 9
    assert memory_db.query(Todo).count() == 20
    assert memory_db.query(Meeting).count() == 2
