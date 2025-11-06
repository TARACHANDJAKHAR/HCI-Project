from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import os
import typing as t

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

class LLMResponder:
    def __init__(self, model_name="gpt2"):
        # Provider and model selection via env vars
        self.provider = os.getenv("LLM_PROVIDER", "hf").lower()  # "hf" or "openai"
        self.model_name = os.getenv("LLM_MODEL", model_name)

        # Conversation and personalization
        self.profile: dict = {}
        self.history: list[dict] = []  # [{role: 'user'|'assistant', content: str}]

        # HF state
        self.tokenizer = None
        self.model = None

        # OpenAI state
        self._openai_client = None
        self._last_error: str | None = None
        self.persona = (
            "You are a warm, gentle, and caring elderly companion. "
            "You comfort the user when they feel sad or lonely, speak simply, "
            "and always encourage positivity and calmness. "
            "ALWAYS answer directly and concisely in 1-3 sentences."
        )

    def _ensure_model_loaded(self):
        if self.provider == "openai":
            if self._openai_client is not None:
                return
            try:
                if OpenAI is None:
                    raise RuntimeError("openai package not installed")
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise RuntimeError("OPENAI_API_KEY not set")
                self._openai_client = OpenAI(api_key=api_key)
                print("OpenAI client initialized for model:", self.model_name)
                self._last_error = None
            except Exception as e:
                print("OpenAI init error:", e)
                self._openai_client = None
                self._last_error = f"OpenAI init error: {e}"
        else:
            if self.model is not None and self.tokenizer is not None:
                return
            try:
                print("Loading HF model:", self.model_name)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
                if self.tokenizer.pad_token is None:
                    self.tokenizer.pad_token = self.tokenizer.eos_token
                self._last_error = None
            except Exception as e:
                print("HF load error:", e)
                self.model = None
                self.tokenizer = None
                self._last_error = f"HF load error: {e}"

    def generate(self, text: str):
        self._ensure_model_loaded()
        try:
            # Track user message and keep a short history (last 4 turns)
            self.history.append({"role": "user", "content": text})
            self.history = self.history[-8:]

            # Build system prompt with personalization and brief instructions
            name = self.profile.get("name")
            prefs = self.profile.get("preferences") or {}
            persona = self.persona
            if name:
                persona += f" The user's name is {name}. Address them by name occasionally."
            if prefs.get("tone"):
                persona += f" Use a {prefs['tone']} tone."

            if self.provider == "openai" and self._openai_client is not None:
                messages = [{"role": "system", "content": persona}]
                for m in self.history[-6:]:
                    messages.append({"role": m["role"], "content": m["content"]})
                try:
                    resp = self._openai_client.chat.completions.create(
                        model=self.model_name,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=220,
                    )
                    content = resp.choices[0].message.content or ""
                    self._last_error = None
                    reply = content.strip()
                    self.history.append({"role": "assistant", "content": reply})
                    return reply
                except Exception as e:
                    print("OpenAI generate error:", e)
                    self._last_error = f"OpenAI generate error: {e}"
                    # Optional HF fallback if configured
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
                    return "I'm here to listen and help you feel better."
            # Default to HF
            if self.model is None or self.tokenizer is None:
                return "I'm here with you. Let's take a deep breath together."
            # Use a concise recent context and a single Assistant cue
            recent_pairs = self.history[-8:]
            recent = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in recent_pairs])
            prompt = f"{persona}\n{recent}\nAssistant:"
            inputs = self.tokenizer(prompt, return_tensors="pt", padding=True)
            outputs = self.model.generate(
                **inputs,
                max_length=220,
                temperature=0.3,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                repetition_penalty=1.15,
            )
            reply = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            self._last_error = None
            out = reply.split("Assistant:")[-1]
            for stopper in ["\nUser:", "\nSystem:", "\nAssistant:"]:
                if stopper in out:
                    out = out.split(stopper)[0]
            out = out.strip()
            if not out:
                out = "Here are three gentle ideas you might try: take a few slow breaths, sip warm water, and rest your eyes briefly."
            self.history.append({"role": "assistant", "content": out})
            return out
        except Exception as e:
            print("LLM error:", e)
            self._last_error = f"LLM error: {e}"
            return "I'm here to listen and help you feel better."

    def status(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model_name,
            "ready": (self._openai_client is not None) if self.provider == "openai" else (self.model is not None and self.tokenizer is not None),
            "last_error": self._last_error,
        }

    def update_profile(self, profile: dict):
        self.profile = profile or {}
        # Reset conversation if desired when profile changes
        if os.getenv("LLM_RESET_ON_PROFILE", "false").lower() == "true":
            self.history = []
