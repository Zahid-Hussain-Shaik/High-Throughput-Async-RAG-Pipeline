import os
from locust import HttpUser, between, task


class RAGUser(HttpUser):
    host = os.getenv("TARGET_HOST", "http://localhost:8000")
    wait_time = between(0.01, 0.1)
    @task
    def query(self):
        self.client.post("/api/v1/query", json={"query": "What does the documentation say about incident escalation?", "top_k": 5}, name="/api/v1/query")
