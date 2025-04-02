from pydantic import BaseModel, Field
from typing import List, Optional

class DockerfileRequest(BaseModel):
    language: str = Field(..., description="Programming language (e.g., python, node, java)")
    version: Optional[str] = Field(None, description="Version of the language (e.g., 3.11, 18, 20)")
    dependencies: Optional[List[str]] = Field(None, description="List of dependencies to include")
    port: Optional[int] = Field(None, description="Port to expose in the Dockerfile")
    app_type: Optional[str] = Field(None, description="Type of application (e.g., web, cli, api)")
    additional_instructions: Optional[str] = Field(None, description="Custom instructions for the AI")
    
    class Config:
        schema_extra = {
            "example": {
                "language": "python",
                "version": "3.11",
                "dependencies": ["flask", "requests"],
                "port": 5000,
                "app_type": "web",
                "additional_instructions": "Include healthcheck"
            }
        }