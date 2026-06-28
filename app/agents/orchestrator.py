import logging
import json

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState, StreamEvent
from app.core.config import settings

#Log errors
logger = logging.getLogger(__name__)

# LLM Setup
llm = ChatAnthropic(
    model=settings.orchestator_model,
    api_key=settings.orchestator_api_key
)


#-------------PROMPTS -------------------------

PLAN_SYSTEM_PROMPT = """You are a research planning expert.
Your job is to decompose a user query into 3-5 specific, searchable sub-questions.

Rules:
- Each sub-question must be independently searchable
- No vague directions like "find information about X"
- Be specific: include years, comparisons, metrics where relevant
- Return ONLY a valid JSON array of strings. No explanation. No markdown.

Example output:
["What are the leading solid-state battery manufacturers in 2025?",
 "What energy density have solid-state batteries achieved vs lithium-ion?",
 "What manufacturing challenges block solid-state battery scale-up?"]"""

CONFIDENCE_SYSTEM_PROMPT = """You are a research quality evaluator.
You will receive the original research plan and the facts gathered so far.
Your job: decide if the facts are sufficient to write a complete, accurate report.

Return ONLY a JSON object with exactly two fields:
{
  "score": <float between 0.0 and 1.0>,
  "reason": "<one sentence explaining the score>"
}

0.0 = facts are completely insufficient
0.75 = good enough to write a solid report  
1.0 = comprehensive coverage, nothing missing"""

REFINE_SYSTEM_PROMPT = """You are a research planning expert.
A previous search did not gather enough facts to answer the query confidently.
You will receive the original plan and the facts gathered so far.
Your job: rewrite the plan with DIFFERENT sub-questions that target the gaps.

Return ONLY a valid JSON array of strings. No explanation. No markdown."""


# ---------- Plan node-------------------------------------------------------
async def plan_node(state: AgentState) -> dict:
    # First node in the graph and runs at the start of every search job
    logger.info(f"[{state['job_id']}] Planning for query: {state['query']}")

    try:
        response = await llm.ainvoke([
            SystemMessage(content=PLAN_SYSTEM_PROMPT),
            HumanMessage(content=f"Research query: {state['query']}"),
        ])

        # Parse response.content string to get a json

        raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()
        sub_questions = json.loads(raw)

        logger.info(f"[{state['job_id']}] Planning sub-questions: {sub_questions}")

        # LangGraph merges this partial update into the full state.
        return {
            "plan": sub_questions,
            "stream_events": [
                StreamEvent(
                    event="planning",
                    message=f"Research plan ready — {len(sub_questions)} sub-questions",
                    data={"sub_questions": sub_questions},
                )
            ],
        }

    except Exception as e:
        logger.error(f"[{state['job_id']}] plan_node failed: {e}")
        # Write the error to state. The graph routes to error_node next.
        return {"error": str(e)}

# --------- Confidence node --------------------------------------

async def confidence_node(state: AgentState) -> dict:
    """
    Runs after the extractor to decide if the report should be written or search again.
    """
    logger.info(f"[{state['job_id']}] Evaluating confidence (iteration {state['iteration']})")

    try:
        facts_summary = json.dumps(state["extracted_facts"], indent=2)
        response = await llm.ainvoke([
            SystemMessage(content=CONFIDENCE_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Original plan:\n{json.dumps(state['plan'], indent=2)}\n\n"
                f""
            )),
        ])


        raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()
        result = json.loads(raw)

        score: float = float(result["score"])
        reason: str = result.get("reason", "")

        # If the score is low, re-write the plan so that the next search loop targets the specific gap instead of repeating the same question
        new_plan = state['plan']
        if score < settings.confidence_threshold:
            new_plan = await _refine_plan(state, reason)

            return {
                "confidence": score,
                "iteration": state['iteration'],
                "plan": new_plan,
                "stream_events": [
                    StreamEvent(
                        event="confidence check",
                        message=f"Confidence {score:.0%} - {reason}",
                        data={"score": score, "iteration": state["iteration"] + 1},
                    )
                ],
            }

    except Exception as e:
        logger.error(f"[{state['job_id']}] confidence_node failed: {e}")
        return {
            "confidence": 1.0,   # returning 0 will cause the loop to run forever
            "iteration": state['iteration'],
            "error": str(e),
        }




# ------refine plan
async def _refine_plan(state: AgentState, gap_reason: str) -> list[str]:
    """
    Called by confidence_node when score is too low.
    Rewrites the plan to target what's missing.

    Prefixed with _ = internal only. LangGraph nodes have a specific
    signature (receive state, return dict). This takes different args
    so it's a plain async helper, not a node.
    """
    try:
        response = await llm.ainvoke([
            SystemMessage(content=REFINE_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Original query: {state['query']}\n\n"
                f"Original plan:\n{json.dumps(state['plan'], indent=2)}\n\n"
                f"Facts gathered so far:\n{json.dumps(state['extracted_facts'], indent=2)}\n\n"
                f"Gap identified: {gap_reason}"
            )),
        ])

        raw = response.content.strip().removeprefix("```json").removesuffix("```").strip()
        return json.loads(raw)

    except Exception as e:
        logger.warning(f"[{state['job_id']}] _refine_plan failed: {e} — keeping original plan")
        # If refinement fails, keep the original plan.
        # Better to re-search with same questions than crash entirely.
        return state["plan"]
