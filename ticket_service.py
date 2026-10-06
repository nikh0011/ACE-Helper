
import sqlite3
import uuid
from datetime import datetime

DB_PATH = "ace_helper.db"

def create_ticket(session_id, message):
    ticket_id = "ACE-" + uuid.uuid4().hex[:6].upper()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tickets
        (ticket_id, conversation_id, status, assigned_to, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            session_id,
            "OPEN",
            "Nikhil",
            created_at
        )
    )

    cursor.execute(
        """
        INSERT INTO ticket_messages
        (ticket_id, sender, message, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            ticket_id,
            "customer",
            message,
            created_at
        )
    )

    conn.commit()
    conn.close()

    return {
        "ticket_id": ticket_id,
        "status": "OPEN",
        "assigned_to": "Nikhil",
        "created_at": created_at
    }
