from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import Organization, User, EmailTemplate, Campaign
from schemas import (
    OrganizationCreate, OrganizationResponse, OrganizationUpdate,
    EmailTemplateCreate, EmailTemplateResponse,
    CampaignCreate, CampaignResponse
)
from typing import List
from fastapi import UploadFile, File
import pandas as pd
import io
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from auth import hash_password, verify_password, create_access_token
from schemas import UserRegister, UserLogin, TokenResponse
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"message": "PhishGuard API is running"}

@app.post("/test-user")
def create_test_user(db: Session = Depends(get_db)):
    # Pehle ek test organization banate hain agar exist nahi karti
    org = db.query(Organization).filter(Organization.domain == "testcompany.com").first()
    if not org:
        org = Organization(
            company_name="Test Company",
            domain="testcompany.com",
            subscription_plan="free",
            status="active"
        )
        db.add(org)
        db.commit()
        db.refresh(org)

    # Ab testing user banate hain
    test_user = User(
        organization_id=org.id,
        name="Test User",
        email="testuser@testcompany.com",
        department="IT",
        role="employee",
        risk_score=0
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    return {"message": "Testing user created successfully", "user_id": test_user.id, "email": test_user.email}
# Naya organization create karo
@app.post("/organizations", response_model=OrganizationResponse)
def create_organization(org: OrganizationCreate, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.domain == org.domain).first()
    if existing:
        return existing

    new_org = Organization(
        company_name=org.company_name,
        domain=org.domain,
        subscription_plan=org.subscription_plan,
        status="active"
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

# Saari organizations ki list dekho
@app.get("/organizations", response_model=List[OrganizationResponse])
def list_organizations(db: Session = Depends(get_db)):
    return db.query(Organization).all()

# Ek specific organization dekho (ID se)
@app.get("/organizations/{org_id}", response_model=OrganizationResponse)
def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}
    return org
# Organization update karo
@app.put("/organizations/{org_id}", response_model=OrganizationResponse)
def update_organization(org_id: int, updates: OrganizationUpdate, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    if updates.company_name is not None:
        org.company_name = updates.company_name
    if updates.subscription_plan is not None:
        org.subscription_plan = updates.subscription_plan
    if updates.status is not None:
        org.status = updates.status

    db.commit()
    db.refresh(org)
    return org

# Organization delete karo
@app.delete("/organizations/{org_id}")
def delete_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    db.delete(org)
    db.commit()
    return {"message": f"Organization {org_id} deleted successfully"}
@app.post("/organizations/{org_id}/import-users")
async def import_users(org_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    contents = await file.read()
    if not contents:
        return {"error": "Uploaded file is empty. Please select the file again."}

    df = pd.read_csv(io.StringIO(contents.decode('utf-8')))

    added_users = []
    skipped_users = []

    for _, row in df.iterrows():
        existing = db.query(User).filter(User.email == row['email']).first()
        if existing:
            skipped_users.append(row['email'])
            continue

        new_user = User(
            organization_id=org_id,
            name=row['name'],
            email=row['email'],
            department=row.get('department', 'General'),
            role=row.get('role', 'employee'),
            risk_score=0
        )
        db.add(new_user)
        added_users.append(row['email'])

    db.commit()

    return {
        "message": "Import complete",
        "added_count": len(added_users),
        "added_users": added_users,
        "skipped_count": len(skipped_users),
        "skipped_users": skipped_users
    }
    db.commit()
    return {
        "message": "Import complete",
        "added_count": len(added_users),
        "added_users": added_users,
        "skipped_count": len(skipped_users),
        "skipped_users": skipped_users
    }
@app.get("/organizations/{org_id}/users")
def list_users(org_id: int, db: Session = Depends(get_db)):
    users = db.query(User).filter(User.organization_id == org_id).all()
    return users
# Email Template banao
@app.post("/organizations/{org_id}/templates", response_model=EmailTemplateResponse)
def create_template(org_id: int, template: EmailTemplateCreate, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    new_template = EmailTemplate(
        organization_id=org_id,
        name=template.name,
        subject=template.subject,
        body=template.body
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

# Organization ke saare templates dekho
@app.get("/organizations/{org_id}/templates", response_model=List[EmailTemplateResponse])
def list_templates(org_id: int, db: Session = Depends(get_db)):
    return db.query(EmailTemplate).filter(EmailTemplate.organization_id == org_id).all()

# Campaign banao
@app.post("/organizations/{org_id}/campaigns", response_model=CampaignResponse)
def create_campaign(org_id: int, campaign: CampaignCreate, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    template = db.query(EmailTemplate).filter(EmailTemplate.id == campaign.template_id).first()
    if not template:
        return {"error": "Template not found"}

    new_campaign = Campaign(
        organization_id=org_id,
        name=campaign.name,
        template_id=campaign.template_id,
        target_department=campaign.target_department,
        status="draft"
    )
    db.add(new_campaign)
    db.commit()
    db.refresh(new_campaign)
    return new_campaign

# Organization ke saare campaigns dekho
@app.get("/organizations/{org_id}/campaigns", response_model=List[CampaignResponse])
def list_campaigns(org_id: int, db: Session = Depends(get_db)):
    return db.query(Campaign).filter(Campaign.organization_id == org_id).all()
@app.get("/organizations/{org_id}/analytics")
def get_analytics(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    total_users = db.query(User).filter(User.organization_id == org_id).count()
    total_templates = db.query(EmailTemplate).filter(EmailTemplate.organization_id == org_id).count()
    total_campaigns = db.query(Campaign).filter(Campaign.organization_id == org_id).count()

    draft_campaigns = db.query(Campaign).filter(
        Campaign.organization_id == org_id,
        Campaign.status == "draft"
    ).count()

    active_campaigns = db.query(Campaign).filter(
        Campaign.organization_id == org_id,
        Campaign.status == "active"
    ).count()

    # Department wise employee count
    from sqlalchemy import func
    dept_counts = db.query(
        User.department, func.count(User.id)
    ).filter(User.organization_id == org_id).group_by(User.department).all()

    department_breakdown = {dept: count for dept, count in dept_counts}

    return {
        "organization": org.company_name,
        "total_employees": total_users,
        "total_email_templates": total_templates,
        "total_campaigns": total_campaigns,
        "draft_campaigns": draft_campaigns,
        "active_campaigns": active_campaigns,
        "department_breakdown": department_breakdown
    }
import secrets

# Domain verification start karo (token generate karo)
@app.post("/organizations/{org_id}/verify-domain/start")
def start_domain_verification(org_id: int, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    token = secrets.token_hex(16)
    org.verification_token = token
    db.commit()
    db.refresh(org)

    return {
        "message": "Add this TXT record to your DNS to verify your domain",
        "record_type": "TXT",
        "host": f"_phishguard.{org.domain}",
        "value": f"phishguard-verification={token}"
    }

# Domain verification check karo
@app.post("/organizations/{org_id}/verify-domain/check")
def check_domain_verification(org_id: int, db: Session = Depends(get_db)):
    import dns.resolver

    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {"error": "Organization not found"}

    if not org.verification_token:
        return {"error": "Verification not started yet. Call /verify-domain/start first."}

    try:
        records = dns.resolver.resolve(f"_phishguard.{org.domain}", "TXT")
        expected_value = f"phishguard-verification={org.verification_token}"

        for record in records:
            if expected_value in str(record):
                org.domain_verified = "true"
                db.commit()
                return {"message": "Domain verified successfully!", "verified": True}

        return {"message": "TXT record found but token does not match", "verified": False}

    except Exception as e:
        return {"message": f"Could not verify: DNS record not found yet. Error: {str(e)}", "verified": False}
    # Register karo
@app.post("/auth/register")
def register(user: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        return {"error": "Email already registered"}

    org = db.query(Organization).filter(Organization.id == user.organization_id).first()
    if not org:
        return {"error": "Organization not found"}

    new_user = User(
        organization_id=user.organization_id,
        name=user.name,
        email=user.email,
        department=user.department,
        role="employee",
        risk_score=0,
        hashed_password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user_id": new_user.id, "email": new_user.email}

# Login karo
@app.post("/auth/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()

    if not user or not user.hashed_password:
        return {"error": "Invalid email or password"}

    if not verify_password(credentials.password, user.hashed_password):
        return {"error": "Invalid email or password"}

    token = create_access_token({"sub": user.email, "user_id": user.id})
    return {"access_token": token, "token_type": "bearer"}