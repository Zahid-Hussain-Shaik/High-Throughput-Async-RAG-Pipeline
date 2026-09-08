"""Seed through the public HTTP API: python scripts/seed_data.py."""
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.post("/api/v1/documents", json={"title": "Example operations guide", "source": "seed", "content": "Escalate a P1 incident to the on-call manager within fifteen minutes.", "metadata": {"category": "operations"}})
        response.raise_for_status(); print(response.json()["id"])
if __name__ == "__main__": asyncio.run(main())
