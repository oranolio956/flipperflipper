import logging
from typing import Dict, Any
from datetime import datetime, timedelta
import asyncio

from celery import Task
from app.core.celery_app import celery_app
from app.core.database import db_manager, check_database_health

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def cleanup_old_results(self) -> Dict[str, Any]:
    """Clean up old task results from Redis"""
    try:
        logger.info("Starting cleanup of old results")
        
        # Get Redis connection from celery
        redis_conn = celery_app.backend.client
        
        # Clean up old results (older than 24 hours)
        cleaned = 0
        pattern = "celery-task-meta-*"
        
        for key in redis_conn.scan_iter(match=pattern, count=100):
            try:
                # Get TTL of the key
                ttl = redis_conn.ttl(key)
                # If key has no TTL or TTL > 24 hours, delete it
                if ttl == -1 or ttl > 86400:
                    redis_conn.delete(key)
                    cleaned += 1
            except Exception as e:
                logger.error(f"Error cleaning up key {key}: {e}")
        
        logger.info(f"Cleaned up {cleaned} old results")
        
        return {
            'task': 'cleanup_old_results',
            'cleaned_keys': cleaned,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")
        raise


@celery_app.task(bind=True)
def health_check(self) -> Dict[str, Any]:
    """Perform health check on all system components"""
    try:
        logger.info("Performing system health check")
        
        health_status = {
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        # Check Redis
        try:
            redis_conn = celery_app.backend.client
            redis_conn.ping()
            health_status['components']['redis'] = {
                'status': 'healthy',
                'info': redis_conn.info('server')['redis_version']
            }
        except Exception as e:
            health_status['components']['redis'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Check Database
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            db_health = loop.run_until_complete(check_database_health())
            health_status['components']['database'] = db_health
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        finally:
            loop.close()
        
        # Check Celery workers
        try:
            active_queues = celery_app.control.inspect().active_queues()
            if active_queues:
                health_status['components']['celery_workers'] = {
                    'status': 'healthy',
                    'active_workers': len(active_queues)
                }
            else:
                health_status['components']['celery_workers'] = {
                    'status': 'unhealthy',
                    'error': 'No active workers found'
                }
        except Exception as e:
            health_status['components']['celery_workers'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # Overall status
        all_healthy = all(
            comp.get('status') == 'healthy' 
            for comp in health_status['components'].values()
        )
        health_status['overall_status'] = 'healthy' if all_healthy else 'degraded'
        
        logger.info(f"Health check completed: {health_status['overall_status']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise


@celery_app.task(bind=True)
def vacuum_database(self) -> Dict[str, Any]:
    """Perform database maintenance tasks"""
    try:
        logger.info("Starting database vacuum")
        
        async def _vacuum():
            async with db_manager.get_session() as session:
                # Analyze tables for query optimization
                await session.execute("ANALYZE;")
                
                # Get table statistics
                result = await session.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
                        n_live_tup AS live_rows,
                        n_dead_tup AS dead_rows
                    FROM pg_stat_user_tables
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                """)
                
                tables = []
                for row in result:
                    tables.append({
                        'schema': row[0],
                        'table': row[1],
                        'size': row[2],
                        'live_rows': row[3],
                        'dead_rows': row[4]
                    })
                
                return tables
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            table_stats = loop.run_until_complete(_vacuum())
            
            return {
                'task': 'vacuum_database',
                'tables_analyzed': len(table_stats),
                'table_stats': table_stats[:10],  # Top 10 tables
                'timestamp': datetime.utcnow().isoformat()
            }
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Error in vacuum task: {e}")
        raise


@celery_app.task(bind=True)
def generate_daily_report(self) -> Dict[str, Any]:
    """Generate daily statistics report"""
    try:
        logger.info("Generating daily report")
        
        # Get Redis connection
        redis_conn = celery_app.backend.client
        
        # Collect statistics
        stats = {
            'date': datetime.utcnow().date().isoformat(),
            'tasks': {},
            'queues': {}
        }
        
        # Get task statistics from Redis
        task_pattern = "celery-task-meta-*"
        total_tasks = 0
        successful_tasks = 0
        failed_tasks = 0
        
        for key in redis_conn.scan_iter(match=task_pattern, count=100):
            total_tasks += 1
            try:
                result = redis_conn.get(key)
                if result and b'"status": "SUCCESS"' in result:
                    successful_tasks += 1
                elif result and b'"status": "FAILURE"' in result:
                    failed_tasks += 1
            except Exception:
                pass
        
        stats['tasks'] = {
            'total': total_tasks,
            'successful': successful_tasks,
            'failed': failed_tasks,
            'success_rate': round(successful_tasks / total_tasks * 100, 2) if total_tasks > 0 else 0
        }
        
        # Get queue statistics
        inspector = celery_app.control.inspect()
        reserved = inspector.reserved()
        active = inspector.active()
        
        if reserved:
            stats['queues']['reserved_tasks'] = sum(len(tasks) for tasks in reserved.values())
        if active:
            stats['queues']['active_tasks'] = sum(len(tasks) for tasks in active.values())
        
        logger.info(f"Daily report generated: {stats}")
        
        return stats
        
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        raise


@celery_app.task(bind=True)
def rotate_logs(self) -> Dict[str, Any]:
    """Rotate application logs"""
    try:
        logger.info("Starting log rotation")
        
        # This is a placeholder - actual log rotation would be handled by
        # logrotate or similar system tool. This task can trigger alerts
        # or perform application-specific log management
        
        return {
            'task': 'rotate_logs',
            'status': 'completed',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in log rotation: {e}")
        raise