from pydantic import AliasChoices, BaseModel, Field


class CredentialsSchema(BaseModel):
    username: str = Field(validation_alias=AliasChoices("email", "username"))
    password: str = Field(validation_alias=AliasChoices("password", "pwd"))


class OTPCodeSchema(BaseModel):
    value: str = Field(validation_alias=AliasChoices("otp", "code"))
