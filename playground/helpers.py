"""Helper functions for playground tests."""

import os
from pathlib import Path
from typing import Optional

import httpx


async def ensure_gemini_provider(base_url: str = "http://localhost:8000") -> str:
    """
    Ensure a Gemini embedding provider is configured.
    
    Reads GEMINI_API_KEY from .env file in project root and creates/returns provider ID.
    
    Args:
        base_url: Base URL of the CortexDB gateway
        
    Returns:
        Provider ID (UUID string)
        
    Raises:
        ValueError: If GEMINI_API_KEY is not found in .env
    """
    # Try to read GEMINI_API_KEY from .env
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        # Try to load from .env file
        env_file = Path(__file__).parent.parent / ".env"
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Please create a .env file in the project root with:\n"
            "GEMINI_API_KEY=your-api-key-here"
        )
    
    # Check if provider already exists
    async with httpx.AsyncClient() as client:
        # List existing providers
        try:
            response = await client.get(f"{base_url}/providers/embeddings")
            response.raise_for_status()
            providers = response.json()
            
            # Look for a gemini provider named "test-gemini"
            for provider in providers:
                if provider.get("name") == "test-gemini" and provider.get("enabled"):
                    print(f"   ℹ️  Using existing provider: {provider['id']}")
                    return provider["id"]
        except Exception:
            pass
        
        # Create new provider
        print("   ℹ️  Creating new Gemini embedding provider...")
        response = await client.post(
            f"{base_url}/providers/embeddings",
            json={
                "name": "test-gemini",
                "provider": "gemini",
                "api_key": api_key,
                "embedding_model": "models/embedding-001",
            }
        )
        response.raise_for_status()
        provider_data = response.json()
        provider_id = provider_data["id"]
        print(f"   ✅ Provider created: {provider_id}")
        return provider_id


async def cleanup_test_provider(base_url: str = "http://localhost:8000") -> None:
    """
    Clean up test provider created by ensure_gemini_provider.
    
    Args:
        base_url: Base URL of the CortexDB gateway
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{base_url}/providers/embeddings")
            response.raise_for_status()
            providers = response.json()
            
            for provider in providers:
                if provider.get("name") == "test-gemini":
                    await client.delete(
                        f"{base_url}/providers/embeddings/{provider['id']}"
                    )
                    print(f"   ℹ️  Deleted test provider: {provider['id']}")
        except Exception as e:
            print(f"   ⚠️  Could not cleanup provider: {e}")

