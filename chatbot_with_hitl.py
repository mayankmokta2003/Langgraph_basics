from langgraph.graph import StateGraph, START
from langchain.tools import tool
from langchain_mistralai import ChatMistralAI
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages
import requests




llm = ChatMistralAI()

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


@tool
def get_stock_price(stock: str) -> dict:
    """ This tool fetches the current price of any Stock """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey=8KVWO5LHF5VOAAA1"
    response = requests.get(url)
    return response.json()

@tool 
def purchase_stock(symbol: str, quantity: int) -> dict:
    return "aa"





tools = [get_stock_price, purchase_stock]









