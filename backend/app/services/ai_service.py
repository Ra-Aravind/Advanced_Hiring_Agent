"""
ai_service.py

Uses Google Gemini to analyze post-interview feedback and produce
a structured hiring recommendation.

Uses the new google.genai SDK (v1+).
"""

import json
import re
import os

from google import genai
from google.genai import types

from app.config import settings


def analyze_interview_feedback(
    interview_id: str,
    candidate_name: str,
    candidate_skill: str,
    interview_type: str,
    phase1_score: float,
    technical_score: float,
    problem_solving_score: float,
    communication_score: float,
    coding_score: float,
    confidence_score: float,
    overall_score: float,
    strengths: str,
    weaknesses: str,
    technical_comments: str,
    interviewer_recommendation: str,
) -> dict:
    """
    Send interview feedback to Gemini and return a structured analysis.

    Returns:
        {
            "recommendation": "HIRE" | "HOLD" | "REJECT",
            "ai_score": 0-100,
            "summary": "...",
            "strengths": ["...", ...],
            "skill_gaps": ["...", ...],
            "risk_factors": ["...", ...],
            "next_steps": "..."
        }
    """

    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        return {
            "recommendation": "HOLD",
            "ai_score": 0,
            "summary": "AI analysis not available — please set GEMINI_API_KEY in .env",
            "strengths": [],
            "skill_gaps": [],
            "risk_factors": ["Gemini API key not configured"],
            "next_steps": "Add your Gemini API key to .env and restart the server.",
        }

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""You are an expert AI hiring assistant for a tech company.
Analyze the following interview data and provide a structured hiring recommendation.

## Candidate Information
- Name: {candidate_name}
- Primary Skill: {candidate_skill}
- Interview Type: {interview_type}
- Phase 1 Assessment Score: {phase1_score}%

## Interview Scores (out of 10)
- Technical Knowledge   : {technical_score}/10
- Problem Solving       : {problem_solving_score}/10
- Communication         : {communication_score}/10
- Coding Ability        : {coding_score}/10
- Confidence            : {confidence_score}/10
- Overall Score         : {overall_score}/10

## Interviewer's Notes
- Strengths   : {strengths or 'Not provided'}
- Weaknesses  : {weaknesses or 'Not provided'}
- Comments    : {technical_comments or 'Not provided'}
- Human Recommendation: {interviewer_recommendation}

## Your Task
Respond ONLY with a valid JSON object (no markdown, no extra text) in this exact format:
{{
    "recommendation": "HIRE" or "HOLD" or "REJECT",
    "ai_score": <integer 0-100 representing overall candidate score>,
    "summary": "<2-3 sentence executive summary of the candidate>",
    "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
    "skill_gaps": ["<gap 1>", "<gap 2>"],
    "risk_factors": ["<risk 1>"],
    "next_steps": "<One actionable recommendation for the recruiter>"
}}

Base your recommendation on the combined Phase 1 and Phase 2 data.
Be objective and concise. The recommendation should support human decision-making."""

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )

        raw = response.text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        # Ensure all required keys exist
        required = ["recommendation", "ai_score", "summary", "strengths", "skill_gaps", "risk_factors", "next_steps"]
        for key in required:
            if key not in result:
                result[key] = "" if key in ["summary", "next_steps"] else []

        return result

    except json.JSONDecodeError:
        return {
            "recommendation": interviewer_recommendation,
            "ai_score": int(overall_score * 10),
            "summary": f"AI returned an unstructured response. Based on scores, overall rating is {overall_score}/10.",
            "strengths": [strengths] if strengths else [],
            "skill_gaps": [weaknesses] if weaknesses else [],
            "risk_factors": [],
            "next_steps": "Review the interviewer feedback manually.",
        }
    except Exception as e:
        return {
            "recommendation": "HOLD",
            "ai_score": 0,
            "summary": f"AI analysis failed: {str(e)}",
            "strengths": [],
            "skill_gaps": [],
            "risk_factors": [str(e)],
            "next_steps": "Check GEMINI_API_KEY in .env and restart the server.",
        }
