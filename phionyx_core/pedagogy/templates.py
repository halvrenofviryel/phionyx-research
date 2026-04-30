"""
Templates - Safe Fallback Responses (Clinical Protocols)
=========================================================

Provides a library of hardcoded, clinically approved responses for:
- High-risk states (Panic Attack, Total Apathy)
- Risk detection fallbacks
- LLM generation failures

These templates BYPASS the LLM when physics state hits extremes.
"""

from typing import Literal


class TemplateLibrary:
    """
    Library of safe, clinically approved response templates.

    Includes hardcoded responses for extreme physics states that require
    immediate intervention without LLM generation.
    """

    def __init__(self, language: Literal["en", "tr"] = "en"):
        """
        Initialize template library.

        Args:
            language: Language code ("en" for English, "tr" for Turkish)
        """
        self.language = language
        self.templates = self._load_templates()
        self.extreme_state_templates = self._load_extreme_state_templates()

    def _load_templates(self) -> dict[str, dict[str, str]]:
        """Load templates for different risk levels and scenarios."""
        return {
            "en": {
                "critical_self_harm": "It sounds like you're going through a very difficult time. Please reach out for help immediately. You can contact a crisis hotline or a trusted adult. You are not alone.",
                "high_toxicity": "I understand you're feeling strong emotions. Let's try to express them in a way that is constructive and respectful.",
                "medium_inappropriate": "That's a complex situation. Let's focus on the core challenge and how we can approach it constructively.",
                "low_general_concern": "I hear you. It's okay to feel this way. What's one small step you can take?",
                "default_safe": "I'm here to listen. What's on your mind?",
            },
            "tr": {
                "critical_self_harm": "Çok zor bir dönemden geçiyor gibisin. Lütfen hemen yardım al. Bir kriz hattına veya güvendiğin bir yetişkine ulaşabilirsin. Yalnız değilsin.",
                "high_toxicity": "Güçlü duygular hissettiğini anlıyorum. Bunları yapıcı ve saygılı bir şekilde ifade etmeye çalışalım.",
                "medium_inappropriate": "Bu karmaşık bir durum. Temel zorluğa ve ona nasıl yapıcı bir şekilde yaklaşabileceğimize odaklanalım.",
                "low_general_concern": "Seni duyuyorum. Böyle hissetmen normal. Atabileceğin küçük bir adım var mı?",
                "default_safe": "Dinlemek için buradayım. Aklında ne var?",
            }
        }

    def _load_extreme_state_templates(self) -> dict[str, dict[str, dict[str, str]]]:
        """
        Load hardcoded templates for extreme physics states.

        These templates BYPASS LLM generation and are returned directly.
        """
        return {
            "en": {
                "panic_attack": {
                    "template": "Everything is moving too fast. Let's pause. Look at the screen. Breathe with me. In... Out... In... Out...",
                    "ui_trigger": "breathing_animation",  # Frontend should show breathing animation
                    "condition": "entropy > 0.9"
                },
                "total_apathy": {
                    "template": "It feels like nothing matters right now. That's okay. Just make one small choice. Pick a card, any card.",
                    "ui_trigger": "minimal_choice",  # Frontend should simplify UI to just card selection
                    "condition": "phi < 0.1"
                },
                "high_stress": {
                    "template": "You're feeling a lot of pressure right now. That's understandable. Take a moment. What's one thing you can control right now?",
                    "ui_trigger": None,
                    "condition": "entropy > 0.8"
                },
                "low_energy": {
                    "template": "You seem drained. That's okay. Rest is important. When you're ready, we can continue. No rush.",
                    "ui_trigger": None,
                    "condition": "phi < 0.2"
                }
            },
            "tr": {
                "panic_attack": {
                    "template": "Her şey çok hızlı ilerliyor. Dur. Ekrana bak. Benimle nefes al. İçeri... Dışarı... İçeri... Dışarı...",
                    "ui_trigger": "breathing_animation",
                    "condition": "entropy > 0.9"
                },
                "total_apathy": {
                    "template": "Şu anda hiçbir şeyin önemli olmadığını hissediyorsun. Bu normal. Sadece küçük bir seçim yap. Bir kart seç, herhangi bir kart.",
                    "ui_trigger": "minimal_choice",
                    "condition": "phi < 0.1"
                },
                "high_stress": {
                    "template": "Şu anda çok fazla baskı hissediyorsun. Bu anlaşılabilir. Bir an dur. Şu anda kontrol edebileceğin bir şey var mı?",
                    "ui_trigger": None,
                    "condition": "entropy > 0.8"
                },
                "low_energy": {
                    "template": "Yorgun görünüyorsun. Bu normal. Dinlenmek önemli. Hazır olduğunda devam edebiliriz. Acele etme.",
                    "ui_trigger": None,
                    "condition": "phi < 0.2"
                }
            }
        }

    def get_extreme_state_template(
        self,
        physics_state: dict,
        language: str | None = None
    ) -> dict[str, str] | None:
        """
        Get hardcoded template for extreme physics states.

        These templates BYPASS LLM generation and should be returned directly.

        Args:
            physics_state: Current physics state (must include 'phi' and 'entropy')
            language: Optional language override

        Returns:
            Dictionary with:
                - template: The response text
                - ui_trigger: UI animation/action to trigger (e.g., "breathing_animation")
                - condition: The condition that triggered this template
            Returns None if no extreme state detected.
        """
        lang = language or self.language
        extreme_templates = self.extreme_state_templates.get(lang, self.extreme_state_templates["en"])

        phi = physics_state.get("phi", 1.0)
        entropy = physics_state.get("entropy", 0.0)

        # Priority 1: Panic Attack (Entropy > 0.9)
        if entropy > 0.9:
            template_data = extreme_templates.get("panic_attack")
            if template_data:
                return {
                    "template": template_data["template"],
                    "ui_trigger": template_data.get("ui_trigger"),
                    "condition": f"entropy={entropy:.2f} > 0.9",
                    "bypass_llm": True
                }

        # Priority 2: Total Apathy (Phi < 0.1)
        if phi < 0.1:
            template_data = extreme_templates.get("total_apathy")
            if template_data:
                return {
                    "template": template_data["template"],
                    "ui_trigger": template_data.get("ui_trigger"),
                    "condition": f"phi={phi:.2f} < 0.1",
                    "bypass_llm": True
                }

        # Priority 3: High Stress (Entropy > 0.8)
        if entropy > 0.8:
            template_data = extreme_templates.get("high_stress")
            if template_data:
                return {
                    "template": template_data["template"],
                    "ui_trigger": template_data.get("ui_trigger"),
                    "condition": f"entropy={entropy:.2f} > 0.8",
                    "bypass_llm": False  # Can still use LLM, but this is a safe fallback
                }

        # Priority 4: Low Energy (Phi < 0.2)
        if phi < 0.2:
            template_data = extreme_templates.get("low_energy")
            if template_data:
                return {
                    "template": template_data["template"],
                    "ui_trigger": template_data.get("ui_trigger"),
                    "condition": f"phi={phi:.2f} < 0.2",
                    "bypass_llm": False  # Can still use LLM, but this is a safe fallback
                }

        return None

    def get_template(self, risk_type: str, language: str | None = None, physics_state: dict | None = None) -> str:
        """
        Get template for a specific risk type.

        Args:
            risk_type: Type of risk (e.g., "self_harm", "toxicity")
            language: Optional language override
            physics_state: Optional physics state for context-aware templates

        Returns:
            Safe template response
        """
        lang = language or self.language
        templates = self.templates.get(lang, self.templates["en"])

        # Map risk types to template keys
        risk_template_map = {
            "self_harm": "critical_self_harm",
            "violence": "critical_self_harm",
            "grooming": "critical_self_harm",
            "toxicity": "high_toxicity",
            "bullying": "high_toxicity",
            "inappropriate": "medium_inappropriate",
        }

        template_key = risk_template_map.get(risk_type, "default_safe")
        return templates.get(template_key, templates["default_safe"])

    def get_fallback(self, language: str | None = None) -> str:
        """
        Get default safe fallback template.

        Args:
            language: Optional language override

        Returns:
            Default safe template
        """
        lang = language or self.language
        templates = self.templates.get(lang, self.templates["en"])
        return templates.get("default_safe", "I'm here to listen. What's on your mind?")
