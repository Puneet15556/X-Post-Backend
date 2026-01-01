from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver



from graph.nodes import *


memory = MemorySaver()

# --------------------------------------------------
# GRAPH BUILDER
# --------------------------------------------------
def build_graph():
    g = StateGraph(State)


    g.add_node("input_topic", tool_router_node)

    g.add_node("generate_post", generate_post)
    g.add_node("human_feedback", wait_for_human)
    g.add_node("refine_post", refine_post)
    g.add_node("accept_post", accept_post)

    g.add_node("call_model_search", call_model_search)
    g.add_node("call_model_timeline", call_model_timeline)
    g.add_node("call_model_post", call_model_post)

    # -------------------------
    # EDGES
    # -------------------------
    g.add_edge(START, "input_topic")

    g.add_conditional_edges(
        "input_topic",
        decide_input,
        {
            "generate": "generate_post",
            "Call_Model_Search": "call_model_search",
            "Call_Model_Timeline": "call_model_timeline"
            
        },
    )

    g.add_edge("generate_post", "human_feedback")

    g.add_conditional_edges(
        "human_feedback",
        decide,
        {
            "accept": "accept_post",
            "refine": "refine_post",
        },
    )

    g.add_edge("refine_post", "human_feedback")
    g.add_edge("accept_post", "call_model_post")

    g.add_edge("call_model_search", END)
    g.add_edge("call_model_timeline", END)
    g.add_edge("call_model_post", END)

    workflow =  g.compile(checkpointer=memory)
    return workflow
