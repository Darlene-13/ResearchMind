import operator
from typing import TypedDict, Annotated


# Streaming redis event
class StreamEvent(TypedDict):
    # Event examples: Planning, Searching, Extracting, Writing, Done, Error
    event: str
    message:str
    data:dict

class SearchResult(TypedDict):
    """
    One result returned by Tavily for a single sub-question.
    """
    sub_question:str
    url:str
    title: str
    content: str

class ExtractedFact(TypedDict):
    """
    One atomic fact pulled out by the extractor agent.
    Keeping facts smaller and making the writers job easier
    """
    fact: str
    source_url: str    # needed for citations
    relevance: float


class AgentState(TypedDict):
    """
    Single source of truth that flows through the entire graph(LangGraph)
    To be passed full state to every node
    Each node reps a sub graph and returns only the fields it changed
    Instead of overwriting langgraph appends because both nodes write on the same field at the same time
    """
    # Original user question
    query: str
    # Unique id for the search job on redis
    job_id: str
    # Sub questions the orchestrator decomposed the query to
    plan: list[str]
    # Don't write report if the confidence level is below the confidence threshold
    confidence: float
    # Prevents runaway jobs that burn API credits.
    iteration: int

    # ---------Search + retrival output.---------
    search_results: Annotated[list[SearchResult], operator.add]
    # Raw results from tavily - one entry per sub question per result
    retrieved_chunks: Annotated[list[dict], operator.add]
    # Chunks retrieved from pgVector (local vector store)


    #---------extractor output -----------------
    # Structured facts pulled from search results + retrieved chunks
    extracted_facts: list[ExtractedFact]

    citations: list[str]

    # --------writer output -------
    report: str

    # meta
    stream_events: Annotated[list[StreamEvent], operator.add]

    # If any node fails, it writes the error message here.
    # Graph routes to an error handler node which publishes it to Redis.
    error: str | None


