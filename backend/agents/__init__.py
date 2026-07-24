"""LangGraph agent pipeline for CivicConnect.

The pipeline processes citizen reports through 9 agents:
1. Validation Supervisor - checks report integrity
2. Image Forensics - detects photo manipulation
3. Issue Classifier - categorizes issue type and urgency
4. Geo-Validator - validates location against PMC boundaries
5. Content Moderator - checks for inappropriate content
6. Report Enhancer - translates and summarizes descriptions
7. Department Router - routes to appropriate PMC department
8. Notifier - sends push notifications and awards points
9. Audit Recorder - logs all agent decisions

Each agent produces typed output with confidence scores.
All decisions are logged in agent_executions table.
"""
