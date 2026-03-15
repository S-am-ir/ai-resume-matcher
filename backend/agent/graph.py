from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import route_query, tailor_resume, track_applications

def router_edge(state: AgentState):
    """Conditional edge based on mode."""
    mode = state.get("current_mode", "tailor")
    print(f"[GRAPH EDGE] Routing to: {mode}")
    if mode == "tailor":
        print("[GRAPH EDGE] → tailor_resume")
        return "tailor_resume"
    elif mode == "track":
        print("[GRAPH EDGE] → track_applications")
        return "track_applications"
    print("[GRAPH EDGE] → tailor_resume (default)")
    return "tailor_resume"

def build_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("route_query", route_query)
    workflow.add_node("tailor_resume", tailor_resume)
    workflow.add_node("track_applications", track_applications)

    # Add edges
    workflow.set_entry_point("route_query")

    workflow.add_conditional_edges(
        "route_query",
        router_edge,
    )

    workflow.add_edge("tailor_resume", END)
    workflow.add_edge("track_applications", END)

    return workflow.compile()
