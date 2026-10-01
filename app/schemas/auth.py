from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    repassword : str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
