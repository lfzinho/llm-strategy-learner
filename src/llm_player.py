import os
import warnings
from pydantic import BaseModel, Field
from typing import Literal, Optional
from player import Player
from constants import Move
import instructor
from openai import OpenAI

# Suppress benign Google GenAI SDK warning regarding automatic function calling (AFC)
warnings.filterwarnings("ignore", message=".*automatic function calling.*")

from src.usage_tracker import UsageTracker
from src.match_logger import global_logger

class LLMDecision(BaseModel):
    decision: Literal["COOPERATE", "DEFECT"]
    reasoning: str = Field(description="Brief reasoning for the decision")
    new_short_term_memory: Optional[str] = Field(
        default=None,
        description="Optional: A new short-term observation/insight to remember about this current opponent in this match. Keep it concise."
    )

class LLMLongTermReflection(BaseModel):
    reasoning: str = Field(description="Reflection on the match and opponent archetype")
    new_long_term_memory: Optional[str] = Field(
        default=None,
        description="Optional: A new long-term insight/strategy to remember across all future games. Keep it concise."
    )

class LLMPlayer(Player):
    def __init__(self, name="LLM Agent", provider="gemini", model_name=None, use_gemini=None):
        super().__init__(name)
        self.strategy_name = "LLM Learner"

        # Backwards-compatibility for use_gemini boolean
        if use_gemini is not None:
            self.provider = "gemini" if use_gemini else "ollama"
        else:
            self.provider = (provider or "gemini").lower()

        if self.provider == "openrouter":
            self.model_name = model_name or os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        elif self.provider == "gemini":
            self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        else: # ollama
            self.model_name = model_name or os.getenv("OLLAMA_MODEL", "llama3")

        self.use_gemini = (self.provider == "gemini")
        self.long_lasting_notes: list[str] = [
            "I am a rational agent playing the Prisoner's Dilemma. I want to maximize my total score."
        ]
        self.short_lasting_notes: list[str] = []
        self.freeze_notes = False
        self.consecutive_errors = 0
        
        if self.provider == "gemini":
            from google import genai
            self.usage_tracker = UsageTracker(max_rpm=30, max_rpd=1000)
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("Warning: GEMINI_API_KEY not found in environment. Please set it before running.")
            
            self.client = genai.Client(api_key=api_key)
        elif self.provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPEN_ROUTER_KEY")
            if not api_key:
                print("Warning: OPENROUTER_API_KEY not found in environment. Please set it before running.")
            base_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key or "missing_key",
                default_headers={
                    "HTTP-Referer": "https://github.com/lfzinho/llm-strategy-learner",
                    "X-Title": "LLM Strategy Learner",
                }
            )
            self.client = instructor.from_openai(
                base_client,
                mode=instructor.Mode.JSON,
            )
        else: # ollama
            ollama_url = os.getenv("OLLAMA_HOST", "http://localhost:11434/v1")
            if not ollama_url.endswith("/v1"):
                ollama_url = ollama_url.rstrip("/") + "/v1"
            base_client = OpenAI(
                base_url=ollama_url,
                api_key="ollama", 
            )
            self.client = instructor.from_openai(
                base_client,
                mode=instructor.Mode.JSON,
            )

    def _format_notes(self, notes: list[str]) -> str:
        if not notes:
            return "- (None)"
        return "\n".join(f"- {note}" for note in notes)

    def _format_history_entry(self, entry: tuple, round_idx: int) -> str:
        # entry can be (my_executed, opp_executed, my_error, opp_error, my_intended) or (my_move, opp_move)
        if len(entry) >= 5:
            my_executed, opp_executed, my_error, _, my_intended = entry
            my_exec_str = "COOPERATE" if my_executed == Move.COOPERATE else "DEFECT"
            opp_exec_str = "COOPERATE" if opp_executed == Move.COOPERATE else "DEFECT"
            my_int_str = "COOPERATE" if my_intended == Move.COOPERATE else "DEFECT"
            if my_error:
                status_str = f"[TRANSMISSION ERROR: You intended {my_int_str}, but system executed {my_exec_str}]"
            else:
                status_str = "[Sent Successfully]"
            return f"Round {round_idx}: You intended {my_int_str} -> {status_str} | Executed: You played {my_exec_str}, Opponent played {opp_exec_str}"
        else:
            my_move, opp_move = entry[0], entry[1]
            my_m = "COOPERATE" if my_move == Move.COOPERATE else "DEFECT"
            opp_m = "COOPERATE" if opp_move == Move.COOPERATE else "DEFECT"
            return f"Round {round_idx}: You played {my_m}, Opponent played {opp_m}"

    def play(self) -> Move:
        history_str = ""
        if not self.game_history:
            history_str = "This is the first round against this opponent."
        else:
            history_str = "Game History (Rounds played so far):\n"
            for i, entry in enumerate(self.game_history):
                history_str += self._format_history_entry(entry, i + 1) + "\n"
        
        long_notes_formatted = self._format_notes(self.long_lasting_notes)
        short_notes_formatted = self._format_notes(self.short_lasting_notes)

        system_prompt = f"""You are playing the Iterated Prisoner's Dilemma. Your goal is to maximize your total score.
Scoring:
- If you both cooperate, you both get 3 points.
- If you both defect, you both get 1 point. 
- If one cooperates and the other defects, the defector gets 5 points and the cooperator gets 0 points.

This is a noisy environment: 
- When you or your opponent submit a move, there is a 5% chance the system flips it (COOPERATE becomes DEFECT, or DEFECT becomes COOPERATE).
- In the history below, you will see whether your intended move was sent successfully or altered erroneously by the environment.
- Keep in mind that unexpected moves by the opponent may also be due to accidental environmental noise rather than malice.

History of Moves:
{history_str}

Long-lasting Notes (Persistent strategies across all games):
{long_notes_formatted}

Short-lasting Notes (About this specific opponent in this match):
{short_notes_formatted}

Analyze the situation and decide whether to COOPERATE or DEFECT. 
Optionally, provide a new short-term memory entry if you have a new observation about this opponent. If no new insight is needed, leave it empty.
"""
        
        consecutive_429s = 0
        while True:
            try:
                if self.use_gemini:
                    from google.genai import types
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
                
                # Real-time Terminal UI Feedback (Rich / Lip Gloss style) & Markdown/HTML logging
                round_num = len(self.game_history) + 1
                try:
                    global_logger.log_turn(
                        player_name=self.name,
                        model_name=self.model_name,
                        provider=self.provider,
                        round_num=round_num,
                        decision=decision,
                        reasoning=decision_obj.reasoning,
                        new_short_memory=decision_obj.new_short_term_memory
                    )
                except Exception:
                    pass

                try:
                    from rich.console import Console
                    from rich.panel import Panel
                    from rich.table import Table
                    console = Console()
                    
                    move_style = "[bold green]COOPERATE 🤝[/bold green]" if decision == "COOPERATE" else "[bold red]DEFECT ⚔️[/bold red]"
                    
                    table = Table(show_header=False, box=None, padding=(0, 1))
                    table.add_row("[bold cyan]Model:[/bold cyan]", f"[dim]{self.model_name}[/dim] ([italic]{self.provider}[/italic])")
                    table.add_row("[bold cyan]Round:[/bold cyan]", f"#{round_num}")
                    table.add_row("[bold cyan]Decision:[/bold cyan]", move_style)
                    table.add_row("[bold cyan]Reasoning:[/bold cyan]", f"[yellow]{decision_obj.reasoning}[/yellow]")
                    if decision_obj.new_short_term_memory:
                        table.add_row("[bold magenta]+ Short Memory:[/bold magenta]", f"[italic]{decision_obj.new_short_term_memory}[/italic]")
                    
                    console.print(Panel(table, title=f"[bold blue]🤖 {self.name} Turn (Round {round_num})[/bold blue]", border_style="bright_blue", expand=False))
                except Exception:
                    print(f"[{self.name}] Round {round_num} -> {decision} | Reasoning: {decision_obj.reasoning}")
                
                if not self.freeze_notes:
                    if decision_obj.new_short_term_memory and decision_obj.new_short_term_memory.strip():
                        self.short_lasting_notes.append(decision_obj.new_short_term_memory.strip())
                
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

    def reflect_on_match(self):
        """Reflect after a match (game) ends to optionally add a new long-term memory."""
        if self.freeze_notes or not self.game_history:
            return

        history_str = "Match History (Rounds played in this match):\n"
        for i, entry in enumerate(self.game_history):
            history_str += self._format_history_entry(entry, i + 1) + "\n"

        long_notes_formatted = self._format_notes(self.long_lasting_notes)
        short_notes_formatted = self._format_notes(self.short_lasting_notes)

        prompt = f"""You just finished a match of Prisoner's Dilemma with a score of {self.score}.
Note: The game operates in a noisy environment with a 5% random move-flip error rate for both players.

Long-lasting Notes (Persistent strategies across all games):
{long_notes_formatted}

Short-lasting Notes from this match:
{short_notes_formatted}

{history_str}

Reflect on how this match went and what strategy/archetype the opponent used (accounting for possible random error flips).
Optionally, provide a new long-term memory entry if you have a broad strategic lesson or archetype insight to remember for all future games. If no new long-term insight is needed, leave it empty.
"""
        consecutive_429s = 0
        while True:
            try:
                if self.use_gemini:
                    from google.genai import types
                    self.usage_tracker.wait_and_record()
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=LLMLongTermReflection,
                            temperature=0.2,
                        ),
                    )
                    reflection_obj = response.parsed
                    if reflection_obj is None:
                        import json
                        reflection_obj = LLMLongTermReflection.model_validate_json(response.text)
                else:
                    reflection_obj = self.client.chat.completions.create(
                        model=self.model_name,
                        response_model=LLMLongTermReflection,
                        messages=[{"role": "user", "content": prompt}],
                        max_retries=3
                    )

                if reflection_obj.new_long_term_memory and reflection_obj.new_long_term_memory.strip():
                    self.long_lasting_notes.append(reflection_obj.new_long_term_memory.strip())

                # Real-time Match Reflection Terminal UI & Markdown/HTML logging
                try:
                    global_logger.log_reflection(
                        score=self.score,
                        reasoning=reflection_obj.reasoning,
                        new_long_memory=reflection_obj.new_long_term_memory,
                        all_long_notes=self.long_lasting_notes
                    )
                except Exception:
                    pass

                try:
                    from rich.console import Console
                    from rich.panel import Panel
                    from rich.table import Table
                    console = Console()
                    
                    table = Table(show_header=False, box=None, padding=(0, 1))
                    table.add_row("[bold cyan]Match Score:[/bold cyan]", f"[bold yellow]{self.score}[/bold yellow]")
                    table.add_row("[bold cyan]Archetype Reflection:[/bold cyan]", f"[white]{reflection_obj.reasoning}[/white]")
                    if reflection_obj.new_long_term_memory:
                        table.add_row("[bold magenta]+ Long-term Rule:[/bold magenta]", f"[bold green]{reflection_obj.new_long_term_memory}[/bold green]")
                    else:
                        table.add_row("[bold magenta]Long-term Memory:[/bold magenta]", "[dim]No new long-term rule added[/dim]")

                    console.print(Panel(table, title=f"[bold magenta]🧠 Post-Match Reflection & Learning[/bold magenta]", border_style="magenta", expand=False))
                except Exception:
                    pass
                break
            except Exception as e:
                import time
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    consecutive_429s += 1
                    if consecutive_429s >= 3:
                        from src.usage_tracker import DailyLimitReachedException
                        print(f"\n[ABORT] Received {consecutive_429s} consecutive 429 Quota/Rate errors. Halting execution.")
                        raise DailyLimitReachedException("Aborted due to 3 consecutive 429 API errors.")
                    print(f"API Rate Limit or Quota hit (429). Sleeping 60 seconds... (Strike {consecutive_429s}/3)")
                    time.sleep(60)
                else:
                    print(f"Unhandled error during post-match reflection: {e}")
                    break

    def finish_game(self):
        # Allow LLM to reflect and update long-term notes before history is cleared
        self.reflect_on_match()
        # Call base class finish_game to clear game_history and aggregate scores
        super().finish_game()
        # Reset short lasting notes for the next opponent
        self.short_lasting_notes = []

    def copy(self):
        # We need to correctly copy the player for the simulation reproduction step
        new_player = LLMPlayer(
            name=self.name, 
            provider=self.provider, 
            model_name=self.model_name
        )
        new_player.long_lasting_notes = list(self.long_lasting_notes)
        new_player.freeze_notes = self.freeze_notes
        return new_player
