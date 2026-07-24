"""Content Moderator agent for CivicConnect.

Checks submitted descriptions for:
- Profanity and inappropriate content
- Spam detection
- Duplicate report identification

Input: Report description text
Output: {clean: bool, flags: list, toxicity: float}

This agent runs after classification to ensure content quality.
"""
