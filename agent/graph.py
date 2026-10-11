from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import InMemorySaver

from agent.state import EcommerceState
from agent.nodes import agent_node
from agent.tools import (
    update_cart,
    capture_information,
)


tools = [
    update_cart,
    capture_information,
]

tool_node = ToolNode(tools)


def route_agent(state: EcommerceState):

    last_message = state["messages"][-1]

    # Route tool calls to the tool node.
    if getattr(last_message, "tool_calls", None):
        return "tools"

    # End the turn when the agent returns a conversational response.
    return END


builder = StateGraph(EcommerceState)


builder.add_node(
    "agent",
    agent_node
)

builder.add_node(
    "tools",
    tool_node
)


builder.add_edge(
    START,
    "agent"
)


builder.add_conditional_edges(
    "agent",
    route_agent,
    {
        "tools": "tools",
        END: END,
    }
)


builder.add_edge(
    "tools",
    "agent"
)


# Store conversation checkpoints in memory during local development.
memory = InMemorySaver()


graph = builder.compile(
    checkpointer=memory
)
