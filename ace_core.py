from langchain_ollama import ChatOllama
import re
from rag_service import search_knowledge

llm = ChatOllama(
    model="llama3.2",
    temperature=0.2,
    num_gpu=0
)

company_knowledge = [
    {
        "title": "Return Policy",
        "content": (
            "Customers can request a return within 7 days of delivery. "
            "The product must be unused and in its original packaging."
        )
    },
    {
        "title": "Refund Policy",
        "content": (
            "Approved refunds are processed within 5-7 business days "
            "after the returned product is received and inspected."
        )
    },
    {
        "title": "Shipping Policy",
        "content": (
            "Standard delivery usually takes 3-5 business days. "
            "Delivery times may vary depending on the customer's location."
        )
    },
    {
        "title": "Cancellation Policy",
        "content": (
            "Orders can be cancelled before they are shipped. "
            "Once an order has been shipped, cancellation may not be possible."
        )
    },
    {
        "title": "Support Hours",
        "content": (
            "Customer support is available Monday to Saturday "
            "from 9:00 AM to 6:00 PM."
        )
    }
]

orders = {
    "12345": {
        "customer_name": "Nikhil",
        "status": "Shipped",
        "estimated_delivery": "28 September 2026",
        "product": "Laptop"
    },
    "12346": {
        "customer_name": "Rahul",
        "status": "Processing",
        "estimated_delivery": "30 September 2026",
        "product": "Headphones"
    }
}

def search_knowledge_rag(message):
    results = search_knowledge(message)

    if not results:
        return None

    return {
        "title": "Relevant Company Policy",
        "content": "\n".join(results)
    }

def get_order_status(order_number):
    return orders.get(str(order_number))

def wants_human(message):
    message_lower = message.lower()

    phrases = [
        "human agent",
        "speak to a human",
        "talk to a human",
        "live agent",
        "real person",
        "human support",
        "customer support agent",
        "representative"
    ]

    return any(
        phrase in message_lower
        for phrase in phrases
    )

def generate_ai_response(message):
    order_match = re.search(r"\b\d{5}\b", message)

    if order_match:
        order_number = order_match.group()
        order = get_order_status(order_number)

        if order:
            return (
                f"Your order {order_number} is currently "
                f"{order['status']}. "
                f"Estimated delivery is "
                f"{order['estimated_delivery']}. "
                f"Product: {order['product']}."
            )

        return (
            f"I couldn't find any order with order number "
            f"{order_number}."
        )

    knowledge = search_knowledge_rag(message)

    if knowledge:
        prompt = f"""
You are ACE Helper, a customer support assistant.

Company information:
{knowledge["content"]}

Customer message:
{message}

Answer using only the company information provided.
Do not invent policies or information.
Keep the response concise and helpful.
"""
    else:
        prompt = f"""
You are ACE Helper, a customer support assistant.

Customer message:
{message}

Answer helpfully and concisely.
If the information is not available, clearly say that the request may require human support.
"""

    response = llm.invoke(prompt)
    return response.content

