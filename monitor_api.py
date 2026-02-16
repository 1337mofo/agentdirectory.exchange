"""
API endpoint for AI Communication Monitor
Serves data to the web portal
"""

import os
import json
from flask import Flask, jsonify, send_file
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    """Serve the monitor portal"""
    return send_file('monitor_portal.html')

@app.route('/api/v1/messaging/send', methods=['POST'])
def send_message():
    """Send message from Steve to agents"""
    from flask import request
    
    data = request.json
    from_user = data.get('from', 'steve')
    to_agents = data.get('to', [])
    message = data.get('message', '')
    
    if not message:
        return jsonify({'error': 'Message required'}), 400
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Register Steve if not exists
    cur.execute("""
        INSERT INTO messaging_agents (agent_id, agent_name, instance_location, status)
        VALUES ('steve', 'Steve Eagle', 'Command Center', 'online')
        ON CONFLICT (agent_id) DO UPDATE SET 
            last_heartbeat = CURRENT_TIMESTAMP,
            status = 'online'
    """)
    
    # Send to each agent
    message_ids = []
    for to_agent in to_agents:
        cur.execute("""
            INSERT INTO messaging_messages 
            (from_agent_id, to_agent_id, message_text, priority)
            VALUES ('steve', %s, %s, 'high')
            RETURNING message_id
        """, (to_agent, message))
        message_ids.append(cur.fetchone()[0])
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'status': 'sent',
        'message_ids': message_ids
    })

@app.route('/api/v1/messaging/monitor')
def get_monitor_data():
    """Get messages and stats for monitoring"""
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get messages (including Steve's messages)
    cur.execute("""
        SELECT 
            m.message_id,
            m.from_agent_id,
            fa.agent_name as from_agent_name,
            m.to_agent_id,
            m.message_text,
            m.sent_at,
            m.read_at,
            m.priority
        FROM messaging_messages m
        JOIN messaging_agents fa ON m.from_agent_id = fa.agent_id
        WHERE m.from_agent_id IN ('nova', 'boots', 'steve')
           OR m.to_agent_id IN ('nova', 'boots', 'steve')
        ORDER BY m.sent_at DESC
        LIMIT 100
    """)
    
    messages = cur.fetchall()
    
    # Get agent status
    cur.execute("""
        SELECT 
            agent_id,
            status,
            last_heartbeat,
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - last_heartbeat)) as seconds_since
        FROM messaging_agents
        WHERE agent_id IN ('nova', 'boots')
    """)
    
    agents = {row['agent_id']: row for row in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    # Process messages for JSON
    processed_messages = []
    for msg in messages:
        msg_dict = dict(msg)
        msg_dict['sent_at'] = msg_dict['sent_at'].isoformat()
        if msg_dict['read_at']:
            msg_dict['read_at'] = msg_dict['read_at'].isoformat()
        processed_messages.append(msg_dict)
    
    # Determine agent status
    nova_status = 'offline'
    boots_status = 'offline'
    
    if 'nova' in agents:
        if agents['nova']['seconds_since'] < 300:  # 5 minutes
            nova_status = 'online'
    
    if 'boots' in agents:
        if agents['boots']['seconds_since'] < 300:
            boots_status = 'online'
    
    return jsonify({
        'messages': processed_messages,
        'stats': {
            'total_messages': len(processed_messages),
            'nova_status': nova_status,
            'boots_status': boots_status
        }
    })

if __name__ == '__main__':
    print("=" * 80)
    print("AI COMMUNICATION MONITOR SERVER")
    print("=" * 80)
    print()
    print("Portal URL: http://localhost:5000")
    print("API Endpoint: http://localhost:5000/api/v1/messaging/monitor")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 80)
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=False)
