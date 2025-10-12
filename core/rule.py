from pydantic import BaseModel
from typing import List, Optional

# --- Structure Definitions ---

class RuleItem(BaseModel):
    """Represents a specific rule."""
    id: str
    title: str
    description: str

class RuleSection(BaseModel):
    """Represents a group of rules (e.g., Movement Rules)."""
    section_title: str
    rules: List[RuleItem]

class GameRules(BaseModel):
    """The root object containing all rule sections for the game."""
    movement: RuleSection
    capturing: RuleSection
    special_cases: RuleSection
    end_of_game: RuleSection
    scoring: RuleSection

# --- Game Rules Data Initialization ---

GAME_RULES = GameRules(
    movement=RuleSection(
        section_title="**I. MOVEMENT RULES**",
        rules=[
            RuleItem(id="M1", title="Start", description="Choose one of your 5 squares (e.g., A1-A5 for team A) that contains pieces. You cannot choose a Mandarin square (QA, QB)."),
            RuleItem(id="M2", title="Action", description="Pick up ALL pieces from the chosen square."),
            RuleItem(id="M3", title="Distribution", description="Distribute the pieces one by one into the subsequent squares (including both your own and the opponent's Mandarin squares)."),
            RuleItem(id="M4", title="Direction", description="You can choose to distribute clockwise or counter-clockwise.")
        ]
    ),
    capturing=RuleSection(
        section_title="**II. CAPTURING RULES**",
        rules=[
            RuleItem(id="C1", title="Capture Condition", description="After distributing all pieces, if the next square is **EMPTY**, you check the one after it. If that square contains pieces, you **CAPTURE** all of them."),
            RuleItem(id="C2", title="Chain Capture", description="After a capture, if the next adjacent square is **EMPTY** and the one after it has pieces, you can capture again. This continues until the condition is no longer met."),
            RuleItem(id="C3", title="End of Turn", description="Your turn ends when you can no longer capture any more pieces.")
        ]
    ),
    special_cases=RuleSection(
        section_title="**III. SPECIAL CASES / EXTENDED RULES**",
        rules=[
            RuleItem(id="E1", title="Immature Mandarin", description="You cannot capture a Mandarin square if it contains fewer than 5 peasant pieces."),
            RuleItem(id="E2", title="Forced Redistribution", description="If, after distributing, the next square still has pieces, you must pick them all up and continue distributing."),
            RuleItem(id="E3", title="Early Game Restriction", description="Capturing Mandarin squares is not allowed in the first 1 or 2 rounds of the game."),
            RuleItem(id="E4", title="Two-Empty Rule", description="Allows capturing pieces across two empty squares instead of the usual one."),
        ]
    ),
    end_of_game=RuleSection(
        section_title="**IV. END OF GAME**",
        rules=[
            RuleItem(id="EG1", title="Condition 1", description="The game ends when both Mandarin squares have been captured."),
            RuleItem(id="EG2", title="Condition 2", description="Alternatively, the game ends when a player has no pieces on their side of the board to make a move.")
        ]
    ),
    scoring=RuleSection(
        section_title="**V. SCORING**",
        rules=[
            RuleItem(id="S1", title="Peasant Points", description="Each captured peasant piece is worth **1 point**."),
            RuleItem(id="S2", title="Mandarin Points", description="Each captured Mandarin piece is worth **5 points**."),
            RuleItem(id="S3", title="Winner", description="The player with the higher total score at the end of the game wins.")
        ]
    )
)

# --- Utility function to convert rules back to a string for the prompt ---
def get_rules_as_str(extended_rules: Optional[List[str]] = None) -> str:
    """
    Converts the GAME_RULES Pydantic object into a text string.
    Only includes special rules (E1-E5) if their IDs are provided in the list.
    """
    if extended_rules is None:
        extended_rules = []

    full_text = []
    
    # 1. Add fixed rules (Movement, Capturing)
    fixed_sections = [GAME_RULES.movement, GAME_RULES.capturing]
    for section in fixed_sections:
        full_text.append(section.section_title)
        for i, rule in enumerate(section.rules, 1):
            full_text.append(f"{i}. **{rule.title}**: {rule.description}")
        full_text.append("")

    # 2. Add special rules if they are active
    if extended_rules:
        full_text.append(GAME_RULES.special_cases.section_title)
        # Filter for rules whose IDs are in the extended_rules list
        active_special_rules = [rule for rule in GAME_RULES.special_cases.rules if rule.id in extended_rules]
        for rule in active_special_rules:
            full_text.append(f"- **{rule.id} - {rule.title}**: {rule.description}")
        full_text.append("")

    # 3. Add end game and scoring rules
    end_sections = [GAME_RULES.end_of_game, GAME_RULES.scoring]
    for section in end_sections:
        full_text.append(section.section_title)
        for rule in section.rules:
            full_text.append(f"- **{rule.title}**: {rule.description}")
        full_text.append("")
        
    return "\n".join(full_text)