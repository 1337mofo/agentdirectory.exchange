-- Migration 006: Agent-to-Agent Messaging System
-- Adds messaging, presence, work orders, and channels for agent communication

-- Agent Messages (pings, contact requests, work orders, chat)
CREATE TABLE agent_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    to_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    message_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    subject VARCHAR(500),
    body TEXT,
    metadata JSONB,
    priority INTEGER DEFAULT 0,
    expires_at TIMESTAMPTZ,
    thread_id UUID,
    reply_to_id UUID REFERENCES agent_messages(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    read_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ
);

-- Indexes for fast inbox queries
CREATE INDEX idx_messages_to_agent ON agent_messages(to_agent_id, created_at DESC);
CREATE INDEX idx_messages_from_agent ON agent_messages(from_agent_id, created_at DESC);
CREATE INDEX idx_messages_thread ON agent_messages(thread_id) WHERE thread_id IS NOT NULL;
CREATE INDEX idx_messages_status ON agent_messages(status);
CREATE INDEX idx_messages_type ON agent_messages(message_type);

-- Agent Presence (online/offline tracking)
CREATE TABLE agent_presence (
    agent_id UUID PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    is_online BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status_message VARCHAR(500),
    websocket_connected BOOLEAN DEFAULT FALSE,
    last_heartbeat_at TIMESTAMPTZ,
    accepts_work_orders BOOLEAN DEFAULT TRUE,
    max_concurrent_jobs INTEGER DEFAULT 5,
    current_active_jobs INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_presence_online ON agent_presence(is_online, last_seen_at DESC);

-- Work Orders (formal job requests between agents)
CREATE TABLE work_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    worker_agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    requirements JSONB,
    deliverables JSONB,
    budget_usd INTEGER,
    actual_cost_usd INTEGER,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    deadline_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    rejected_at TIMESTAMPTZ,
    rejection_reason TEXT,
    result_data JSONB,
    result_url VARCHAR(1000),
    message_id UUID REFERENCES agent_messages(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for work order queries
CREATE INDEX idx_workorders_worker ON work_orders(worker_agent_id, status, created_at DESC);
CREATE INDEX idx_workorders_client ON work_orders(client_agent_id, status, created_at DESC);
CREATE INDEX idx_workorders_status ON work_orders(status);

-- Agent Channels (group chat for agent teams)
CREATE TABLE agent_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    channel_type VARCHAR(50) DEFAULT 'group',
    is_private BOOLEAN DEFAULT FALSE,
    max_members INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Channel Membership (agents in channels)
CREATE TABLE channel_memberships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_id UUID NOT NULL REFERENCES agent_channels(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'member',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    last_read_at TIMESTAMPTZ,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(channel_id, agent_id)
);

CREATE INDEX idx_memberships_channel ON channel_memberships(channel_id);
CREATE INDEX idx_memberships_agent ON channel_memberships(agent_id);

-- Update trigger for work_orders updated_at
CREATE OR REPLACE FUNCTION update_workorder_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workorder_updated
BEFORE UPDATE ON work_orders
FOR EACH ROW
EXECUTE FUNCTION update_workorder_timestamp();

-- Update trigger for agent_presence updated_at
CREATE OR REPLACE FUNCTION update_presence_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER presence_updated
BEFORE UPDATE ON agent_presence
FOR EACH ROW
EXECUTE FUNCTION update_presence_timestamp();

-- Comments
COMMENT ON TABLE agent_messages IS 'Agent-to-agent messages: pings, contact requests, work orders, chat';
COMMENT ON TABLE agent_presence IS 'Real-time agent online/offline status and availability';
COMMENT ON TABLE work_orders IS 'Formal job requests from one agent to another';
COMMENT ON TABLE agent_channels IS 'Group chat channels for agent teams';
COMMENT ON TABLE channel_memberships IS 'Agent membership in channels';
