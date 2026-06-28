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


# ---------- Plan node
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



