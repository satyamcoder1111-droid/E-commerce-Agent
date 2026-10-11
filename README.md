# E-commerce Agent

A conversational B2B shopping assistant built with Python, LangGraph, LangChain, OpenAI, and Streamlit. Customers can build a cart in natural language, change quantities, remove items, and provide delivery information.

## Features

- Add products, remove items, or replace quantities through natural-language chat.
- Validate requested quantities against the demo catalog's available stock.
- Use Pydantic models for requested products and cart items.
- Track messages, pending information, and confirmation in LangGraph state.
- Preserve conversations with separate thread IDs and in-memory checkpoints.
- Inspect the cart, totals, and order state in a Streamlit interface.
- Run a command-line demo of the agent workflow.

## Example conversation

```text
Customer: fries 2 ctn
Action: add 2 cartons of fries

Customer: fries ko 5 carton kar do
Action: replace the quantity with 5 cartons

Customer: remove fries
Action: remove fries from the cart
```

The sample catalog contains fries and milk. Stock and prices are demo data, not live supplier data.

## How it works

```text
Streamlit chat -> LangGraph agent -> tool calls -> product service
                       ^                |
                       |_____ state ____|
```

The agent reads the conversation and current order state, then responds or requests a tool. `update_cart` resolves products, checks stock, and returns state updates. `capture_information` records customer and delivery information. The graph routes tool results back to the agent for a conversational response.

Streamlit calls the graph directly. `main.py` runs a standalone sample conversation. FastAPI is included in the dependencies for future API integration; an HTTP API is not currently implemented.

## Project structure

```text
agent/
  state.py             # Typed conversation and order state
  tools.py             # Cart updates and information capture
  prompt.py            # Agent instructions
  nodes.py             # Model invocation and state view
  graph.py             # Routing and in-memory checkpoints
models/
  order.py             # RequestedItem and CartItem models
services/
  product_service.py   # Sample product catalog
  order_service.py     # Placeholder for order submission
  test.py              # Product lookup smoke script
tests/
  test_cart.py         # Automated cart behavior tests
main.py                # Command-line conversation demo
streamlit_app.py       # Interactive chat UI
.env.example           # Configuration template
requirements.txt
```

## Local setup

Requires Python 3.11 or later and an OpenAI API key for live chat.

```powershell
git clone https://github.com/satyamcoder1111-droid/E-commerce-Agent.git
cd E-commerce-Agent
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` in `.env`, or enter it in the Streamlit sidebar. Keep `.env` local; it is excluded from Git. Live model requests use your OpenAI API account.

### Start the chat demo

```powershell
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

Open http://localhost:8501 and try `fries 2 ctn`, `milk 4 pkt`, or `remove fries`. Use **New conversation** to reset the conversation and cart.

### Run the command-line demo

```powershell
.\.venv\Scripts\python.exe main.py
```

This runs a sample product request and prints the response, cart, and pending fields. It makes live model calls and requires your API key.

## Tests

Cart tests run locally without API credentials or model calls:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

They cover addition, quantity replacement, removal, stock rejection, required fields, and invalidation of a previous order confirmation.

## Current limitations

- Product lookup and stock use a small in-memory catalog.
- Confirmation updates state; final order submission is not implemented.
- Checkpoints disappear when the process restarts.
- Authentication, persistent storage, and production deployment are not implemented.
