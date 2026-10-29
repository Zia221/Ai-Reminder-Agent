
import json
from uuid import uuid4

from openai import OpenAI

from app.core.config import settings


def get_openai_client():
    api_key = settings.openai_api_key

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return OpenAI(api_key=api_key)


def get_model():
    return settings.openai_model


def analyze_skill_gaps(profile):
    client = get_openai_client()

    prompt = f"""
You are an expert AI career mentor.

Analyze this user's skill profile.

Target role: {profile.target_role}
Experience level: {profile.experience_level}
Current skills: {profile.current_skills}
Learning goals: {profile.learning_goals}

Return ONLY valid JSON using this structure:
{{
  "target_role": "string",
  "summary": "string",
  "skill_gaps": [
    {{
      "skill": "string",
      "current_level": "string",
      "target_level": "string",
      "importance": "high|medium|low",
      "reason": "string"
    }}
  ]
}}

Be realistic. Do not claim the user knows a skill unless it is in their profile.
"""

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {
                "role": "system",
                "content": "Return valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def generate_learning_roadmap(profile, skill_gaps):
    client = get_openai_client()

    prompt = f"""
Create a personalized learning roadmap.

Target role: {profile.target_role}
Experience level: {profile.experience_level}
Current skills: {profile.current_skills}
Learning goals: {profile.learning_goals}
Skill gaps: {skill_gaps}

Return ONLY valid JSON:
{{
  "title": "string",
  "description": "string",
  "milestones": [
    {{
      "id": "string",
      "title": "string",
      "description": "string",
      "skills": ["string"],
      "estimated_days": 7,
      "status": "not_started"
    }}
  ]
}}

Create 4 to 8 milestones.
Keep the roadmap practical and ordered.
"""

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {
                "role": "system",
                "content": "Return valid JSON only.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    for milestone in data.get("milestones", []):
        milestone["id"] = str(uuid4())
        milestone["status"] = "not_started"

    return data


def mentor_chat(message, profile, roadmap):
    client = get_openai_client()

    context = {
        "profile": {
            "target_role": profile.target_role,
            "experience_level": profile.experience_level,
            "current_skills": profile.current_skills,
            "learning_goals": profile.learning_goals,
        },
        "roadmap": roadmap.milestones if roadmap else [],
    }

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly, practical AI learning mentor. "
                    "Use the user's profile and roadmap to personalize "
                    "answers. Explain concepts clearly and encourage "
                    "hands-on practice. Do not claim milestones are "
                    "completed unless their status says completed."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"User context: {context}\\n\\n"
                    f"User question: {message}"
                ),
            },
        ],
    )

    return response.choices[0].message.content
