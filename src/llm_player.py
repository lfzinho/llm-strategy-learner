import os
from pydantic import BaseModel, Field
from typing import Literal, Optional
from player import Player
from constants import Move
import instructor
from openai import OpenAI
from google import genai
from google.genai import types

from src.usage_tracker import UsageTracker

class LLMDecision(BaseModel):
    decision: Literal["COOPERATE", "DEFECT"]
    reasoning: str = Field(description="Brief reasoning for the decision")
    updated_long_lasting_notes: Optional[str] = Field(
        default=None, 
        description="Update these notes to remember broad strategies for all time. Keep them concise."
    )
    updated_short_lasting_notes: Optional[str] = Field(
        default=None,
        description="Update these notes to remember the current opponent's behavior in this match. Keep them concise."
    )

class LLMPlayer(Player):
    def __init__(self, name="LLM Agent", use_gemini=True, model_name="gemini-3.6-flash"):
        super().__init__(name)
        self.strategy_name = "LLM Learner"
        self.use_gemini = use_gemini
        self.model_name = model_name
        self.long_lasting_notes = "I am a rational agent playing the Prisoner's Dilemma. I want to maximize my total score."
        self.short_lasting_notes = ""
        self.freeze_notes = False
        self.consecutive_errors = 0
        
        if self.use_gemini:
            self.usage_tracker = UsageTracker(max_rpm=30, max_rpd=1000)
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("Warning: GEMINI_API_KEY not found in environment. Please set it before running.")
            
            self.client = genai.Client(api_key=api_key)
        else:
            base_client = OpenAI(
                base_url="http://localhost:11434/v1",
                api_key="ollama", 
            )
            self.client = instructor.from_openai(
                base_client,
                mode=instructor.Mode.JSON,
            )

    def play(self) -> Move:
        history_str = ""
        if not self.game_history:
            history_str = "This is the first round against this opponent."
        else:
            history_str = "Game History (My Move, Opponent's Move):\n"
            for i, (my_move, opp_move) in enumerate(self.game_history):
                my_m = "COOPERATE" if my_move == Move.COOPERATE else "DEFECT"
                opp_m = "COOPERATE" if opp_move == Move.COOPERATE else "DEFECT"
                history_str += f"Round {i+1}: I played {my_m}, Opponent played {opp_m}\n"
        
        system_prompt = f"""You are playing the Prisoner's Dilemma. Your goal is to maximize your total score.
If you both cooperate, you both get 3 points. If you both defect, you both get 1 point. 
If one cooperates and the other defects, the defector gets 5 points and the cooperator gets 0 points.

Long-lasting Notes (Persistent strategies across all games):
{self.long_lasting_notes}

Short-lasting Notes (About this specific opponent):
{self.short_lasting_notes}

{history_str}

Analyze the situation and decide whether to COOPERATE or DEFECT. 
You may also update your notes if you feel it's necessary. Keep notes concise and insightful.
If you don't want to update the notes, simply leave the fields empty.
"""
        
        consecutive_429s = 0
        while True:
            try:
                if self.use_gemini:
                    self.usage_tracker.wait_and_record()
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=system_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=LLMDecision,
                            temperature=0.2,
                        ),
                    )
                    decision_obj = response.parsed
                    # If parsed is None (maybe SDK version difference), parse the text
                    if decision_obj is None:
                        import json
                        decision_obj = LLMDecision.model_validate_json(response.text)
                else:
                    decision_obj = self.client.chat.completions.create(
                        model=self.model_name,
                        response_model=LLMDecision,
                        messages=[{"role": "user", "content": system_prompt}],
                        max_retries=3
                    )
                    
                decision = decision_obj.decision
                
                if not self.freeze_notes:
                    if decision_obj.updated_long_lasting_notes:
                        self.long_lasting_notes = decision_obj.updated_long_lasting_notes
                    if decision_obj.updated_short_lasting_notes:
                        self.short_lasting_notes = decision_obj.updated_short_lasting_notes
                
                consecutive_429s = 0
                return Move.COOPERATE if decision == "COOPERATE" else Move.DEFECT
                    
            except Exception as e:
                import time
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    consecutive_429s += 1
                    if consecutive_429s >= 3:
                        from src.usage_tracker import DailyLimitReachedException
                        print(f"\n[ABORT] Received {consecutive_429s} consecutive 429 Quota/Rate errors. Halting execution.")
                        raise DailyLimitReachedException("Aborted due to 3 consecutive 429 API errors.")
                        
                    print(f"API Rate Limit or Quota hit (429). The system will now sleep for 60 seconds before retrying... (Strike {consecutive_429s}/3)")
                    time.sleep(60)
                else:
                    print(f"Unhandled error during LLM call: {e}")
                    return Move.DEFECT

    def finish_game(self):
        # Call base class finish_game to clear game_history and aggregate scores
        super().finish_game()
        # Reset short lasting notes for the next opponent
        self.short_lasting_notes = ""

    def copy(self):
        # We need to correctly copy the player for the simulation reproduction step
        new_player = LLMPlayer(
            name=self.name, 
            use_gemini=self.use_gemini, 
            model_name=self.model_name
        )
        new_player.long_lasting_notes = self.long_lasting_notes
        new_player.freeze_notes = self.freeze_notes
        return new_player
