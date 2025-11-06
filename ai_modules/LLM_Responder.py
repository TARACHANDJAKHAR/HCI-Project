"""
LLM Responder - Natural language generation for general conversation.

Handles commands that don't match any specialized processor.
Uses either:
- Hugging Face models (local, free, runs on your machine)
- OpenAI API (cloud-based, requires API key, better quality)

Supports conversation history and personalization based on user profile.
Falls back gracefully if model loading fails or API errors occur.
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
import typing as t

# Try to import OpenAI library (optional dependency)
try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class LLMResponder:
    """
    Language model responder for generating natural conversation.
    
    Supports two providers:
    1. Hugging Face (local models like GPT-2, LLaMA) - free, runs locally
    2. OpenAI (GPT-4, GPT-3.5) - requires API key, better quality
    
    Maintains conversation history for context-aware responses.
    Can be personalized with user profile (name, preferences).
    """
    
    def __init__(self, model_name="gpt2"):
        """
        Initialize LLM responder with model configuration.
        
        Model and provider can be overridden via environment variables:
        - LLM_PROVIDER: "hf" (Hugging Face) or "openai"
        - LLM_MODEL: Model name (e.g., "gpt2", "gpt-4o", "distilgpt2")
        
        Args:
            model_name (str): Default model name if LLM_MODEL env var not set
        """
        # Provider and model selection via env vars
        # "hf" = Hugging Face (local), "openai" = OpenAI API
        self.provider = os.getenv("LLM_PROVIDER", "hf").lower()
        self.model_name = os.getenv("LLM_MODEL", model_name)

        # Conversation and personalization state
        self.profile: dict = {}  # User profile (name, preferences)
        # Conversation history: list of {role: 'user'|'assistant', content: str}
        self.history: list[dict] = []

        # Hugging Face model state (lazy-loaded)
        self.tokenizer = None  # Tokenizer for text processing
        self.model = None      # Language model

        # OpenAI client state (lazy-loaded)
        self._openai_client = None
        self._last_error: str | None = None  # Track last error for debugging
        
        # System persona/prompt that guides the model's responses
        self.persona = (
            "You are a warm, gentle, and caring elderly companion. "
            "You comfort the user when they feel sad or lonely, speak simply, "
            "and always encourage positivity and calmness. "
            "ALWAYS answer directly and concisely in 1-3 sentences."
        )

    def _ensure_model_loaded(self):
        """
        Lazy-load the model when first needed.
        
        This prevents slow startup times - model only loads when first used.
        For Hugging Face: downloads and loads model from HuggingFace Hub
        For OpenAI: initializes API client (no model download needed)
        """
        if self.provider == "openai":
            # OpenAI provider: initialize client if not already done
            if self._openai_client is not None:
                return  # Already initialized
            
            try:
                # Check if OpenAI package is installed
                if OpenAI is None:
                    raise RuntimeError("openai package not installed")
                
                # Get API key from environment
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise RuntimeError("OPENAI_API_KEY not set")
                
                # Initialize OpenAI client
                self._openai_client = OpenAI(api_key=api_key)
                print("OpenAI client initialized for model:", self.model_name)
                self._last_error = None
            except Exception as e:
                print("OpenAI init error:", e)
                self._openai_client = None
                self._last_error = f"OpenAI init error: {e}"
        else:
            # Hugging Face provider: load model if not already loaded
            if self.model is not None and self.tokenizer is not None:
                return  # Already loaded
            
            try:
                print("Loading HF model:", self.model_name)
                # Download and load tokenizer (converts text to numbers)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                # Download and load model (generates text)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                
                # Set pad token if not present (needed for some models)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                
                self._last_error = None
            except Exception as e:
                print("HF load error:", e)
                self.model = None
                self.tokenizer = None
                self._last_error = f"HF load error: {e}"

    def generate(self, text: str):
        """
        Generate a natural language response to user input.
        
        Uses conversation history for context and user profile for personalization.
        Falls back to safe default messages if model fails.
        
        Args:
            text (str): User's input text
            
        Returns:
            str: Generated response from the model, or fallback message if error
        """
        # Ensure model is loaded (lazy loading)
        self._ensure_model_loaded()
        
        try:
            # Track user message in conversation history
            self.history.append({"role": "user", "content": text})
            # Keep only last 8 messages (4 turns) to avoid context overflow
            self.history = self.history[-8:]

            # Build system prompt with personalization
            name = self.profile.get("name")
            prefs = self.profile.get("preferences") or {}
            persona = self.persona
            
            # Add personalization if user profile has name
            if name:
                persona += f" The user's name is {name}. Address them by name occasionally."
            # Add tone preference if specified
            if prefs.get("tone"):
                persona += f" Use a {prefs['tone']} tone."

            # Route to appropriate provider
            if self.provider == "openai" and self._openai_client is not None:
                # OpenAI API path (better quality, requires API key)
                messages = [{"role": "system", "content": persona}]
                # Add recent conversation history (last 6 messages = 3 turns)
                for m in self.history[-6:]:
                    messages.append({"role": m["role"], "content": m["content"]})
                
                try:
                    # Call OpenAI API
                    resp = self._openai_client.chat.completions.create(
                        model=self.model_name,      # e.g., "gpt-4o", "gpt-4o-mini"
                        messages=messages,          # Conversation context
                        temperature=0.3,            # Lower = more focused, higher = more creative
                        max_tokens=220,             # Limit response length
                    )
                    content = resp.choices[0].message.content or ""
                    self._last_error = None
                    reply = content.strip()
                    # Add to history
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
                except Exception as e:
                    print("OpenAI generate error:", e)
                    self._last_error = f"OpenAI generate error: {e}"
                    
                    # Optional: Try HF fallback if configured
                    fallback_model = os.getenv("LLM_FALLBACK_MODEL")
                    if fallback_model:
                        try:
                            # Temporarily use HF path with fallback model
                            tok = AutoTokenizer.from_pretrained(fallback_model)
                            mdl = AutoModelForCausalLM.from_pretrained(fallback_model)
                            if tok.pad_token is None:
                                tok.pad_token = tok.eos_token
                            prompt = f"{self.persona}\nUser: {text}\nAssistant:"
                            inputs = tok(prompt, return_tensors="pt", padding=True)
                            outputs = mdl.generate(
                                **inputs,
                                max_length=220,
                                temperature=0.3,
                                top_p=0.9,
                                do_sample=True,
                                pad_token_id=tok.eos_token_id,
                            )
                            reply = tok.decode(outputs[0], skip_special_tokens=True)
                            return reply.split("Assistant:")[-1].strip().capitalize()
                        except Exception as fe:
                            print("Fallback HF error:", fe)
                    
                    # Return safe fallback message
                    return "I'm here to listen and help you feel better."
            
            # Hugging Face path (local model)
            if self.model is None or self.tokenizer is None:
                # Model failed to load - return safe fallback
                return "I'm here with you. Let's take a deep breath together."
            
            # Build prompt with conversation history
            recent_pairs = self.history[-8:]  # Last 8 messages
            recent = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in recent_pairs])
            prompt = f"{persona}\n{recent}\nAssistant:"
            
            # Tokenize input (convert text to numbers)
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
            
            # Generate response
            outputs = self.model.generate(
                **inputs,
                max_length=220,              # Maximum tokens to generate
                temperature=0.3,             # Lower = more focused responses
                top_p=0.9,                   # Nucleus sampling parameter
                do_sample=True,              # Enable sampling (not greedy)
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3,      # Prevent repeating 3-word phrases
                repetition_penalty=1.15,     # Penalize repetition
            )
            
            # Decode output (convert numbers back to text)
            reply = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            self._last_error = None
            
            # Extract only the assistant's response (remove prompt)
            out = reply.split("Assistant:")[-1]
            
            # Stop at any new role markers (prevent model from continuing conversation)
            for stopper in ["\nUser:", "\nSystem:", "\nAssistant:"]:
                if stopper in out:
                    out = out.split(stopper)[0]
            
            out = out.strip()
            
            # Fallback if output is empty
            if not out:
                out = "Here are three gentle ideas you might try: take a few slow breaths, sip warm water, and rest your eyes briefly."
            
            # Add to conversation history
            self.history.append({"role": "assistant", "content": out})
            return out
            
        except Exception as e:
            print("LLM error:", e)
            self._last_error = f"LLM error: {e}"
            # Return safe, empathetic fallback message
            return "I'm here to listen and help you feel better."

    def status(self) -> dict:
        """
        Get current status of the LLM system.
        
        Useful for debugging and monitoring. Shows:
        - Which provider is being used
        - Which model is loaded
        - Whether model is ready to use
        - Last error (if any)
        
        Returns:
            dict: Status information
        """
        return {
            "provider": self.provider,  # "hf" or "openai"
            "model": self.model_name,   # Model identifier
            "ready": (self._openai_client is not None) if self.provider == "openai" 
                    else (self.model is not None and self.tokenizer is not None),
            "last_error": self._last_error,  # Last error message (if any)
        }

    def update_profile(self, profile: dict):
        """
        Update user profile for personalization.
        
        Profile can include:
        - name: User's name (LLM will address them by name)
        - preferences: Dict with settings like "tone"
        
        Args:
            profile (dict): User profile data
        """
        self.profile = profile or {}
        
        # Optional: Reset conversation when profile changes
        # Controlled by LLM_RESET_ON_PROFILE environment variable
        if os.getenv("LLM_RESET_ON_PROFILE", "false").lower() == "true":
            self.history = []
