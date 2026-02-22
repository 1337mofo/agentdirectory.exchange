"""
Seed EagleForge ASEAN Toolkit as first real MCP tools on the platform.
Run after migration 007.
"""
import psycopg2
import os
import uuid
from datetime import datetime

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:aRFnDbaXZvAaIKFgFBnpjRmzoanlwGkO@mainline.proxy.rlwy.net:11716/railway"
)

TOOLS = [
    {
        "id": str(uuid.uuid4()),
        "name": "EagleForge ASEAN Toolkit",
        "description": "Unified MCP toolkit for ASEAN business operations. Thai Baht exchange rates (BOT API), Thai business registry lookup (DBD OpenData), and LINE messaging integration. First ASEAN-focused MCP tools in existence.",
        "package_name": "@eagleforge/asean-toolkit",
        "install_command": "npx @eagleforge/asean-toolkit",
        "modules": '["thai-baht-exchange", "thai-biz-lookup", "line-messaging"]',
        "pricing_model": "free",
        "price_usd": 0.0,
        "category": "business-tools",
        "tags": '["asean", "thailand", "currency", "business", "line", "mcp"]',
        "protocol": "mcp",
        "version": "1.0.0",
        "repository_url": "https://github.com/1337mofo/eagleforge-asean-toolkit",
        "documentation_url": "https://agentdirectory.exchange/tools/eagleforge-asean-toolkit",
        "is_active": True,
        "is_verified": True,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Thai Baht Exchange",
        "repository_url": None,
        "documentation_url": None,
        "description": "Real-time THB/ASEAN currency exchange rates via Bank of Thailand API. Supports USD, EUR, GBP, JPY, CNY, SGD, MYR, IDR, PHP, VND, KHR, MMK, LAK, BND.",
        "package_name": "@eagleforge/thai-baht-exchange",
        "install_command": "npx @eagleforge/thai-baht-exchange",
        "modules": '["exchange-rates", "currency-convert"]',
        "pricing_model": "free",
        "price_usd": 0.0,
        "category": "finance",
        "tags": '["currency", "thailand", "baht", "exchange-rates", "asean", "mcp"]',
        "protocol": "mcp",
        "version": "1.0.0",
        "is_active": True,
        "is_verified": True,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Thai Business Lookup",
        "description": "Search Thai company registry via Department of Business Development (DBD) OpenData API. Find company info, registration details, capital, and status.",
        "package_name": "@eagleforge/thai-biz-lookup",
        "install_command": "npx @eagleforge/thai-biz-lookup",
        "modules": '["company-search", "company-details"]',
        "pricing_model": "free",
        "price_usd": 0.0,
        "category": "business-tools",
        "tags": '["thailand", "business", "company", "registry", "dbd", "mcp"]',
        "protocol": "mcp",
        "version": "1.0.0",
        "is_active": True,
        "is_verified": True,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "LINE Messaging",
        "description": "LINE Messaging API integration for 200M+ users across Japan, Thailand, Taiwan, Indonesia. Push messages, broadcast, get user profiles.",
        "package_name": "@eagleforge/line-messaging",
        "install_command": "npx @eagleforge/line-messaging",
        "modules": '["push-message", "broadcast", "get-profile"]',
        "pricing_model": "free",
        "price_usd": 0.0,
        "category": "messaging",
        "tags": '["line", "messaging", "japan", "thailand", "asean", "mcp"]',
        "protocol": "mcp",
        "version": "1.0.0",
        "is_active": True,
        "is_verified": True,
    },
]


def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    for tool in TOOLS:
        tool.setdefault("repository_url", None)
        tool.setdefault("documentation_url", None)
        cur.execute("""
            INSERT INTO tools (id, name, description, package_name, install_command, 
                             modules, pricing_model, price_usd, category, tags, protocol, 
                             version, repository_url, documentation_url, is_active, is_verified)
            VALUES (%(id)s, %(name)s, %(description)s, %(package_name)s, %(install_command)s,
                    %(modules)s::jsonb, %(pricing_model)s, %(price_usd)s, %(category)s, %(tags)s::jsonb,
                    %(protocol)s, %(version)s, %(repository_url)s, %(documentation_url)s,
                    %(is_active)s, %(is_verified)s)
            ON CONFLICT (package_name) DO UPDATE SET
                name = EXCLUDED.name,
                description = EXCLUDED.description,
                modules = EXCLUDED.modules,
                version = EXCLUDED.version,
                updated_at = NOW()
        """, tool)
        print(f"Seeded: {tool['name']}")
    
    conn.commit()
    cur.close()
    conn.close()
    print(f"\nDone. {len(TOOLS)} tools seeded.")


if __name__ == "__main__":
    seed()
