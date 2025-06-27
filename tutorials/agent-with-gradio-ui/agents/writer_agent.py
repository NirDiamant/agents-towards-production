# agents/writer_agent.py

import asyncio
from typing import Dict, List, Any
import os
from datetime import datetime
from openai import AsyncOpenAI

class WriterAgent:
    """
    AI-powered writing agent using OpenAI GPT models.
    Specializes in creating high-quality content based on research data.
    """
    
    def __init__(self, openai_api_key: str = None):
        self.name = "Writer Agent"
        self.openai_client = AsyncOpenAI(api_key=openai_api_key or os.getenv("OPENAI_API_KEY"))
        self.capabilities = [
            "AI-powered content creation",
            "Multiple writing styles and formats",
            "Research-based article writing", 
            "Content optimization and enhancement"
        ]
        self.writing_history = []
        
        # Writer agent's specialized prompt
        self.system_prompt = """You are an expert content writer specialized in creating high-quality, engaging, and informative content. Your role is to:

1. Transform research data into compelling, well-structured content
2. Adapt writing style based on target audience and requirements
3. Ensure content is accurate, engaging, and actionable
4. Create clear, logical flow with proper structure and formatting
5. Optimize content for readability and comprehension

Always prioritize clarity, accuracy, and engagement. Use research data effectively to support your points and create valuable content for readers."""
    
    async def write(self, research_data: str, requirements: str = "", style: str = "Professional") -> str:
        """
        Create content based on research data using AI
        """
        try:
            # Create the writing prompt based on research and requirements
            content = await self._generate_content(research_data, requirements, style)
            
            # Log the writing task
            writing_log = {
                "timestamp": datetime.now().isoformat(),
                "style": style,
                "requirements": requirements,
                "word_count": len(content.split()),
                "status": "completed"
            }
            self.writing_history.append(writing_log)
            
            return content
            
        except Exception as e:
            error_msg = f"Writing failed: {str(e)}"
            print(f"Writer Agent Error: {error_msg}")
            return f"❌ Writing Error: {error_msg}"
    
    async def _generate_content(self, research_data: str, requirements: str, style: str) -> str:
        """Generate content using GPT based on research data"""
        try:
            # Create style-specific instructions
            style_instructions = self._get_style_instructions(style)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"""Create high-quality content based on the following research data.

RESEARCH DATA:
{research_data}

REQUIREMENTS:
{requirements if requirements else "Create comprehensive, informative content"}

WRITING STYLE: {style}
{style_instructions}

Please create well-structured content that:
1. Uses the research data effectively
2. Follows the specified writing style
3. Meets the stated requirements
4. Is engaging and informative
5. Has clear headings and organization
6. Includes actionable insights where appropriate

Format the content in markdown with proper headings, bullet points, and emphasis."""}
                ],
                temperature=0.7,  # Balanced creativity and coherence
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Add metadata header
            final_content = f"""# ✍️ Content Created by Writer Agent

*Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Style: {style}*

{content}

---
**Content Metadata:**
- Writing Style: {style}
- Word Count: ~{len(content.split())} words
- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Based on: Research Agent findings
"""
            
            return final_content
            
        except Exception as e:
            return f"Failed to generate content: {str(e)}"
    
    def _get_style_instructions(self, style: str) -> str:
        """Get specific instructions for different writing styles"""
        style_guides = {
            "Professional": """
- Use formal tone and business language
- Focus on facts, data, and actionable insights
- Structure with clear executive summary and key points
- Include relevant statistics and evidence
- Write for business stakeholders and decision-makers
            """,
            "Casual": """
- Use conversational, friendly tone
- Include relatable examples and analogies
- Break down complex concepts simply
- Add personality and engagement
- Write as if explaining to a friend
            """,
            "Academic": """
- Use scholarly tone with proper citations
- Include methodology and evidence-based arguments
- Structure with abstract, introduction, analysis, conclusion
- Reference research findings extensively
- Write for academic audience with domain expertise
            """,
            "Creative": """
- Use engaging storytelling elements
- Include metaphors, analogies, and creative examples
- Focus on narrative flow and emotional connection
- Use varied sentence structure and descriptive language
- Write to inspire and engage readers
            """
        }
        
        return style_guides.get(style, style_guides["Professional"])
    
    async def enhance_content(self, content: str, enhancement_type: str = "readability") -> str:
        """Enhance existing content using AI"""
        try:
            enhancement_prompts = {
                "readability": "Improve the readability and flow of this content while maintaining all key information",
                "engagement": "Make this content more engaging and compelling while keeping it professional",
                "conciseness": "Make this content more concise and to-the-point while preserving important details",
                "seo": "Optimize this content for search engines while maintaining quality and readability"
            }
            
            prompt = enhancement_prompts.get(enhancement_type, enhancement_prompts["readability"])
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"""{prompt}:

{content}

Please provide the enhanced version while maintaining the original structure and key messages."""}
                ],
                temperature=0.5,
                max_tokens=2000
            )
            
            enhanced_content = response.choices[0].message.content
            
            return f"""# ✨ Enhanced Content

*Enhancement Type: {enhancement_type.title()}*
*Enhanced at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*

{enhanced_content}
"""
            
        except Exception as e:
            return f"Failed to enhance content: {str(e)}"
    
    async def create_summary(self, content: str, summary_type: str = "executive") -> str:
        """Create different types of summaries"""
        try:
            summary_prompts = {
                "executive": "Create a brief executive summary highlighting key points and actionable insights",
                "bullet": "Create a bullet-point summary of the main points",
                "abstract": "Create an academic-style abstract summarizing the content",
                "tldr": "Create a very brief TL;DR summary"
            }
            
            prompt = summary_prompts.get(summary_type, summary_prompts["executive"])
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at creating concise, informative summaries."},
                    {"role": "user", "content": f"""{prompt} for the following content:

{content}"""}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Failed to create summary: {str(e)}"
    
    def get_writing_statistics(self) -> Dict[str, Any]:
        """Get statistics about writing activities"""
        if not self.writing_history:
            return {"total_pieces": 0, "total_words": 0, "average_words": 0}
        
        total_pieces = len(self.writing_history)
        total_words = sum(log.get("word_count", 0) for log in self.writing_history)
        average_words = total_words // total_pieces if total_pieces > 0 else 0
        
        style_breakdown = {}
        for log in self.writing_history:
            style = log.get("style", "Unknown")
            style_breakdown[style] = style_breakdown.get(style, 0) + 1
        
        return {
            "total_pieces": total_pieces,
            "total_words": total_words,
            "average_words": average_words,
            "style_breakdown": style_breakdown,
            "last_activity": self.writing_history[-1]["timestamp"] if self.writing_history else None
        }