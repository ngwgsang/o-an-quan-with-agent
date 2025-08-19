from pydantic import BaseModel
from typing import List

class BasePersona(BaseModel):
    characteristics: List[str]
    typical_strategy: List[str]
    case_example: str

ATTACKER = BasePersona(
    characteristics=[
        "Always prioritizes attacking first",
        "Accepts high risk"
    ],
    typical_strategy=[
        "Focuses resources on short-term power",
        "Attacks continuously to overwhelm the opponent"
    ],
    case_example=(
        "In a strategy game, the Attacker will go all-out to assault "
        "the opponent’s base instead of strengthening defenses."
    )
)

DEFENDER = BasePersona(
    characteristics=[
        "Prefers caution and safety",
        "Avoids unnecessary risks"
    ],
    typical_strategy=[
        "Strengthens defenses before attacking",
        "Maintains stable board presence"
    ],
    case_example=(
        "In a strategy game, the Defender fortifies their base and "
        "waits for the opponent to make mistakes before counter-attacking."
    )
)

BALANCED = BasePersona(
    characteristics=[
        "Balances risk and reward",
        "Adapts based on situation"
    ],
    typical_strategy=[
        "Mixes offensive and defensive strategies",
        "Carefully evaluates before committing to an attack"
    ],
    case_example=(
        "In a strategy game, the Balanced player attacks when there "
        "is an opening but also ensures defenses are not left weak."
    )
)

STRATEGIC = BasePersona(
    characteristics=[
        "Thinks long-term",
        "Focuses on control rather than immediate gains"
    ],
    typical_strategy=[
        "Creates favorable positions for future moves",
        "Forces opponent into disadvantage over time"
    ],
    case_example=(
        "In a strategy game, the Strategic player sets traps and "
        "positions pieces for future dominance rather than instant rewards."
    )
)