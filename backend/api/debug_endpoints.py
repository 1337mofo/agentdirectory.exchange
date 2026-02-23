"""
Debug Endpoints - Temporary debugging for rate limiting system
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from database.base import get_db
import traceback

router = APIRouter(prefix="/api/v1/debug", tags=["Debug"])


@router.get("/test-rate-limiting")
def test_rate_limiting_import():
    """Test if rate limiting module imports correctly"""
    try:
        from api import rate_limiting
        return {
            "status": "ok",
            "module": "rate_limiting imported successfully",
            "functions": [
                "get_client_ip",
                "check_ip_signup_limit",
                "is_disposable_email",
                "check_daily_spending_cap"
            ]
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@router.post("/test-registration-flow")
def test_registration_flow(request: Request, db: Session = Depends(get_db)):
    """Test registration flow step by step"""
    results = {}
    
    # Test 1: Import rate limiting
    try:
        from api.rate_limiting import get_client_ip
        results["import"] = "OK"
    except Exception as e:
        results["import"] = f"FAILED: {e}"
        return {"status": "error", "results": results}
    
    # Test 2: Get client IP
    try:
        client_ip = get_client_ip(request)
        results["get_ip"] = f"OK: {client_ip}"
    except Exception as e:
        results["get_ip"] = f"FAILED: {e}"
        return {"status": "error", "results": results}
    
    # Test 3: Check IP limit
    try:
        from api.rate_limiting import check_ip_signup_limit
        ip_allowed = check_ip_signup_limit(client_ip, db)
        results["check_ip_limit"] = f"OK: allowed={ip_allowed}"
    except Exception as e:
        results["check_ip_limit"] = f"FAILED: {e}\n{traceback.format_exc()}"
        return {"status": "error", "results": results}
    
    # Test 4: Check disposable email
    try:
        from api.rate_limiting import is_disposable_email
        is_disposable = is_disposable_email("test@example.com", db)
        results["check_disposable"] = f"OK: disposable={is_disposable}"
    except Exception as e:
        results["check_disposable"] = f"FAILED: {e}\n{traceback.format_exc()}"
        return {"status": "error", "results": results}
    
    # Test 5: Check spending cap
    try:
        from api.rate_limiting import check_daily_spending_cap
        cap_ok = check_daily_spending_cap(db)
        results["check_spending_cap"] = f"OK: within_cap={cap_ok}"
    except Exception as e:
        results["check_spending_cap"] = f"FAILED: {e}\n{traceback.format_exc()}"
        return {"status": "error", "results": results}
    
    return {"status": "success", "results": results}
