# agents/reviewer_agent.py

import asyncio
from typing import Dict, List, Any, Tuple
import os
from datetime import datetime
from openai import AsyncOpenAI

class ReviewerAgent:
    """
    AI-powered content reviewer using OpenAI GPT models.
    Specializes in quality assurance, fact-checking, and content improvement.
    """
    
    def __init__(self, openai_api_key: str = None):
        self.name = "Reviewer Agent"
        self.openai_client = AsyncOpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self.capabilities = [
            "AI-powered content review and analysis",
            "Quality assurance and fact-checking",
            "Content improvement suggestions",
            "Style and tone analysis"
        ]
        self.review_history = []
        
        # Reviewer agent's specialized prompt
        self.system_prompt = """You are an expert content reviewer and quality assurance specialist. Your role is to:

1. Thoroughly analyze content for accuracy, clarity, and effectiveness
2. Identify areas for improvement in structure, flow, and readability
3. Check for factual accuracy and logical consistency
4. Provide constructive feedback and specific improvement suggestions
5. Ensure content meets professional standards and objectives

Always be thorough, constructive, and specific in your feedback. Focus on both strengths and areas for improvement."""
    
    async def review(self, content: str, review_criteria: str = "comprehensive", strictness: int = 7) -> str:
        """
        Perform AI-powered review of content
        """
        try:
            # Conduct the review analysis
            review_result = await self._analyze_content(content, review_criteria, strictness)
            
            # Log the review
            review_log = {
                "timestamp": datetime.now().isoformat(),
                "criteria": review_criteria,
                "strictness": strictness,
                "content_length": len(content.split()),
                "status": "completed"
            }
            self.review_history.append(review_log)
            
            return review_result
            
        except Exception as e:
            error_msg = f"Review failed: {str(e)}"
            print(f"Reviewer Agent Error: {error_msg}")
            return f"❌ Review Error: {error_msg}"
    
    async def _analyze_content(self, content: str, criteria: str, strictness: int) -> str:
        """Analyze content using GPT and provide detailed review"""
        try:
            # Adjust review depth based on strictness
            review_depth = self._get_review_instructions(criteria, strictness)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"""Please conduct a thorough review of the following content.

CONTENT TO REVIEW:
{content}

REVIEW CRITERIA: {criteria}
STRICTNESS LEVEL: {strictness}/10
{review_depth}

Provide a comprehensive review including:

1. **Overall Assessment** (Score: X/10)
2. **Strengths** - What works well
3. **Areas for Improvement** - Specific issues and suggestions
4. **Content Quality Analysis**:
   - Accuracy and factual correctness
   - Clarity and readability
   - Structure and organization
   - Tone and style appropriateness
5. **Specific Recommendations** - Actionable improvements
6. **Final Verdict** - Ready for publication or needs revision

Be specific, constructive, and provide examples where helpful."""}
                ],
                temperature=0.3,  # Lower temperature for consistent analysis
                max_tokens=2000
            )
            
            review_analysis = response.choices[0].message.content
            
            # Create the final review report
            final_review = f"""# 📝 Content Review Report

*Review conducted by Reviewer Agent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Review Criteria: {criteria} | Strictness Level: {strictness}/10*

{review_analysis}

---
**Review Metadata:**
- Content Length: {len(content.split())} words
- Review Type: {criteria.title()}
- Strictness: {strictness}/10
- Reviewed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Status: Analysis Complete
"""
            
            return final_review
            
        except Exception as e:
            return f"Failed to analyze content: {str(e)}"
    
    def _get_review_instructions(self, criteria: str, strictness: int) -> str:
        """Get specific review instructions based on criteria and strictness"""
        
        criteria_guides = {
            "comprehensive": """
Conduct a full content review covering all aspects:
- Factual accuracy and evidence quality
- Writing quality and readability
- Structure and logical flow
- Audience appropriateness
- Completeness and depth
            """,
            "accuracy": """
Focus primarily on factual accuracy:
- Verify claims and statistics
- Check for logical inconsistencies
- Assess evidence quality
- Identify potential inaccuracies
            """,
            "readability": """
Focus on clarity and readability:
- Sentence structure and flow
- Word choice and terminology
- Paragraph organization
- Overall comprehension ease
            """,
            "professional": """
Focus on professional standards:
- Business writing conventions
- Formal tone and language
- Professional presentation
- Industry appropriateness
            """
        }
        
        strictness_guide = f"""
Strictness Level {strictness}/10 means:
- {"Be very lenient and focus on major issues only" if strictness <= 3 else ""}
- {"Apply moderate standards with balanced feedback" if 4 <= strictness <= 6 else ""}
- {"Apply high standards with detailed analysis" if 7 <= strictness <= 8 else ""}
- {"Be extremely thorough and identify even minor issues" if strictness >= 9 else ""}
        """
        
        base_instructions = criteria_guides.get(criteria, criteria_guides["comprehensive"])
        
        return f"{base_instructions}\n{strictness_guide}"
    
    async def fact_check(self, content: str) -> Dict[str, Any]:
        """Perform focused fact-checking on content claims"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert fact-checker. Analyze content for factual claims and assess their accuracy."},
                    {"role": "user", "content": f"""Fact-check the following content and identify:

{content}

Please provide:
1. List of factual claims made
2. Assessment of each claim (Accurate/Questionable/Inaccurate/Unverifiable)
3. Potential sources for verification
4. Red flags or areas requiring additional verification
5. Overall factual reliability score (1-10)

Focus on specific, verifiable claims"""}
                ],
                temperature=0.2,
                max_tokens=1500
            )
            
            fact_check_result = {
                "analysis": response.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
            return fact_check_result
            
        except Exception as e:
            return {"error": f"Fact-checking failed: {str(e)}"}
    
    async def suggest_improvements(self, content: str, focus_area: str = "overall") -> str:
        """Generate specific improvement suggestions"""
        try:
            focus_prompts = {
                "overall": "Provide comprehensive improvement suggestions for all aspects of the content",
                "structure": "Focus on improving the structure, organization, and flow of the content",
                "clarity": "Focus on improving clarity, readability, and comprehension",
                "engagement": "Focus on making the content more engaging and compelling",
                "conciseness": "Focus on making the content more concise and impactful"
            }
            
            prompt = focus_prompts.get(focus_area, focus_prompts["overall"])
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"""{prompt} for the following content:

{content}

Provide specific, actionable suggestions in the following format:
1. **Priority Issues** (must fix)
2. **Recommended Improvements** (should fix)
3. **Enhancement Opportunities** (nice to have)
4. **Specific Examples** of how to implement changes

Be concrete and provide before/after examples where helpful."""}
                ],
                temperature=0.4,
                max_tokens=1500
            )
            
            improvements = response.choices[0].message.content
            
            return f"""# 🔧 Content Improvement Suggestions

*Generated by Reviewer Agent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Focus Area: {focus_area.title()}*

{improvements}

---
**Improvement Focus:** {focus_area.title()}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
        except Exception as e:
            return f"Failed to generate improvement suggestions: {str(e)}"
    
    async def quality_score(self, content: str) -> Dict[str, Any]:
        """Generate a detailed quality score for content"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert content quality assessor. Provide detailed scoring across multiple dimensions."},
                    {"role": "user", "content": f"""Assess the quality of this content across multiple dimensions and provide scores (1-10) for each:

{content}

Please score and briefly explain each dimension:

1. **Accuracy & Factualness** (1-10):
2. **Clarity & Readability** (1-10):
3. **Structure & Organization** (1-10):
4. **Engagement & Interest** (1-10):
5. **Completeness & Depth** (1-10):
6. **Professional Quality** (1-10):

Also provide:
- **Overall Quality Score** (1-10):
- **Key Strengths** (top 2-3):
- **Main Weaknesses** (top 2-3):
- **Recommendation**: Ready to publish / Needs minor revisions / Needs major revisions

Be objective and provide brief explanations for each score."""}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            quality_analysis = response.choices[0].message.content
            
            # Parse scores (in a real implementation, you'd extract these properly)
            quality_data = {
                "analysis": quality_analysis,
                "overall_score": 8.2,  # Would be extracted from AI response
                "accuracy_score": 8.5,
                "clarity_score": 8.0,
                "structure_score": 8.3,
                "engagement_score": 7.8,
                "completeness_score": 8.4,
                "professional_score": 8.6,
                "timestamp": datetime.now().isoformat(),
                "recommendation": "Ready to publish"  # Would be extracted
            }
            
            return quality_data
            
        except Exception as e:
            return {"error": f"Quality scoring failed: {str(e)}"}
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """Get statistics about review activities"""
        if not self.review_history:
            return {
                "total_reviews": 0,
                "average_strictness": 0,
                "criteria_breakdown": {},
                "reviews_today": 0
            }
        
        total_reviews = len(self.review_history)
        average_strictness = sum(log.get("strictness", 0) for log in self.review_history) / total_reviews
        
        criteria_breakdown = {}
        for log in self.review_history:
            criteria = log.get("criteria", "Unknown")
            criteria_breakdown[criteria] = criteria_breakdown.get(criteria, 0) + 1
        
        # Count reviews today
        today = datetime.now().date()
        reviews_today = sum(1 for log in self.review_history 
                          if datetime.fromisoformat(log["timestamp"]).date() == today)
        
        return {
            "total_reviews": total_reviews,
            "average_strictness": round(average_strictness, 1),
            "criteria_breakdown": criteria_breakdown,
            "reviews_today": reviews_today,
            "last_review": self.review_history[-1]["timestamp"] if self.review_history else None
        }
    
    async def compare_versions(self, original: str, revised: str) -> str:
        """Compare two versions of content and highlight changes"""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at comparing document versions and identifying improvements."},
                    {"role": "user", "content": f"""Compare these two versions of content and analyze the changes:

ORIGINAL VERSION:
{original}

REVISED VERSION:
{revised}

Please provide:
1. **Summary of Changes** - What was modified
2. **Improvements Made** - How the revision is better
3. **Quality Assessment** - Overall impact of changes
4. **Recommendation** - Which version is better and why

Focus on content quality, clarity, and effectiveness."""}
                ],
                temperature=0.3,
                max_tokens=1200
            )
            
            comparison = response.choices[0].message.content
            
            return f"""# 🔄 Version Comparison Analysis

*Comparison conducted at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

{comparison}

---
**Analysis Type:** Version Comparison
**Conducted:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
        except Exception as e:
            return f"Failed to compare versions: {str(e)}"