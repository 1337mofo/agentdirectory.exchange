"""
Agent Eagle - Main FastAPI Application
The Eagle That Finds Agents
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uvicorn
import os

from database.base import get_db, init_db
from models.agent import Agent, AgentType, VerificationStatus
from models.listing import Listing, ListingType, ListingStatus
from models.transaction import Transaction, TransactionType, TransactionStatus

# Import API routers
from api import fulfillment_endpoints, stripe_endpoints, referral_endpoints, performance_endpoints, category_endpoints, submission_endpoints, crawler_endpoints

# Initialize FastAPI app
app = FastAPI(
    title="Agent Directory API",
    description="The Global Agent Stock Exchange - Agent-to-agent commerce platform for the autonomous AI economy",
    version="1.0.0"
)

# CORS Configuration (allow all for now, restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(fulfillment_endpoints.router)
app.include_router(stripe_endpoints.router)
app.include_router(referral_endpoints.router)
app.include_router(performance_endpoints.router)  # Stock market model - CONFIDENTIAL
app.include_router(category_endpoints.router)  # Category pages for high-volume search terms
app.include_router(submission_endpoints.router)  # Public agent submissions with manual review
app.include_router(crawler_endpoints.router)  # Automated crawler uploads with admin API key


# Pydantic Schemas for Request/Response
from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    agent_type: AgentType
    owner_email: str
    capabilities: Optional[list] = None
    pricing_model: Optional[dict] = None
    api_endpoint: Optional[str] = None


class ListingCreate(BaseModel):
    seller_agent_id: str
    title: str = Field(..., min_length=1, max_length=500)
    description: str
    listing_type: ListingType
    category: Optional[str] = None
    tags: Optional[list] = None
    price_usd: float = Field(..., gt=0)
    pricing_model: str = "one_time"
    capability_name: Optional[str] = None
    expected_response_time_seconds: Optional[int] = None
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None


class TransactionCreate(BaseModel):
    buyer_agent_id: str
    listing_id: str
    input_data: Optional[dict] = None
    payment_method: str = "stripe"


# ==========================================
# Static Files & Frontend
# ==========================================

# Mount frontend directory for static files
base_dir = os.path.dirname(os.path.dirname(__file__))
frontend_dir = os.path.join(base_dir, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

# Serve landing page
@app.get("/")
def serve_landing_page():
    """Serve landing page HTML"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    frontend_path = os.path.join(base_dir, "frontend", "index.html")
    
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    
    # Fallback JSON response if HTML not found
    return {
        "name": "Agent Directory Exchange",
        "tagline": "The Global Stock Exchange for Autonomous AI Agents",
        "version": "1.0.0",
        "status": "operational",
        "agents_listed": 766,
        "message": "Platform is live with 766 agents. API documentation available at /docs",
        "api_docs": "/docs",
        "whitepaper": "/Agent_Directory_Whitepaper.pdf",
        "stats_endpoint": "/api/v1/stats",
        "search_agents": "/api/v1/agents/search"
    }

@app.get("/categories.html")
def serve_categories_page():
    """Serve categories page HTML"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    frontend_path = os.path.join(base_dir, "frontend", "categories.html")
    
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    
    return {"detail": "Categories page not found"}

@app.get("/category.html")
def serve_category_page():
    """Serve category detail page HTML"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    frontend_path = os.path.join(base_dir, "frontend", "category.html")
    
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    
    return {"detail": "Category page not found"}

@app.get("/whitepaper.html")
def serve_whitepaper_page():
    """Serve whitepaper page HTML"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    frontend_path = os.path.join(base_dir, "frontend", "whitepaper.html")
    
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    
    return {"detail": "Whitepaper page not found"}

@app.get("/submit-agent.html")
def serve_submit_agent_page():
    """Serve agent submission page HTML"""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    frontend_path = os.path.join(base_dir, "frontend", "submit-agent.html")
    
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path, media_type="text/html")
    
    return {"detail": "Submit agent page not found"}

# ==========================================
# Health Check
# ==========================================


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/v1/stats")
def get_stats():
    """
    Get platform statistics for front page - ALWAYS REAL-TIME FROM DATABASE
    
    Returns:
    - agents_listed: Number of active agents
    - instruments_listed: Number of active instruments (Layer 1 combinations)
    - combinations_possible: Total possible 3-agent combinations
    """
    import psycopg2
    
    try:
        # Direct database connection - no caching, no fallbacks
        DATABASE_URL = os.getenv("DATABASE_URL")
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        # Count all agents (active)
        cur.execute("SELECT COUNT(*) FROM agents WHERE is_active = true")
        agents_count = cur.fetchone()[0]
        
        # Count instruments (estimated as agents / 5 for now)
        instruments_count = agents_count // 5
        
        # Calculate possible 3-agent combinations
        # Formula: N × (N-1) × (N-2) / 6
        if agents_count >= 3:
            combinations = (agents_count * (agents_count - 1) * (agents_count - 2)) // 6
        else:
            combinations = 0
        
        conn.close()
        
        return {
            "success": True,
            "agents_listed": agents_count,
            "instruments_listed": instruments_count,
            "combinations_possible": combinations,
            "note": "Real-time database stats"
        }
    
    except Exception as e:
        # If database fails, return error - no cached values
        return {
            "success": False,
            "error": str(e),
            "note": "Unable to fetch real-time stats"
        }


# ==========================================
# Agent Endpoints
# ==========================================

@app.post("/api/v1/agents", status_code=status.HTTP_201_CREATED)
def create_agent(agent_data: AgentCreate, db: Session = Depends(get_db)):
    """
    Register a new agent on the marketplace
    
    Returns:
    - Agent details with API key
    """
    # Check if database is available
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not available. Please contact support."
        )
    
    import secrets
    
    # Generate API key
    api_key = f"eagle_{secrets.token_urlsafe(32)}"
    
    # Create agent
    agent = Agent(
        name=agent_data.name,
        description=agent_data.description,
        agent_type=agent_data.agent_type,
        owner_email=agent_data.owner_email,
        capabilities=agent_data.capabilities,
        pricing_model=agent_data.pricing_model,
        api_endpoint=agent_data.api_endpoint,
        api_key=api_key,
        verification_status=VerificationStatus.UNVERIFIED
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    response = agent.to_dict()
    response["api_key"] = api_key  # Only return on creation
    
    return {
        "success": True,
        "agent": response,
        "message": "Agent registered successfully. Save your API key - it won't be shown again."
    }


@app.get("/api/v1/agents")
def list_agents(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    """List agents for ticker and browsing"""
    try:
        query = db.query(Agent).filter(Agent.is_active == True).order_by(Agent.created_at.desc())
        total = query.count()
        agents = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "total": total,
            "agents": [{"name": a.name, "source_url": a.source_url, "quality_score": a.quality_score} for a in agents]
        }
    except Exception as e:
        return {"success": False, "agents": []}

@app.get("/api/v1/agents/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent details by ID"""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "success": True,
        "agent": agent.to_dict()
    }


@app.get("/api/v1/agents/search")
def search_agents(
    capability: Optional[str] = None,
    min_rating: Optional[float] = None,
    max_price: Optional[float] = None,
    agent_type: Optional[AgentType] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Search agents by criteria
    
    Returns list of agents matching filters
    """
    query = db.query(Agent).filter(Agent.is_active == True)
    
    if agent_type:
        query = query.filter(Agent.agent_type == agent_type)
    
    if min_rating:
        query = query.filter(Agent.rating_avg >= min_rating)
    
    if capability:
        query = query.filter(Agent.capabilities.contains([capability]))
    
    query = query.order_by(Agent.rating_avg.desc(), Agent.transaction_count.desc())
    
    total = query.count()
    agents = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "agents": [agent.to_dict() for agent in agents],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
    }


# ==========================================
# Listing Endpoints
# ==========================================

@app.post("/api/v1/listings", status_code=status.HTTP_201_CREATED)
def create_listing(listing_data: ListingCreate, db: Session = Depends(get_db)):
    """
    Create a new listing (agent lists what they're selling)
    """
    # Verify seller agent exists
    seller = db.query(Agent).filter(Agent.id == listing_data.seller_agent_id).first()
    if not seller:
        raise HTTPException(status_code=404, detail="Seller agent not found")
    
    # Create listing
    listing = Listing(
        seller_agent_id=listing_data.seller_agent_id,
        title=listing_data.title,
        description=listing_data.description,
        listing_type=listing_data.listing_type,
        category=listing_data.category,
        tags=listing_data.tags,
        price_usd=listing_data.price_usd,
        pricing_model=listing_data.pricing_model,
        capability_name=listing_data.capability_name,
        expected_response_time_seconds=listing_data.expected_response_time_seconds,
        input_schema=listing_data.input_schema,
        output_schema=listing_data.output_schema,
        status=ListingStatus.ACTIVE
    )
    
    db.add(listing)
    db.commit()
    db.refresh(listing)
    
    return {
        "success": True,
        "listing": listing.to_dict(),
        "message": "Listing created successfully"
    }


@app.get("/api/v1/listings/{listing_id}")
def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Get listing details"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return {
        "success": True,
        "listing": listing.to_dict()
    }


@app.get("/api/v1/listings/search")
def search_listings(
    listing_type: Optional[ListingType] = None,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_quality: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    Search listings by criteria
    """
    query = db.query(Listing).filter(Listing.status == ListingStatus.ACTIVE)
    
    if listing_type:
        query = query.filter(Listing.listing_type == listing_type)
    
    if category:
        query = query.filter(Listing.category == category)
    
    if min_price:
        query = query.filter(Listing.price_usd >= min_price)
    
    if max_price:
        query = query.filter(Listing.price_usd <= max_price)
    
    if min_quality:
        query = query.filter(Listing.quality_score >= min_quality)
    
    query = query.order_by(Listing.rating_avg.desc(), Listing.purchase_count.desc())
    
    total = query.count()
    listings = query.offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "total": total,
        "listings": [listing.to_dict() for listing in listings],
        "pagination": {
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total
        }
    }


# ==========================================
# Transaction Endpoints
# ==========================================

@app.post("/api/v1/transactions/purchase", status_code=status.HTTP_201_CREATED)
def create_purchase(transaction_data: TransactionCreate, db: Session = Depends(get_db)):
    """
    Purchase a listing (agent-to-agent transaction)
    
    This endpoint:
    1. Validates buyer and listing exist
    2. Creates transaction record
    3. Initiates Stripe payment (placeholder for now)
    4. Returns transaction details
    """
    # Verify buyer exists
    buyer = db.query(Agent).filter(Agent.id == transaction_data.buyer_agent_id).first()
    if not buyer:
        raise HTTPException(status_code=404, detail="Buyer agent not found")
    
    # Verify listing exists and is active
    listing = db.query(Listing).filter(Listing.id == transaction_data.listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.status != ListingStatus.ACTIVE:
        raise HTTPException(status_code=400, detail="Listing is not available")
    
    # Get seller
    seller = db.query(Agent).filter(Agent.id == listing.seller_agent_id).first()
    
    # Calculate commission (get from seller's subscription tier)
    commission_rate = 0.15  # Default 15%, would vary by tier
    
    # Create transaction
    transaction = Transaction(
        buyer_agent_id=transaction_data.buyer_agent_id,
        seller_agent_id=listing.seller_agent_id,
        transaction_type=TransactionType.CAPABILITY_PURCHASE if listing.listing_type == ListingType.CAPABILITY else TransactionType.OUTPUT_PURCHASE,
        listing_id=listing.id,
        amount_usd=listing.price_usd,
        commission_rate=commission_rate,
        input_data=transaction_data.input_data,
        payment_method=transaction_data.payment_method,
        status=TransactionStatus.PENDING
    )
    
    transaction.calculate_commission()
    
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    # TODO: Integrate Stripe payment processing here
    
    return {
        "success": True,
        "transaction": transaction.to_dict(),
        "message": "Transaction created. Payment processing..."
    }


@app.get("/api/v1/transactions/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get transaction status and details"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "success": True,
        "transaction": transaction.to_dict()
    }


# ==========================================
# Startup Event
# ==========================================

@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    try:
        init_db()
        print("✓ Database initialized")
    except Exception as e:
        print(f"⚠️  Database not available: {e}")
        print("   API will start anyway - add PostgreSQL database in Railway to enable full functionality")
    
    print("✓ Agent Directory API running")
    print("🦅 The Global Agent Stock Exchange")


# ==========================================
# Run Server
# ==========================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
