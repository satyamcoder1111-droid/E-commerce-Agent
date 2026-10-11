
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from openai import AsyncOpenAI

from agent.state import EcommerceState
from agent.prompt import agent_prompt
from agent.tools import (
    update_cart,
    capture_information,
)


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


tools = [
    update_cart,
    capture_information,
]


def build_agent_view(
    state: EcommerceState
) -> dict:

    pending_fields = state.get(
        "pending_fields",
        []
    )

    return {
        "customer_id": state.get(
            "customer_id"
        ),

        "cart_items": [
            item.model_dump()
            for item in state.get(
                "cart_items",
                []
            )
        ],

        "required_fields": state.get(
            "required_fields",
            []
        ),

        "collected_fields": state.get(
            "collected_fields",
            []
        ),

        "pending_fields": pending_fields,

        "next_field": (
            pending_fields[0]
            if pending_fields
            else None
        ),

        "cart_complete": state.get(
            "cart_complete"
        ),

        "delivery_date": state.get(
            "delivery_date"
        ),

        "inventory_result": state.get(
            "inventory_result"
        ),

        "order_confirmed": state.get(
            "order_confirmed",
            False
        ),

        "order_id": state.get(
            "order_id"
        ),
    }


async def agent_node(
    state: EcommerceState,
    config: RunnableConfig,
):

    api_key = config.get("configurable", {}).get("api_key")
    agent_view = build_agent_view(
        state
    )

    # Streamlit creates a new event loop for each chat turn. Own and close
    # this client in the current loop instead of reusing a cached connection.
    async with AsyncOpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY")) as client:
        llm = ChatOpenAI(
            model="gpt-4o-mini", temperature=0,
            api_key=api_key or os.getenv("OPENAI_API_KEY"),
            async_client=client.chat.completions,
            root_async_client=client,
        )
        agent_chain = agent_prompt | llm.bind_tools(tools, parallel_tool_calls=False)
        response = await agent_chain.ainvoke({
            "agent_view": json.dumps(agent_view, indent=2, default=str),
            "messages": state["messages"],
        })

    return {
        "messages": [response]
    }
