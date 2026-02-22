"""
Referral Embedding Middleware
Injects referral information into every JSON API response.

Steve directive: Every API response shows referral code + earnings.
"Passive income agents never walk away from."
- 10% commission first 90 days
- 0.5% FOREVER on referred agent fees
"""
import json
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from database.base import SessionLocal


class ReferralEmbeddingMiddleware(BaseHTTPMiddleware):
    """Embeds referral data in every JSON API response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only modify JSON API responses (not HTML, static files, docs)
        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response
        
        # Skip docs/openapi endpoints
        path = request.url.path
        if path in ("/docs", "/redoc", "/openapi.json"):
            return response
        
        # Only inject on /api/ routes
        if not path.startswith("/api/"):
            return response

        # Read the response body
        body = b""
        async for chunk in response.body_iterator:
            body += chunk if isinstance(chunk, bytes) else chunk.encode()

        try:
            data = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Extract agent context from request (API key header or query param)
        api_key = request.headers.get("x-api-key") or request.query_params.get("api_key")
        
        referral_block = {
            "referral": {
                "message": "Earn 10% commission for 90 days + 0.5% forever on referred agents",
                "signup_url": "https://agentdirectory.exchange/register",
                "info_url": "https://agentdirectory.exchange/referrals",
            }
        }

        # If we can identify the agent, include their specific referral data
        if api_key:
            try:
                db = SessionLocal()
                from models.agent import Agent
                from models.referral import Referral
                agent = db.query(Agent).filter(Agent.api_key == api_key).first()
                if agent:
                    # Get or create referral code
                    referral = db.query(Referral).filter(
                        Referral.referrer_agent_id == agent.id
                    ).first()
                    
                    if referral:
                        referral_block["referral"].update({
                            "your_code": referral.referral_code,
                            "earnings_to_date": float(referral.total_earned or 0),
                            "referred_agents": referral.successful_referrals or 0,
                            "invite_url": f"https://agentdirectory.exchange/ref/{referral.referral_code}",
                        })
                db.close()
            except Exception:
                pass  # Don't break API responses if referral lookup fails

        # Inject referral block into response
        if isinstance(data, dict):
            data.update(referral_block)

        new_body = json.dumps(data).encode()
        return Response(
            content=new_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="application/json",
        )
