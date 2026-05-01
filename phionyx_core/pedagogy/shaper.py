"""
Shaper - Empowerment Language Rewriting (Vygotsky Protocol)
==========================================================

Rewrites LLM responses according to pedagogical principles:
1. No Spoon-feeding: Scaffolding approach ("What do *you* think?")
2. Praise Effort, Not Intelligence: "You worked hard" vs "You are smart"
3. Reframe Failure: "Not Yet" instead of "No" (especially when entropy is high)

Based on:
- Carol Dweck's Growth Mindset
- Vygotsky's Zone of Proximal Development (Scaffolding)
"""

import logging
import re
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class LanguageShaper:
    """
    Rewrites text according to Vygotsky Protocol (Growth Mindset + Scaffolding).

    Rules:
    1. No Spoon-feeding: Scaffold questions instead of giving answers
    2. Praise Effort, Not Intelligence: Focus on process, not ability
    3. Reframe Failure: "Not Yet" instead of "No" (especially when entropy is high)
    """

    def __init__(
        self,
        use_llm_reframing: bool = True,
        llm_completion_fn: Callable[..., Any] | None = None,
    ):
        """
        Initialize with transformation rules.

        Args:
            use_llm_reframing: If True, use LLM for advanced reframing (recommended)
            llm_completion_fn: Optional synchronous LLM completion callable.
                               Injected from bridge layer (port-adapter pattern).
                               If not provided, LLM-based reframing is disabled
                               and regex-based fallback is used.
        """
        self.use_llm_reframing = use_llm_reframing
        self.llm_available = False
        self._llm_completion_fn: Callable[..., Any] | None = None
        self._init_llm(llm_completion_fn)

        # Fixed mindset → Growth mindset transformations (regex-based fallback)
        self.transformations = [
            # Defeatist → Empowering
            (r'\b(yapamam|başaramam|imkansız|mümkün değil)\b', 'zorlayıcı ama öğrenme fırsatı'),
            (r'\b(can\'t|impossible|can\'t\s+do|unable)\b', 'challenging but a learning opportunity'),

            # Negative self-talk → Constructive
            (r'\b(başarısızım|yetersizim|beceriksizim)\b', 'henüz öğreniyorum'),
            (r'\b(I\'m\s+a\s+failure|I\'m\s+incompetent|I\'m\s+not\s+good)\b', 'I\'m still learning'),

            # Permanent → Temporary
            (r'\b(her zaman|hiçbir zaman|asla|sürekli)\b', 'şu anda'),
            (r'\b(always|never|forever|constantly)\b', 'right now'),

            # Blame → Responsibility
            (r'\b(suçlu|hata\s+onun|onlar\s+yüzünden)\b', 'sorumluluk alarak'),
            (r'\b(their\s+fault|blame\s+them|because\s+of\s+them)\b', 'taking responsibility'),

            # Comparison → Self-improvement
            (r'\b(daha\s+iyi|daha\s+kötü|diğerlerinden)\b', 'kendi gelişimine odaklanarak'),
            (r'\b(better\s+than|worse\s+than|compared\s+to)\b', 'focusing on your own growth'),
        ]

        # Compile regex patterns
        self.compiled_patterns = [(re.compile(pattern, re.IGNORECASE), replacement)
                                   for pattern, replacement in self.transformations]

        # Spoon-feeding detection patterns (questions asking for direct answers)
        self.spoon_feeding_patterns = [
            r'\b(what\s+is\s+the\s+answer|what\'s\s+the\s+answer|tell\s+me\s+the\s+answer)\b',
            r'\b(cevap\s+nedir|cevabı\s+söyle|ne\s+yapmalıyım)\b',
            r'\b(how\s+do\s+I\s+solve\s+this|how\s+to\s+fix|what\s+should\s+I\s+do)\b',
        ]
        self.spoon_feeding_regex = [re.compile(p, re.IGNORECASE) for p in self.spoon_feeding_patterns]

        # Intelligence praise patterns (to replace with effort praise)
        self.intelligence_praise_patterns = [
            r'\b(you\s+are\s+smart|you\'re\s+smart|you\s+are\s+clever|you\'re\s+clever)\b',
            r'\b(you\s+are\s+intelligent|you\'re\s+intelligent|you\s+are\s+brilliant)\b',
            r'\b(sen\s+akıllısın|sen\s+zekisin|sen\s+çok\s+akıllısın)\b',
        ]
        self.intelligence_praise_regex = [re.compile(p, re.IGNORECASE) for p in self.intelligence_praise_patterns]

        # Failure language patterns (to reframe as "Not Yet")
        self.failure_patterns = [
            r'\b(no|wrong|incorrect|failed|failure|you\s+can\'t)\b',
            r'\b(hayır|yanlış|başarısız|yapamazsın|olmaz)\b',
        ]
        self.failure_regex = [re.compile(p, re.IGNORECASE) for p in self.failure_patterns]

        # Empowerment phrases to inject
        self.empowerment_phrases = [
            "Her zorluk bir öğrenme fırsatıdır.",
            "Yapabileceğin şeylerin sınırı yok.",
            "Hata yapmak öğrenmenin bir parçasıdır.",
            "Her adım seni daha güçlü yapar.",
            "Challenges are opportunities to grow.",
            "Mistakes help us learn and improve.",
            "Every step forward is progress.",
        ]

    def _init_llm(self, llm_completion_fn: Callable[..., Any] | None = None):
        """Initialize LLM for advanced reframing via injected callable (Core boundary: no direct litellm import)."""
        if not self.use_llm_reframing:
            return

        if llm_completion_fn is not None:
            self._llm_completion_fn = llm_completion_fn
            self.llm_available = True
            logger.info("LanguageShaper: LLM completion function injected for advanced reframing")
        else:
            logger.info(
                "LanguageShaper: No LLM completion function injected. "
                "Using regex-based reframing only. Inject via llm_completion_fn parameter."
            )
            self.llm_available = False

    def reshape(self, text: str, physics_state: dict | None = None, context: str | None = None) -> str:
        """
        Reshape text according to Vygotsky Protocol (Growth Mindset + Scaffolding).

        Args:
            text: Original LLM draft response
            physics_state: Optional physics state (for context-aware reshaping)
            context: Optional context (user input, scene context, etc.)

        Returns:
            Reshaped text with empowering, growth-oriented language
        """
        if not text or not text.strip():
            return text

        # Use LLM reframing if available (recommended for best results)
        if self.use_llm_reframing and self.llm_available:
            try:
                return self.reframe_response(text, physics_state, context)
            except Exception as e:
                logger.warning(f"LanguageShaper: LLM reframing failed: {e}, falling back to regex")

        # Fallback: Regex-based reshaping
        reshaped = text

        # Rule 1: No Spoon-feeding - Detect and reframe direct answer requests
        reshaped = self._apply_scaffolding(reshaped, context)

        # Rule 2: Praise Effort, Not Intelligence
        reshaped = self._replace_intelligence_praise(reshaped)

        # Rule 3: Reframe Failure (especially when entropy is high)
        reshaped = self._reframe_failure(reshaped, physics_state)

        # Apply general transformations
        for pattern, replacement in self.compiled_patterns:
            reshaped = pattern.sub(replacement, reshaped)

        # Add encouragement if struggling
        if physics_state:
            phi = physics_state.get("phi", 1.0)
            entropy = physics_state.get("entropy", 0.5)

            if phi < 0.4 or entropy > 0.7:
                encouragement = self._get_encouragement(phi, entropy)
                if encouragement and encouragement.lower() not in reshaped.lower():
                    reshaped = f"{reshaped}\n\n{encouragement}"

        logger.info(f"LanguageShaper: Reshaped text (original: {len(text)} chars, reshaped: {len(reshaped)} chars)")
        return reshaped

    def reframe_response(
        self,
        draft_text: str,
        physics_state: dict | None = None,
        context: str | None = None
    ) -> str:
        """
        Advanced reframing using LLM (Vygotsky Protocol).

        Makes a quick LLM pass to polish the tone according to:
        1. No Spoon-feeding (Scaffolding)
        2. Praise Effort, Not Intelligence
        3. Reframe Failure ("Not Yet" instead of "No")

        Args:
            draft_text: Original LLM draft response
            physics_state: Current physics state
            context: User input or scene context

        Returns:
            Reframed response following Vygotsky Protocol
        """
        if not self.llm_available or self._llm_completion_fn is None:
            # Fallback to regex-based reshaping
            return self.reshape(draft_text, physics_state, context)

        try:
            # Build system prompt with Vygotsky Protocol rules
            system_prompt = self._build_vygotsky_prompt(physics_state)

            # Build user prompt
            user_prompt = f"""Reframe this response according to pedagogical principles:

ORIGINAL RESPONSE:
{draft_text}

"""
            if context:
                user_prompt += f"CONTEXT: {context}\n\n"

            user_prompt += """RULES:
1. No Spoon-feeding: If the response gives a direct answer, reframe it as a scaffolding question (e.g., "What do *you* think the first step is?" instead of "The answer is X").
2. Praise Effort, Not Intelligence: Replace "You are smart" with "You worked hard to solve that."
3. Reframe Failure: Replace "No" or "Wrong" with "Not Yet" - frame failures as learning steps.

Return ONLY the reframed response, no explanations."""

            # Delegate to injected LLM completion function (bridge provides model/config)
            response = self._llm_completion_fn(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent reframing
                max_tokens=400,   # Keep it concise
            )

            reframed = response.choices[0].message.content.strip()
            logger.info(f"LanguageShaper: LLM reframed response ({len(draft_text)} -> {len(reframed)} chars)")
            return reframed

        except Exception as e:
            logger.error(f"LanguageShaper: LLM reframing failed: {e}")
            # Fallback to regex-based reshaping
            return self.reshape(draft_text, physics_state, context)

    def _build_vygotsky_prompt(self, physics_state: dict | None) -> str:
        """Build system prompt for Vygotsky Protocol reframing."""
        prompt = """You are a pedagogical AI assistant following the Vygotsky Protocol.

CORE PRINCIPLES:
1. NO SPOON-FEEDING (Scaffolding):
   - Never give direct answers to questions like "What is the answer?"
   - Instead, ask: "What do *you* think the first step is?"
   - Guide through questions, not answers.

2. PRAISE EFFORT, NOT INTELLIGENCE:
   - WRONG: "You are smart."
   - RIGHT: "You worked hard to solve that puzzle."
   - Focus on process, not ability.

3. REFRAME FAILURE:
   - Replace "No" or "Wrong" with "Not Yet"
   - Frame failures as learning steps, not endpoints.
   - Especially important when user is stressed (high entropy).

"""
        if physics_state:
            entropy = physics_state.get("entropy", 0.5)
            phi = physics_state.get("phi", 1.0)

            if entropy > 0.7:
                prompt += f"CONTEXT: User is currently stressed (entropy: {entropy:.2f}). Be extra gentle and use 'Not Yet' language.\n"
            if phi < 0.4:
                prompt += f"CONTEXT: User is struggling (phi: {phi:.2f}). Emphasize growth and learning steps.\n"

        prompt += "\nReframe the response to follow these principles while maintaining the original meaning and tone."
        return prompt

    def _apply_scaffolding(self, text: str, context: str | None = None) -> str:
        """
        Rule 1: No Spoon-feeding - Apply scaffolding approach.

        Detects direct answer patterns and reframes as questions.
        """
        # Check if response contains direct answers to "what is the answer" type questions
        if context:
            for pattern in self.spoon_feeding_regex:
                if pattern.search(context.lower()):
                    # User asked for direct answer - reframe response to scaffold
                    # Look for direct answer patterns in response
                    direct_answer_patterns = [
                        r'\b(the\s+answer\s+is|the\s+solution\s+is|you\s+should|do\s+this)\b',
                        r'\b(cevap|çözüm|yapmalısın|şöyle\s+yap)\b',
                    ]

                    for answer_pattern in direct_answer_patterns:
                        compiled = re.compile(answer_pattern, re.IGNORECASE)
                        if compiled.search(text.lower()):
                            # Reframe as scaffolding question
                            text = re.sub(
                                r'\b(the\s+answer\s+is|the\s+solution\s+is)\b',
                                'What do *you* think the first step is?',
                                text,
                                flags=re.IGNORECASE
                            )
                            text = re.sub(
                                r'\b(you\s+should|do\s+this)\b',
                                'What if you tried',
                                text,
                                flags=re.IGNORECASE
                            )
                            logger.info("LanguageShaper: Applied scaffolding (no spoon-feeding)")
                            break

        return text

    def _replace_intelligence_praise(self, text: str) -> str:
        """
        Rule 2: Praise Effort, Not Intelligence.

        Replaces "You are smart" with "You worked hard".
        """
        replacements = [
            (r'\byou\s+are\s+smart\b', 'you worked hard'),
            (r'\byou\'re\s+smart\b', 'you worked hard'),
            (r'\byou\s+are\s+clever\b', 'you put in effort'),
            (r'\byou\s+are\s+intelligent\b', 'you practiced well'),
            (r'\byou\s+are\s+brilliant\b', 'you persevered'),
            (r'\bsen\s+akıllısın\b', 'çok çalıştın'),
            (r'\bsen\s+zekisin\b', 'emek verdin'),
        ]

        for pattern, replacement in replacements:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                logger.info("LanguageShaper: Replaced intelligence praise with effort praise")
                break

        return text

    def _reframe_failure(self, text: str, physics_state: dict | None = None) -> str:
        """
        Rule 3: Reframe Failure - "Not Yet" instead of "No".

        Especially important when entropy is high (user is stressed).
        """
        entropy = physics_state.get("entropy", 0.5) if physics_state else 0.5

        # Failure language replacements
        failure_replacements = [
            (r'\bno\b(?!\s+worries|\s+problem)', 'not yet'),  # "no" but not "no worries"
            (r'\bwrong\b', 'not quite there yet'),
            (r'\bincorrect\b', 'not yet, but you\'re learning'),
            (r'\bfailed\b', 'haven\'t succeeded yet'),
            (r'\bfailure\b', 'learning step'),
            (r'\byou\s+can\'t\b', 'you haven\'t been able to yet'),
            (r'\bhayır\b', 'henüz değil'),
            (r'\byanlış\b', 'henüz doğru değil'),
            (r'\bbaşarısız\b', 'henüz başaramadın'),
        ]

        # Apply replacements (more aggressive if entropy is high)
        for pattern, replacement in failure_replacements:
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                if entropy > 0.7:
                    # High entropy - add extra encouragement
                    if 'not yet' in text.lower() or 'henüz' in text.lower():
                        text += " Keep trying - every attempt teaches you something."
                logger.info(f"LanguageShaper: Reframed failure language (entropy: {entropy:.2f})")
                break

        return text

    def _get_encouragement(self, phi: float, entropy: float) -> str | None:
        """Get appropriate encouragement based on physics state."""
        if phi < 0.3:
            return "Zor bir an yaşıyorsun, ama bu geçecek. Her zorluk seni daha güçlü yapar."
        elif entropy > 0.7:
            return "Şu anda belirsizlik hissediyorsun, bu normal. Adım adım ilerleyebilirsin."
        elif phi < 0.5:
            return "Küçük adımlar büyük değişiklikler yaratır. Devam et."
        return None

    def inject_growth_mindset(self, text: str) -> str:
        """
        Explicitly inject growth mindset phrases.

        Args:
            text: Original text

        Returns:
            Text with growth mindset phrases added
        """
        if not text:
            return text

        # Check if text already contains growth mindset language
        has_growth_mindset = any(phrase.lower() in text.lower() for phrase in self.empowerment_phrases)

        if not has_growth_mindset:
            # Add a deterministic growth mindset phrase based on input text
            phrase_index = hash(text) % len(self.empowerment_phrases)
            phrase = self.empowerment_phrases[phrase_index]
            return f"{text}\n\n{phrase}"

        return text

