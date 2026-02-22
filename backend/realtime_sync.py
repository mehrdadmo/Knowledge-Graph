import asyncio
import json
import asyncpg
from typing import Callable, Optional
from loguru import logger
import aiohttp
from schemas import CDCNotification
from knowledge_graph_sync import KnowledgeGraphSync
from config import settings


class CDCListener:
    """
    Listens for PostgreSQL notifications and triggers real-time sync
    """
    
    def __init__(self):
        self.pg_dsn = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
        self.sync = KnowledgeGraphSync()
        self.api_base_url = "http://localhost:8000"
        self.running = False
        self.connection: Optional[asyncpg.Connection] = None
    
    async def start_listening(self):
        """Start listening for PostgreSQL notifications"""
        logger.info("Starting CDC listener...")
        
        try:
            # Connect to PostgreSQL
            self.connection = await asyncpg.connect(self.pg_dsn)
            logger.info("Connected to PostgreSQL for CDC")
            
            # Listen for notification channels
            await self.connection.execute("LISTEN hitl_finished")
            await self.connection.execute("LISTEN document_created")
            logger.info("Listening for CDC notifications")
            
            self.running = True
            
            # Main notification loop
            while self.running:
                try:
                    # Wait for notification with timeout
                    notification = await self.connection.notifies.get(timeout=1.0)
                    await self.handle_notification(notification)
                    
                except asyncio.TimeoutError:
                    # Timeout is normal, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Error in notification loop: {e}")
                    await asyncio.sleep(1)
        
        except Exception as e:
            logger.error(f"CDC listener failed: {e}")
            raise
        
        finally:
            if self.connection:
                await self.connection.close()
            logger.info("CDC listener stopped")
    
    async def handle_notification(self, notification):
        """Handle incoming PostgreSQL notification"""
        try:
            logger.info(f"Received notification: {notification.channel} - {notification.payload}")
            
            # Parse notification payload
            payload = json.loads(notification.payload)
            
            if notification.channel == "hitl_finished":
                await self.handle_hitl_finished(payload)
            elif notification.channel == "document_created":
                await self.handle_document_created(payload)
            
        except Exception as e:
            logger.error(f"Error handling notification: {e}")
    
    async def handle_hitl_finished(self, payload: dict):
        """Handle hitl_finished notification"""
        try:
            # Create CDC notification object
            cdc_notification = CDCNotification(
                document_id=payload.get('document_id'),
                field_id=payload.get('field_id'),
                field_name=payload.get('field_name'),
                hitl_value=payload.get('hitl_value'),
                finished_at=payload.get('finished_at')
            )
            
            logger.info(f"Processing HITL finished for document {cdc_notification.document_id}")
            
            # Trigger immediate sync for the document
            await self.trigger_sync(cdc_notification.document_id, "hitl_finished")
            
            # Also notify API endpoint
            await self.notify_api_endpoint(cdc_notification)
            
        except Exception as e:
            logger.error(f"Error handling hitl_finished: {e}")
    
    async def handle_document_created(self, payload: dict):
        """Handle document_created notification"""
        try:
            document_id = payload.get('document_id')
            logger.info(f"Processing document created for document {document_id}")
            
            # Trigger sync for new document
            await self.trigger_sync(document_id, "document_created")
            
        except Exception as e:
            logger.error(f"Error handling document_created: {e}")
    
    async def trigger_sync(self, document_id: int, trigger_source: str):
        """Trigger sync for a specific document"""
        try:
            logger.info(f"Triggering sync for document {document_id} from {trigger_source}")
            
            # Perform sync directly
            self.sync.sync_single_document(document_id)
            
            logger.info(f"Sync completed for document {document_id}")
            
        except Exception as e:
            logger.error(f"Sync failed for document {document_id}: {e}")
    
    async def notify_api_endpoint(self, notification: CDCNotification):
        """Notify API endpoint about CDC event"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base_url}/cdc/notification",
                    json=notification.dict(),
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info("API notification sent successfully")
                    else:
                        logger.warning(f"API notification failed: {response.status}")
                        
        except Exception as e:
            logger.warning(f"Failed to notify API endpoint: {e}")
    
    def stop(self):
        """Stop the CDC listener"""
        logger.info("Stopping CDC listener...")
        self.running = False


class RealTimeSyncService:
    """
    Service that manages real-time synchronization
    """
    
    def __init__(self):
        self.cdc_listener = CDCListener()
        self.running = False
    
    async def start(self):
        """Start the real-time sync service"""
        logger.info("Starting Real-Time Sync Service...")
        self.running = True
        
        try:
            # Start CDC listener
            await self.cdc_listener.start_listening()
            
        except Exception as e:
            logger.error(f"Real-time sync service failed: {e}")
            raise
    
    def stop(self):
        """Stop the real-time sync service"""
        logger.info("Stopping Real-Time Sync Service...")
        self.running = False
        self.cdc_listener.stop()


# CLI command to run the service
async def run_realtime_sync():
    """Run the real-time sync service"""
    service = RealTimeSyncService()
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, stopping service...")
        service.stop()
    except Exception as e:
        logger.error(f"Service crashed: {e}")
        service.stop()
        raise


if __name__ == "__main__":
    # Run the real-time sync service
    asyncio.run(run_realtime_sync())
