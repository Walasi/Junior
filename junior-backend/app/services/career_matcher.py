import requests
from app.models.skill import UserSkill, CareerOpportunity
from sqlalchemy.orm import Session

# Mock job API – replace with real (Adzuna, Indeed, etc.)
def fetch_jobs_from_api(skills: list, location: str = None) -> list:
    # Placeholder: return dummy data
    return [
        {
            "title": f"Junior {skill} Developer",
            "company": "TechCorp",
            "url": "https://example.com/job1",
            "description": f"Looking for someone with {skill} skills."
        }
        for skill in skills[:2]
    ]

def update_career_opportunities(db: Session, user_id: int):
    # Get user's skills
    skills = db.query(UserSkill).filter(UserSkill.user_id == user_id).all()
    if not skills:
        return
    skill_names = [s.skill_name for s in skills]
    jobs = fetch_jobs_from_api(skill_names)
    for job in jobs:
        existing = db.query(CareerOpportunity).filter(
            CareerOpportunity.user_id == user_id,
            CareerOpportunity.title == job["title"],
            CareerOpportunity.company == job["company"]
        ).first()
        if not existing:
            opp = CareerOpportunity(
                user_id=user_id,
                title=job["title"],
                company=job.get("company"),
                url=job.get("url"),
                description=job.get("description"),
                matched_skills=", ".join(skill_names)
            )
            db.add(opp)
    db.commit()