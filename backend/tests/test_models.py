from decimal import Decimal
from datetime import date
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from app.db.session import Base
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

# Use SQLite in-memory for testing model constraints and relationships
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

def test_company_and_team_creation(db_session):
    company = Company(id="co_1", name="Acme Logistics", timezone="America/Chicago")
    team = Team(id="team_lead", company_id="co_1", name="Leadership")
    user = User(id="u1", company_id="co_1", name="Avery Admin", email="avery@acme.test", role="admin")
    
    db_session.add_all([company, team, user])
    db_session.commit()

    saved_team = db_session.query(Team).filter_by(id="team_lead").first()
    assert saved_team is not None
    assert saved_team.name == "Leadership"
    assert saved_team.company.name == "Acme Logistics"

def test_measurable_and_score_relationship(db_session):
    company = Company(id="co_1", name="Acme Logistics")
    team = Team(id="team_lead", company_id="co_1", name="Leadership")
    user = User(id="u2", company_id="co_1", name="Blake Brooks", email="blake@acme.test", role="team_member")
    measurable = Measurable(
        id="m1",
        team_id="team_lead",
        owner_id="u2",
        name="New deals closed",
        unit="count",
        goal_type="at_least",
        goal_value=Decimal("10.0")
    )
    score = Score(measurable_id="m1", week_start=date(2026, 11, 2), value=Decimal("12.0"))

    db_session.add_all([company, team, user, measurable, score])
    db_session.commit()

    saved_score = db_session.query(Score).filter_by(measurable_id="m1").first()
    assert saved_score.value == Decimal("12.0")
    assert saved_score.measurable.name == "New deals closed"

def test_rock_and_milestones(db_session):
    company = Company(id="co_1", name="Acme Logistics")
    team = Team(id="team_lead", company_id="co_1", name="Leadership")
    user = User(id="u2", company_id="co_1", name="Blake Brooks", email="blake@acme.test", role="team_member")
    rock = Rock(id="r1", team_id="team_lead", owner_id="u2", title="Launch partner portal", quarter="2026-Q4", status="on_track")
    ms = Milestone(id="ms1", rock_id="r1", title="Partner API spec", due_date=date(2026, 10, 15), done=True)

    db_session.add_all([company, team, user, rock, ms])
    db_session.commit()

    saved_rock = db_session.query(Rock).filter_by(id="r1").first()
    assert len(saved_rock.milestones) == 1
    assert saved_rock.milestones[0].title == "Partner API spec"
    assert saved_rock.milestones[0].done is True
