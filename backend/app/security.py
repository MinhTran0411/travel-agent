from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError, ExpiredSignatureError
import httpx
from app.config import get_settings
from typing import List, Optional, Callable, Dict
from functools import wraps

settings = get_settings()
security = HTTPBearer()

class JWKS:
    def __init__(self):
        self.jwks_url = settings.jwks_url
        self._jwks = None

    async def get_jwks(self):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url)
            if response.status_code == 200:
                self._jwks = response.json()
                return self._jwks
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch JWKS"
            )

    def get_key(self, kid):
        if not self._jwks:
            return None
        for key in self._jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None

jwks = JWKS()

async def verify_token(request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Verify token from FastAPI dependency injection and store in request state."""
    try:
        token = credentials.credentials
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get the key ID from the token header
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token header"
            )

        # Get the public key from JWKS
        key = jwks.get_key(kid)
        if not key:
            # Refresh JWKS if key not found
            await jwks.get_jwks()
            key = jwks.get_key(kid)
            if not key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token key"
                )

        # Verify the token signature, issuer, and expiration
        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.jwt_issuer,
            options={
                "verify_exp": True,  # Verify expiration
                "verify_iss": True,  # Verify issuer
                "verify_aud": False  # Don't verify audience
            }
        )

        # Ensure email is present in the token
        if "email" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing email claim"
            )

        # Store token data in request state for middleware
        request.state.token_data = payload
        return payload

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_user_roles(token_data: dict) -> List[str]:
    """Extract roles from token data."""
    return token_data.get("realm_access", {}).get("roles", [])

def require_roles(required_roles: List[str]):
    """Decorator to require specific roles for an endpoint."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get token data from the first argument (self) or from kwargs
            token_data = kwargs.get("token_data")
            if not token_data:
                for arg in args:
                    if isinstance(arg, dict) and "realm_access" in arg:
                        token_data = arg
                        break

            if not token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token data not found"
                )

            user_roles = get_user_roles(token_data)
            if not any(role in user_roles for role in required_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Predefined role requirements
require_admin = require_roles(["ROLE_ADMIN"])
require_user = require_roles(["ROLE_USER"]) 