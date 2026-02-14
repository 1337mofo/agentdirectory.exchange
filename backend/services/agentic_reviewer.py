#!/usr/bin/env python3
"""
Agentic Agent Submission Reviewer
100% autonomous approval/rejection with anti-spam security
"""

import re
import requests
from datetime import datetime, timedelta
from typing import Tuple, Optional
from urllib.parse import urlparse
import hashlib


class AgenticReviewer:
    """
    Autonomous agent submission reviewer
    Makes approve/reject decisions without human intervention
    """
    
    # Anti-spam thresholds
    MAX_SUBMISSIONS_PER_EMAIL_PER_DAY = 3
    MAX_SUBMISSIONS_PER_IP_PER_HOUR = 5
    MIN_DESCRIPTION_LENGTH = 50
    MAX_DESCRIPTION_LENGTH = 2000
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100
    
    # Quality score thresholds
    AUTO_APPROVE_SCORE = 80
    AUTO_REJECT_SCORE = 40
    
    # Spam keywords
    SPAM_KEYWORDS = [
        'viagra', 'casino', 'poker', 'lottery', 'crypto scam',
        'get rich quick', 'make money fast', 'click here',
        'limited time offer', 'act now', 'free money'
    ]
    
    # Trusted domains for auto-approval
    TRUSTED_DOMAINS = [
        'github.com', 'huggingface.co', 'openai.com',
        'anthropic.com', 'cohere.ai', 'replicate.com',
        'modal.com', 'together.ai', 'fireworks.ai'
    ]
    
    def __init__(self, db_session):
        self.db = db_session
    
    def review_submission(self, submission_data: dict, submitter_ip: Optional[str] = None) -> Tuple[bool, str, int]:
        """
        Review agent submission autonomously
        
        Returns:
            (should_approve: bool, reason: str, quality_score: int)
        """
        name = submission_data.get('name', '')
        description = submission_data.get('description', '')
        website = submission_data.get('website', '')
        email = submission_data.get('email', '')
        api_endpoint = submission_data.get('api_endpoint')
        
        quality_score = 70  # Base score
        rejection_reasons = []
        approval_points = []
        
        # 1. Rate limiting checks
        rate_check, rate_reason = self._check_rate_limits(email, submitter_ip)
        if not rate_check:
            return False, f"Rate limit exceeded: {rate_reason}", 0
        
        # 2. Email validation
        email_valid, email_reason = self._validate_email(email)
        if not email_valid:
            return False, f"Invalid email: {email_reason}", 0
        
        # 3. Name validation
        name_valid, name_reason = self._validate_name(name)
        if not name_valid:
            rejection_reasons.append(f"Name issue: {name_reason}")
            quality_score -= 20
        else:
            approval_points.append("Valid name")
        
        # 4. Description quality check
        desc_score, desc_feedback = self._check_description_quality(description)
        quality_score += desc_score
        if desc_score < 0:
            rejection_reasons.append(desc_feedback)
        else:
            approval_points.append(desc_feedback)
        
        # 5. URL validation and trust check
        url_score, url_feedback = self._validate_url(website)
        quality_score += url_score
        if url_score < 0:
            rejection_reasons.append(url_feedback)
        else:
            approval_points.append(url_feedback)
        
        # 6. Spam content detection
        spam_detected, spam_reason = self._detect_spam(name, description, website)
        if spam_detected:
            return False, f"Spam detected: {spam_reason}", 0
        
        # 7. Duplicate detection
        duplicate, dup_reason = self._check_duplicates(name, website, email)
        if duplicate:
            return False, f"Duplicate submission: {dup_reason}", 0
        
        # 8. API endpoint validation (if provided)
        if api_endpoint:
            api_score, api_feedback = self._validate_api_endpoint(api_endpoint)
            quality_score += api_score
            if api_score > 0:
                approval_points.append(api_feedback)
        
        # Final decision
        if quality_score >= self.AUTO_APPROVE_SCORE:
            reason = "Auto-approved: " + "; ".join(approval_points)
            return True, reason, quality_score
        
        elif quality_score <= self.AUTO_REJECT_SCORE:
            reason = "Auto-rejected: " + "; ".join(rejection_reasons)
            return False, reason, quality_score
        
        else:
            # Middle ground - approve but with lower quality score
            reason = "Approved with moderate quality: " + "; ".join(approval_points[:2])
            return True, reason, quality_score
    
    def _check_rate_limits(self, email: str, ip: Optional[str]) -> Tuple[bool, str]:
        """Check submission rate limits"""
        from models.agent import Agent
        
        # Check email rate limit (3 per day)
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        email_submissions = self.db.query(Agent).filter(
            Agent.owner_email == email,
            Agent.created_at >= one_day_ago,
            Agent.submission_source == 'web_form'
        ).count()
        
        if email_submissions >= self.MAX_SUBMISSIONS_PER_EMAIL_PER_DAY:
            return False, f"{email_submissions} submissions in 24 hours (max {self.MAX_SUBMISSIONS_PER_EMAIL_PER_DAY})"
        
        # IP rate limit would require storing IPs (privacy concern)
        # For now, email-based rate limiting is sufficient
        
        return True, "Rate limit OK"
    
    def _validate_email(self, email: str) -> Tuple[bool, str]:
        """Validate email format and check for disposable domains"""
        # Basic format check (already validated by Pydantic EmailStr)
        
        # Check for disposable email domains
        disposable_domains = [
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org'
        ]
        
        domain = email.split('@')[1].lower()
        if domain in disposable_domains:
            return False, "Disposable email addresses not allowed"
        
        return True, "Valid email"
    
    def _validate_name(self, name: str) -> Tuple[bool, str]:
        """Validate agent name"""
        if len(name) < self.MIN_NAME_LENGTH:
            return False, f"Name too short (min {self.MIN_NAME_LENGTH} chars)"
        
        if len(name) > self.MAX_NAME_LENGTH:
            return False, f"Name too long (max {self.MAX_NAME_LENGTH} chars)"
        
        # Check for excessive special characters
        special_chars = sum(not c.isalnum() and not c.isspace() for c in name)
        if special_chars > len(name) * 0.3:
            return False, "Too many special characters in name"
        
        # Check for all caps (spam indicator)
        if name.isupper() and len(name) > 10:
            return False, "Name is all caps (spam indicator)"
        
        return True, "Name validated"
    
    def _check_description_quality(self, description: str) -> Tuple[int, str]:
        """Score description quality"""
        score = 0
        
        if len(description) < self.MIN_DESCRIPTION_LENGTH:
            return -20, f"Description too short (min {self.MIN_DESCRIPTION_LENGTH} chars)"
        
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            return -10, f"Description too long (max {self.MAX_DESCRIPTION_LENGTH} chars)"
        
        # Good length
        if 100 <= len(description) <= 500:
            score += 10
        
        # Check for proper sentences
        sentences = description.count('.') + description.count('!') + description.count('?')
        if sentences >= 2:
            score += 5
        
        # Check for technical terms (AI/ML indicators)
        technical_terms = [
            'agent', 'ai', 'machine learning', 'model', 'api',
            'natural language', 'llm', 'neural', 'automation'
        ]
        term_count = sum(1 for term in technical_terms if term.lower() in description.lower())
        score += min(term_count * 3, 15)
        
        # Penalize excessive emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            "]+", flags=re.UNICODE)
        emojis = len(emoji_pattern.findall(description))
        if emojis > 5:
            score -= 10
        
        feedback = f"Description quality: {score:+d} points"
        return score, feedback
    
    def _validate_url(self, url: str) -> Tuple[int, str]:
        """Validate and score URL"""
        score = 0
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme or not parsed.netloc:
                return -30, "Invalid URL format"
            
            # Check if domain is trusted
            domain = parsed.netloc.lower()
            for trusted in self.TRUSTED_DOMAINS:
                if trusted in domain:
                    score += 20
                    return score, f"Trusted domain: {trusted}"
            
            # Check for proper TLD
            if domain.endswith(('.com', '.org', '.io', '.ai', '.dev', '.co')):
                score += 5
            
            # Try to verify URL is reachable (HEAD request with timeout)
            try:
                response = requests.head(url, timeout=5, allow_redirects=True)
                if response.status_code < 400:
                    score += 10
                    return score, "URL is reachable"
                else:
                    return -10, f"URL returned {response.status_code}"
            except:
                # URL not reachable, but don't fail for this
                return 0, "URL format OK (not verified)"
        
        except Exception as e:
            return -20, f"URL validation error: {str(e)[:50]}"
        
        return score, "URL validated"
    
    def _detect_spam(self, name: str, description: str, url: str) -> Tuple[bool, str]:
        """Detect spam content"""
        combined_text = f"{name} {description} {url}".lower()
        
        for keyword in self.SPAM_KEYWORDS:
            if keyword.lower() in combined_text:
                return True, f"Spam keyword detected: '{keyword}'"
        
        # Check for excessive links in description
        link_count = description.lower().count('http://') + description.lower().count('https://')
        if link_count > 3:
            return True, "Too many links in description"
        
        # Check for repeated characters (spam indicator)
        if re.search(r'(.)\1{5,}', combined_text):
            return True, "Repeated characters detected"
        
        return False, ""
    
    def _check_duplicates(self, name: str, url: str, email: str) -> Tuple[bool, str]:
        """Check for duplicate submissions"""
        from models.agent import Agent
        
        # Check for exact name match
        existing_name = self.db.query(Agent).filter(
            Agent.name.ilike(name)
        ).first()
        
        if existing_name:
            return True, f"Agent with name '{name}' already exists"
        
        # Check for same URL
        existing_url = self.db.query(Agent).filter(
            Agent.source_url == url
        ).first()
        
        if existing_url:
            return True, f"Agent with URL '{url}' already exists"
        
        # Check for very similar names (Levenshtein distance would be better)
        name_hash = hashlib.md5(name.lower().strip().encode()).hexdigest()
        similar = self.db.query(Agent).filter(
            Agent.name.ilike(f"%{name[:10]}%")
        ).first()
        
        if similar and similar.name.lower().strip() != name.lower().strip():
            # Similar name exists, but allow if sufficiently different
            pass
        
        return False, ""
    
    def _validate_api_endpoint(self, api_endpoint: str) -> Tuple[int, str]:
        """Validate API endpoint if provided"""
        score = 0
        
        try:
            parsed = urlparse(api_endpoint)
            
            if not parsed.scheme or not parsed.netloc:
                return 0, "API endpoint format invalid (skipped)"
            
            # Bonus points for having API endpoint
            score += 5
            
            # Check if it's HTTPS
            if parsed.scheme == 'https':
                score += 5
                return score, "HTTPS API endpoint provided"
            else:
                return score, "HTTP API endpoint (insecure)"
        
        except:
            return 0, "API endpoint validation skipped"
        
        return score, "API endpoint OK"
