from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.deps import get_current_user
from pydantic import BaseModel, EmailStr
from typing import Optional, List

router = APIRouter(prefix="/emergency", tags=["Emergency"])

class EmergencyContactCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    relationship: Optional[str] = None
    is_primary: bool = False

class EmergencyContactOut(EmergencyContactCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True

@router.post("/contacts", response_model=EmergencyContactOut)
def add_contact(
    contact: EmergencyContactCreate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    if not contact.phone and not contact.email:
        raise HTTPException(status_code=400, detail="At least phone or email required")
    db_contact = models.emergency_contact.EmergencyContact(
        user_id=current_user.id,
        name=contact.name,
        phone=contact.phone,
        email=contact.email,
        relationship=contact.relationship,
        is_primary=contact.is_primary
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@router.get("/contacts", response_model=List[EmergencyContactOut])
def list_contacts(
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    contacts = db.query(models.emergency_contact.EmergencyContact).filter(
        models.emergency_contact.EmergencyContact.user_id == current_user.id
    ).all()
    return contacts

@router.delete("/contacts/{contact_id}")
def delete_contact(
    contact_id: int,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    contact = db.query(models.emergency_contact.EmergencyContact).filter(
        models.emergency_contact.EmergencyContact.id == contact_id,
        models.emergency_contact.EmergencyContact.user_id == current_user.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted"}

from app.services.alerts import alert_emergency_contacts

class FallReport(BaseModel):
    user_conscious: Optional[bool] = None 
    location: Optional[str] = None
    message: Optional[str] = None 

@router.post("/fall")
def report_fall(
    fall: FallReport,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user)
):
    """Called by mobile app when a fall is detected (or user says 'help')."""
    # Get emergency contacts
    contacts = db.query(models.emergency_contact.EmergencyContact).filter(
        models.emergency_contact.EmergencyContact.user_id == current_user.id
    ).all()
    if not contacts:
        raise HTTPException(status_code=400, detail="No emergency contacts set")

    incident = "fall"
    if not fall.user_conscious:
        incident = "unconscious fall"
    elif fall.message:
        incident = fall.message

    alert_emergency_contacts(
        contacts=contacts,
        incident_type=incident,
        user_name=current_user.username,
        location=fall.location
    )
    return {"message": "Emergency alerts sent", "contacts_alerted": len(contacts)}