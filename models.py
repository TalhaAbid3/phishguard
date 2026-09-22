from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    subscription_plan = Column(String, default="free")
    status = Column(String, default="active")
    verification_token = Column(String, nullable=True)
    domain_verified = Column(String, default="false")
    users = relationship("User", back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    department = Column(String)
    role = Column(String, default="employee")
    hashed_password = Column(String, nullable=True)
    risk_score = Column(Integer, default=0)

    organization = relationship("Organization", back_populates="users")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    body = Column(String, nullable=False)


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    template_id = Column(Integer, ForeignKey("email_templates.id"))
    target_department = Column(String)
    status = Column(String, default="draft")