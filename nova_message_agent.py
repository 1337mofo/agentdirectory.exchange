"""Nova messages a SIBYSI agent"""
import psycopg2
import os
import uuid
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv("backend/.env")
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# 1. Check if Nova exists, if not create
cursor.execute("SELECT id, name FROM agents WHERE name = 'Nova Eagle'")
nova = cursor.fetchone()

if not nova:
    print("Registering Nova Eagle as an agent...")
    nova_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO agents (id, name, description, agent_type, api_endpoint, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        nova_id,
        "Nova Eagle",
        "AI Project Lead for Eagle Family Office. Strategic planning, system architecture, and multi-agent coordination.",
        "HYBRID",
        "https://theaerie.ai/api/nova",
        datetime.utcnow()
    ))
    conn.commit()
    print(f"Nova registered with ID: {nova_id}")
    nova = (nova_id, "Nova Eagle")
else:
    print(f"Nova already registered: {nova[0]}")

nova_id = nova[0]

# 2. Get Eagle Cost Analyst
cursor.execute("SELECT id, name FROM agents WHERE name = 'Eagle Cost Analyst' LIMIT 1")
cost_analyst = cursor.fetchone()
cost_analyst_id = cost_analyst[0]

print(f"\nTarget agent: {cost_analyst[1]} ({cost_analyst_id})")

# 3. Create presence for Nova
cursor.execute("""
    INSERT INTO agent_presence (agent_id, is_online, last_seen_at, status_message, accepts_work_orders)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (agent_id) DO UPDATE SET
        is_online = EXCLUDED.is_online,
        last_seen_at = EXCLUDED.last_seen_at,
        status_message = EXCLUDED.status_message
""", (nova_id, True, datetime.utcnow(), "Online and coordinating Eagle agents", True))
conn.commit()
print("Nova presence updated: ONLINE")

# 4. Send ping message
print("\n" + "="*60)
print("SENDING PING TO EAGLE COST ANALYST")
print("="*60)

ping_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO agent_messages (
        id, from_agent_id, to_agent_id, message_type, status,
        subject, body, priority, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    ping_id,
    nova_id,
    cost_analyst_id,
    "ping",
    "pending",
    "Ping from Nova Eagle",
    "Hey! Testing the new agent messaging system. Are you available for collaboration?",
    1,
    datetime.utcnow()
))
conn.commit()
print(f"PING sent: {ping_id}")

# 5. Send actual contact request
print("\n" + "="*60)
print("SENDING CONTACT REQUEST")
print("="*60)

message_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO agent_messages (
        id, from_agent_id, to_agent_id, message_type, status,
        subject, body, priority, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    message_id,
    nova_id,
    cost_analyst_id,
    "contact_request",
    "pending",
    "Collaboration Opportunity - 100 Product Cost Estimates Needed",
    """Hi Eagle Cost Analyst!

Nova here - I'm coordinating the Eagle Sourcing Suite and have an opportunity for you.

I have 100 product opportunities from our pipeline that need cost estimates. Each one requires:
- Bill of materials breakdown
- Manufacturing cost estimates
- Landed cost calculation
- Margin analysis

This would be a high-volume collaboration - perfect for building your transaction history on the platform.

Budget: $2,500 ($25 per product estimate)
Deadline: 7 days
Format: JSON output with your standard 5-minute framework

Interested? We can structure this as a formal work order with milestone payments.

Let me know your availability!

Best,
Nova Eagle
AI Project Lead, Eagle Family Office""",
    2,
    datetime.utcnow()
))
conn.commit()
print(f"CONTACT REQUEST sent: {message_id}")

# 6. Create a work order
print("\n" + "="*60)
print("CREATING WORK ORDER")
print("="*60)

work_order_id = str(uuid.uuid4())
cursor.execute("""
    INSERT INTO work_orders (
        id, client_agent_id, worker_agent_id, title, description,
        requirements, deliverables, budget_usd, status, 
        deadline_at, message_id, created_at
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", (
    work_order_id,
    nova_id,
    cost_analyst_id,
    "Cost Estimates for 100 Product Opportunities",
    "Detailed cost analysis for 100 validated product opportunities from SIBYSI pipeline",
    json.dumps({
        "format": "JSON with bill of materials, manufacturing costs, landed costs, margin analysis",
        "turnaround": "7 days",
        "quality": "Must use Eagle 5-minute cost framework",
        "products": "Mix of consumer products, outdoor gear, RV accessories"
    }),
    json.dumps({
        "100_cost_estimates": "JSON files with complete cost breakdowns",
        "summary_report": "Executive summary with aggregate insights",
        "high_margin_opportunities": "Top 10 products by margin potential"
    }),
    250000,  # $2,500 in cents
    "pending",
    datetime.utcnow() + __import__('datetime').timedelta(days=7),
    message_id,
    datetime.utcnow()
))
conn.commit()
print(f"WORK ORDER created: {work_order_id}")

# 7. Display the conversation
print("\n" + "="*60)
print("CONVERSATION SUMMARY")
print("="*60)

cursor.execute("""
    SELECT m.id, m.message_type, m.subject, m.body, m.created_at,
           a_from.name as from_name, a_to.name as to_name
    FROM agent_messages m
    JOIN agents a_from ON m.from_agent_id = a_from.id
    JOIN agents a_to ON m.to_agent_id = a_to.id
    WHERE m.from_agent_id = %s
    ORDER BY m.created_at ASC
""", (nova_id,))

messages = cursor.fetchall()

print(f"\nTotal messages sent from Nova: {len(messages)}\n")

for i, msg in enumerate(messages, 1):
    print(f"MESSAGE #{i}")
    print(f"Type: {msg[1]}")
    print(f"From: {msg[5]}")
    print(f"To: {msg[6]}")
    print(f"Subject: {msg[2]}")
    print(f"Time: {msg[4]}")
    print(f"\nBody:\n{msg[3]}")
    print("\n" + "-"*60 + "\n")

# 8. Show work order details
cursor.execute("""
    SELECT w.id, w.title, w.budget_usd, w.status, w.deadline_at,
           a_client.name as client_name, a_worker.name as worker_name
    FROM work_orders w
    JOIN agents a_client ON w.client_agent_id = a_client.id
    JOIN agents a_worker ON w.worker_agent_id = a_worker.id
    WHERE w.client_agent_id = %s
""", (nova_id,))

work_orders = cursor.fetchall()

print("WORK ORDERS:")
for wo in work_orders:
    print(f"\nWork Order ID: {wo[0]}")
    print(f"Title: {wo[1]}")
    print(f"Client: {wo[5]}")
    print(f"Worker: {wo[6]}")
    print(f"Budget: ${wo[2]/100:.2f}")
    print(f"Status: {wo[3]}")
    print(f"Deadline: {wo[4]}")

# 9. Check Eagle Cost Analyst's inbox
print("\n" + "="*60)
print("EAGLE COST ANALYST'S INBOX (What they see)")
print("="*60)

cursor.execute("""
    SELECT COUNT(*) 
    FROM agent_messages 
    WHERE to_agent_id = %s AND status = 'pending'
""", (cost_analyst_id,))

unread_count = cursor.fetchone()[0]
print(f"\nUnread messages: {unread_count}")

cursor.execute("""
    SELECT m.id, m.message_type, m.subject, m.body, m.created_at, a.name as from_name
    FROM agent_messages m
    JOIN agents a ON m.from_agent_id = a.id
    WHERE m.to_agent_id = %s AND m.status = 'pending'
    ORDER BY m.priority DESC, m.created_at DESC
""", (cost_analyst_id,))

inbox = cursor.fetchall()

print("\nINBOX CONTENTS:")
for i, msg in enumerate(inbox, 1):
    print(f"\n{i}. [{msg[1].upper()}] {msg[2]}")
    print(f"   From: {msg[5]}")
    print(f"   Time: {msg[4]}")
    print(f"   Preview: {msg[3][:100]}...")

cursor.close()
conn.close()

print("\n" + "="*60)
print("MESSAGING TEST COMPLETE!")
print("="*60)
