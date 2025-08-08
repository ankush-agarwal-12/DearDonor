from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.organization import OrganizationCreate, OrganizationResponse
from app.core.security import hash_password, verify_password, create_access_token, get_current_org
from app.models.organization import Organization
from app.core.config import get_settings
from pydantic import BaseModel
from app.models.email_template import OrganizationEmailTemplate
from fastapi import Body
from app.core.security import decode_supabase_jwt
from typing import Optional, Dict

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/register", response_model=TokenResponse)
def register(org: OrganizationCreate, db: Session = Depends(get_db)):
    existing = db.query(Organization).filter(Organization.email == org.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization already registered")
    hashed_pwd = hash_password(org.password)
    new_org = Organization(
        name=org.name,
        email=org.email,
        password_hash=hashed_pwd,
        slug=org.slug,
        office_address=org.office_address,
        phone=org.phone,
        website=org.website,
        registration_number=org.registration_number,
        pan_number=org.pan_number,
        csr_number=org.csr_number,
        tax_exemption_number=org.tax_exemption_number,
        social_media=org.social_media,
        signature_holder=org.signature_holder,
        status=org.status,
        email_verified=org.email_verified
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    # Add default email templates
    default_template = """Dear {{Name}},\n\nThank you for your generous donation of Rs. {{Amount}} /- ({{AmountInWords}}) to {{orgName}}. Your contribution will help us make a difference in the lives of stray animals.\n\nReceipt Details:\n- Receipt Number: {{receiptNumber}}\n- Date: {{Date}}\n- Purpose: {{Purpose}}\n- Payment Mode: {{PaymentMode}}\n\nThe official receipt is attached to this email.\n\nBest regards,\n{{orgDepartment}}\n{{orgName}}\n\nContact us:\n{{orgEmail}} | {{orgPhone}}\n{{orgSocial}}"""
    default_subject = "Donation Receipt - Thank You, {{Name}}"
    db.add(OrganizationEmailTemplate(
        organization_id=new_org.id,
        template_type="receipt_template",
        content=default_template,
        is_active=True
    ))
    db.add(OrganizationEmailTemplate(
        organization_id=new_org.id,
        template_type="receipt_subject",
        content=default_subject,
        is_active=True
    ))
    db.commit()
    token = create_access_token({"org_id": str(new_org.id)})
    return TokenResponse(access_token=token)

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.email == data.email).first()
    if not org or not verify_password(data.password, org.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"org_id": str(org.id)})
    return TokenResponse(access_token=token)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/change-password", status_code=204)
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    org_id: str = Depends(get_current_org),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org or not verify_password(data.old_password, org.password_hash):
        raise HTTPException(status_code=401, detail="Invalid current password")
    org.password_hash = hash_password(data.new_password)
    db.commit()
    return

@router.get("/me", response_model=OrganizationResponse)
def get_me(db: Session = Depends(get_db), org_id: str = Depends(get_current_org)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

# Phase 2: Supabase login token exchange
class ExchangeRequest(BaseModel):
    supabase_token: str

@router.post("/exchange", response_model=TokenResponse)
def exchange_supabase_token(payload: ExchangeRequest = Body(...), db: Session = Depends(get_db)):
    """Accept a Supabase JWT, verify it, map to an organization, and issue internal JWT.

    Mapping preference:
    1) If your organizations table has an auth_user_id column (planned), match on it.
    2) Fallback: Match by email claim from Supabase (preferred claim: email).
    """
    claims = decode_supabase_jwt(payload.supabase_token)
    supabase_user_id = claims.get("sub")
    supabase_email = claims.get("email")

    if not supabase_user_id and not supabase_email:
        raise HTTPException(status_code=401, detail="Supabase token missing required claims")

    org = None

    # Try auth_user_id column if it exists in DB (safe check by attribute on model)
    if hasattr(Organization, "auth_user_id") and supabase_user_id:
        try:
            org = db.query(Organization).filter(getattr(Organization, "auth_user_id") == supabase_user_id).first()
        except Exception:
            org = None

    # Fallback to email match
    if org is None and supabase_email:
        org = db.query(Organization).filter(Organization.email == supabase_email).first()

    if org is None:
        raise HTTPException(status_code=404, detail="No organization linked to this Supabase user")

    token = create_access_token({"org_id": str(org.id)})
    return TokenResponse(access_token=token)

# New Supabase-based login endpoint
class SupabaseLoginRequest(BaseModel):
    email: str
    password: str

@router.post("/supabase-login", response_model=TokenResponse)
def supabase_login(data: SupabaseLoginRequest, db: Session = Depends(get_db)):
    """
    Login via Supabase Auth and return backend JWT.
    
    This endpoint:
    1. Authenticates with Supabase Auth
    2. Gets Supabase JWT
    3. Exchanges it for backend JWT
    4. Returns backend JWT (same format as /auth/login)
    """
    import requests
    
    # Step 1: Authenticate with Supabase
    supabase_auth_url = f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    auth_data = {
        "email": data.email,
        "password": data.password
    }
    
    try:
        response = requests.post(supabase_auth_url, headers=headers, json=auth_data)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        supabase_response = response.json()
        supabase_token = supabase_response.get("access_token")
        
        if not supabase_token:
            raise HTTPException(status_code=401, detail="Failed to get Supabase token")
        
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    # Step 2: Exchange Supabase JWT for backend JWT (reuse existing logic)
    claims = decode_supabase_jwt(supabase_token)
    supabase_user_id = claims.get("sub")
    supabase_email = claims.get("email")

    if not supabase_user_id and not supabase_email:
        raise HTTPException(status_code=401, detail="Invalid token claims")

    org = None

    # Try auth_user_id column first
    if hasattr(Organization, "auth_user_id") and supabase_user_id:
        try:
            org = db.query(Organization).filter(getattr(Organization, "auth_user_id") == supabase_user_id).first()
        except Exception:
            org = None

    # Fallback to email match
    if org is None and supabase_email:
        org = db.query(Organization).filter(Organization.email == supabase_email).first()

    if org is None:
        raise HTTPException(status_code=404, detail="No organization linked to this account")

    # Step 3: Return backend JWT (same format as original /auth/login)
    token = create_access_token({"org_id": str(org.id)})
    return TokenResponse(access_token=token)

# Phase 3: Supabase-based registration endpoint
class SupabaseRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    slug: Optional[str] = None
    office_address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    registration_number: Optional[str] = None
    pan_number: Optional[str] = None
    csr_number: Optional[str] = None
    tax_exemption_number: Optional[str] = None
    tax_exemption_12a: Optional[str] = None
    tax_exemption_80g: Optional[str] = None
    social_media: Optional[Dict] = None
    signature_holder: Optional[Dict] = None

@router.post("/supabase-register", response_model=TokenResponse)
def supabase_register(data: SupabaseRegisterRequest, db: Session = Depends(get_db)):
    """
    Register via Supabase Auth and create organization profile.
    
    Phase 3 implementation:
    1. Create user in Supabase Auth
    2. Create organization profile with auth_user_id link
    3. Add default email templates
    4. Return backend JWT (same format as /auth/register)
    """
    import requests
    import re
    
    # Check if organization with this email already exists
    existing = db.query(Organization).filter(Organization.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Organization already registered")
    
    # Generate slug if not provided
    if not data.slug:
        # Convert to lowercase, replace spaces with hyphens, remove special chars
        slug = re.sub(r'[^a-z0-9\s-]', '', data.name.lower())
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug)
        data.slug = slug[:50]  # Limit length
    
    # Ensure unique slug
    base_slug = data.slug
    counter = 1
    while True:
        slug_check = db.query(Organization).filter(Organization.slug == data.slug).first()
        if not slug_check:
            break
        data.slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Step 1: Create user in Supabase Auth using service role key
    supabase_signup_url = f"{settings.SUPABASE_URL}/auth/v1/admin/users"
    headers = {
        "apikey": settings.SUPABASE_SERVICE_KEY,  # Service role for admin operations
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }
    
    user_data = {
        "email": data.email,
        "password": data.password,
        "email_confirm": True,  # Auto-confirm email for smooth UX
        "user_metadata": {
            "organization_name": data.name,
            "role": "organization_admin"
        }
    }
    
    try:
        response = requests.post(supabase_signup_url, headers=headers, json=user_data)
        if response.status_code not in [200, 201]:
            error_detail = response.json().get("msg", "Failed to create user")
            raise HTTPException(status_code=400, detail=f"Registration failed: {error_detail}")
        
        supabase_user = response.json()
        supabase_user_id = supabase_user.get("id")
        
        if not supabase_user_id:
            raise HTTPException(status_code=500, detail="Failed to get user ID from Supabase")
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail="Authentication service unavailable")
    
    try:
        # Step 2: Create organization profile with auth_user_id link
        new_org = Organization(
            name=data.name,
            email=data.email,
            password_hash="",  # Phase 4: Stop writing password_hash (empty for now)
            slug=data.slug,
            office_address=data.office_address,
            phone=data.phone,
            website=data.website,
            registration_number=data.registration_number,
            pan_number=data.pan_number,
            csr_number=data.csr_number,
            tax_exemption_number=data.tax_exemption_number,
            tax_exemption_12a=data.tax_exemption_12a,
            tax_exemption_80g=data.tax_exemption_80g,
            social_media=data.social_media or {},
            signature_holder=data.signature_holder or {},
            status="active",
            email_verified=True,  # Trusting Supabase's email verification
            auth_user_id=supabase_user_id  # Link to Supabase user
        )
        
        db.add(new_org)
        db.commit()
        db.refresh(new_org)
        
        # Step 3: Add default email templates (same logic as original)
        default_template = """Dear {{Name}},\n\nThank you for your generous donation of Rs. {{Amount}} /- ({{AmountInWords}}) to {{orgName}}. Your contribution will help us make a difference in the lives of stray animals.\n\nReceipt Details:\n- Receipt Number: {{receiptNumber}}\n- Date: {{Date}}\n- Purpose: {{Purpose}}\n- Payment Mode: {{PaymentMode}}\n\nThe official receipt is attached to this email.\n\nBest regards,\n{{orgDepartment}}\n{{orgName}}\n\nContact us:\n{{orgEmail}} | {{orgPhone}}\n{{orgSocial}}"""
        default_subject = "Donation Receipt - Thank You, {{Name}}"
        
        db.add(OrganizationEmailTemplate(
            organization_id=new_org.id,
            template_type="receipt_template",
            content=default_template,
            is_active=True
        ))
        db.add(OrganizationEmailTemplate(
            organization_id=new_org.id,
            template_type="receipt_subject",
            content=default_subject,
            is_active=True
        ))
        db.commit()
        
        # Step 4: Return backend JWT (same format as original /auth/register)
        token = create_access_token({"org_id": str(new_org.id)})
        return TokenResponse(access_token=token)
        
    except Exception as e:
        # Rollback: Delete Supabase user if organization creation fails
        try:
            delete_url = f"{settings.SUPABASE_URL}/auth/v1/admin/users/{supabase_user_id}"
            requests.delete(delete_url, headers=headers)
        except:
            pass  # Best effort cleanup
        
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create organization: {str(e)}")

# Password Reset Endpoints
class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    access_token: str  # Reset token from Supabase
    new_password: str

@router.post("/forgot-password", status_code=200)
def forgot_password(data: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset via Supabase Auth.
    
    This endpoint:
    1. Checks if email exists in our organizations
    2. Sends reset email via Supabase Auth
    3. Returns success message
    """
    import requests
    
    # Check if organization with this email exists
    org = db.query(Organization).filter(Organization.email == data.email).first()
    if not org:
        # Return success even if email doesn't exist (security best practice)
        return {"message": "If the email exists, a password reset link has been sent"}
    
    # Check if organization has auth_user_id (is using Supabase auth)
    if not hasattr(org, 'auth_user_id') or not org.auth_user_id:
        # Organization is still using old auth system
        raise HTTPException(
            status_code=400, 
            detail="Password reset not available. Please contact support or use the legacy login."
        )
    
    # Send password reset email via Supabase
    reset_url = f"{settings.SUPABASE_URL}/auth/v1/recover"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    
    # You can customize the redirect URL for your frontend
    redirect_url = "http://localhost:8081/reset-password"  # Change to your frontend URL
    
    reset_data = {
        "email": data.email,
        "options": {
            "redirectTo": redirect_url
        }
    }
    
    try:
        response = requests.post(reset_url, headers=headers, json=reset_data)
        
        # Supabase returns 200 even if email doesn't exist (security feature)
        if response.status_code == 200:
            return {"message": "If the email exists, a password reset link has been sent"}
        else:
            raise HTTPException(status_code=503, detail="Password reset service unavailable")
            
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Password reset service unavailable")

@router.post("/reset-password", status_code=200)
def reset_password(data: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Complete password reset using Supabase reset token.
    
    This endpoint:
    1. Verifies the reset token with Supabase
    2. Updates the password via Supabase Admin API
    3. Returns success message
    """
    import requests
    
    # Verify the reset token and update password via Supabase
    update_url = f"{settings.SUPABASE_URL}/auth/v1/user"
    headers = {
        "apikey": settings.SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {data.access_token}",  # Reset token
        "Content-Type": "application/json"
    }
    
    update_data = {
        "password": data.new_password
    }
    
    try:
        response = requests.put(update_url, headers=headers, json=update_data)
        
        if response.status_code == 200:
            return {"message": "Password has been reset successfully"}
        elif response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid or expired reset token")
        else:
            raise HTTPException(status_code=400, detail="Failed to reset password")
            
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Password reset service unavailable") 