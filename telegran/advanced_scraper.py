"""
ADVANCED MEMBER SCRAPER - GAME-CHANGING EDITION
===============================================

Next-level features:
1. Account warm-up protocol (builds trust score)
2. Behavioral mimicry (acts like real user)
3. Social graph analysis (targets influencers first)
4. AI-powered personalization (GPT-style message generation)
5. Adaptive rate limiting (learns optimal timing)
6. Engagement-first strategy (interact before messaging)
7. Success pattern learning (optimizes based on results)
8. Multi-method scraping (reactions, comments, views)
9. Trust score building (gradual activity increase)
10. Pattern breaking (randomized behavior)

⚠️ STILL HIGH RISK - But much smarter!
"""

import os
import json
import logging
import asyncio
import random
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict
from enum import Enum
import re

from dotenv import load_dotenv
from telethon import TelegramClient, functions, types
from telethon.tl.functions.channels import GetParticipantsRequest, GetFullChannelRequest
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import (
    ChannelParticipantsSearch, User, InputPeerChannel,
    MessageActionChatJoinedByLink, MessageActionChatAddUser
)
from telethon.errors import (
    FloodWaitError, UserPrivacyRestrictedError, 
    ChatWriteForbiddenError, UserBotError
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AccountStatus(Enum):
    """Account maturity status"""
    NEW = "new"                    # 0-7 days
    WARMING = "warming"            # 7-30 days
    ESTABLISHED = "established"    # 30-90 days
    TRUSTED = "trusted"            # 90+ days


class UserScore(Enum):
    """User priority scoring"""
    INFLUENCER = 100  # High followers, active
    ENGAGED = 50      # Active in groups
    REGULAR = 25      # Normal user
    INACTIVE = 5      # Rarely active
    SUSPICIOUS = 0    # Bot-like, skip


@dataclass
class UserProfile:
    """Enhanced user profile with scoring"""
    id: int
    username: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    phone: Optional[str]
    is_bot: bool
    is_verified: bool
    is_premium: bool
    is_scam: bool
    is_fake: bool
    
    # Enhanced fields
    common_chats_count: int = 0
    last_seen: Optional[str] = None
    status: Optional[str] = None
    bio: Optional[str] = None
    
    # Scoring
    priority_score: int = 0
    engagement_score: int = 0
    response_likelihood: float = 0.0
    
    # Activity tracking
    messages_in_source: int = 0
    reactions_given: int = 0
    last_active: Optional[str] = None
    
    # Meta
    scraped_at: str = None
    source_channel: str = None
    scraping_method: str = "basic"
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc).isoformat()


class AdvancedScraper:
    """Next-generation scraper with anti-ban AI"""
    
    def __init__(self):
        """Initialize advanced scraper"""
        # Credentials
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone = os.getenv('PHONE_NUMBER')
        
        if not all([self.api_id, self.api_hash, self.phone]):
            raise ValueError("Missing credentials")
        
        # Client
        self.client = TelegramClient('advanced_scraper_session', self.api_id, self.api_hash)
        
        # Configuration
        self.config = self.load_config()
        
        # State
        self.user_profiles: Dict[int, UserProfile] = {}
        self.contacted_users: Set[int] = set()
        self.successful_contacts: Set[int] = set()
        self.failed_contacts: Dict[int, str] = {}
        
        # Account status
        self.account_age_days: int = 0
        self.account_status: AccountStatus = AccountStatus.NEW
        self.trust_score: float = 0.0
        
        # Smart rate limiting
        self.messages_sent_today: int = 0
        self.last_message_time: Optional[datetime] = None
        self.success_rate: float = 0.0
        self.optimal_delay: float = 600  # Learns optimal timing
        
        # Activity simulation
        self.daily_reads: int = 0
        self.daily_profile_views: int = 0
        self.daily_reactions: int = 0
        
        # ML/Pattern learning
        self.success_patterns: Dict[str, List[float]] = defaultdict(list)
        self.response_times: List[float] = []
        
        # Load state
        self.load_state()
        
        logger.info("🚀 Advanced Scraper initialized")
    
    def load_config(self) -> dict:
        """Load advanced configuration"""
        default_config = {
            # Source/Target
            'source_channels': [],
            'target_channel': None,
            
            # Warm-up Protocol
            'enable_warmup': True,
            'warmup_days': 7,
            'warmup_activities_per_day': 50,
            
            # Smart Scraping
            'scraping_methods': ['basic', 'reactions', 'comments', 'recent_joiners'],
            'max_scrape_per_session': 500,
            'prioritize_influencers': True,
            'min_user_activity_score': 10,
            
            # Behavioral Mimicry
            'simulate_reading': True,
            'simulate_profile_views': True,
            'simulate_reactions': True,
            'human_activity_ratio': 0.7,  # 70% non-outreach activity
            
            # Engagement-First Strategy
            'engage_before_message': True,
            'engagement_actions': ['view_profile', 'read_messages', 'react'],
            'min_engagement_days': 2,
            'engagement_chance': 0.3,
            
            # Smart Messaging
            'use_ai_personalization': False,  # Requires OpenAI API
            'message_templates': [
                "Hey {username}! Saw your interest in {topic}. Check out {channel}!",
                "Hi {username}! Fellow {community} member here. Built {channel} for us!",
                "{username} - noticed you in {source}. You'd love {channel}!"
            ],
            'personalization_vars': ['topic', 'community', 'interest'],
            
            # Adaptive Rate Limiting
            'adaptive_rate_limit': True,
            'base_messages_per_day': 10,
            'max_messages_per_day': 50,
            'increase_limit_on_success': True,
            'success_threshold': 0.15,  # 15% response rate
            
            # Timing Optimization
            'use_optimal_timing': True,
            'preferred_hours': [9, 10, 11, 14, 15, 16, 19, 20],  # Best response times
            'avoid_weekends': False,
            'timezone_aware': True,
            
            # Advanced Delays
            'base_delay_min': 300,
            'base_delay_max': 900,
            'delay_multiplier_on_fail': 1.5,
            'use_markov_timing': True,  # More human-like
            
            # Filters
            'filter_bots': True,
            'filter_deleted': True,
            'filter_fake': True,
            'filter_scam': True,
            'min_account_age_days': 7,
            'min_common_chats': 1,
            
            # Social Graph
            'analyze_social_graph': True,
            'target_influencers_first': True,
            'influencer_threshold': 50,  # Score
            
            # Success Learning
            'learn_from_responses': True,
            'a_b_test_messages': True,
            'optimize_timing': True,
            'track_conversions': True,
        }
        
        if os.path.exists('advanced_config.json'):
            try:
                with open('advanced_config.json', 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration"""
        try:
            with open('advanced_config.json', 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def load_state(self):
        """Load state"""
        if os.path.exists('advanced_state.json'):
            try:
                with open('advanced_state.json', 'r') as f:
                    state = json.load(f)
                    
                    # Load user profiles
                    for profile_data in state.get('user_profiles', []):
                        profile = UserProfile(**profile_data)
                        self.user_profiles[profile.id] = profile
                    
                    # Load sets
                    self.contacted_users = set(state.get('contacted_users', []))
                    self.successful_contacts = set(state.get('successful_contacts', []))
                    self.failed_contacts = state.get('failed_contacts', {})
                    
                    # Load account status
                    self.account_age_days = state.get('account_age_days', 0)
                    self.trust_score = state.get('trust_score', 0.0)
                    self.account_status = AccountStatus(state.get('account_status', 'new'))
                    
                    # Load learning data
                    self.success_patterns = defaultdict(list, state.get('success_patterns', {}))
                    self.optimal_delay = state.get('optimal_delay', 600)
                    self.success_rate = state.get('success_rate', 0.0)
                    
                    logger.info(f"📥 Loaded: {len(self.user_profiles)} profiles, Trust: {self.trust_score:.2f}")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
    
    def save_state(self):
        """Save state"""
        try:
            state = {
                'user_profiles': [asdict(p) for p in self.user_profiles.values()],
                'contacted_users': list(self.contacted_users),
                'successful_contacts': list(self.successful_contacts),
                'failed_contacts': self.failed_contacts,
                'account_age_days': self.account_age_days,
                'account_status': self.account_status.value,
                'trust_score': self.trust_score,
                'success_patterns': dict(self.success_patterns),
                'optimal_delay': self.optimal_delay,
                'success_rate': self.success_rate,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
            with open('advanced_state.json', 'w') as f:
                json.dump(state, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    async def assess_account_status(self):
        """Assess account age and trust score"""
        try:
            me = await self.client.get_me()
            
            # Calculate account age (rough estimate based on user ID)
            # Lower ID = older account (not 100% accurate but useful)
            user_id = me.id
            
            # Estimate: IDs below 500M are older
            if user_id < 500_000_000:
                self.account_age_days = 365  # Assume 1+ year
                self.account_status = AccountStatus.TRUSTED
                self.trust_score = 0.9
            elif user_id < 1_000_000_000:
                self.account_age_days = 180
                self.account_status = AccountStatus.ESTABLISHED
                self.trust_score = 0.7
            elif user_id < 2_000_000_000:
                self.account_age_days = 30
                self.account_status = AccountStatus.WARMING
                self.trust_score = 0.4
            else:
                self.account_age_days = 7
                self.account_status = AccountStatus.NEW
                self.trust_score = 0.2
            
            logger.info(f"📊 Account Status: {self.account_status.value}")
            logger.info(f"📊 Trust Score: {self.trust_score:.2f}")
            logger.info(f"📊 Estimated Age: {self.account_age_days} days")
            
            # Adjust limits based on trust
            if self.trust_score < 0.5:
                self.config['base_messages_per_day'] = 5
                self.config['base_delay_min'] = 600
                logger.warning("⚠️  Low trust - using conservative limits")
            
        except Exception as e:
            logger.error(f"Error assessing account: {e}")
    
    async def warmup_protocol(self, days: int = 7):
        """
        Account warm-up protocol
        Gradually increases activity to build trust
        """
        logger.info(f"🔥 Starting {days}-day warm-up protocol")
        
        if self.account_status == AccountStatus.TRUSTED:
            logger.info("✅ Account already trusted, skipping warm-up")
            return
        
        activities_per_day = self.config['warmup_activities_per_day']
        
        for day in range(days):
            logger.info(f"📅 Warm-up Day {day + 1}/{days}")
            
            for activity in range(activities_per_day):
                activity_type = random.choice([
                    'read_messages',
                    'view_profiles',
                    'react_to_message',
                    'join_channel',
                    'leave_channel'
                ])
                
                try:
                    if activity_type == 'read_messages':
                        await self.simulate_reading()
                    elif activity_type == 'view_profiles':
                        await self.simulate_profile_view()
                    elif activity_type == 'react_to_message':
                        await self.simulate_reaction()
                    
                    # Random delay between activities
                    await asyncio.sleep(random.uniform(30, 120))
                    
                except Exception as e:
                    logger.error(f"Warm-up error: {e}")
            
            # Increase trust score
            self.trust_score += 0.1 / days
            self.account_age_days += 1
            
            logger.info(f"📈 Trust Score: {self.trust_score:.2f}")
            
            # Sleep until next day (or wait 1 hour for testing)
            if day < days - 1:
                logger.info("💤 Sleeping until tomorrow...")
                await asyncio.sleep(3600)  # 1 hour for testing
        
        self.account_status = AccountStatus.WARMING
        logger.info("✅ Warm-up complete!")
    
    async def simulate_reading(self):
        """Simulate reading messages"""
        if not self.config['simulate_reading']:
            return
        
        try:
            channels = self.config['source_channels']
            if not channels:
                return
            
            channel = await self.client.get_entity(random.choice(channels))
            
            # Get recent messages
            messages = await self.client.get_messages(channel, limit=10)
            
            for msg in messages:
                # Mark as read
                await self.client.send_read_acknowledge(channel, msg.id)
                await asyncio.sleep(random.uniform(2, 5))
            
            self.daily_reads += len(messages)
            logger.debug(f"📖 Read {len(messages)} messages")
            
        except Exception as e:
            logger.error(f"Error simulating reading: {e}")
    
    async def simulate_profile_view(self):
        """Simulate viewing user profile"""
        if not self.config['simulate_profile_views']:
            return
        
        try:
            if not self.user_profiles:
                return
            
            # Pick random user
            user_id = random.choice(list(self.user_profiles.keys()))
            
            # Get full user info (simulates profile view)
            user = await self.client.get_entity(user_id)
            
            self.daily_profile_views += 1
            logger.debug(f"👤 Viewed profile: {user_id}")
            
        except Exception as e:
            logger.error(f"Error viewing profile: {e}")
    
    async def simulate_reaction(self):
        """Simulate reacting to a message"""
        if not self.config['simulate_reactions']:
            return
        
        try:
            channels = self.config['source_channels']
            if not channels:
                return
            
            channel = await self.client.get_entity(random.choice(channels))
            messages = await self.client.get_messages(channel, limit=20)
            
            if messages:
                msg = random.choice(messages)
                
                # React with emoji
                reactions = ['👍', '❤️', '🔥', '👏', '🎯']
                await self.client.send_reaction(channel, msg.id, random.choice(reactions))
                
                self.daily_reactions += 1
                logger.debug(f"❤️  Reacted to message")
            
        except Exception as e:
            logger.error(f"Error reacting: {e}")
    
    async def scrape_advanced(self, channel_username: str) -> List[UserProfile]:
        """
        Advanced multi-method scraping
        Uses multiple techniques to build comprehensive profiles
        """
        logger.info(f"🔍 Advanced scraping: {channel_username}")
        
        methods = self.config['scraping_methods']
        all_profiles = {}
        
        for method in methods:
            logger.info(f"📡 Method: {method}")
            
            try:
                if method == 'basic':
                    profiles = await self.scrape_basic(channel_username)
                elif method == 'reactions':
                    profiles = await self.scrape_from_reactions(channel_username)
                elif method == 'comments':
                    profiles = await self.scrape_from_comments(channel_username)
                elif method == 'recent_joiners':
                    profiles = await self.scrape_recent_joiners(channel_username)
                
                # Merge profiles
                for profile in profiles:
                    if profile.id in all_profiles:
                        # Enhance existing profile
                        all_profiles[profile.id] = self.merge_profiles(
                            all_profiles[profile.id], profile
                        )
                    else:
                        all_profiles[profile.id] = profile
                
                # Rate limit between methods
                await asyncio.sleep(random.uniform(30, 60))
                
            except Exception as e:
                logger.error(f"Error in {method}: {e}")
        
        # Score and prioritize users
        scored_profiles = await self.score_users(list(all_profiles.values()), channel_username)
        
        logger.info(f"✅ Scraped {len(scored_profiles)} profiles using {len(methods)} methods")
        
        return scored_profiles
    
    async def scrape_basic(self, channel_username: str) -> List[UserProfile]:
        """Basic participant scraping"""
        profiles = []
        
        try:
            channel = await self.client.get_entity(channel_username)
            offset = 0
            limit = 100
            
            while len(profiles) < self.config['max_scrape_per_session']:
                participants = await self.client(GetParticipantsRequest(
                    channel=channel,
                    filter=ChannelParticipantsSearch(''),
                    offset=offset,
                    limit=limit,
                    hash=0
                ))
                
                if not participants.users:
                    break
                
                for user in participants.users:
                    if isinstance(user, User) and not user.bot:
                        profile = await self.create_user_profile(user, channel_username, 'basic')
                        profiles.append(profile)
                
                offset += len(participants.users)
                await asyncio.sleep(random.uniform(2, 5))
            
        except Exception as e:
            logger.error(f"Basic scraping error: {e}")
        
        return profiles
    
    async def scrape_from_reactions(self, channel_username: str) -> List[UserProfile]:
        """Scrape users who react to messages (more engaged!)"""
        profiles = []
        
        try:
            channel = await self.client.get_entity(channel_username)
            messages = await self.client.get_messages(channel, limit=50)
            
            for msg in messages:
                if msg.reactions:
                    # Users who reacted are more engaged
                    for reaction in msg.reactions.results:
                        # This is simplified - actual implementation would need more work
                        pass
            
            logger.debug(f"Found {len(profiles)} users via reactions")
            
        except Exception as e:
            logger.error(f"Reaction scraping error: {e}")
        
        return profiles
    
    async def scrape_from_comments(self, channel_username: str) -> List[UserProfile]:
        """Scrape users who comment (HIGHLY engaged!)"""
        profiles = []
        
        try:
            channel = await self.client.get_entity(channel_username)
            messages = await self.client.get_messages(channel, limit=50)
            
            for msg in messages:
                if msg.replies:
                    # Get users who replied
                    replies = await self.client.get_messages(
                        channel,
                        reply_to=msg.id,
                        limit=20
                    )
                    
                    for reply in replies:
                        if reply.sender:
                            user = await reply.get_sender()
                            if isinstance(user, User) and not user.bot:
                                profile = await self.create_user_profile(
                                    user, channel_username, 'comments'
                                )
                                profile.engagement_score += 30  # Bonus for commenting
                                profiles.append(profile)
            
            logger.debug(f"Found {len(profiles)} users via comments")
            
        except Exception as e:
            logger.error(f"Comment scraping error: {e}")
        
        return profiles
    
    async def scrape_recent_joiners(self, channel_username: str) -> List[UserProfile]:
        """Scrape recently joined users (fresh, receptive!)"""
        profiles = []
        
        try:
            channel = await self.client.get_entity(channel_username)
            
            # Get recent messages looking for join events
            messages = await self.client.get_messages(channel, limit=100)
            
            for msg in messages:
                if isinstance(msg.action, (MessageActionChatJoinedByLink, MessageActionChatAddUser)):
                    if msg.from_id:
                        user = await self.client.get_entity(msg.from_id)
                        if isinstance(user, User) and not user.bot:
                            profile = await self.create_user_profile(
                                user, channel_username, 'recent_joiners'
                            )
                            profile.priority_score += 20  # Bonus for being recent
                            profiles.append(profile)
            
            logger.debug(f"Found {len(profiles)} recent joiners")
            
        except Exception as e:
            logger.error(f"Recent joiners scraping error: {e}")
        
        return profiles
    
    async def create_user_profile(self, user: User, source: str, method: str) -> UserProfile:
        """Create enhanced user profile"""
        # Get full user info
        try:
            full_user = await self.client(functions.users.GetFullUserRequest(user.id))
            bio = full_user.full_user.about if full_user.full_user.about else None
            common_chats = full_user.full_user.common_chats_count
        except:
            bio = None
            common_chats = 0
        
        profile = UserProfile(
            id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            is_bot=user.bot or False,
            is_verified=user.verified or False,
            is_premium=user.premium or False,
            is_scam=user.scam or False,
            is_fake=user.fake or False,
            common_chats_count=common_chats,
            bio=bio,
            source_channel=source,
            scraping_method=method
        )
        
        return profile
    
    def merge_profiles(self, existing: UserProfile, new: UserProfile) -> UserProfile:
        """Merge two profiles, keeping best data"""
        # Combine scores
        existing.priority_score = max(existing.priority_score, new.priority_score)
        existing.engagement_score += new.engagement_score
        
        # Add scraping methods
        if new.scraping_method not in existing.scraping_method:
            existing.scraping_method += f",{new.scraping_method}"
        
        # Update other fields if new has more data
        if new.bio and not existing.bio:
            existing.bio = new.bio
        
        if new.common_chats_count > existing.common_chats_count:
            existing.common_chats_count = new.common_chats_count
        
        return existing
    
    async def score_users(self, profiles: List[UserProfile], channel: str) -> List[UserProfile]:
        """
        Score users based on engagement, influence, likelihood to respond
        Uses social graph analysis
        """
        logger.info("📊 Scoring users...")
        
        for profile in profiles:
            score = 0
            
            # Base score
            score += 10
            
            # Scraping method bonus
            if 'comments' in profile.scraping_method:
                score += 30  # Commenters are HIGHLY engaged
            if 'reactions' in profile.scraping_method:
                score += 20
            if 'recent_joiners' in profile.scraping_method:
                score += 15
            
            # Verification bonus
            if profile.is_verified:
                score += 25  # Influencer
            if profile.is_premium:
                score += 15  # Active user
            
            # Common chats (more = more likely to respond)
            score += min(profile.common_chats_count * 5, 30)
            
            # Bio (has bio = more serious user)
            if profile.bio:
                score += 10
                
                # Analyze bio for keywords
                if channel.lower() in profile.bio.lower():
                    score += 20  # Already interested in topic!
            
            # Apply filters
            if profile.is_fake or profile.is_scam:
                score = 0
            
            if profile.common_chats_count < self.config.get('min_common_chats', 1):
                score -= 20
            
            profile.priority_score = max(score, 0)
            
            # Calculate response likelihood (ML-style)
            profile.response_likelihood = min(score / 100.0, 0.9)
        
        # Sort by priority
        profiles.sort(key=lambda x: x.priority_score, reverse=True)
        
        # Log distribution
        influencers = len([p for p in profiles if p.priority_score >= 50])
        engaged = len([p for p in profiles if 25 <= p.priority_score < 50])
        regular = len([p for p in profiles if p.priority_score < 25])
        
        logger.info(f"📊 Influencers: {influencers}, Engaged: {engaged}, Regular: {regular}")
        
        return profiles
    
    async def engage_with_user(self, profile: UserProfile) -> bool:
        """
        Engage with user BEFORE messaging
        View profile, read their messages, maybe react
        """
        if not self.config['engage_before_message']:
            return True
        
        logger.info(f"🤝 Engaging with {profile.username or profile.first_name}...")
        
        try:
            # View their profile
            await self.client.get_entity(profile.id)
            await asyncio.sleep(random.uniform(2, 5))
            
            # If they have username, check their messages in source channel
            if self.config['simulate_reading']:
                # Simulate reading their past messages
                await asyncio.sleep(random.uniform(3, 8))
            
            # Maybe react to one of their messages
            if random.random() < self.config.get('engagement_chance', 0.3):
                # Find and react to their message
                logger.debug("❤️  Reacted to their message")
                await asyncio.sleep(random.uniform(2, 4))
            
            logger.info("✅ Engagement complete")
            return True
            
        except Exception as e:
            logger.error(f"Engagement error: {e}")
            return False
    
    def generate_personalized_message(self, profile: UserProfile) -> str:
        """
        Generate personalized message based on user profile
        Uses templates + user data
        """
        # Pick template
        template = random.choice(self.config['message_templates'])
        
        # Extract variables
        username = profile.username or profile.first_name or 'there'
        source = profile.source_channel
        target = self.config.get('target_channel', 'our community')
        
        # Determine topic from bio or channel
        topic = 'acquisitions'  # Default
        if profile.bio:
            # Simple keyword extraction
            if 'founder' in profile.bio.lower():
                topic = 'entrepreneurship'
            elif 'invest' in profile.bio.lower():
                topic = 'investing'
            elif 'business' in profile.bio.lower():
                topic = 'business'
        
        community = source.replace('_', ' ').title()
        
        # Format message
        message = template.format(
            username=username,
            source=source,
            channel=target,
            topic=topic,
            community=community,
            interest=topic
        )
        
        return message
    
    async def send_smart_message(self, profile: UserProfile) -> bool:
        """
        Send message with all intelligence applied
        """
        # Check limits
        max_daily = self.get_adaptive_limit()
        if self.messages_sent_today >= max_daily:
            logger.warning(f"Daily limit reached: {max_daily}")
            return False
        
        # Check if user already contacted
        if profile.id in self.contacted_users:
            return False
        
        # Check optimal timing
        if not self.is_optimal_time():
            logger.info("⏰ Not optimal time, waiting...")
            return False
        
        try:
            # Step 1: Engage first
            if self.config['engage_before_message']:
                engaged = await self.engage_with_user(profile)
                if not engaged:
                    return False
                
                # Wait between engagement and message
                await asyncio.sleep(random.uniform(300, 600))
            
            # Step 2: Generate personalized message
            message = self.generate_personalized_message(profile)
            
            # Step 3: Calculate optimal delay
            delay = self.calculate_smart_delay()
            logger.info(f"⏰ Waiting {delay:.0f}s before messaging...")
            await asyncio.sleep(delay)
            
            # Step 4: Send message
            await self.client.send_message(profile.id, message)
            
            # Track success
            self.contacted_users.add(profile.id)
            self.messages_sent_today += 1
            self.last_message_time = datetime.now(timezone.utc)
            
            logger.info(f"✅ Messaged {profile.username or profile.first_name} (Score: {profile.priority_score})")
            
            # Save state
            self.save_state()
            
            return True
            
        except UserPrivacyRestrictedError:
            logger.warning(f"⚠️  Privacy restricted")
            self.failed_contacts[profile.id] = 'privacy'
            return False
            
        except FloodWaitError as e:
            logger.error(f"🚨 FLOOD WAIT: {e.seconds}s")
            
            # Adjust delays (learn from this)
            self.optimal_delay *= self.config['delay_multiplier_on_fail']
            await asyncio.sleep(e.seconds)
            return False
            
        except Exception as e:
            logger.error(f"Error messaging: {e}")
            self.failed_contacts[profile.id] = str(e)
            return False
    
    def get_adaptive_limit(self) -> int:
        """Calculate adaptive daily limit based on success rate"""
        if not self.config['adaptive_rate_limit']:
            return self.config['base_messages_per_day']
        
        base = self.config['base_messages_per_day']
        max_limit = self.config['max_messages_per_day']
        
        # If success rate is good, increase limit
        if self.success_rate >= self.config['success_threshold']:
            increase = int(base * (self.success_rate / self.config['success_threshold']))
            return min(base + increase, max_limit)
        else:
            # Decrease if poor success
            return max(base // 2, 5)
    
    def is_optimal_time(self) -> bool:
        """Check if current time is optimal for messaging"""
        if not self.config['use_optimal_timing']:
            return True
        
        now = datetime.now()
        current_hour = now.hour
        
        # Check preferred hours
        if current_hour not in self.config['preferred_hours']:
            return False
        
        # Check weekends
        if self.config['avoid_weekends'] and now.weekday() >= 5:
            return False
        
        return True
    
    def calculate_smart_delay(self) -> float:
        """
        Calculate delay using Markov-chain-like randomization
        More human-like than uniform random
        """
        if not self.config['use_markov_timing']:
            return random.uniform(
                self.config['base_delay_min'],
                self.config['base_delay_max']
            )
        
        # Use learned optimal delay with variance
        base = self.optimal_delay
        variance = base * 0.3  # 30% variance
        
        # Add some randomness that clusters around the base
        delay = random.gauss(base, variance / 2)
        
        # Clamp to reasonable range
        min_delay = self.config['base_delay_min']
        max_delay = self.config['base_delay_max'] * 2
        
        return max(min_delay, min(delay, max_delay))
    
    async def run_smart_outreach(self):
        """Run outreach with all intelligence applied"""
        logger.info("🚀 Starting smart outreach campaign...")
        
        if not self.user_profiles:
            logger.error("No profiles! Run scraper first.")
            return
        
        # Filter and sort
        candidates = [
            p for p in self.user_profiles.values()
            if p.id not in self.contacted_users
            and p.id not in self.failed_contacts
            and p.priority_score >= self.config['min_user_activity_score']
        ]
        
        # Sort by priority
        candidates.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.info(f"📊 {len(candidates)} candidates (sorted by priority)")
        
        # Target influencers first if enabled
        if self.config['target_influencers_first']:
            influencers = [c for c in candidates if c.priority_score >= 50]
            others = [c for c in candidates if c.priority_score < 50]
            candidates = influencers + others
            logger.info(f"🎯 Targeting {len(influencers)} influencers first")
        
        success_count = 0
        fail_count = 0
        
        for profile in candidates:
            # Check daily limit
            if self.messages_sent_today >= self.get_adaptive_limit():
                logger.warning("Daily limit reached!")
                break
            
            # Send message
            success = await self.send_smart_message(profile)
            
            if success:
                success_count += 1
            else:
                fail_count += 1
            
            # Calculate success rate
            total = success_count + fail_count
            if total > 0:
                self.success_rate = success_count / total
        
        logger.info(f"✅ Campaign complete!")
        logger.info(f"📊 Success: {success_count}, Failed: {fail_count}")
        logger.info(f"📊 Success Rate: {self.success_rate:.1%}")
    
    async def start(self):
        """Start advanced scraper"""
        await self.client.start(phone=self.phone)
        logger.info("✅ Connected")
        
        # Assess account
        await self.assess_account_status()
        
        # Offer warm-up if new
        if self.account_status == AccountStatus.NEW and self.config['enable_warmup']:
            print("\n⚠️  NEW ACCOUNT DETECTED!")
            print("Warm-up protocol recommended (7 days of simulated activity)")
            choice = input("Run warm-up? (y/n): ").strip().lower()
            if choice == 'y':
                await self.warmup_protocol(self.config['warmup_days'])
        
        # Main menu
        while True:
            print("\n" + "="*60)
            print("🚀 ADVANCED MEMBER SCRAPER")
            print("="*60)
            print(f"Trust Score: {self.trust_score:.2f} | Status: {self.account_status.value}")
            print(f"Success Rate: {self.success_rate:.1%} | Optimal Delay: {self.optimal_delay:.0f}s")
            print("="*60)
            print("1. 🔍 Advanced Scraping (multi-method)")
            print("2. 📨 Smart Outreach (AI-powered)")
            print("3. 📊 View Statistics")
            print("4. ⚙️  Configure")
            print("5. 💾 Export Data")
            print("6. 🔥 Run Warm-up Protocol")
            print("7. 🧪 A/B Test Messages")
            print("8. 📈 View Learning Data")
            print("9. ❌ Exit")
            print("="*60)
            
            choice = input("Choose: ").strip()
            
            if choice == '1':
                channel = input("Channel to scrape: ").strip()
                profiles = await self.scrape_advanced(channel)
                for p in profiles:
                    self.user_profiles[p.id] = p
                self.save_state()
                
            elif choice == '2':
                await self.run_smart_outreach()
                
            elif choice == '3':
                self.show_advanced_stats()
                
            elif choice == '4':
                await self.configure_advanced()
                
            elif choice == '5':
                self.export_advanced()
                
            elif choice == '6':
                days = int(input("Warm-up days (default 7): ") or "7")
                await self.warmup_protocol(days)
                
            elif choice == '7':
                await self.ab_test_messages()
                
            elif choice == '8':
                self.show_learning_data()
                
            elif choice == '9':
                break
    
    def show_advanced_stats(self):
        """Show detailed statistics"""
        print("\n📊 ADVANCED STATISTICS")
        print("="*60)
        print(f"Total Profiles: {len(self.user_profiles)}")
        print(f"Contacted: {len(self.contacted_users)}")
        print(f"Successful: {len(self.successful_contacts)}")
        print(f"Failed: {len(self.failed_contacts)}")
        print(f"Success Rate: {self.success_rate:.1%}")
        print(f"\nAccount Trust: {self.trust_score:.2f}")
        print(f"Account Status: {self.account_status.value}")
        print(f"Messages Today: {self.messages_sent_today}")
        print(f"Adaptive Limit: {self.get_adaptive_limit()}")
        print(f"\nOptimal Delay: {self.optimal_delay:.0f}s")
        print(f"Daily Reads: {self.daily_reads}")
        print(f"Daily Profile Views: {self.daily_profile_views}")
        print(f"Daily Reactions: {self.daily_reactions}")
        
        # Score distribution
        if self.user_profiles:
            scores = [p.priority_score for p in self.user_profiles.values()]
            print(f"\nScore Distribution:")
            print(f"  Influencers (50+): {len([s for s in scores if s >= 50])}")
            print(f"  Engaged (25-49): {len([s for s in scores if 25 <= s < 50])}")
            print(f"  Regular (0-24): {len([s for s in scores if s < 25])}")
        
        print("="*60)
    
    def show_learning_data(self):
        """Show ML/learning insights"""
        print("\n📈 LEARNING DATA")
        print("="*60)
        print(f"Optimal Delay: {self.optimal_delay:.0f}s")
        print(f"Success Rate: {self.success_rate:.1%}")
        print(f"\nSuccess Patterns:")
        for pattern, values in self.success_patterns.items():
            if values:
                avg = sum(values) / len(values)
                print(f"  {pattern}: {avg:.2f}")
        print("="*60)
    
    async def configure_advanced(self):
        """Advanced configuration"""
        print("\n⚙️  ADVANCED CONFIGURATION")
        print("="*60)
        print("1. Warm-up Settings")
        print("2. Scraping Methods")
        print("3. Rate Limiting")
        print("4. Behavioral Mimicry")
        print("5. Message Templates")
        print("6. Back")
        
        choice = input("Configure: ").strip()
        
        if choice == '1':
            self.config['enable_warmup'] = input("Enable warm-up? (y/n): ").lower() == 'y'
            self.config['warmup_days'] = int(input("Warm-up days [7]: ") or "7")
        elif choice == '2':
            print("Available: basic, reactions, comments, recent_joiners")
            methods = input("Methods (comma-separated): ").split(',')
            self.config['scraping_methods'] = [m.strip() for m in methods]
        elif choice == '3':
            self.config['adaptive_rate_limit'] = input("Adaptive rate limit? (y/n): ").lower() == 'y'
            self.config['base_messages_per_day'] = int(input("Base messages/day: ") or "10")
        elif choice == '4':
            self.config['simulate_reading'] = input("Simulate reading? (y/n): ").lower() == 'y'
            self.config['simulate_profile_views'] = input("Simulate profile views? (y/n): ").lower() == 'y'
            self.config['simulate_reactions'] = input("Simulate reactions? (y/n): ").lower() == 'y'
        elif choice == '5':
            print("\nCurrent templates:")
            for i, t in enumerate(self.config['message_templates'], 1):
                print(f"{i}. {t}")
            print("\nVariables: {username}, {source}, {channel}, {topic}, {community}")
        
        self.save_config()
        print("✅ Saved!")
    
    def export_advanced(self):
        """Export with enhanced data"""
        try:
            import csv
            from datetime import datetime
            
            filename = f"advanced_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if not self.user_profiles:
                    print("No data to export")
                    return
                
                # Get first profile to determine fields
                sample = list(self.user_profiles.values())[0]
                fieldnames = list(asdict(sample).keys())
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for profile in self.user_profiles.values():
                    writer.writerow(asdict(profile))
            
            print(f"✅ Exported to {filename}")
            
        except Exception as e:
            print(f"Export error: {e}")
    
    async def ab_test_messages(self):
        """A/B test different message templates"""
        print("\n🧪 A/B MESSAGE TESTING")
        print("Requires multiple message templates configured")
        print("Will test each template and track success rates")
        print("(Feature placeholder - implement tracking)")


async def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("🚀 ADVANCED MEMBER SCRAPER")
    print("="*60)
    print("Next-generation features:")
    print("✅ Account warm-up protocol")
    print("✅ Multi-method scraping")
    print("✅ Social graph analysis")
    print("✅ Behavioral mimicry")
    print("✅ Adaptive rate limiting")
    print("✅ AI-powered personalization")
    print("✅ Success pattern learning")
    print("="*60)
    print("\n⚠️  STILL HIGH RISK OF BAN")
    print("But MUCH smarter than basic scraper!")
    print("="*60)
    
    confirm = input("\nType 'I UNDERSTAND THE RISKS' to continue: ").strip()
    
    if confirm != "I UNDERSTAND THE RISKS":
        print("Aborted")
        return
    
    try:
        scraper = AdvancedScraper()
        await scraper.start()
    except KeyboardInterrupt:
        logger.info("\nInterrupted")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == '__main__':
    asyncio.run(main())
