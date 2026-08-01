# AI Pipeline Report Details UI Plan

## Objective
Implement a transparent, interactive "How AI Processed Your Report" UI section on `app/app/report-details.tsx` featuring progress tracking, human-friendly agent cards, confidence indicators, natural status explanations, expandable agent reasoning, and a final AI summary card.

## UI Design & Component Specifications

1. **Progress Tracker**:
   - Visual step flow: Report Submitted → AI Verification → Department Assigned → Manual Review / Resolution.

2. **Agent Friendly Label Mapping**:
   - Moderator → Content Verification
   - Forensics → Photo Analysis
   - GeoValidator → Location Verification
   - Classifier → Issue Identification (with visual confidence bar % + reasoning bullets)
   - Enhancer → Description Enhancement (with AI summary/prompt optimization)
   - Router → Department Assignment (assigned department + SLA expected time)
   - QualityGate → Final AI Decision / Quality Gate (clear rationale if pending review)

3. **Interactive Features**:
   - Main section collapsible toggle ("Show AI Inspection Details").
   - Individual agent cards expandable on tap to inspect deeper reasoning & confidence metrics.
   - Natural language failure / status explanations for non-technical users.

4. **Final AI Summary Card**:
   - Highlights key outcomes (category, department, manual review status, next steps).

## Implementation Plan
1. Record plan in `docs/plans/ai_pipeline_report_details.md`.
2. Update `app/app/report-details.tsx` with the new AI Pipeline inspection components, progress tracker, interactive agent cards, confidence bars, and summary card.
3. Run `npx tsc --noEmit` in `app/` to ensure zero TypeScript errors.
