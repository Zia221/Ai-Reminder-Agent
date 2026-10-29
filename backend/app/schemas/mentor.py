
from pydantic import BaseModel, Field


class SkillProfileCreate(BaseModel):
    target_role: str = Field(min_length=2, max_length=150)
    experience_level: str = Field(
        pattern="^(beginner|intermediate|advanced)$"
    )
    current_skills: list[str] = Field(default_factory=list)
    learning_goals: str = Field(min_length=5, max_length=3000)


class SkillProfileRead(SkillProfileCreate):
    id: int


class SkillGapItem(BaseModel):
    skill: str
    current_level: str
    target_level: str
    importance: str
    reason: str


class SkillGapAnalysis(BaseModel):
    target_role: str
    summary: str
    skill_gaps: list[SkillGapItem]


class RoadmapMilestone(BaseModel):
    id: str
    title: str
    description: str
    skills: list[str]
    estimated_days: int
    status: str = "not_started"


class RoadmapCreate(BaseModel):
    title: str
    description: str
    skill_gaps: list[SkillGapItem]
    milestones: list[RoadmapMilestone]


class RoadmapRead(BaseModel):
    id: int
    title: str
    description: str
    skill_gaps: list[SkillGapItem]
    milestones: list[RoadmapMilestone]


class MilestoneUpdate(BaseModel):
    status: str = Field(
        pattern="^(not_started|in_progress|completed)$"
    )


class MentorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class MentorChatResponse(BaseModel):
    reply: str
