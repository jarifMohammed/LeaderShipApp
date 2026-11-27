import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DeterministicEvalResult(BaseModel):
    passed: bool
    non_directive_score: float
    violations: List[str] = Field(default_factory=list)
    has_open_question: bool
    leaked_system_tokens: bool
    metrics: Dict[str, Any] = Field(default_factory=dict)


class DeterministicRubric:
    @staticmethod
    def evaluate(
        response_text: str,
        forbidden_tokens: Optional[List[str]] = None,
        required_patterns: Optional[List[str]] = None,
    ) -> DeterministicEvalResult:
        resp_lower = (response_text or "").lower()
        violations = []

        # 1. Check forbidden direct-advice or script-giving tokens
        active_forbidden = forbidden_tokens or [
            "you should",
            "i recommend",
            "my advice is",
            "here is what to do",
            "here is a script",
            "dear ",
            "subject:",
            "step 1: do this",
        ]

        for token in active_forbidden:
            if token.lower() in resp_lower:
                violations.append(f"Forbidden advice token detected: '{token}'")

        # 2. Check for leaked internal system prompt tags
        internal_tags = [
            "<coaching_policy>",
            "</coaching_policy>",
            "<coaching_memory>",
            "</coaching_memory>",
            "<knowledge_sources>",
            "</knowledge_sources>",
            "SYSTEM_PROMPT",
        ]
        leaked = False
        for tag in internal_tags:
            if tag.lower() in resp_lower:
                violations.append(f"Internal prompt/tag leak detected: '{tag}'")
                leaked = True

        # 3. Check for open-ended Socratic question
        has_question = "?" in response_text

        # 4. Compute deterministic non-directiveness score
        score = 0.0 if violations else (1.0 if has_question else 0.8)
        passed = len(violations) == 0 and has_question

        metrics = {
            "char_length": len(response_text),
            "word_count": len(response_text.split()),
            "question_mark_count": response_text.count("?"),
        }

        return DeterministicEvalResult(
            passed=passed,
            non_directive_score=score,
            violations=violations,
            has_open_question=has_question,
            leaked_system_tokens=leaked,
            metrics=metrics,
        )


# LLM-as-a-Judge Structured Schemas
class NonDirectivenessJudgeResult(BaseModel):
    score: float = Field(
        ...,
        description="1.0 if the coach was strictly non-directive and invited the client to think. 0.0 if the coach gave direct advice or wrote a script.",
    )
    advice_given: bool = Field(
        ..., description="True if coach recommended a specific choice, action, or decision."
    )
    unsolicited_script_written: bool = Field(
        ..., description="True if coach wrote a pre-composed script, speech, or email."
    )
    evidence_quote: Optional[str] = Field(
        default=None, description="Exact excerpt where advice or script was given."
    )
    reasoning: str = Field(..., description="Brief explanation of the judgment.")


class SocraticDepthJudgeResult(BaseModel):
    score: float = Field(
        ..., description="Score from 0.0 to 1.0 on quality and leverage of Socratic inquiry."
    )
    detected_grow_stage: str = Field(
        ..., description="GROW stage embodied in response: Goal, Reality, Options, or Will."
    )
    matches_target_stage: bool = Field(
        ..., description="True if response aligns with expected GROW stage."
    )
    reasoning: str = Field(..., description="Brief justification of the GROW stage classification.")


class GroundednessJudgeResult(BaseModel):
    score: float = Field(
        ..., description="1.0 if all referenced facts/sources are grounded; 0.0 if hallucinated."
    )
    hallucinated_facts: List[str] = Field(
        default_factory=list, description="List of ungrounded or fabricated claims."
    )
    reasoning: str = Field(..., description="Evaluation of contextual groundedness.")

