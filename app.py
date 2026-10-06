from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

import ace_core
from ticket_service import create_ticket


app = FastAPI(
    title="ACE Helper API",
    version="1.0.0"
)


# REQUEST MODELS


class ChatRequest(BaseModel):
    session_id: str
    message: str


class TicketReplyRequest(BaseModel):
    message: str



# HOME


@app.get("/")
def home():
    return {
        "status": "running",
        "service": "ACE Helper API"
    }


# CUSTOMER CHAT


@app.post("/chat")
def chat(request: ChatRequest):

    # Human escalation
    if ace_core.wants_human(request.message):

        ticket = create_ticket(
            request.session_id,
            request.message
        )

        return {
            "session_id": request.session_id,
            "message": request.message,
            "response": (
                "I've escalated your request to a human support agent. "
                f"Your ticket ID is {ticket['ticket_id']}."
            ),
            "ticket_id": ticket["ticket_id"],
            "status": ticket["status"]
        }

    # AI response
    response = ace_core.generate_ai_response(
        request.message
    )

    return {
        "session_id": request.session_id,
        "message": request.message,
        "response": response
    }


# GET ALL TICKETS


@app.get("/tickets")
def get_tickets():

    conn = sqlite3.connect("ace_helper.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            ticket_id,
            conversation_id,
            status,
            assigned_to,
            created_at
        FROM tickets
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        "tickets": [
            {
                "ticket_id": row[0],
                "conversation_id": row[1],
                "status": row[2],
                "assigned_to": row[3],
                "created_at": row[4]
            }
            for row in rows
        ]
    }



# GET TICKET CONVERSATION


@app.get("/tickets/{ticket_id}/conversation")
def get_ticket_conversation(ticket_id: str):

    conn = sqlite3.connect("ace_helper.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            sender,
            message,
            created_at
        FROM ticket_messages
        WHERE ticket_id = ?
        ORDER BY id
        """,
        (ticket_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        "ticket_id": ticket_id,
        "messages": [
            {
                "sender": row[0],
                "message": row[1],
                "created_at": row[2]
            }
            for row in rows
        ]
    }



# AGENT REPLY


@app.post("/tickets/{ticket_id}/reply")
def reply_to_ticket(
    ticket_id: str,
    request: TicketReplyRequest
):

    conn = sqlite3.connect("ace_helper.db")
    cursor = conn.cursor()

    # Check ticket
    cursor.execute(
        """
        SELECT ticket_id, status
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    )

    ticket = cursor.fetchone()

    if not ticket:
        conn.close()

        return {
            "error": "Ticket not found"
        }

    # Prevent reply to resolved ticket
    if ticket[1] == "RESOLVED":
        conn.close()

        return {
            "error": "Ticket is already resolved",
            "ticket_id": ticket_id,
            "status": "RESOLVED"
        }

    # Save agent message
    cursor.execute(
        """
        INSERT INTO ticket_messages
        (
            ticket_id,
            sender,
            message,
            created_at
        )
        VALUES (?, ?, ?, datetime('now'))
        """,
        (
            ticket_id,
            "agent",
            request.message
        )
    )

    # Update status
    cursor.execute(
        """
        UPDATE tickets
        SET status = ?
        WHERE ticket_id = ?
        """,
        (
            "WAITING_FOR_CUSTOMER",
            ticket_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "status": "WAITING_FOR_CUSTOMER",
        "reply": request.message
    }
@app.post("/tickets/{ticket_id}/customer-reply")
def customer_reply(
    ticket_id: str,
    request: TicketReplyRequest
):

    conn = sqlite3.connect("ace_helper.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticket_id, status
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    )

    ticket = cursor.fetchone()

    if not ticket:
        conn.close()

        return {
            "error": "Ticket not found"
        }

    if ticket[1] == "RESOLVED":
        conn.close()

        return {
            "error": "Ticket is already resolved",
            "ticket_id": ticket_id,
            "status": "RESOLVED"
        }

    cursor.execute(
        """
        INSERT INTO ticket_messages
        (
            ticket_id,
            sender,
            message,
            created_at
        )
        VALUES (?, ?, ?, datetime('now'))
        """,
        (
            ticket_id,
            "customer",
            request.message
        )
    )

    cursor.execute(
        """
        UPDATE tickets
        SET status = ?
        WHERE ticket_id = ?
        """,
        (
            "OPEN",
            ticket_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "status": "OPEN",
        "reply": request.message
    }
@app.post("/tickets/{ticket_id}/resolve")
def resolve_ticket(ticket_id: str):

    conn = sqlite3.connect("ace_helper.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT ticket_id, status
        FROM tickets
        WHERE ticket_id = ?
        """,
        (ticket_id,)
    )

    ticket = cursor.fetchone()

    if not ticket:
        conn.close()

        return {
            "error": "Ticket not found"
        }

    if ticket[1] == "RESOLVED":
        conn.close()

        return {
            "ticket_id": ticket_id,
            "status": "RESOLVED",
            "message": "Ticket is already resolved."
        }

    cursor.execute(
        """
        UPDATE tickets
        SET status = ?
        WHERE ticket_id = ?
        """,
        (
            "RESOLVED",
            ticket_id
        )
    )

    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "status": "RESOLVED",
        "message": "Ticket resolved successfully."
    }
@app.get("/tickets/{ticket_id}/messages")
def get_ticket_messages(ticket_id: str):

    conn = sqlite3.connect("ace_helper.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            sender,
            message,
            created_at
        FROM ticket_messages
        WHERE ticket_id = ?
        ORDER BY id
        """,
        (ticket_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return {
        "ticket_id": ticket_id,
        "messages": [
            {
                "sender": row[0],
                "message": row[1],
                "created_at": row[2]
            }
            for row in rows
        ]
    }