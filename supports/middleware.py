from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# From our Django Simple JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

# HTTPBearer for extracting Authorization header
security = HTTPBearer()


async def jwt_middleware(request: Request, call_next):
    """
    Middleware for JWT authentication.

    If the request URL path is not in the unprotected_paths list, it will attempt
    to extract and validate the JWT token.

    Args:
        request (Request): The incoming FastAPI request
        call_next: The next middleware or route handler

    Returns:
        Response: The response from the next handler or an error response
    """
    # List of routes that don't need authentication
    unprotected_paths = [
        # Add your unprotected paths here
        "/docs",  # Swagger UI
        "/openapi.json",  # OpenAPI schema
    ]

    if request.url.path not in unprotected_paths:
        try:
            # Extract the Authorization header
            credentials: HTTPAuthorizationCredentials = await security(request)
            token = credentials.credentials

            # Decode and verify the JWT
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Optionally, you can add the payload to request state
            request.state.user = payload

        except jwt.ExpiredSignatureError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Token has expired"},
            )
        except jwt.InvalidTokenError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
            )
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Authorization header is missing or invalid"},
            )

    response = await call_next(request)
    return response
