"""LMS API client service.

This module provides a client for interacting with the LMS backend API.
It handles authentication, error handling, and data fetching.
"""

import httpx
from typing import Optional, List, Dict, Any

from config import settings


class LMSAPIClient:
    """Client for the LMS backend API."""

    def __init__(self):
        self.base_url = settings.lms_api_base_url
        self.api_key = settings.lms_api_key
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create an async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check if the backend is healthy.
        
        Returns:
            Dict with 'status' ('up' or 'down'), 'items_count', and 'details'.
        """
        try:
            client = await self.get_client()
            response = await client.get("/items/")
            if response.status_code == 200:
                items = response.json()
                return {
                    "status": "up",
                    "items_count": len(items),
                    "details": f"Backend responding with {len(items)} items"
                }
            else:
                return {
                    "status": "down",
                    "items_count": 0,
                    "details": f"Unexpected status code: {response.status_code}"
                }
        except httpx.ConnectError as e:
            return {
                "status": "down",
                "items_count": 0,
                "details": f"Connection failed: {str(e)}"
            }
        except Exception as e:
            return {
                "status": "down",
                "items_count": 0,
                "details": f"Error: {str(e)}"
            }

    async def get_labs(self) -> List[Dict[str, Any]]:
        """Get all labs from the backend.
        
        Returns:
            List of lab objects with 'id', 'title', 'type' fields.
        """
        try:
            client = await self.get_client()
            response = await client.get("/items/")
            response.raise_for_status()
            items = response.json()
            # Filter only labs (type == "lab")
            labs = [item for item in items if item.get("type") == "lab"]
            return labs
        except httpx.ConnectError:
            return []
        except Exception:
            return []

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get all items (labs and tasks) from the backend.
        
        Returns:
            List of all items.
        """
        try:
            client = await self.get_client()
            response = await client.get("/items/")
            response.raise_for_status()
            return response.json()
        except httpx.ConnectError:
            return []
        except Exception:
            return []

    async def sync_data(self) -> Dict[str, Any]:
        """Trigger the ETL pipeline to sync data.
        
        Returns:
            Dict with sync results (new_records, total_records).
        """
        try:
            client = await self.get_client()
            response = await client.post("/pipeline/sync", json={})
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status code: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}

    async def get_scores(self, lab_identifier: str) -> Optional[Dict[str, Any]]:
        """Get scores for a specific lab.
        
        Args:
            lab_identifier: Lab identifier (e.g., "lab-01", "lab-07").
            
        Returns:
            Dict with scores data or None if not found.
        """
        try:
            client = await self.get_client()
            response = await client.get(
                "/analytics/scores",
                params={"lab": lab_identifier}
            )
            if response.status_code == 200:
                return {"scores": response.json()}
            return None
        except Exception as e:
            return {"error": str(e)}

    async def get_pass_rates(self, lab_identifier: str) -> Optional[List[Dict[str, Any]]]:
        """Get pass rates for tasks in a specific lab.
        
        Args:
            lab_identifier: Lab identifier (e.g., "lab-01", "lab-07").
            
        Returns:
            List of task pass rates or None if not found.
        """
        try:
            client = await self.get_client()
            response = await client.get(
                "/analytics/pass-rates",
                params={"lab": lab_identifier}
            )
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    async def get_analytics_timeline(self) -> Optional[List[Dict[str, Any]]]:
        """Get submissions timeline analytics.
        
        Returns:
            List of timeline data points.
        """
        try:
            client = await self.get_client()
            response = await client.get("/analytics/timeline")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    async def get_analytics_groups(self) -> Optional[List[Dict[str, Any]]]:
        """Get group performance analytics.
        
        Returns:
            List of group performance data.
        """
        try:
            client = await self.get_client()
            response = await client.get("/analytics/groups")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    async def get_completion_rate(self, lab_identifier: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get completion rate for course or specific lab.
        
        Args:
            lab_identifier: Optional lab identifier.
            
        Returns:
            Dict with completion rate data.
        """
        try:
            client = await self.get_client()
            params = {}
            if lab_identifier:
                params["lab"] = lab_identifier
            response = await client.get("/analytics/completion-rate", params=params)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception:
            return None

    async def get_lab_by_title(self, title_query: str) -> Optional[Dict[str, Any]]:
        """Find a lab by title (partial match).

        Args:
            title_query: The title or partial title to search for.

        Returns:
            Lab object if found, None otherwise.
        """
        labs = await self.get_labs()
        query_lower = title_query.lower()

        for lab in labs:
            if query_lower in lab.get("title", "").lower():
                return lab
        return None

    async def compare_all_labs_scores(self, comparison_type: str = "all") -> Dict[str, Any]:
        """Compare pass rates across all labs.

        Args:
            comparison_type: 'lowest', 'highest', or 'all'.

        Returns:
            Dict with comparison results.
        """
        labs = await self.get_labs()
        lab_scores = []

        for lab in labs:
            lab_id = lab.get("id", 0)
            lab_title = lab.get("title", "Unknown")
            lab_num = str(lab_id).zfill(2)
            lab_identifier = f"lab-{lab_num}"

            pass_rates = await self.get_pass_rates(lab_identifier)
            if pass_rates:
                total_score = sum(t.get("avg_score", 0) for t in pass_rates)
                avg_score = total_score / len(pass_rates) if pass_rates else 0
                total_attempts = sum(t.get("attempts", 0) for t in pass_rates)
                lab_scores.append({
                    "lab_id": lab_id,
                    "title": lab_title,
                    "avg_score": avg_score,
                    "attempts": total_attempts
                })

        if not lab_scores:
            return {"error": "No score data available"}

        lab_scores.sort(key=lambda x: x["avg_score"], reverse=True)

        if comparison_type == "lowest":
            lowest = lab_scores[-1]
            return {
                "result": "lowest",
                "lab": lowest["title"],
                "score": lowest["avg_score"],
                "attempts": lowest["attempts"]
            }
        elif comparison_type == "highest":
            highest = lab_scores[0]
            return {
                "result": "highest",
                "lab": highest["title"],
                "score": highest["avg_score"],
                "attempts": highest["attempts"]
            }
        else:
            return {
                "result": "ranking",
                "labs": lab_scores
            }

    async def find_lowest_lab(self) -> Dict[str, Any]:
        """Find the lab with the lowest pass rate."""
        return await self.compare_all_labs_scores("lowest")

    async def find_highest_lab(self) -> Dict[str, Any]:
        """Find the lab with the highest pass rate."""
        return await self.compare_all_labs_scores("highest")


# Global client instance
lms_client = LMSAPIClient()
