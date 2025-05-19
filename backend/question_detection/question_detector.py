"""
Question Detector Module

Responsible for detecting questions within transcribed text using NLP techniques.
"""

import re
import logging
from typing import Optional, List, Dict, Any
import nltk
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os

# Configure logging
logger = logging.getLogger(__name__)

class QuestionDetector:
    def __init__(self):
        self.question_patterns = [
            r"^(?:can|could|would|will|should|do|does|did|is|are|was|were|have|has|had)\s+\w+",  # Yes/no questions
            r"^(?:what|which|when|where|why|who|whom|whose|how)\s+",  # WH-questions
            r"\?\s*$"  # Ends with question mark
        ]
        self.question_starters = [
            "what", "which", "when", "where", "why", "who", "whom", "whose", "how",
            "can", "could", "would", "will", "should", "do", "does", "did",
            "is", "are", "was", "were", "have", "has", "had", "may", "might"
        ]
        
        # NLP components
        self.model = None
        self.tokenizer = None
        self.nltk_initialized = False
        
        # Try to initialize NLTK and transformers model
        self._initialize_nlp()
    
    def _initialize_nlp(self):
        """Initialize NLP components"""
        try:
            # Initialize NLTK for sentence tokenization
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt', quiet=True)
            self.nltk_initialized = True
            
            # Initialize transformers model for question classification
            # Only if CUDA (GPU) is available or model already downloaded
            model_name = "distilbert-base-uncased-finetuned-sst-2-english"  # Using sentiment model as placeholder
            
            if torch.cuda.is_available() or os.path.exists(os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "transformers", model_name)):
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                if torch.cuda.is_available():
                    self.model = self.model.to("cuda")
                logger.info("Loaded transformers model for question detection")
            else:
                logger.info("Skipping loading transformers model (no GPU available and model not cached)")
                
        except Exception as e:
            logger.error(f"Error initializing NLP components: {str(e)}")
    
    def _is_question_rule_based(self, text: str) -> bool:
        """Check if text is a question using rule-based approach"""
        # Check if empty
        if not text or not text.strip():
            return False
            
        # Normalize text for matching
        text = text.strip().lower()
        
        # Check against patterns
        for pattern in self.question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Check for question starters
        words = text.split()
        if words and words[0] in self.question_starters:
            return True
            
        return False
    
    def _is_question_model_based(self, text: str) -> bool:
        """Check if text is a question using model-based approach"""
        if not self.model or not self.tokenizer:
            return False
            
        try:
            # Preprocess
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
            # Model inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Get prediction (this is simplified - would need actual question classifier)
            # For now, using sentiment as proxy (negative = question)
            logits = outputs.logits
            prediction = torch.nn.functional.softmax(logits, dim=-1)
            
            # This is a placeholder logic - in a real implementation, 
            # you would use a model specifically trained for question detection
            is_question_prob = prediction[0][0].item()  # Using negative sentiment as proxy
            return is_question_prob > 0.7
            
        except Exception as e:
            logger.error(f"Error in model-based question detection: {str(e)}")
            return False
    
    def detect_question(self, transcript: str) -> Optional[str]:
        """
        Detect if transcript contains a question and extract it
        
        Args:
            transcript: Transcribed text to analyze
            
        Returns:
            Extracted question if found, None otherwise
        """
        if not transcript:
            return None
            
        # Split transcript into sentences if NLTK is available
        sentences = [transcript]
        if self.nltk_initialized:
            try:
                sentences = sent_tokenize(transcript)
            except Exception as e:
                logger.error(f"Error tokenizing sentences: {str(e)}")
        
        # Check each sentence for question
        for sentence in sentences:
            # Apply rule-based detection
            if self._is_question_rule_based(sentence):
                logger.info(f"Detected question (rule-based): {sentence}")
                return sentence.strip()
                
            # Apply model-based detection if available
            if self.model and self._is_question_model_based(sentence):
                logger.info(f"Detected question (model-based): {sentence}")
                return sentence.strip()
                
        return None
        
    def extract_question_metadata(self, question: str) -> Dict[str, Any]:
        """Extract metadata about the detected question"""
        if not question:
            return {}
            
        # Determine question type
        question_type = "unknown"
        question_lower = question.lower().strip()
        
        if question_lower.startswith(("what", "which", "when", "where", "why", "who", "whom", "whose", "how")):
            question_type = "wh"
            
            # Further classify WH question types
            if question_lower.startswith("what"):
                question_type = "what"
            elif question_lower.startswith("who") or question_lower.startswith("whom") or question_lower.startswith("whose"):
                question_type = "who"
            elif question_lower.startswith("where"):
                question_type = "where"
            elif question_lower.startswith("when"):
                question_type = "when"
            elif question_lower.startswith("why"):
                question_type = "why"
            elif question_lower.startswith("how"):
                question_type = "how"
            elif question_lower.startswith("which"):
                question_type = "which"
                
        elif any(question_lower.startswith(starter) for starter in 
                ["can", "could", "would", "will", "should", "do", "does", "did",
                 "is", "are", "was", "were", "have", "has", "had"]):
            question_type = "yes_no"
            
        # Determine if rhetorical (simplified heuristic)
        is_rhetorical = False
        rhetorical_patterns = [
            r"isn't it obvious",
            r"don't you think",
            r"wouldn't you agree",
            r"who (would|wouldn't)",
            r"what's the point",
            r"why bother"
        ]
        for pattern in rhetorical_patterns:
            if re.search(pattern, question_lower):
                is_rhetorical = True
                break
                
        return {
            "question_type": question_type,
            "is_rhetorical": is_rhetorical,
            "word_count": len(question.split()),
            "contains_question_mark": "?" in question
        }
