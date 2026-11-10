"""
AI Service using Ollama (local LLM).
Handles:
1. Question generation from recruiter commands
2. Subjective/code answer evaluation
3. Result narrative (strengths, weaknesses, feedback)
Falls back to rule-based logic if Ollama is unavailable.
"""
import json
import re
import httpx
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

OLLAMA_API = f"{settings.OLLAMA_BASE_URL}/api/generate"
OLLAMA_CHAT = f"{settings.OLLAMA_BASE_URL}/api/chat"
OLLAMA_TAGS = f"{settings.OLLAMA_BASE_URL}/api/tags"


async def _ollama_available() -> bool:
    """Check if Ollama server is running."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(OLLAMA_TAGS)
            return resp.status_code == 200
    except Exception:
        return False


async def _ollama_generate(prompt: str, model: Optional[str] = None) -> str:
    """Send a prompt to Ollama and return the response text."""
    chosen_model = model or settings.OLLAMA_MODEL
    payload = {
        "model": chosen_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9,
            "num_predict": 4096,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(OLLAMA_API, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except Exception as e:
        logger.error(f"Ollama generate error: {e}")
        # Try fallback model
        if chosen_model != settings.OLLAMA_FALLBACK_MODEL:
            return await _ollama_generate(prompt, settings.OLLAMA_FALLBACK_MODEL)
        raise


def _extract_json(text: str) -> Optional[dict | list]:
    """Extract JSON from LLM response (may have markdown fences)."""
    # Try to find JSON block
    patterns = [
        r"```json\s*([\s\S]+?)\s*```",
        r"```\s*([\s\S]+?)\s*```",
        r"(\{[\s\S]+\})",
        r"(\[[\s\S]+\])",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
    # Try parsing the whole response
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# ==============================================================
# FEATURE 1: Parse Recruiter Command → Assessment Config
# ==============================================================

COMMAND_PARSE_PROMPT = """You are an AI assistant for a technical recruitment platform.
Parse the recruiter's command and extract assessment configuration.

Command: "{command}"

Return a JSON object with exactly these fields:
{{
  "technology": "one of: Python, Java, C, C++, HTML, CSS, Power BI",
  "title": "descriptive assessment title",
  "total_questions": <integer>,
  "difficulty_mix": {{
    "beginner": <integer>,
    "intermediate": <integer>,
    "advanced": <integer>
  }},
  "duration_minutes": <integer, default 60>,
  "passing_score": <integer 1-100, default 60>,
  "instructions": "brief instructions for candidates"
}}

Rules:
- difficulty_mix must sum to total_questions
- If only one difficulty mentioned, put all questions there
- If duration not specified, use 2 minutes per question
- Return ONLY valid JSON, no other text
"""


async def parse_recruiter_command(command: str) -> dict:
    """Parse natural language command into assessment config."""
    if not await _ollama_available():
        return _fallback_parse_command(command)

    prompt = COMMAND_PARSE_PROMPT.format(command=command)
    try:
        response = await _ollama_generate(prompt)
        parsed = _extract_json(response)
        if parsed and isinstance(parsed, dict):
            return {"success": True, "config": parsed, "raw_response": response}
        else:
            logger.warning(f"Could not parse JSON from Ollama response: {response}")
            return _fallback_parse_command(command)
    except Exception as e:
        logger.error(f"Command parse error: {e}")
        return _fallback_parse_command(command)


def _fallback_parse_command(command: str) -> dict:
    """Rule-based fallback when Ollama is unavailable."""
    cmd_lower = command.lower()

    # Technology detection
    tech_map = {
        "python": "Python", "java": "Java", "c++": "C++", "cpp": "C++",
        " c ": "C", "html": "HTML", "css": "CSS", "power bi": "Power BI", "powerbi": "Power BI",
    }
    technology = "Python"
    for key, val in tech_map.items():
        if key in cmd_lower:
            technology = val
            break

    # Total questions
    nums = re.findall(r"\b(\d+)\s*(?:question|q\b)", cmd_lower)
    total = int(nums[0]) if nums else 20

    # Difficulty detection
    beginner = intermediate = advanced = 0
    b_match = re.search(r"(\d+)\s*beginner", cmd_lower)
    i_match = re.search(r"(\d+)\s*intermediate", cmd_lower)
    a_match = re.search(r"(\d+)\s*advanced", cmd_lower)

    if b_match:
        beginner = int(b_match.group(1))
    if i_match:
        intermediate = int(i_match.group(1))
    if a_match:
        advanced = int(a_match.group(1))

    if beginner + intermediate + advanced == 0:
        if "beginner" in cmd_lower:
            beginner = total
        elif "advanced" in cmd_lower:
            advanced = total
        else:
            intermediate = total

    # Normalize to total
    total_mix = beginner + intermediate + advanced
    if total_mix != total and total_mix > 0:
        intermediate = total - beginner - advanced

    config = {
        "technology": technology,
        "title": f"{technology} Technical Assessment",
        "total_questions": total,
        "difficulty_mix": {"beginner": beginner, "intermediate": intermediate, "advanced": advanced},
        "duration_minutes": max(30, total * 2),
        "passing_score": 60,
        "instructions": f"Complete all {total} questions within the allocated time. Read each question carefully before answering.",
    }
    return {"success": True, "config": config, "raw_response": "Fallback rule-based parsing used (Ollama unavailable)"}


# ==============================================================
# FEATURE 2: Generate Questions using AI
# ==============================================================

QUESTION_GEN_PROMPT = """You are an expert technical question generator for software recruitment.

Generate {count} unique {difficulty} level {question_type} questions for {technology}.

Requirements:
- All questions must be appropriate for {difficulty} level developers
- For MCQ: provide exactly 4 options (A, B, C, D) with exactly one correct answer
- For short_answer/code: provide a model answer and evaluation criteria
- Questions should test practical knowledge, not just theory
- Be specific and unambiguous

Return a JSON array of question objects. Each object must have:
{{
  "question_text": "the question",
  "question_type": "{question_type}",
  "difficulty": "{difficulty}",
  "options": [  // only for mcq and true_false
    {{"label": "A", "text": "option text", "is_correct": false}},
    {{"label": "B", "text": "option text", "is_correct": true}},
    {{"label": "C", "text": "option text", "is_correct": false}},
    {{"label": "D", "text": "option text", "is_correct": false}}
  ],
  "correct_answer": "the correct answer or explanation for short/code",
  "explanation": "why this is correct and others wrong",
  "tags": ["tag1", "tag2"],
  "max_score": 10
}}

Return ONLY valid JSON array, no other text.
"""


async def generate_questions(
    technology: str,
    difficulty: str,
    count: int,
    question_type: str = "mcq",
) -> list[dict]:
    """Generate questions using Ollama LLM."""
    if not await _ollama_available():
        return []

    prompt = QUESTION_GEN_PROMPT.format(
        count=count,
        difficulty=difficulty,
        question_type=question_type,
        technology=technology,
    )
    try:
        response = await _ollama_generate(prompt)
        parsed = _extract_json(response)
        if isinstance(parsed, list):
            return parsed[:count]
        return []
    except Exception as e:
        logger.error(f"Question generation error: {e}")
        return []


# ==============================================================
# FEATURE 3: Evaluate Subjective / Code Answers
# ==============================================================

EVAL_PROMPT = """You are an expert technical interviewer evaluating a candidate's answer.

Technology: {technology}
Difficulty: {difficulty}
Question: {question}
Model Answer / Criteria: {correct_answer}
Candidate's Answer: {candidate_answer}

Evaluate the answer using this rubric:
- Technical Accuracy (40%): Is the answer technically correct?
- Completeness (30%): Does it cover all key aspects?
- Clarity (20%): Is it clear and well-explained?
- Best Practices (10%): Does it follow good practices?

Maximum score: {max_score}

Return a JSON object:
{{
  "score": <number 0 to {max_score}>,
  "is_correct": <true if score >= 70% of max>,
  "feedback": "specific, constructive feedback in 2-3 sentences",
  "accuracy_score": <0-40>,
  "completeness_score": <0-30>,
  "clarity_score": <0-20>,
  "best_practices_score": <0-10>
}}

Return ONLY valid JSON, no other text.
"""


async def evaluate_subjective_answer(
    technology: str,
    difficulty: str,
    question: str,
    correct_answer: str,
    candidate_answer: str,
    max_score: int = 10,
) -> dict:
    """Use Ollama to score a subjective or code answer."""
    if not candidate_answer or not candidate_answer.strip():
        return {
            "score": 0,
            "is_correct": False,
            "feedback": "No answer provided.",
        }

    if not await _ollama_available():
        return _fallback_evaluate(candidate_answer, correct_answer, max_score)

    prompt = EVAL_PROMPT.format(
        technology=technology,
        difficulty=difficulty,
        question=question,
        correct_answer=correct_answer,
        candidate_answer=candidate_answer,
        max_score=max_score,
    )
    try:
        response = await _ollama_generate(prompt)
        parsed = _extract_json(response)
        if parsed and isinstance(parsed, dict):
            # Clamp score
            parsed["score"] = max(0, min(float(parsed.get("score", 0)), max_score))
            return parsed
        return _fallback_evaluate(candidate_answer, correct_answer, max_score)
    except Exception as e:
        logger.error(f"Evaluation error: {e}")
        return _fallback_evaluate(candidate_answer, correct_answer, max_score)


def _fallback_evaluate(candidate_answer: str, correct_answer: str, max_score: int) -> dict:
    """Lenient keyword-based evaluation when Ollama is unavailable."""
    if not candidate_answer or not candidate_answer.strip():
        return {"score": 0, "is_correct": False, "feedback": "No answer provided."}

    # Extract words > 3 chars to ignore stop words
    candidate_words = set(w for w in candidate_answer.lower().split() if len(w) > 3)
    correct_words = set(w for w in correct_answer.lower().split() if len(w) > 3)
    
    overlap = len(candidate_words & correct_words)
    
    # If 2 or more keywords match, or if it's a short answer and 1 matches, give full marks
    if overlap >= 2 or (len(correct_words) <= 2 and overlap >= 1):
        return {
            "score": max_score,
            "is_correct": True,
            "feedback": "Correct! (Evaluated via keyword matching).",
        }
    elif overlap == 1 and len(correct_words) > 2:
        return {
            "score": max_score / 2.0,
            "is_correct": True,
            "feedback": "Partially correct. (Evaluated via keyword matching).",
        }
        
    return {
        "score": 0,
        "is_correct": False,
        "feedback": "Incorrect. Did not match expected keywords.",
    }


# ==============================================================
# FEATURE 4: Generate Result Narrative
# ==============================================================

NARRATIVE_PROMPT = """You are a technical recruitment analyst. Analyze this candidate's assessment results.

Technology: {technology}
Overall Score: {percentage:.1f}% ({total_score}/{max_score})
Result: {result_label}

Question-level performance summary:
{performance_summary}

Generate a professional assessment report. Return JSON:
{{
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "weaknesses": ["weakness 1", "weakness 2"],
  "ai_feedback": "2-3 paragraph professional feedback narrative for the recruiter"
}}

Be specific, actionable, and professional. Return ONLY valid JSON.
"""


async def generate_result_narrative(
    technology: str,
    percentage: float,
    total_score: float,
    max_score: float,
    passed: bool,
    per_question_scores: list,
) -> dict:
    """Generate strengths, weaknesses, and AI feedback for a result."""
    if not await _ollama_available():
        return _fallback_narrative(percentage, passed)

    # Summarize performance
    correct = sum(1 for q in per_question_scores if q.get("is_correct"))
    total_q = len(per_question_scores)
    poor_questions = [q["question_text"][:80] for q in per_question_scores if q.get("score", 0) < q.get("max_score", 10) * 0.5][:3]

    summary = f"Answered {correct}/{total_q} questions correctly. "
    if poor_questions:
        summary += f"Struggled with: {'; '.join(poor_questions)}"

    prompt = NARRATIVE_PROMPT.format(
        technology=technology,
        percentage=percentage,
        total_score=total_score,
        max_score=max_score,
        result_label="PASS" if passed else "FAIL",
        performance_summary=summary,
    )
    try:
        response = await _ollama_generate(prompt)
        parsed = _extract_json(response)
        if parsed and isinstance(parsed, dict):
            return parsed
        return _fallback_narrative(percentage, passed)
    except Exception as e:
        logger.error(f"Narrative generation error: {e}")
        return _fallback_narrative(percentage, passed)


def _fallback_narrative(percentage: float, passed: bool) -> dict:
    """Fallback narrative when Ollama is unavailable."""
    if passed:
        return {
            "strengths": ["Demonstrated sufficient knowledge of the subject", "Completed the assessment within the time limit"],
            "weaknesses": ["Some areas may need further development"],
            "ai_feedback": f"The candidate scored {percentage:.1f}% and passed the assessment. A manual review of their answers is recommended for a comprehensive evaluation.",
        }
    else:
        return {
            "strengths": ["Attempted all questions"],
            "weaknesses": ["Did not meet the minimum passing threshold", "Further study in the subject area is recommended"],
            "ai_feedback": f"The candidate scored {percentage:.1f}% and did not meet the passing threshold. A review of fundamental concepts is recommended before retaking.",
        }


# ==============================================================
# FEATURE 5: Shortlist Candidates using AI
# ==============================================================

async def ai_shortlist_analysis(
    technology: str,
    candidates: list[dict],
    min_percentage: float,
) -> dict:
    """Analyze shortlisting decision and provide recruiter insights."""
    shortlisted = [c for c in candidates if c["percentage"] >= min_percentage]
    rejected = [c for c in candidates if c["percentage"] < min_percentage]

    summary = {
        "total": len(candidates),
        "shortlisted": len(shortlisted),
        "rejected": len(rejected),
        "avg_score": sum(c["percentage"] for c in candidates) / max(len(candidates), 1),
        "top_score": max((c["percentage"] for c in candidates), default=0),
    }
    return summary
