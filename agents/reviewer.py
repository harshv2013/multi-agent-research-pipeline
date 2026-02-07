"""
Reviewer Agent - validates content quality and accuracy.

Responsibilities:
- Evaluate content quality across multiple criteria
- Verify factual accuracy against research
- Assess completeness and clarity
- Provide constructive feedback
- Make approve/reject/revise decisions
"""
from typing import Dict, Any
import time
import json

from .base_agent import BaseAgent
from config import AgentPrompts
from state.schemas import AgentState, ReviewOutput
from tools.validation import ContentValidator


class ReviewerAgent(BaseAgent):
    """
    Reviewer agent that evaluates content quality.
    
    Review criteria:
    1. Factual Accuracy (matches research)
    2. Completeness (covers all key points)
    3. Clarity (well-structured, readable)
    4. Engagement (compelling, professional)
    5. Citations (proper attribution)
    
    Decisions:
    - APPROVE: Content meets quality standards
    - REQUEST_REVISION: Needs improvements
    - REJECT: Major issues, start over
    """
    
    def __init__(self):
        super().__init__(name="reviewer")
        self.validator = ContentValidator()
    
    def execute(self, state: AgentState) -> Dict[str, Any]:
        """
        Execute content review process.
        
        Args:
            state: Current workflow state
            
        Returns:
            State updates with review results
        """
        start_time = time.time()
        self.log_execution_start(state)
        
        try:
            # Get content and research
            content = state['content_draft']
            research = state['research_findings']
            
            self.logger.info(f"Reviewing content (version {state['content_version']})")
            
            # Perform comprehensive review
            review_output = self._perform_review(content, research)
            
            # Prepare state updates
            updates = {
                'current_agent': self.name,
                'review_score': review_output['overall_score'],
                'review_feedback': self._format_feedback(review_output),
                'review_decision': review_output['decision'],
                'revision_count': state['revision_count'] + (1 if review_output['decision'] == 'request_revision' else 0)
            }
            
            # If approved, set as final output
            if review_output['decision'] == 'approve':
                updates['final_output'] = content
                updates['metadata'] = {
                    'word_count': len(content.split()),
                    'quality_score': review_output['overall_score'],
                    'sources_used': len(state['research_sources']),
                    'revisions': state['revision_count']
                }
            
            # Add completion message
            message_update = self.add_message_to_state(
                state,
                recipient='supervisor',
                content=f"Review complete: {review_output['decision'].upper()} "
                       f"(score: {review_output['overall_score']:.2f})",
                message_type="result"
            )
            updates.update(message_update)
            
            duration_ms = (time.time() - start_time) * 1000
            self.log_execution_end(state, duration_ms)
            
            return updates
            
        except Exception as e:
            self.logger.error(f"Review failed: {str(e)}")
            return {
                'current_agent': self.name,
                'review_score': 0.0,
                'review_feedback': f"Review failed: {str(e)}",
                'review_decision': 'reject',
                'errors': [f"Review error: {str(e)}"]
            }
    
    def _perform_review(self, content: str, research: str) -> ReviewOutput:
        """
        Perform comprehensive content review.
        
        Args:
            content: Content to review
            research: Original research
            
        Returns:
            ReviewOutput with scores and feedback
        """
        # Step 1: Automated validation
        validation_result = self.validator.validate(content, research)
        
        # Step 2: LLM-based review
        llm_review = self._llm_review(content, research)
        
        # Step 3: Combine results
        combined_review = self._combine_reviews(validation_result, llm_review)
        
        return combined_review
    
    def _llm_review(self, content: str, research: str) -> Dict[str, Any]:
        """
        LLM-based content review.
        
        Args:
            content: Content to review
            research: Original research
            
        Returns:
            Review results from LLM
        """
        system_prompt = AgentPrompts.REVIEWER
        user_prompt = f"""
Review the following content for quality and accuracy.

CONTENT TO REVIEW:
{content}

ORIGINAL RESEARCH:
{research[:1500]}...

Evaluate on these criteria (score 0-10 each):
1. Factual Accuracy: Claims supported by research?
2. Completeness: Covers all key points?
3. Clarity: Well-structured and readable?
4. Engagement: Compelling and professional?
5. Citations: Proper attribution?

Respond with JSON:
{{
    "factual_accuracy": 0-10,
    "completeness": 0-10,
    "clarity": 0-10,
    "engagement": 0-10,
    "citations": 0-10,
    "strengths": ["strength1", "strength2", ...],
    "issues": ["issue1", "issue2", ...],
    "recommendations": ["rec1", "rec2", ...],
    "decision": "approve|request_revision|reject"
}}

Provide your review:
"""
        
        try:
            response = self.invoke_llm(system_prompt, user_prompt)
            
            # Parse JSON
            response = response.replace("```json", "").replace("```", "").strip()
            review_data = json.loads(response)
            
            return review_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse review JSON: {e}")
            return self._fallback_review()
        except Exception as e:
            self.logger.error(f"LLM review failed: {e}")
            return self._fallback_review()
    
    # def _combine_reviews(
    #     self,
    #     validation_result: Any,
    #     llm_review: Dict[str, Any]
    # ) -> ReviewOutput:
    #     """
    #     Combine automated validation and LLM review.
        
    #     Args:
    #         validation_result: Result from ContentValidator
    #         llm_review: Result from LLM review
            
    #     Returns:
    #         Combined ReviewOutput
    #     """
    #     # Calculate criterion scores
    #     criterion_scores = {
    #         'factual_accuracy': llm_review.get('factual_accuracy', 5) / 10.0,
    #         'completeness': llm_review.get('completeness', 5) / 10.0,
    #         'clarity': llm_review.get('clarity', 5) / 10.0,
    #         'engagement': llm_review.get('engagement', 5) / 10.0,
    #         'citations': llm_review.get('citations', 5) / 10.0
    #     }
        
    #     # Overall score (weighted average)
    #     overall_score = (
    #         criterion_scores['factual_accuracy'] * 0.3 +
    #         criterion_scores['completeness'] * 0.2 +
    #         criterion_scores['clarity'] * 0.2 +
    #         criterion_scores['engagement'] * 0.15 +
    #         criterion_scores['citations'] * 0.15
    #     )
        
    #     # Combine with validation score
    #     final_score = (overall_score + validation_result.score) / 2
        
    #     # Combine issues
    #     all_issues = validation_result.issues + llm_review.get('issues', [])
    #     all_strengths = llm_review.get('strengths', [])
    #     all_recommendations = validation_result.suggestions + llm_review.get('recommendations', [])
        
    #     # Decision logic
    #     decision = self._make_decision(
    #         final_score,
    #         all_issues,
    #         llm_review.get('decision', 'request_revision')
    #     )
        
    #     return ReviewOutput(
    #         overall_score=final_score,
    #         criterion_scores=criterion_scores,
    #         strengths=all_strengths[:5],
    #         issues=all_issues[:5],
    #         recommendations=all_recommendations[:5],
    #         decision=decision
    #     )
    
    def _combine_reviews(
        self,
        validation_result: Any,
        llm_review: Dict[str, Any]
    ) -> ReviewOutput:
        """
        Combine automated validation and LLM review.
        
        Args:
            validation_result: Result from ContentValidator
            llm_review: Result from LLM review
            
        Returns:
            Combined ReviewOutput
        """
        # Calculate criterion scores
        criterion_scores = {
            'factual_accuracy': llm_review.get('factual_accuracy', 5) / 10.0,
            'completeness': llm_review.get('completeness', 5) / 10.0,
            'clarity': llm_review.get('clarity', 5) / 10.0,
            'engagement': llm_review.get('engagement', 5) / 10.0,
            'citations': llm_review.get('citations', 5) / 10.0
        }
        
        # Overall score with improved weights
        # Citations less important (5%), accuracy/completeness more important
        overall_score = (
            criterion_scores['factual_accuracy'] * 0.35 +
            criterion_scores['completeness'] * 0.25 +
            criterion_scores['clarity'] * 0.20 +
            criterion_scores['engagement'] * 0.15 +
            criterion_scores['citations'] * 0.05
        )
        
        # Combine with validation score (70% LLM, 30% validation)
        final_score = (overall_score * 0.7 + validation_result.score * 0.3)
        
        # Bonus for high-quality content
        if overall_score >= 0.85:
            final_score = min(final_score + 0.05, 1.0)
        
        self.logger.info(
            f"Score: LLM={overall_score:.2f}, "
            f"Validation={validation_result.score:.2f}, "
            f"Final={final_score:.2f}"
        )
        
        # Combine issues
        all_issues = validation_result.issues + llm_review.get('issues', [])
        all_strengths = llm_review.get('strengths', [])
        all_recommendations = validation_result.suggestions + llm_review.get('recommendations', [])
        
        # Decision logic
        decision = self._make_decision(
            final_score,
            all_issues,
            llm_review.get('decision', 'request_revision')
        )
        
        return ReviewOutput(
            overall_score=final_score,
            criterion_scores=criterion_scores,
            strengths=all_strengths[:5],
            issues=all_issues[:5],
            recommendations=all_recommendations[:5],
            decision=decision
        )



    # def _make_decision(
    #     self,
    #     score: float,
    #     issues: list,
    #     llm_decision: str
    # ) -> str:
    #     """
    #     Make final review decision.
        
    #     Args:
    #         score: Overall quality score
    #         issues: List of issues found
    #         llm_decision: LLM's recommended decision
            
    #     Returns:
    #         Decision: approve, request_revision, or reject
    #     """
    #     # Critical issues = reject
    #     critical_keywords = ['plagiarism', 'incorrect', 'false', 'misleading']
    #     has_critical = any(
    #         any(kw in issue.lower() for kw in critical_keywords)
    #         for issue in issues
    #     )
        
    #     if has_critical:
    #         self.logger.warning("Critical issues found, rejecting content")
    #         return 'reject'
        
    #     # High score = approve (lowered threshold from 0.8 to 0.7)
    #     if score >= 0.8 and len(issues) <= 2:
    #         self.logger.info(f"Content approved with score {score:.2f}")
    #         return 'approve'

    #     # Medium score = approve if few issues
    #     if score >= 0.6 and len(issues) <= 2:
    #         self.logger.info(f"Content approved with acceptable score {score:.2f}")
    #         return 'approve'
            
    #     # Very low score = reject
    #     if score < 0.4:
    #         self.logger.warning(f"Content rejected with low score {score:.2f}")
    #         return 'reject'
        
    #     # Otherwise, request revision
    #     self.logger.info(f"Content needs revision (score: {score:.2f}, issues: {len(issues)})")
    #     return 'request_revision'

    def _make_decision(
        self,
        score: float,
        issues: list,
        llm_decision: str
    ) -> str:
        """Make final review decision."""
        
        # Critical issues = reject (but be more specific about what's critical)
        critical_keywords = ['plagiarism', 'fabricated', 'completely false', 'dangerous misinformation']  # More specific
        has_critical = any(
            any(kw in issue.lower() for kw in critical_keywords)
            for issue in issues
        )
        
        if has_critical:
            self.logger.warning("Critical issues found, rejecting content")
            return 'reject'
        
        # LOWER THRESHOLD: High score = approve (0.85 instead of 0.7)
        if score >= 0.85 and len(issues) <= 3:  # Changed from 0.7
            self.logger.info(f"Content approved with high score {score:.2f}")
            return 'approve'
        
        # Medium score with minor issues = approve
        if score >= 0.75 and len(issues) <= 2:  # Changed from 0.6
            self.logger.info(f"Content approved with acceptable score {score:.2f}")
            return 'approve'
        
        # Low score = reject (keep at 0.4)
        if score < 0.4:
            self.logger.warning(f"Content rejected with low score {score:.2f}")
            return 'reject'
        
        # Otherwise, request revision
        self.logger.info(f"Content needs revision (score: {score:.2f}, issues: {len(issues)})")
        return 'request_revision'

    
    def _format_feedback(self, review_output: ReviewOutput) -> str:
        """
        Format review output as readable feedback.
        
        Args:
            review_output: ReviewOutput object
            
        Returns:
            Formatted feedback string
        """
        parts = [
            f"=== CONTENT REVIEW ===",
            f"Overall Score: {review_output['overall_score']:.2f}/1.0",
            f"Decision: {review_output['decision'].upper()}",
            ""
        ]
        
        # Criterion scores
        parts.append("Criterion Scores:")
        for criterion, score in review_output['criterion_scores'].items():
            parts.append(f"  - {criterion.replace('_', ' ').title()}: {score:.2f}")
        
        # Strengths
        if review_output['strengths']:
            parts.append("\n✓ Strengths:")
            for strength in review_output['strengths']:
                parts.append(f"  - {strength}")
        
        # Issues
        if review_output['issues']:
            parts.append("\n✗ Issues to Address:")
            for issue in review_output['issues']:
                parts.append(f"  - {issue}")
        
        # Recommendations
        if review_output['recommendations']:
            parts.append("\n→ Recommendations:")
            for rec in review_output['recommendations']:
                parts.append(f"  - {rec}")
        
        return "\n".join(parts)
    
    def _fallback_review(self) -> Dict[str, Any]:
        """Fallback review when LLM fails."""
        return {
            'factual_accuracy': 6,
            'completeness': 6,
            'clarity': 6,
            'engagement': 6,
            'citations': 6,
            'strengths': ['Content was generated'],
            'issues': ['Unable to perform detailed review'],
            'recommendations': ['Manual review recommended'],
            'decision': 'request_revision'
        }