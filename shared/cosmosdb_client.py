"""
CosmosDB client for mood data persistence.
"""
import os
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, exceptions, PartitionKey

logger = logging.getLogger(__name__)


class MoodDatabase:
    """Handles all CosmosDB operations for mood data."""
    
    def __init__(self):
        """Initialize CosmosDB client and connect to database."""
        endpoint = os.getenv("COSMOS_ENDPOINT")
        key = os.getenv("COSMOS_KEY")

        if not endpoint or not key:
            raise ValueError("COSMOS_ENDPOINT and COSMOS_KEY must be set in environment")
        
        try:
            self.client = CosmosClient(endpoint, key)
            self.database = self.client.get_database_client("moodmapper")
            self.container = self.database.get_container_client("moods")
            logger.info("Successfully connected to CosmosDB")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to connect to CosmosDB: {e}")
            raise
    
    def create_mood_entry(
        self,
        user_id: str,
        text: str,
        analysis: None = None,
    ) -> Dict[str, Any]:
        """
        Store new mood entry in database.
        
        Args:
            user_id: Unique user identifier
            text: Original mood text
            analysis: AI analysis result
            playlist: Generated playlist
            source: Input method ("text" or "voice")
            
        Returns:
            Created mood UUID
            
        Raises:
            CosmosHttpResponseError: If database operation fails
        """
        mood_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": None
        }
        
        try:
            created = self.container.create_item(body=mood_doc)
            logger.info(f"Mood entry created: {created['id']} for user {user_id}")
            return created['id']
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create mood entry: {e}")
            raise
    
    def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Fetch user's mood history, most recent first.
        
        Args:
            user_id: User identifier
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            List of mood documents
        """
        query = """
        SELECT * FROM c 
        WHERE c.user_id = @user_id 
        ORDER BY c.timestamp DESC
        OFFSET @offset LIMIT @limit
        """
        
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@offset", "value": offset},
            {"name": "@limit", "value": limit}
        ]
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            logger.info(f"Retrieved {len(items)} mood entries for user {user_id}")
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to query mood history: {e}")
            return []
    
    def get_mood_by_id(
        self,
        mood_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get specific mood entry by ID.
        
        Args:
            mood_id: Mood entry identifier
            user_id: User identifier (partition key)
            
        Returns:
            Mood document or None if not found
        """
        try:
            item = self.container.read_item(
                item=mood_id,
                partition_key=user_id
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            logger.warning(f"Mood {mood_id} not found for user {user_id}")
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Error reading mood: {e}")
            return None
    
    def get_mood_stats(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate mood statistics for user over specified period.
        
        Args:
            user_id: User identifier
            days: Number of days to analyze
            
        Returns:
            Dict with stats: total_entries, most_common_moods, avg_confidence
        """
        from datetime import timedelta
        from collections import Counter
        
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = """
        SELECT c.analysis.label as label, c.analysis.confidence as confidence 
        FROM c 
        WHERE c.user_id = @user_id AND c.timestamp >= @cutoff
        """
        
        parameters = [
            {"name": "@user_id", "value": user_id},
            {"name": "@cutoff", "value": cutoff}
        ]
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            if not items:
                return {
                    "total_entries": 0,
                    "most_common_moods": [],
                    "avg_confidence": 0,
                    "period_days": days
                }
            
            labels = [item["label"] for item in items]
            confidences = [item.get("confidence", 5) for item in items]
            
            most_common = Counter(labels).most_common(3)
            
            stats = {
                "total_entries": len(items),
                "most_common_moods": [
                    {"mood": mood, "count": count} 
                    for mood, count in most_common
                ],
                "avg_confidence": round(sum(confidences) / len(confidences), 1),
                "period_days": days
            }
            
            logger.info(f"Stats calculated for user {user_id}: {stats['total_entries']} entries")
            return stats
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Stats query error: {e}")
            return {"error": str(e), "period_days": days}