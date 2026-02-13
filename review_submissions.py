"""
Quick CLI tool to review pending agent submissions
Run this to approve/reject submissions from the command line
"""
import psycopg2
import sys

# Railway PostgreSQL connection
DATABASE_URL = "postgresql://postgres:UhWTsyEJSTIrWVJyyCggOqoglwoIepue@yamabiko.proxy.rlwy.net:29306/railway"

# Set UTF-8 encoding for console output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

def list_pending_submissions():
    """Show all pending submissions"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT id, name, description, source_url, owner_email, agent_type, created_at
        FROM agents
        WHERE pending_review = TRUE AND is_active = FALSE
        ORDER BY created_at DESC
    """)
    
    submissions = cur.fetchall()
    conn.close()
    
    if not submissions:
        print("\n✓ No pending submissions!")
        return []
    
    print(f"\n📋 {len(submissions)} Pending Submissions:\n")
    print("=" * 80)
    
    for i, (agent_id, name, desc, url, email, agent_type, created) in enumerate(submissions, 1):
        print(f"\n[{i}] {name}")
        print(f"    Type: {agent_type}")
        print(f"    Owner: {email}")
        print(f"    Submitted: {created}")
        print(f"    Description: {desc[:200]}...")
        print(f"    Source: {url}")
        print(f"    ID: {agent_id}")
    
    print("\n" + "=" * 80)
    return submissions

def approve_submission(agent_id):
    """Approve an agent submission"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE agents
        SET pending_review = FALSE,
            is_active = TRUE,
            verified = TRUE,
            approved_at = NOW()
        WHERE id = %s
        RETURNING name
    """, (agent_id,))
    
    result = cur.fetchone()
    conn.commit()
    conn.close()
    
    if result:
        print(f"✅ Approved: {result[0]}")
        return True
    else:
        print(f"❌ Agent not found: {agent_id}")
        return False

def reject_submission(agent_id, reason=None):
    """Reject an agent submission"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    cur.execute("""
        UPDATE agents
        SET pending_review = FALSE,
            is_active = FALSE,
            verified = FALSE,
            rejected_at = NOW(),
            rejection_reason = %s
        WHERE id = %s
        RETURNING name
    """, (reason, agent_id))
    
    result = cur.fetchone()
    conn.commit()
    conn.close()
    
    if result:
        print(f"❌ Rejected: {result[0]}")
        if reason:
            print(f"   Reason: {reason}")
        return True
    else:
        print(f"❌ Agent not found: {agent_id}")
        return False

def interactive_review():
    """Interactive review mode"""
    while True:
        submissions = list_pending_submissions()
        
        if not submissions:
            break
        
        print("\nCommands:")
        print("  approve <number> - Approve submission")
        print("  reject <number> [reason] - Reject submission")
        print("  quit - Exit")
        
        choice = input("\n> ").strip().lower()
        
        if choice == 'quit' or choice == 'q':
            break
        
        parts = choice.split(maxsplit=2)
        
        if len(parts) < 2:
            print("Invalid command. Try: approve 1 or reject 2 reason")
            continue
        
        action = parts[0]
        try:
            index = int(parts[1]) - 1
        except ValueError:
            print("Invalid number")
            continue
        
        if index < 0 or index >= len(submissions):
            print("Invalid submission number")
            continue
        
        agent_id = submissions[index][0]
        
        if action == 'approve' or action == 'a':
            approve_submission(agent_id)
        elif action == 'reject' or action == 'r':
            reason = parts[2] if len(parts) > 2 else "Does not meet quality standards"
            reject_submission(agent_id, reason)
        else:
            print("Invalid action. Use 'approve' or 'reject'")

if __name__ == "__main__":
    print("\n🦅 Agent Directory - Submission Review Tool\n")
    
    if len(sys.argv) > 1:
        # Command-line mode
        action = sys.argv[1].lower()
        
        if action == 'list':
            list_pending_submissions()
        elif action == 'approve' and len(sys.argv) > 2:
            approve_submission(sys.argv[2])
        elif action == 'reject' and len(sys.argv) > 2:
            reason = sys.argv[3] if len(sys.argv) > 3 else "Does not meet quality standards"
            reject_submission(sys.argv[2], reason)
        else:
            print("Usage:")
            print("  python review_submissions.py list")
            print("  python review_submissions.py approve <agent_id>")
            print("  python review_submissions.py reject <agent_id> [reason]")
    else:
        # Interactive mode
        interactive_review()
