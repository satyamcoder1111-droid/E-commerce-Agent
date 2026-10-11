"""Local chat interface for testing the e-commerce LangGraph agent."""

import asyncio
import os
from pathlib import Path
from uuid import uuid4

import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv(Path(__file__).resolve().parent / ".env")
st.set_page_config(page_title="E Commerce Bot", page_icon="🛒", layout="wide")
st.title("🛒 E Commerce Bot")
st.caption("Chat with the agent using demo products: fries and milk.")


def reset_chat():
    st.session_state.thread_id = str(uuid4())
    st.session_state.history = []
    st.session_state.order_state = None


if "thread_id" not in st.session_state:
    reset_chat()

with st.sidebar:
    st.header("Test settings")
    customer_id = st.number_input("Customer ID", min_value=1, value=123,
                                  disabled=bool(st.session_state.history))
    api_key = os.getenv("OPENAI_API_KEY") or st.text_input(
        "OpenAI API key", type="password", help="Used only by this local app."
    )
    st.caption("Demo stock: fries 20 cartons; milk 50 packs. Prices: ₹1,100 and ₹80.")
    st.caption("Order submission is not implemented yet. Confirmation only updates the state.")
    if st.button("New conversation"):
        reset_chat()
        st.rerun()


@st.cache_resource
def get_graph():
    from agent.graph import graph
    return graph


for message in st.session_state.history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if not api_key:
    st.info("Enter your OpenAI API key in the sidebar, or set OPENAI_API_KEY in .env.")

prompt = st.chat_input("Try: fries 2 ctn", disabled=not bool(api_key))
if prompt:
    with st.chat_message("user"):
        st.write(prompt)
    with st.chat_message("assistant"):
        with st.spinner("Checking your order…"):
            try:
                graph = get_graph()
                inputs = {"messages": [HumanMessage(content=prompt)]}
                if st.session_state.order_state is None:
                    inputs.update({
                        "customer_id": int(customer_id),
                        "requested_items": [], "cart_items": [],
                        "required_fields": ["customer_id", "items", "cart_complete", "delivery_date", "confirmation"],
                        "collected_fields": ["customer_id"],
                        "pending_fields": ["items", "cart_complete", "delivery_date", "confirmation"],
                        "cart_complete": False, "delivery_date": None,
                        "inventory_result": None, "order_confirmed": False,
                        "order_id": None, "total_amount": None, "error": None,
                    })
                result = asyncio.run(graph.ainvoke(inputs, config={
                    "configurable": {"thread_id": st.session_state.thread_id, "api_key": api_key},
                    "recursion_limit": 20,
                }))
                answer = result["messages"][-1].content
                st.write(answer)
                st.session_state.history.extend([
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": answer},
                ])
                st.session_state.order_state = result
            except Exception as exc:
                from openai import AuthenticationError, RateLimitError, APIConnectionError
                if isinstance(exc, AuthenticationError):
                    st.error("API key was rejected. Check your configured key.")
                elif isinstance(exc, RateLimitError):
                    st.error("API rate limit or quota reached. Check your API usage and billing.")
                elif isinstance(exc, APIConnectionError):
                    st.error("Could not connect to the AI service. Check your connection and retry.")
                else:
                    st.error(f"The agent encountered an application error ({type(exc).__name__}). Start a new conversation and retry.")

state = st.session_state.order_state
if state:
    st.subheader("Current cart")
    rows = [item.model_dump() for item in state.get("cart_items", [])]
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
        st.metric("Cart total", f"₹{sum(row['total_price'] for row in rows):,.2f}")
    else:
        st.caption("Your cart is empty.")
    with st.expander("Inspect order state"):
        st.json({key: value for key, value in state.items()
                 if key not in ("messages", "cart_items", "requested_items")})
