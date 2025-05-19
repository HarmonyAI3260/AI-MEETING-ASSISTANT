"""
Answer Generator Module

Responsible for generating answers to detected questions using LLMs.
"""

import os
import logging
import asyncio
import openai
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logger = logging.getLogger(__name__)

class AnswerGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None
        self.model = "gpt-4o"  # Default to the latest model
        self.max_context_length = 10  # Max number of conversation turns to include as context
        self.last_requests = {}  # Track recent requests to avoid duplicates
    
    async def initialize(self):
        """Initialize the answer generator"""
        logger.info("Initializing Answer Generator")
        try:
            if self.api_key:
                self.openai_client = openai.AsyncClient(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
                return True
            else:
                logger.warning("OpenAI API key not found. Using mock answers for testing.")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize Answer Generator: {str(e)}")
            return False
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    def _prepare_context(self, conversation_history: List[str]) -> str:
        """Prepare conversation context from history"""
        if not conversation_history:
            return ""
        
        # Take only the most recent conversation parts
        recent_history = conversation_history[-self.max_context_length:]
        
        # Format the conversation context
        context = "Recent conversation:\n\n"
        for i, message in enumerate(recent_history):
            context += f"[{i+1}] {message}\n"
        
        return context
    
    def _is_duplicate_request(self, question: str) -> bool:
        """Check if this is a duplicate request within a short time window"""
        current_time = datetime.now()
        
        # Clean up old requests older than 30 seconds
        for q in list(self.last_requests.keys()):
            if (current_time - self.last_requests[q]).total_seconds() > 30:
                del self.last_requests[q]
        
        # Check if question was recently asked
        for q in self.last_requests:
            if self._similarity(q, question) > 0.8:  # Simple similarity threshold
                return True
        
        # Record this question
        self.last_requests[question] = current_time
        return False
    
    def _similarity(self, text1: str, text2: str) -> float:
        """
        Calculate a simple similarity score between two texts
        Based on word overlap - a more sophisticated method would be better in production
        """
        if not text1 or not text2:
            return 0.0
            
        # Normalize and tokenize
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
            
        return len(intersection) / len(union)
    
    async def generate_answer(self, question: str, context: List[str] = None) -> str:
        """
        Generate an answer to a question using an LLM
        
        Args:
            question: The question to answer
            context: List of conversation history for context
            
        Returns:
            Generated answer text
        """
        if not question:
            return ""
            
        # Check for duplicate questions
        if self._is_duplicate_request(question):
            logger.info(f"Detected duplicate question: {question}")
            return ""  # Skip duplicate questions
            
        # Prepare prompt with context
        conversation_context = self._prepare_context(context) if context else ""
        
        prompt_template = f"""You are an AI assistant helping during a live meeting. 
Based on the conversation context and the question, provide a concise, helpful answer 
in 1-2 sentences. Be clear, accurate, and to the point.

{conversation_context}

Question: {question}

Provide a brief answer:"""
        
        try:
            if self.openai_client:
                # Call OpenAI API
                response = await self.openai_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful AI assistant that provides brief, accurate answers during live meetings."},
                        {"role": "user", "content": prompt_template}
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                
                answer = response.choices[0].message.content.strip()
                logger.info(f"Generated answer for: {question}")
                return answer
            else:
                # Use mock answers for testing when no API key is available
                logger.warning("Using mock answer (no OpenAI API key)")
                return self._generate_mock_answer(question)
                
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return "I couldn't generate an answer at this time."
    
    def _generate_mock_answer(self, question: str) -> str:
        """Generate a mock answer for testing purposes"""
        question_lower = question.lower()
        
        if "who" in question_lower:
            return "The person responsible is likely in the project team, but I don't have specific details based on the conversation."
        elif "when" in question_lower:
            return "Based on what was discussed, the timeline appears to be within the next two weeks, but no exact date was specified."
        elif "where" in question_lower:
            return "The location wasn't explicitly mentioned in the conversation."
        elif "why" in question_lower:
            return "Based on the discussion, this approach was chosen to optimize efficiency and reduce overhead costs."
        elif "how" in question_lower:
            return "The process involves setting up the environment, configuring parameters, and executing the deployment script."
        else:
            return "Based on the available context, I don't have enough information to provide a definitive answer to this question."
    
    async def cleanup(self):
        """Clean up resources"""
        self.last_requests.clear()
        logger.info("Answer Generator resources cleaned up")
