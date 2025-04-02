from pydantic import BaseModel, Field
from typing import Optional


class BaseImage(BaseModel):
    generic: str = Field(..., description="The generic image name used")
    harbor_path: str = Field(..., description="The full Harbor path that was substituted")

class DockerfileResponse(BaseModel):
    status: str = Field(..., description="Status of the request (success or error)")
    dockerfile_content: str = Field(..., description="The generated Dockerfile content")
    base_image: BaseImage = Field(..., description="Information about the base image used")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "dockerfile_content": "FROM harbor.company.com/custom-images/python:3.11-slim\n\nWORKDIR /app\n\nCOPY . .\n\nRUN pip install flask requests\n\nEXPOSE 5000\n\nCMD [\"python\", \"app.py\"]",
                "base_image": {
                    "generic": "python:3.11-slim",
                    "harbor_path": "harbor.company.com/custom-images/python:3.11-slim-hardened"
                }
            }
        }

class ErrorResponse(BaseModel):
    status: str = Field("error", description="Status of the request (always 'error' for error responses)")
    message: str = Field(..., description="Human-readable error message")
    error_code: Optional[str] = Field(None, description="Specific error code for client handling")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Failed to generate Dockerfile: Language not supported",
                "error_code": "UNSUPPORTED_LANGUAGE"
            }
        }