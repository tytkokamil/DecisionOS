import os
import json

class AIService:
    def __init__(self):
        self._client = None
        # Model is intentionally configurable to avoid hard-coding.
        # Set OPENAI_MODEL in your environment (e.g., .env) to override.
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    
    @property
    def client(self):
        """Lazy load OpenAI client"""
        if self._client is None:
            try:
                from openai import OpenAI
                api_key = os.getenv('OPENAI_API_KEY', 'dummy-key')
                self._client = OpenAI(api_key=api_key)
            except Exception as e:
                print(f"OpenAI client initialization failed: {e}")
                self._client = None
        return self._client
    
    def analyze_decision(self, decision):
        """Analyze a decision and provide insights"""
        if not self.client:
            return {
                "insights": ["AI service not available - check OpenAI API key"],
                "risks": [],
                "recommendations": []
            }
        
        prompt = f"""
You are an expert business consultant helping to analyze decisions.

Decision Title: {decision.title}
Description: {decision.description}
Priority: {decision.get_priority_display()}

Provide a structured analysis with:
1. Key Insights (3-5 bullet points)
2. Potential Risks (3 risks with severity: low/medium/high)
3. Recommendations (3 actionable recommendations)

Return ONLY valid JSON.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful business analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"AI Analysis Error: {e}")
            return {
                "insights": ["Analysis temporarily unavailable"],
                "risks": [],
                "recommendations": []
            }
    
    def generate_alternatives(self, decision, count=3):
        """Generate alternative options"""
        if not self.client:
            return []
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative problem solver."},
                    {"role": "user", "content": f"Generate {count} alternatives for: {decision.title}"}
                ],
                temperature=0.8
            )
            return []
        except:
            return []
    
    def generate_summary(self, decision):
        """Generate executive summary"""
        if not self.client:
            return "AI summary not available - configure OpenAI API key"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional writer."},
                    {"role": "user", "content": f"Summarize: {decision.title} - {decision.description}"}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Summary generation failed: {str(e)}"

    def quality_check(self, decision):
        """Decision Quality Check.

        Returns a structured JSON-like dict:
        {
          "score": 0-100,
          "missing_information": [{"item": str, "why": str}],
          "questions": [str],
          "risks": [str],
          "suggested_improvements": [str]
        }

        Works even without OpenAI: falls back to deterministic heuristics.
        """

        # --- Heuristic baseline (works offline) ---
        missing = []
        questions = []
        risks = []
        improvements = []

        desc = (decision.description or '').strip()
        options_count = getattr(decision, 'options', None)
        try:
            options_count = decision.options.count()
        except Exception:
            options_count = 0

        # Basic completeness checks
        if len(desc) < 80:
            missing.append({
                "item": "Insufficient context / detail",
                "why": "The description is quite short; reviewers may not have enough context to assess impact and trade-offs."
            })
            questions.append("What is the concrete problem statement and desired outcome?")
            improvements.append("Expand the description with context, constraints, and a clear success criterion.")

        if options_count == 0:
            missing.append({
                "item": "Alternatives / options",
                "why": "No options were listed. Decisions are stronger when alternatives and trade-offs are explicit."
            })
            questions.append("Which alternatives were considered (at least 2), and why were they rejected?")
            improvements.append("Add 2–3 alternatives with pros/cons and a short rationale.")

        if not getattr(decision, 'assigned_to', None):
            missing.append({
                "item": "Responsible owner",
                "why": "There is no assignee/owner to drive the decision to completion."
            })
            questions.append("Who is responsible for implementing and tracking this decision?")
            improvements.append("Assign an owner so follow-up tasks and accountability are clear.")

        if not getattr(decision, 'due_date', None):
            missing.append({
                "item": "Deadline",
                "why": "No due date is set. Without a deadline, reviews and implementation often stall."
            })
            questions.append("By when does this decision need to be approved/implemented?")
            improvements.append("Set a realistic due date to prevent the decision from stalling.")

        if not (getattr(decision, 'tags', '') or '').strip():
            missing.append({
                "item": "Tags / classification",
                "why": "Tags help find decisions later (search, reporting, reuse)."
            })
            improvements.append("Add 1–3 tags to classify the decision (e.g., 'tech-stack', 'hiring', 'budget').")

        # Risk prompt (basic)
        if getattr(decision, 'priority', '') in ('high', 'critical'):
            risks.append("High priority decision: validate risks, costs, and rollback plan before implementation.")
            questions.append("What are the top 3 risks and a mitigation/rollback plan?")

        # Score: start at 100, subtract for each missing bucket
        score = 100
        score -= 15 if len(desc) < 80 else 0
        score -= 25 if options_count == 0 else 0
        score -= 10 if not getattr(decision, 'assigned_to', None) else 0
        score -= 5 if not getattr(decision, 'due_date', None) else 0
        score -= 5 if not (getattr(decision, 'tags', '') or '').strip() else 0
        score = max(0, min(100, score))

        baseline = {
            "score": score,
            "missing_information": missing,
            "questions": questions,
            "risks": risks,
            "suggested_improvements": improvements,
        }

        # --- If OpenAI is available, enrich the baseline ---
        if not self.client:
            return baseline

        prompt = {
            "role": "user",
            "content": (
                "You are a Decision Governance assistant. Evaluate the decision quality and completeness. "
                "Return ONLY valid JSON with keys: score (0-100), missing_information (list of {item, why}), "
                "questions (list), risks (list), suggested_improvements (list).\n\n"
                f"Decision Title: {decision.title}\n"
                f"Description: {decision.description}\n"
                f"Priority: {getattr(decision, 'priority', '')}\n"
                f"Status: {getattr(decision, 'status', '')}\n"
                f"Has owner: {'yes' if getattr(decision, 'assigned_to', None) else 'no'}\n"
                f"Due date: {getattr(decision, 'due_date', None) or 'none'}\n"
                f"Tags: {(getattr(decision, 'tags', '') or '').strip() or 'none'}\n"
                f"Options count: {options_count}\n\n"
                "Be concrete and actionable. If information is missing, ask targeted questions."
            ),
        }

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strict JSON-only assistant."},
                    prompt,
                ],
                temperature=0.2,
                response_format={"type": "json_object"},
            )
            enriched = json.loads(response.choices[0].message.content)

            # Merge: keep baseline as fallback, but prefer LLM items when present
            out = dict(baseline)
            for k in ("missing_information", "questions", "risks", "suggested_improvements"):
                if isinstance(enriched.get(k), list) and enriched.get(k):
                    out[k] = enriched[k]
            if isinstance(enriched.get("score"), (int, float)):
                out["score"] = max(0, min(100, int(enriched["score"])))
            return out
        except Exception as e:
            print(f"AI Quality Check Error: {e}")
            return baseline

ai_service = AIService()