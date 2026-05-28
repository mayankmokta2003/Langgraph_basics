from langgraph.graph import StateGraph, START
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
import requests
from dotenv import load_dotenv
load_dotenv()



llm = ChatMistralAI(model="mistral-small-2506")

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def get_stock_price(symbol: str) -> dict:
    """ This tool fetches the current price of any Stock """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=8KVWO5LHF5VOAAA1"
    response = requests.get(url)
    return response.json()

@tool 
def purchase_stock(symbol: str, quantity: int) -> dict:
    """
    Simulate purchasing a given quantity of a stock symbol.

    HUMAN-IN-THE-LOOP:
    Before confirming the purchase, this tool will interrupt
    and wait for a human decision ("yes" / anything else).
    """
    decision = interrupt(
        f"Approve buying {symbol} shares of {quantity}? (yes/no)"
    )
    if isinstance(decision, str) and decision.lower() == "yes":
        return {
            "statues": "success",
            "message": f"Purchase order placed for {quantity} shares of {symbol}.",
            "symbol": symbol,
            "quantity": quantity,
        }
    else:
        return{
             "status": "cancelled",
            "message": f"Purchase of {quantity} shares of {symbol} was declined by human.",
            "symbol": symbol,
            "quantity": quantity,
        }






tools = [get_stock_price, purchase_stock]
llm_with_tools = llm.bind_tools(tools)

def chat_node(state: ChatState):
    """LLM node that may answer or request a tool call."""
    message = state["messages"]
    response = llm_with_tools.invoke(message)
    return {"messages": [response]}

tool_node = ToolNode(tools)

checkpointer = MemorySaver()


graph = StateGraph(ChatState)

graph.add_node("chat_node", chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START, "chat_node")
graph.add_conditional_edges("chat_node", tools_condition)
graph.add_edge("tools", "chat_node")

chatbot = graph.compile(checkpointer=checkpointer)


if __name__ == "__main__":
    thread_id = "demo-thread"
    while True:
        user_input = input("You: ")
        if user_input.lower().strip() == {"exit", "quit"}:
            print("GOODBYE")
            break
        state = {"messages" : [HumanMessage(content=user_input)]}
        result = chatbot.invoke(state, config={"configurable": {"thread_id": thread_id}})

        interrupts = result.get("__interrupt__", [])

        if interrupts:
            # Our interrupt payload is the string we passed to interrupt(...)
            prompt_to_human = interrupts[0].value
            print(f"HITL: {prompt_to_human}")
            decision = input("Your decision: ").strip().lower()

            # Resume graph with the human decision ("yes" / "no" / whatever)
            result = chatbot.invoke(
                Command(resume=decision),
                config={"configurable": {"thread_id": thread_id}},
            )

        # Get the latest message from the assistant
        messages = result["messages"]
        last_msg = messages[-1]
        print(f"Bot: {last_msg.content}\n")






