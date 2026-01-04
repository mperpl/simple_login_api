from pydantic import BaseModel, ConfigDict, Field, EmailStr, SecretStr


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=16)
    email: EmailStr
    password: SecretStr = Field(min_length=3, max_length=16)


class UserLogin(BaseModel):
    email: EmailStr
    password: SecretStr


class UserChangePassword(BaseModel):
    old_password: SecretStr
    new_password: SecretStr = Field(min_length=3, max_length=16)


class UserDisplay(BaseModel):
    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str
