from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.db.database import Base


class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, nullable=True)  # reference to user-service user id (logical)
    invite_code = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OrgUnit(Base):
    __tablename__ = "org_units"
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    parent_id = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OrgMember(Base):
    __tablename__ = "org_members"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # reference to user-service user id
    org_unit_id = Column(Integer, nullable=False)
    position = Column(String, nullable=True)
    manager_id = Column(Integer, nullable=True)  # direct manager (user id)
