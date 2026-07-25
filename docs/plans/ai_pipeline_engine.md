# Task Plan: Python AI Engine & Multi-Agent Orchestration

> Execution plan for implementing the LangGraph multi-agent pipeline and AI engine for CivicConnect.

## Plan Summary
1. Define typed shared state contract in `backend/agents/state.py`.
2. Implement 9 specialized agents:
   - Supervisor (Validation)
   - Forensics (Image analysis & duplicate detection)
   - Classifier (Category, urgency, tags)
   - Geo Validator (Ward boundary matching)
   - Moderator (Spam, abuse, toxicity filtering)
   - Enhancer (Summary & translation)
   - Department Router (PMC Department routing)
   - Notifier (Citizen alerts & point rewards)
   - Audit Recorder (DB audit logging)
3. Construct LangGraph state graph in `backend/agents/pipeline.py`.
4. Integrate with `AIPipelineService` and `report_service.py`.
5. Build test suite in `backend/tests/test_ai_pipeline.py`.

## Status
- [ ] Shared state contract
- [ ] 9 Agent nodes implementation
- [ ] LangGraph graph compilation
- [ ] Service integration
- [ ] Test suite & quality verification
