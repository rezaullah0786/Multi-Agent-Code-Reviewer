from typing import Any, Dict
from langgraph.graph import END, START, StateGraph

from app.workflow.nodes import (
    aggregator_validation_node,
    ast_analysis_node,
    performance_agent_node,
    retrieval_node,
    security_agent_node,
    style_agent_node,
)
from app.workflow.state import ReviewState


def build_review_graph():
    """Constructs and compiles the multi-agent code reviewer LangGraph workflow."""
    builder = StateGraph(ReviewState)

    # Register Nodes
    builder.add_node("ast_analysis", ast_analysis_node)
    builder.add_node("retrieval", retrieval_node)
    builder.add_node("security_agent", security_agent_node)
    builder.add_node("performance_agent", performance_agent_node)
    builder.add_node("style_agent", style_agent_node)
    builder.add_node("aggregator_validation", aggregator_validation_node)

    # Define Graph Flow
    builder.add_edge(START, "ast_analysis")
    builder.add_edge("ast_analysis", "retrieval")
    builder.add_edge("retrieval", "security_agent")
    builder.add_edge("security_agent", "performance_agent")
    builder.add_edge("performance_agent", "style_agent")
    builder.add_edge("style_agent", "aggregator_validation")
    builder.add_edge("aggregator_validation", END)

    return builder.compile()


review_graph = build_review_graph()


def run_review_workflow(initial_state: Dict[str, Any]) -> Dict[str, Any]:
    """Helper function to execute the compiled LangGraph workflow."""
    return review_graph.invoke(initial_state)
