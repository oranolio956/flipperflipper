"""
Flood Wait Handler - Critical for Production
Handles Telegram's rate limiting properly
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Any
from telethon.errors import FloodWaitError, SlowModeWaitError

logger = logging.getLogger(__name__)


class FloodWaitHandler:
    """Intelligent flood wait handling with retry logic"""
    
    def __init__(self):
        self.wait_until = {}  # chat_id -> datetime
        self.retry_queue = []  # Messages to retry
        
    async def execute_with_flood_protection(
        self,
        func: Callable,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        Execute function with automatic flood wait handling
        
        Args:
            func: Async function to execute
            max_retries: Maximum retry attempts
            *args, **kwargs: Arguments for func
            
        Returns:
            Result of func or None if failed
        """
        retries = 0
        last_error = None
        
        while retries < max_retries:
            try:
                # Check if we're still in flood wait
                if await self._should_wait():
                    wait_time = self._get_wait_time()
                    logger.warning(f"⏸️  Still in flood wait, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Success! Clear any wait restrictions
                self._clear_wait()
                return result
                
            except FloodWaitError as e:
                last_error = e
                wait_seconds = e.seconds
                retries += 1
                
                logger.error(
                    f"🚨 FloodWaitError: Must wait {wait_seconds}s "
                    f"(Retry {retries}/{max_retries})"
                )
                
                # Store wait time
                self._set_wait(wait_seconds)
                
                if retries < max_retries:
                    # Add some buffer time (20% extra)
                    buffer_time = wait_seconds * 1.2
                    logger.info(f"⏰ Waiting {buffer_time}s before retry...")
                    await asyncio.sleep(buffer_time)
                else:
                    logger.error(f"❌ Max retries reached for flood wait")
                    
            except SlowModeWaitError as e:
                last_error = e
                wait_seconds = e.seconds
                retries += 1
                
                logger.warning(
                    f"⏳ Slow mode wait: {wait_seconds}s "
                    f"(Retry {retries}/{max_retries})"
                )
                
                if retries < max_retries:
                    await asyncio.sleep(wait_seconds + 1)
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error: {type(e).__name__}: {e}")
                raise
        
        # All retries failed
        if last_error:
            logger.error(f"❌ Failed after {max_retries} retries: {last_error}")
        
        return None
    
    def _set_wait(self, seconds: int):
        """Record flood wait time"""
        self.wait_until['global'] = datetime.now() + timedelta(seconds=seconds)
    
    def _clear_wait(self):
        """Clear flood wait"""
        if 'global' in self.wait_until:
            del self.wait_until['global']
    
    async def _should_wait(self) -> bool:
        """Check if we're still in flood wait"""
        if 'global' not in self.wait_until:
            return False
        
        wait_until = self.wait_until['global']
        now = datetime.now()
        
        return now < wait_until
    
    def _get_wait_time(self) -> int:
        """Get remaining wait time in seconds"""
        if 'global' not in self.wait_until:
            return 0
        
        wait_until = self.wait_until['global']
        now = datetime.now()
        
        if now >= wait_until:
            return 0
        
        delta = wait_until - now
        return int(delta.total_seconds())


class RetryQueue:
    """
    Queue for messages that failed due to flood wait
    Automatically retries them when possible
    """
    
    def __init__(self, flood_handler: FloodWaitHandler):
        self.queue = []
        self.flood_handler = flood_handler
        self.processing = False
    
    def add(self, func: Callable, args: tuple, kwargs: dict, priority: int = 0):
        """Add item to retry queue"""
        item = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'priority': priority,
            'added_at': datetime.now(),
            'attempts': 0
        }
        
        self.queue.append(item)
        self.queue.sort(key=lambda x: (-x['priority'], x['added_at']))
        
        logger.info(f"➕ Added to retry queue (queue size: {len(self.queue)})")
    
    async def process_queue(self):
        """Process retry queue in background"""
        if self.processing:
            return
        
        self.processing = True
        
        try:
            while self.queue:
                item = self.queue[0]  # Peek at first item
                
                # Check if too old (don't retry messages > 1 hour old)
                age = (datetime.now() - item['added_at']).total_seconds()
                if age > 3600:
                    logger.warning(f"⏭️  Skipping old queued item ({age}s old)")
                    self.queue.pop(0)
                    continue
                
                # Try to execute
                logger.info(f"🔄 Processing queued item (attempt {item['attempts'] + 1})...")
                
                result = await self.flood_handler.execute_with_flood_protection(
                    item['func'],
                    *item['args'],
                    **item['kwargs']
                )
                
                if result is not None:
                    # Success!
                    logger.info(f"✅ Queued item processed successfully")
                    self.queue.pop(0)
                else:
                    # Failed
                    item['attempts'] += 1
                    
                    if item['attempts'] >= 5:
                        logger.error(f"❌ Queued item failed after 5 attempts, dropping")
                        self.queue.pop(0)
                    else:
                        logger.warning(f"⚠️  Queued item failed, will retry later")
                        # Move to end of queue
                        self.queue.append(self.queue.pop(0))
                
                # Small delay between queue items
                await asyncio.sleep(5)
                
        finally:
            self.processing = False
    
    def get_stats(self) -> dict:
        """Get queue statistics"""
        return {
            'size': len(self.queue),
            'oldest_age': (
                (datetime.now() - self.queue[0]['added_at']).total_seconds()
                if self.queue else 0
            ),
            'processing': self.processing
        }
