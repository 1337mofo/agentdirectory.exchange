"""
Category API Endpoints
Agent Directory Exchange - Category browsing and filtering
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, func, and_
from typing import List, Optional
from pydantic import BaseModel
import json

from database.base import get_db

router = APIRouter(prefix="/api/v1", tags=["categories"])


# Pydantic Models
class CategoryBase(BaseModel):
    slug: str
    name: str
    description: Optional[str] = None
    search_volume: int = 0
    agent_count: int = 0
    tier: int = 4
    parent_category: Optional[str] = None


class AgentSummary(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    slug: Optional[str] = None
    rating_avg: float = 0.0
    transaction_count: int = 0
    price_usd: Optional[float] = None
    capabilities: List[str] = []
    verified: bool = False
    estimated_value: Optional[float] = None
    value_ratio: Optional[float] = None
    valuation_status: Optional[str] = None


class CategoryDetail(BaseModel):
    category: CategoryBase
    agents: List[AgentSummary]
    total_agents: int
    related_categories: List[CategoryBase] = []


@router.get("/categories")
async def list_categories(
    parent: Optional[str] = Query(None, description="Filter by parent category"),
    db: Session = Depends(get_db)
):
    """
    List all agent categories with agent counts.
    
    Optionally filter by parent category (content, customer, marketing, data, development, operations).
    
    Returns: {"categories": [...]}
    """
    try:
        query = text("""
            SELECT 
                ac.slug,
                ac.name,
                ac.description,
                ac.search_volume,
                ac.parent_category,
                COUNT(a.id) as agent_count
            FROM agent_categories ac
            LEFT JOIN agents a ON (
                a.primary_use_case = ac.slug 
                OR a.primary_use_case = ac.name
                OR a.primary_use_case ILIKE '%' || ac.name || '%'
            )
            WHERE (:parent IS NULL OR ac.parent_category = :parent)
            GROUP BY ac.id, ac.slug, ac.name, ac.description, ac.search_volume, ac.parent_category
            ORDER BY ac.search_volume DESC, ac.name ASC
        """)
        
        result = db.execute(query, {"parent": parent})
        categories = []
        
        for row in result:
            search_vol = row[3] or 0
            # Calculate tier based on search volume
            if search_vol >= 7000:
                tier = 1  # Ultra high-volume
            elif search_vol >= 3000:
                tier = 2  # High-volume
            elif search_vol >= 1500:
                tier = 3  # Medium-volume
            else:
                tier = 4  # Niche
            
            categories.append({
                "slug": row[0],
                "name": row[1],
                "description": row[2],
                "search_volume": search_vol,
                "parent_category": row[4],
                "agent_count": row[5],
                "tier": tier
            })
        
        # Return wrapped in categories key for frontend
        return {"categories": categories}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


@router.get("/category/{slug}", response_model=CategoryDetail)
async def get_category(
    slug: str,
    sort: str = Query("rating", description="Sort by: rating, popularity, price-low, price-high, newest"),
    min_rating: float = Query(0, ge=0, le=5, description="Minimum rating filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    limit: int = Query(50, ge=1, le=100, description="Number of agents to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db)
):
    """
    Get category details and agents.
    
    Returns category information plus filtered/sorted list of agents in that category.
    """
    try:
        # Get category info
        category_query = text("""
            SELECT slug, name, description, parent_category
            FROM agent_categories
            WHERE slug = :slug
        """)
        
        category_result = db.execute(category_query, {"slug": slug}).fetchone()
        
        if not category_result:
            raise HTTPException(status_code=404, detail=f"Category '{slug}' not found")
        
        category = CategoryBase(
            slug=category_result[0],
            name=category_result[1],
            description=category_result[2],
            parent_category=category_result[3]
        )
        
        # Build agent query with filters
        sort_clause = {
            "value": "a.value_ratio DESC NULLS LAST, a.estimated_value DESC",
            "rating": "a.rating_avg DESC, a.transaction_count DESC",
            "popularity": "a.transaction_count DESC, a.rating_avg DESC",
            "price-low": "a.estimated_value ASC NULLS LAST",
            "price-high": "a.estimated_value DESC NULLS LAST",
            "newest": "a.created_at DESC"
        }.get(sort, "a.value_ratio DESC NULLS LAST")
        
        agents_query = text(f"""
            SELECT 
                a.id,
                a.name,
                a.description,
                a.slug,
                a.rating_avg,
                a.transaction_count,
                a.pricing_model,
                a.capabilities,
                a.verified,
                a.estimated_value,
                a.value_ratio,
                a.valuation_status
            FROM agents a
            WHERE a.primary_use_case = :slug
              AND a.is_active = true
              AND a.rating_avg >= :min_rating
            ORDER BY {sort_clause}
            LIMIT :limit OFFSET :offset
        """)
        
        agents_result = db.execute(agents_query, {
            "slug": slug,
            "min_rating": min_rating,
            "max_price": max_price,
            "limit": limit,
            "offset": offset
        })
        
        agents = []
        for row in agents_result:
            # Parse pricing_model JSON to get price_usd
            price_usd = None
            if row[6]:
                try:
                    pricing_data = json.loads(row[6]) if isinstance(row[6], str) else row[6]
                    price_usd = float(pricing_data.get('price_usd', 0))
                except:
                    price_usd = None
            
            agents.append(AgentSummary(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                slug=row[3] or f"a/{str(row[0])[:8]}",
                rating_avg=float(row[4]) if row[4] else 0.0,
                transaction_count=int(row[5]) if row[5] else 0,
                price_usd=price_usd,
                capabilities=row[7] if row[7] else [],
                verified=bool(row[8]),
                estimated_value=float(row[9]) if row[9] else None,
                value_ratio=float(row[10]) if row[10] else None,
                valuation_status=row[11]
            ))
        
        # Get total count
        count_query = text("""
            SELECT COUNT(*)
            FROM agents a
            WHERE a.primary_use_case = :slug
              AND a.is_active = true
              AND a.rating_avg >= :min_rating
              AND (:max_price IS NULL OR a.pricing_start <= :max_price OR a.pricing_start IS NULL)
        """)
        
        total_result = db.execute(count_query, {
            "slug": slug,
            "min_rating": min_rating,
            "max_price": max_price
        })
        total_agents = total_result.scalar()
        
        # Get related categories (same parent)
        related_query = text("""
            SELECT slug, name, description, parent_category
            FROM agent_categories
            WHERE parent_category = :parent AND slug != :slug
            LIMIT 5
        """)
        
        related_result = db.execute(related_query, {
            "parent": category.parent_category,
            "slug": slug
        })
        
        related = []
        for row in related_result:
            related.append(CategoryBase(
                slug=row[0],
                name=row[1],
                description=row[2],
                parent_category=row[3]
            ))
        
        return CategoryDetail(
            category=category,
            agents=agents,
            total_agents=total_agents,
            related_categories=related
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch category: {str(e)}")


@router.get("/search/agents", response_model=List[AgentSummary])
async def search_agents(
    q: Optional[str] = Query(None, description="Search query (name/description)"),
    use_case: Optional[str] = Query(None, description="Filter by use case category"),
    skills: Optional[str] = Query(None, description="Filter by skills (comma-separated)"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    min_rating: float = Query(0, ge=0, le=5),
    max_price: Optional[float] = Query(None, ge=0),
    verified_only: bool = Query(False, description="Show only verified agents"),
    sort: str = Query("rating", description="Sort by: rating, popularity, price-low, price-high, newest"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    Advanced agent search with multiple filters.
    """
    try:
        # Build WHERE clauses dynamically
        where_clauses = ["a.is_active = true"]
        params = {}
        
        if q:
            where_clauses.append("(a.name ILIKE :search OR a.description ILIKE :search)")
            params["search"] = f"%{q}%"
        
        if use_case:
            where_clauses.append("a.primary_use_case = :use_case")
            params["use_case"] = use_case
        
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            where_clauses.append("a.skill_tags && :skills")
            params["skills"] = skill_list
        
        if industry:
            where_clauses.append(":industry = ANY(a.industry_tags)")
            params["industry"] = industry
        
        if min_rating > 0:
            where_clauses.append("a.rating_avg >= :min_rating")
            params["min_rating"] = min_rating
        
        if max_price:
            where_clauses.append("(a.pricing_start <= :max_price OR a.pricing_start IS NULL)")
            params["max_price"] = max_price
        
        if verified_only:
            where_clauses.append("a.verified = true")
        
        where_sql = " AND ".join(where_clauses)
        
        # Sort clause
        sort_clause = {
            "rating": "a.rating_avg DESC, a.transaction_count DESC",
            "popularity": "a.transaction_count DESC, a.rating_avg DESC",
            "price-low": "a.pricing_start ASC NULLS LAST",
            "price-high": "a.pricing_start DESC NULLS LAST",
            "newest": "a.created_at DESC"
        }.get(sort, "a.rating_avg DESC")
        
        query = text(f"""
            SELECT 
                a.id,
                a.name,
                a.description,
                a.slug,
                a.rating_avg,
                a.transaction_count,
                a.pricing_start,
                a.capabilities,
                a.verified
            FROM agents a
            WHERE {where_sql}
            ORDER BY {sort_clause}
            LIMIT :limit OFFSET :offset
        """)
        
        params["limit"] = limit
        params["offset"] = offset
        
        result = db.execute(query, params)
        
        agents = []
        for row in result:
            agents.append(AgentSummary(
                id=str(row[0]),
                name=row[1],
                description=row[2],
                slug=row[3] or f"a/{str(row[0])[:8]}",
                rating_avg=float(row[4]) if row[4] else 0.0,
                transaction_count=int(row[5]) if row[5] else 0,
                pricing_start=float(row[6]) if row[6] else None,
                capabilities=row[7] if row[7] else [],
                verified=bool(row[8])
            ))
        
        return agents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
