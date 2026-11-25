from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    Text,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base

class Company(Base):
    __tablename__ = "companies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    timezone: Mapped[str] = mapped_column(String, nullable=False, default="America/Chicago")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    teams: Mapped[List["Team"]] = relationship("Team", back_populates="company", cascade="all, delete-orphan")
    users: Mapped[List["User"]] = relationship("User", back_populates="company", cascade="all, delete-orphan")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="teams")
    memberships: Mapped[List["TeamMembership"]] = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")
    measurables: Mapped[List["Measurable"]] = relationship("Measurable", back_populates="team", cascade="all, delete-orphan")
    rocks: Mapped[List["Rock"]] = relationship("Rock", back_populates="team", cascade="all, delete-orphan")
    issues: Mapped[List["Issue"]] = relationship("Issue", back_populates="team", cascade="all, delete-orphan")
    todos: Mapped[List["Todo"]] = relationship("Todo", back_populates="team", cascade="all, delete-orphan")
    meetings: Mapped[List["Meeting"]] = relationship("Meeting", back_populates="team", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    company_id: Mapped[str] = mapped_column(String, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship("Company", back_populates="users")
    memberships: Mapped[List["TeamMembership"]] = relationship("TeamMembership", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'team_member', 'observer')", name="chk_user_role"),
    )


class TeamMembership(Base):
    __tablename__ = "team_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="memberships")
    team: Mapped["Team"] = relationship("Team", back_populates="memberships")

    __table_args__ = (
        UniqueConstraint("user_id", "team_id", name="uq_user_team_membership"),
    )


class Measurable(Base):
    __tablename__ = "measurables"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    goal_type: Mapped[str] = mapped_column(String, nullable=False)
    goal_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    goal_min: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    goal_max: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="measurables")
    owner: Mapped["User"] = relationship("User")
    scores: Mapped[List["Score"]] = relationship("Score", back_populates="measurable", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("goal_type IN ('at_least', 'at_most', 'between', 'exactly')", name="chk_measurable_goal_type"),
        CheckConstraint(
            "(goal_type != 'between' AND goal_value IS NOT NULL) OR (goal_type = 'between' AND goal_min IS NOT NULL AND goal_max IS NOT NULL AND goal_min <= goal_max)",
            name="chk_measurable_goal_definition"
        ),
    )


class Score(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    measurable_id: Mapped[str] = mapped_column(String, ForeignKey("measurables.id", ondelete="CASCADE"), nullable=False)
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    measurable: Mapped["Measurable"] = relationship("Measurable", back_populates="scores")

    __table_args__ = (
        UniqueConstraint("measurable_id", "week_start", name="uq_measurable_week_score"),
    )


class Rock(Base):
    __tablename__ = "rocks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    quarter: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="rocks")
    owner: Mapped["User"] = relationship("User")
    milestones: Mapped[List["Milestone"]] = relationship("Milestone", back_populates="rock", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('on_track', 'off_track', 'complete')", name="chk_rock_status"),
    )


class Milestone(Base):
    __tablename__ = "milestones"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    rock_id: Mapped[str] = mapped_column(String, ForeignKey("rocks.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    rock: Mapped["Rock"] = relationship("Rock", back_populates="milestones")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_measurable_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("measurables.id", ondelete="SET NULL"), nullable=True)
    source_week_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    solved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    team: Mapped["Team"] = relationship("Team", back_populates="issues")
    owner: Mapped["User"] = relationship("User")
    source_measurable: Mapped[Optional["Measurable"]] = relationship("Measurable")
    todos: Mapped[List["Todo"]] = relationship("Todo", back_populates="source_issue")

    __table_args__ = (
        CheckConstraint(
            "(source_measurable_id IS NULL AND source_week_start IS NULL) OR (source_measurable_id IS NOT NULL AND source_week_start IS NOT NULL)",
            name="chk_issue_source_integrity"
        ),
        CheckConstraint(
            "solved_at IS NULL OR (solved_at IS NOT NULL AND resolution_note IS NOT NULL)",
            name="chk_issue_solved_note_required"
        ),
        # Partial unique index ensuring no duplicate unsolved issues for the same measurable & week
        Index(
            "uq_unsolved_source_issue",
            "source_measurable_id",
            "source_week_start",
            unique=True,
            sqlite_where=(solved_at.is_(None) & source_measurable_id.isnot(None)),
            postgresql_where=(solved_at.is_(None) & source_measurable_id.isnot(None))
        ),
    )


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    owner_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    source_issue_id: Mapped[Optional[str]] = mapped_column(String, ForeignKey("issues.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    done_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="todos")
    owner: Mapped["User"] = relationship("User")
    source_issue: Mapped[Optional["Issue"]] = relationship("Issue", back_populates="todos")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    team_id: Mapped[str] = mapped_column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    facilitator_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    current_section: Mapped[str] = mapped_column(String, default="scorecard", nullable=False)
    section_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    team: Mapped["Team"] = relationship("Team", back_populates="meetings")
    facilitator: Mapped["User"] = relationship("User")
    attendees: Mapped[List["MeetingAttendee"]] = relationship("MeetingAttendee", back_populates="meeting", cascade="all, delete-orphan")
    ratings: Mapped[List["MeetingRating"]] = relationship("MeetingRating", back_populates="meeting", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("current_section IN ('scorecard', 'ids', 'conclude', 'ended')", name="chk_meeting_current_section"),
        # Partial unique index ensuring only one active (un-ended) meeting per team
        Index(
            "uq_active_team_meeting",
            "team_id",
            unique=True,
            sqlite_where=(ended_at.is_(None)),
            postgresql_where=(ended_at.is_(None))
        ),
    )


class MeetingAttendee(Base):
    __tablename__ = "meeting_attendees"

    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="attendees")
    user: Mapped["User"] = relationship("User")


class MeetingRating(Base):
    __tablename__ = "meeting_ratings"

    meeting_id: Mapped[str] = mapped_column(String, ForeignKey("meetings.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="ratings")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 10", name="chk_meeting_rating_range"),
    )
