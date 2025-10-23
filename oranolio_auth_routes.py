#!/usr/bin/env python3
"""
Oranolio Authentication Routes for Oranolio RAT - Elite C2 Framework
Handles Oranolio-specific authentication and authorization
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, g
from typing import Dict, Any, Optional

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import utilities
from auth_utils import auth_manager, login_required, api_key_or_login_required
from error_handler import error_handler, ErrorSeverity, ErrorCategory, ErrorContext
from validation_schemas import validate_input

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
oranolio_auth_bp = Blueprint('oranolio_auth', __name__, url_prefix='/oranolio')

class OranolioAuthManager:
    """Manages Oranolio-specific authentication features"""
    
    def __init__(self):
        self.user_sessions = {}
        self.security_events = []
        self.max_events = 1000
    
    def create_user_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a user session with additional Oranolio features"""
        session_id = f"oranolio_{int(datetime.now().timestamp() * 1000)}"
        
        session_info = {
            'session_id': session_id,
            'user_id': user_id,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'session_data': session_data,
            'is_active': True
        }
        
        self.user_sessions[session_id] = session_info
        
        # Log security event
        self._log_security_event('session_created', user_id, 'info')
        
        logger.info(f"Oranolio session created: {session_id} for user {user_id}")
        return session_id
    
    def validate_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate a user session"""
        if session_id not in self.user_sessions:
            return None
        
        session_info = self.user_sessions[session_id]
        
        # Check if session is active
        if not session_info['is_active']:
            return None
        
        # Check session timeout (24 hours)
        if datetime.now() - session_info['last_activity'] > timedelta(hours=24):
            session_info['is_active'] = False
            self._log_security_event('session_expired', session_info['user_id'], 'warning')
            return None
        
        # Update last activity
        session_info['last_activity'] = datetime.now()
        
        return session_info
    
    def terminate_user_session(self, session_id: str, user_id: str = None) -> bool:
        """Terminate a user session"""
        if session_id not in self.user_sessions:
            return False
        
        session_info = self.user_sessions[session_id]
        
        # Check if user has permission to terminate this session
        if user_id and session_info['user_id'] != user_id:
            return False
        
        # Mark session as inactive
        session_info['is_active'] = False
        session_info['terminated_at'] = datetime.now()
        
        # Log security event
        self._log_security_event('session_terminated', session_info['user_id'], 'info')
        
        logger.info(f"Oranolio session terminated: {session_id}")
        return True
    
    def _log_security_event(self, event_type: str, user_id: str, severity: str, details: Dict[str, Any] = None):
        """Log a security event"""
        event = {
            'event_type': event_type,
            'user_id': user_id,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'details': details or {}
        }
        
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]
    
    def get_user_sessions(self, user_id: str) -> list:
        """Get all sessions for a user"""
        return [
            session for session in self.user_sessions.values()
            if session['user_id'] == user_id
        ]
    
    def get_security_events(self, user_id: str = None, limit: int = 100) -> list:
        """Get security events"""
        events = self.security_events
        
        if user_id:
            events = [event for event in events if event['user_id'] == user_id]
        
        return events[-limit:] if events else []
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        total_events = len(self.security_events)
        active_sessions = len([s for s in self.user_sessions.values() if s['is_active']])
        
        recent_events = [
            event for event in self.security_events
            if datetime.fromisoformat(event['timestamp']) > datetime.now() - timedelta(hours=24)
        ]
        
        # Count events by severity
        severity_counts = {}
        for event in recent_events:
            severity = event['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return {
            'total_events': total_events,
            'active_sessions': active_sessions,
            'recent_events_24h': len(recent_events),
            'severity_counts': severity_counts
        }

# Global Oranolio auth manager
oranolio_auth_manager = OranolioAuthManager()

@oranolio_auth_bp.route('/login', methods=['POST'])
def oranolio_login():
    """Oranolio-specific login with enhanced security"""
    try:
        data = request.get_json()
        
        # Validate input
        validation_result = validate_input('login', data)
        if not validation_result.is_valid:
            return jsonify({'error': 'Validation failed', 'details': validation_result.errors}), 400
        
        email = validation_result.sanitized_value['email']
        password = validation_result.sanitized_value['password']
        
        # Authenticate user
        user = auth_manager.authenticate_user(email, password, request.remote_addr, request.headers.get('User-Agent'))
        
        if not user:
            oranolio_auth_manager._log_security_event('login_failed', email, 'warning')
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create Oranolio session
        session_data = {
            'login_method': 'oranolio',
            'features': ['elite_commands', 'advanced_security', 'real_time_monitoring']
        }
        
        session_id = oranolio_auth_manager.create_user_session(str(user.id), session_data)
        
        # Update Flask session
        session['oranolio_session_id'] = session_id
        session['user_id'] = user.id
        session['email'] = user.email
        
        # Log successful login
        oranolio_auth_manager._log_security_event('login_success', str(user.id), 'info')
        
        return jsonify({
            'success': True,
            'message': 'Oranolio login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'session_id': session_id
            }
        })
        
    except Exception as e:
        context = ErrorContext(
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.HIGH, ErrorCategory.AUTHENTICATION)
        
        return jsonify({'error': 'Oranolio login failed'}), 500

@oranolio_auth_bp.route('/logout', methods=['POST'])
@login_required
def oranolio_logout():
    """Oranolio-specific logout"""
    try:
        user_id = session.get('user_id')
        session_id = session.get('oranolio_session_id')
        
        if session_id:
            oranolio_auth_manager.terminate_user_session(session_id, str(user_id))
        
        # Clear Flask session
        session.clear()
        
        # Log logout
        oranolio_auth_manager._log_security_event('logout', str(user_id), 'info')
        
        return jsonify({
            'success': True,
            'message': 'Oranolio logout successful'
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.AUTHENTICATION)
        
        return jsonify({'error': 'Oranolio logout failed'}), 500

@oranolio_auth_bp.route('/sessions', methods=['GET'])
@login_required
def get_user_sessions():
    """Get user sessions"""
    try:
        user_id = session.get('user_id')
        sessions = oranolio_auth_manager.get_user_sessions(str(user_id))
        
        # Convert to serializable format
        sessions_data = []
        for session_info in sessions:
            sessions_data.append({
                'session_id': session_info['session_id'],
                'created_at': session_info['created_at'].isoformat(),
                'last_activity': session_info['last_activity'].isoformat(),
                'ip_address': session_info['ip_address'],
                'is_active': session_info['is_active']
            })
        
        return jsonify({
            'success': True,
            'sessions': sessions_data
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get sessions'}), 500

@oranolio_auth_bp.route('/sessions/<session_id>/terminate', methods=['POST'])
@login_required
def terminate_session(session_id):
    """Terminate a specific session"""
    try:
        user_id = session.get('user_id')
        success = oranolio_auth_manager.terminate_user_session(session_id, str(user_id))
        
        if not success:
            return jsonify({'error': 'Session not found or cannot be terminated'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Session terminated successfully'
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to terminate session'}), 500

@oranolio_auth_bp.route('/security/events', methods=['GET'])
@login_required
def get_security_events():
    """Get security events for the user"""
    try:
        user_id = session.get('user_id')
        limit = request.args.get('limit', 100, type=int)
        
        events = oranolio_auth_manager.get_security_events(str(user_id), limit)
        
        return jsonify({
            'success': True,
            'events': events,
            'total': len(events)
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get security events'}), 500

@oranolio_auth_bp.route('/security/stats', methods=['GET'])
@login_required
def get_security_stats():
    """Get security statistics"""
    try:
        stats = oranolio_auth_manager.get_security_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to get security stats'}), 500

@oranolio_auth_bp.route('/elite/access', methods=['GET'])
@login_required
def check_elite_access():
    """Check if user has access to elite features"""
    try:
        user_id = session.get('user_id')
        user = auth_manager.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has elite access
        elite_access = user.is_verified and user.is_active
        
        return jsonify({
            'success': True,
            'elite_access': elite_access,
            'features': {
                'elite_commands': elite_access,
                'advanced_security': elite_access,
                'real_time_monitoring': elite_access,
                'payload_generation': elite_access
            }
        })
        
    except Exception as e:
        context = ErrorContext(
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            additional_data={'error': str(e)}
        )
        error_handler.handle_error(e, context, ErrorSeverity.MEDIUM, ErrorCategory.APPLICATION)
        
        return jsonify({'error': 'Failed to check elite access'}), 500

def register_oranolio_auth_routes(app):
    """Register Oranolio authentication routes with Flask app"""
    app.register_blueprint(oranolio_auth_bp)
    logger.info("Oranolio authentication routes registered")

# Example usage and testing
if __name__ == "__main__":
    print("Oranolio Authentication Routes")
    print("=" * 40)
    print("Routes registered:")
    print("  POST /oranolio/login - Oranolio login")
    print("  POST /oranolio/logout - Oranolio logout")
    print("  GET  /oranolio/sessions - Get user sessions")
    print("  POST /oranolio/sessions/<id>/terminate - Terminate session")
    print("  GET  /oranolio/security/events - Get security events")
    print("  GET  /oranolio/security/stats - Get security stats")
    print("  GET  /oranolio/elite/access - Check elite access")
    print("Oranolio authentication routes ready!")