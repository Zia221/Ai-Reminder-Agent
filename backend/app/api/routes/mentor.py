
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.skill_profile import SkillProfile
from app.models.learning_roadmap import LearningRoadmap
from app.schemas.mentor import (
    SkillProfileCreate,
    SkillProfileRead,
    SkillGapAnalysis,
    RoadmapRead,
    MilestoneUpdate,
    MentorChatRequest,
    MentorChatResponse,
)
from app.services.mentor_service import (
    analyze_skill_gaps,
    generate_learning_roadmap,
    mentor_chat,
)

router = APIRouter(
    prefix="/mentor",
    tags=["AI Mentor"],
)


@router.post("/profile", response_model=SkillProfileRead)
def create_or_update_profile(
    payload: SkillProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(SkillProfile).where(
            SkillProfile.user_id == current_user.id
        )
    )

    if profile is None:
        profile = SkillProfile(
            user_id=current_user.id,
            **payload.model_dump(),
        )
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)

    db.commit()
    db.refresh(profile)

    return profile


@router.get("/profile", response_model=SkillProfileRead)
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(SkillProfile).where(
            SkillProfile.user_id == current_user.id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Skill profile not found",
        )

    return profile


@router.post("/analyze", response_model=SkillGapAnalysis)
def analyze_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(SkillProfile).where(
            SkillProfile.user_id == current_user.id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Create your skill profile first",
        )

    try:
        result = analyze_skill_gaps(profile)
        return result
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI skill analysis failed. Check your API key and try again.",
        )


@router.post("/roadmap", response_model=RoadmapRead)
def create_roadmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(SkillProfile).where(
            SkillProfile.user_id == current_user.id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Create your skill profile first",
        )

    try:
        analysis = analyze_skill_gaps(profile)
        roadmap_data = generate_learning_roadmap(
            profile,
            analysis.get("skill_gaps", []),
        )

        roadmap = LearningRoadmap(
            user_id=current_user.id,
            title=roadmap_data["title"],
            description=roadmap_data["description"],
            skill_gaps=analysis.get("skill_gaps", []),
            milestones=roadmap_data.get("milestones", []),
        )

        db.add(roadmap)
        db.commit()
        db.refresh(roadmap)

        return roadmap

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="AI roadmap generation failed. Check your API key and try again.",
        )


@router.get("/roadmap", response_model=RoadmapRead)
def get_roadmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    roadmap = db.scalar(
        select(LearningRoadmap)
        .where(LearningRoadmap.user_id == current_user.id)
        .order_by(LearningRoadmap.created_at.desc())
    )

    if roadmap is None:
        raise HTTPException(
            status_code=404,
            detail="Learning roadmap not found",
        )

    return roadmap


@router.patch(
    "/milestones/{milestone_id}",
    response_model=RoadmapRead,
)
def update_milestone(
    milestone_id: str,
    payload: MilestoneUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    roadmap = db.scalar(
        select(LearningRoadmap)
        .where(LearningRoadmap.user_id == current_user.id)
        .order_by(LearningRoadmap.created_at.desc())
    )

    if roadmap is None:
        raise HTTPException(
            status_code=404,
            detail="Learning roadmap not found",
        )

    milestones = list(roadmap.milestones)

    for milestone in milestones:
        if str(milestone.get("id")) == milestone_id:
            milestone["status"] = payload.status

            roadmap.milestones = milestones
            flag_modified(roadmap, "milestones")
            
            db.commit()
            db.refresh(roadmap)
            
            return roadmap
            
    raise HTTPException(
        status_code=404,
        detail="Milestone not found",
    )


@router.post("/chat", response_model=MentorChatResponse)
def chat_with_mentor(
    payload: MentorChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = db.scalar(
        select(SkillProfile).where(
            SkillProfile.user_id == current_user.id
        )
    )

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Create your skill profile first",
        )

    roadmap = db.scalar(
        select(LearningRoadmap)
        .where(LearningRoadmap.user_id == current_user.id)
        .order_by(LearningRoadmap.created_at.desc())
    )

    try:
        reply = mentor_chat(
            payload.message,
            profile,
            roadmap,
        )

        return {"reply": reply}

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI mentor is unavailable. Check your API key and try again.",
        )
