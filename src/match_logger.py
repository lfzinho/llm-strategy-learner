import os
import json
import html

class MatchLogger:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        self.events = []
        os.makedirs(self.output_dir, exist_ok=True)
        self.md_file = os.path.join(self.output_dir, "match_log.md")
        self.html_file = os.path.join(self.output_dir, "match_log.html")
        
        # Initialize or clear MD file
        with open(self.md_file, "w", encoding="utf-8") as f:
            f.write("# 🎯 LLM Strategy Learner - Live Session Log\n\n")
            f.write("> Iterated Prisoner's Dilemma with Real-time Reflection & 5% Communication Noise\n\n---\n\n")

    def log_match_start(self, match_num, total_matches, opponent_strategy):
        event = {
            "type": "match_start",
            "match_num": match_num,
            "total_matches": total_matches,
            "opponent_strategy": opponent_strategy
        }
        self.events.append(event)
        
        with open(self.md_file, "a", encoding="utf-8") as f:
            f.write(f"## ⚔️ Match {match_num}/{total_matches} vs **{opponent_strategy}**\n\n")

    def log_turn(self, player_name, model_name, provider, round_num, decision, reasoning, new_short_memory=None):
        event = {
            "type": "turn",
            "player_name": player_name,
            "model_name": model_name,
            "provider": provider,
            "round_num": round_num,
            "decision": decision,
            "reasoning": reasoning,
            "new_short_memory": new_short_memory
        }
        self.events.append(event)

        badge = "🟢 **COOPERATE** 🤝" if decision == "COOPERATE" else "🔴 **DEFECT** ⚔️"
        with open(self.md_file, "a", encoding="utf-8") as f:
            f.write(f"### 🤖 Round {round_num} - {badge}\n")
            f.write(f"- **Model**: `{model_name}` ({provider})\n")
            f.write(f"- **Decision**: {badge}\n")
            f.write(f"- **Reasoning**: *{reasoning}*\n")
            if new_short_memory:
                f.write(f"- **+ Short-term Memory**: `{new_short_memory}`\n")
            f.write("\n")

    def log_reflection(self, score, reasoning, new_long_memory=None, all_long_notes=None):
        event = {
            "type": "reflection",
            "score": score,
            "reasoning": reasoning,
            "new_long_memory": new_long_memory,
            "all_long_notes": all_long_notes or []
        }
        self.events.append(event)

        with open(self.md_file, "a", encoding="utf-8") as f:
            f.write(f"#### 🧠 Post-Match Reflection\n")
            f.write(f"- **Final Score**: **{score}**\n")
            f.write(f"- **Archetype Analysis**: {reasoning}\n")
            if new_long_memory:
                f.write(f"- **+ New Long-term Rule**: 💡 `{new_long_memory}`\n")
            else:
                f.write(f"- **Long-term Memory**: *(No new rule added)*\n")
            f.write("\n---\n\n")

    def export_html(self):
        """Generates a modern, dark-themed HTML report mimicking Charm / Bubble Tea / Rich terminal style."""
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LLM Strategy Learner - Match Logs</title>
<style>
  :root {
    --bg: #0d1117;
    --card-bg: #161b22;
    --border: #30363d;
    --cyan: #38bdf8;
    --yellow: #eab308;
    --green: #22c55e;
    --red: #ef4444;
    --magenta: #d946ef;
    --text: #f0f6fc;
    --text-dim: #8b949e;
  }
  body {
    background-color: var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono', 'Fira Code', 'Segoe UI', Menlo, monospace;
    line-height: 1.6;
    padding: 2rem;
    max-width: 1000px;
    margin: 0 auto;
  }
  h1, h2, h3, h4 {
    margin-top: 0;
  }
  .header-card {
    border: 2px solid var(--cyan);
    border-radius: 12px;
    background: linear-gradient(145deg, #161b22, #0d1117);
    padding: 1.5rem 2rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 8px 24px rgba(56, 189, 248, 0.15);
  }
  .header-card h1 {
    color: var(--cyan);
    margin-bottom: 0.5rem;
    font-size: 1.8rem;
  }
  .header-card p {
    color: var(--text-dim);
    margin: 0;
  }
  .match-rule {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin: 3rem 0 1.5rem;
  }
  .match-rule hr {
    flex: 1;
    border: none;
    border-top: 2px solid var(--border);
  }
  .match-badge {
    background: #21262d;
    border: 1px solid var(--cyan);
    color: var(--cyan);
    font-weight: bold;
    padding: 0.4rem 1rem;
    border-radius: 8px;
    font-size: 1.1rem;
  }
  .turn-card {
    background: var(--card-bg);
    border: 1px solid #1d4ed8;
    border-left: 5px solid var(--cyan);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  }
  .turn-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.5rem;
    margin-bottom: 0.8rem;
    color: var(--cyan);
    font-weight: bold;
  }
  .decision-cooperate {
    background: rgba(34, 197, 94, 0.15);
    color: var(--green);
    border: 1px solid var(--green);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-weight: bold;
  }
  .decision-defect {
    background: rgba(239, 68, 68, 0.15);
    color: var(--red);
    border: 1px solid var(--red);
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    font-weight: bold;
  }
  .kv-row {
    display: flex;
    margin-bottom: 0.4rem;
  }
  .kv-key {
    width: 140px;
    flex-shrink: 0;
    color: var(--cyan);
    font-weight: 600;
  }
  .kv-val {
    flex: 1;
  }
  .reasoning-text {
    color: var(--yellow);
    font-style: italic;
  }
  .memory-text {
    color: var(--magenta);
    background: rgba(217, 70, 239, 0.1);
    padding: 0.1rem 0.4rem;
    border-radius: 4px;
  }
  .reflection-card {
    background: #1a1024;
    border: 1px solid var(--magenta);
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    margin: 1.5rem 0 2.5rem;
    box-shadow: 0 4px 16px rgba(217, 70, 239, 0.2);
  }
  .reflection-title {
    color: var(--magenta);
    font-weight: bold;
    font-size: 1.1rem;
    border-bottom: 1px solid rgba(217, 70, 239, 0.3);
    padding-bottom: 0.5rem;
    margin-bottom: 0.8rem;
  }
  .score-badge {
    background: #3b2d18;
    color: var(--yellow);
    font-weight: bold;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    border: 1px solid var(--yellow);
  }
</style>
</head>
<body>
  <div class="header-card">
    <h1>🎯 LLM Strategy Learner</h1>
    <p>Real-time Iterated Prisoner's Dilemma Session with 5% Environmental Noise</p>
  </div>
"""
        for ev in self.events:
            if ev["type"] == "match_start":
                html_content += f"""
  <div class="match-rule">
    <hr>
    <div class="match-badge">⚔️ Match {ev['match_num']}/{ev['total_matches']} vs {html.escape(ev['opponent_strategy'])}</div>
    <hr>
  </div>
"""
            elif ev["type"] == "turn":
                is_coop = ev["decision"] == "COOPERATE"
                dec_class = "decision-cooperate" if is_coop else "decision-defect"
                dec_text = "COOPERATE 🤝" if is_coop else "DEFECT ⚔️"
                
                short_mem_html = ""
                if ev.get("new_short_memory"):
                    short_mem_html = f"""
    <div class="kv-row">
      <div class="kv-key" style="color: var(--magenta);">+ Short Memory:</div>
      <div class="kv-val"><span class="memory-text">{html.escape(ev['new_short_memory'])}</span></div>
    </div>
"""
                html_content += f"""
  <div class="turn-card">
    <div class="turn-title">
      <span>🤖 {html.escape(ev['player_name'])} Turn (Round {ev['round_num']})</span>
      <span class="{dec_class}">{dec_text}</span>
    </div>
    <div class="kv-row">
      <div class="kv-key">Model:</div>
      <div class="kv-val"><span style="color: var(--text-dim);">{html.escape(ev['model_name'])} ({html.escape(ev['provider'])})</span></div>
    </div>
    <div class="kv-row">
      <div class="kv-key">Reasoning:</div>
      <div class="kv-val"><span class="reasoning-text">"{html.escape(ev['reasoning'])}"</span></div>
    </div>
    {short_mem_html}
  </div>
"""
            elif ev["type"] == "reflection":
                long_mem_html = """
    <div class="kv-row">
      <div class="kv-key" style="color: var(--magenta);">Long-term Memory:</div>
      <div class="kv-val" style="color: var(--text-dim); font-style: italic;">No new long-term rule added</div>
    </div>
"""
                if ev.get("new_long_memory"):
                    long_mem_html = f"""
    <div class="kv-row">
      <div class="kv-key" style="color: var(--magenta);">+ Long-term Rule:</div>
      <div class="kv-val"><strong style="color: var(--green);">💡 {html.escape(ev['new_long_memory'])}</strong></div>
    </div>
"""
                html_content += f"""
  <div class="reflection-card">
    <div class="reflection-title">🧠 Post-Match Reflection & Learning</div>
    <div class="kv-row">
      <div class="kv-key">Match Score:</div>
      <div class="kv-val"><span class="score-badge">{ev['score']} pts</span></div>
    </div>
    <div class="kv-row">
      <div class="kv-key">Archetype Analysis:</div>
      <div class="kv-val">{html.escape(ev['reasoning'])}</div>
    </div>
    {long_mem_html}
  </div>
"""

        html_content += """
</body>
</html>
"""
        with open(self.html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

# Global singleton instance for easy import across modules
global_logger = MatchLogger()
