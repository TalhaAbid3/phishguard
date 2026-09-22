from pydantic import BaseModel
from typing import Optional

class OrganizationCreate(BaseModel):
    company_name: str
    domain: str
    subscription_plan: Optional[str] = "free"

class OrganizationResponse(BaseModel):
    id: int
    company_name: str
    domain: str
    subscription_plan: str
    status: str

    class Config:
        from_attributes = True

class OrganizationUpdate(BaseModel):
    company_name: Optional[str] = None
    subscription_plan: Optional[str] = None
    status: Optional[str] = None

class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    body: str

class EmailTemplateResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    subject: str
    body: str

    class Config:
        from_attributes = True

class CampaignCreate(BaseModel):
    name: str
    template_id: int
    target_department: Optional[str] = None

class CampaignResponse(BaseModel):
    id: int
    organization_id: int
    name: str
    template_id: int
    target_department: Optional[str]
    status: str

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    organization_id: int
    department: Optional[str] = "General"

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"