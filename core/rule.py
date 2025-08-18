from pydantic import BaseModel
from typing import List, Optional

# --- Định nghĩa cấu trúc ---

class RuleItem(BaseModel):
    """Đại diện cho một quy tắc cụ thể."""
    id: str # Thêm ID để dễ dàng lọc (E1, E2,...)
    title: str
    description: str

class RuleSection(BaseModel):
    """Đại diện cho một nhóm các quy tắc."""
    section_title: str
    rules: List[RuleItem]

class GameRules(BaseModel):
    """Đối tượng gốc chứa toàn bộ các nhóm quy tắc của trò chơi."""
    movement: RuleSection
    capturing: RuleSection
    special_cases: RuleSection
    end_of_game: RuleSection
    scoring: RuleSection

# --- Khởi tạo dữ liệu luật chơi ---

GAME_RULES = GameRules(
    movement=RuleSection(
        section_title="**I. LUẬT DI CHUYỂN (MOVEMENT RULES)**",
        rules=[
            RuleItem(id="M1", title="Bắt đầu", description="Chọn 1 trong 5 ô của bạn (ví dụ: A1-A5 cho đội A) phải có quân bên trong. Không được chọn ô Quan (QA, QB)."),
            RuleItem(id="M2", title="Hành động", description="Bốc TẤT CẢ quân trong ô đã chọn lên."),
            RuleItem(id="M3", title="Rải quân", description="Rải lần lượt từng quân vào các ô kế tiếp (bao gồm cả ô Quan của đối thủ và của mình)."),
            RuleItem(id="M4", title="Hướng đi", description="Bạn có thể chọn rải theo chiều kim đồng hồ (`clockwise`) hoặc ngược chiều kim đồng hồ (`counter_clockwise`).")
        ]
    ),
    capturing=RuleSection(
        section_title="**II. LUẬT ĂN QUÂN (CAPTURING RULES)**",
        rules=[
            RuleItem(id="C1", title="Điều kiện ăn", description="Sau khi rải hết quân, nếu ô tiếp theo **TRỐNG**, bạn sẽ xét ô kế tiếp nữa. Nếu ô đó có quân, bạn sẽ **ĂN** toàn bộ số quân trong ô đó."),
            RuleItem(id="C2", title="Ăn dây (Chain Capture)", description="Sau khi ăn một ô, nếu ô liền kề tiếp theo lại **TRỐNG** và ô sau nó nữa có quân, bạn được quyền ăn tiếp ô đó. Cứ tiếp tục như vậy cho đến khi không thỏa mãn điều kiện ăn."),
            RuleItem(id="C3", title="Kết thúc lượt", description="Lượt của bạn kết thúc khi không thể ăn được nữa.")
        ]
    ),
    special_cases=RuleSection(
        section_title="**III. CÁC TÌNH HUỐNG ĐẶC BIỆT (SPECIAL CASES / EXTENDED RULES)**",
        rules=[
            RuleItem(id="E1", title="Luật Quan Non (Immature Mandarin)", description="Không được ăn ô Quan nếu trong ô đó có ít hơn 5 dân."),
            RuleItem(id="E2", title="Luật Rải Lại Bắt Buộc (Forced Redistribution)", description="Khi rải quân xong mà ô tiếp theo vẫn còn quân, bắt buộc phải bốc quân ở ô đó lên và rải tiếp."),
            RuleItem(id="E3", title="Luật Hạn Chế Đầu Game (Early Game Restriction)", description="Không được phép ăn ô Quan trong 1 hoặc 2 vòng đầu tiên của ván cờ."),
            RuleItem(id="E4", title="Luật Hai Ô Trống (Two-Empty Rule)", description="Cho phép ăn quân cách 2 ô trống, thay vì 1 ô trống như thông thường."),
            RuleItem(id="E5", title="Luật Ăn Dây Bắt Buộc (Forced Capture Chain)", description="Nếu có thể ăn dây, người chơi bắt buộc phải tiếp tục ăn cho đến hết chuỗi, không được dừng lại giữa chừng.")
        ]
    ),
    end_of_game=RuleSection(
        section_title="**IV. KẾT THÚC GAME (END OF GAME)**",
        rules=[
            RuleItem(id="EG1", title="Điều kiện 1", description="Game kết thúc khi cả hai ô Quan đều đã bị ăn hết."),
            RuleItem(id="EG2", title="Điều kiện 2", description="Hoặc khi đến lượt một người chơi nhưng cả 5 ô của người đó đều không còn quân.")
        ]
    ),
    scoring=RuleSection(
        section_title="**V. CÁCH TÍNH ĐIỂM (SCORING)**",
        rules=[
            RuleItem(id="S1", title="Điểm Dân", description="Mỗi quân Dân (peasant) bạn ăn được tính là **1 điểm**."),
            RuleItem(id="S2", title="Điểm Quan", description="Mỗi quân Quan (mandarin) bạn ăn được tính là **5 điểm**."),
            RuleItem(id="S3", title="Người thắng", description="Người thắng là người có tổng điểm cao hơn sau khi kết thúc game.")
        ]
    )
)

def get_rules_as_str(extended_rules: Optional[List[str]] = None) -> str:
    """
    Chuyển đổi đối tượng Pydantic GAME_RULES thành một chuỗi văn bản.
    Chỉ bao gồm các luật đặc biệt (E1-E5) nếu chúng được cung cấp trong danh sách.
    """
    if extended_rules is None:
        extended_rules = []

    full_text = []
    
    # 1. Thêm các luật cố định (Di chuyển, Ăn quân)
    fixed_sections = [GAME_RULES.movement, GAME_RULES.capturing]
    for section in fixed_sections:
        full_text.append(section.section_title)
        for i, rule in enumerate(section.rules, 1):
            full_text.append(f"{i}. **{rule.title}**: {rule.description}")
        full_text.append("")

    # 2. Thêm các luật đặc biệt nếu có
    if extended_rules:
        full_text.append(GAME_RULES.special_cases.section_title)
        # Lọc ra các luật có id nằm trong danh sách extended_rules
        active_special_rules = [rule for rule in GAME_RULES.special_cases.rules if rule.id in extended_rules]
        for rule in active_special_rules:
            full_text.append(f"- **{rule.id} - {rule.title}**: {rule.description}")
        full_text.append("")

    # 3. Thêm các luật cuối game và tính điểm
    end_sections = [GAME_RULES.end_of_game, GAME_RULES.scoring]
    for section in end_sections:
        full_text.append(section.section_title)
        for rule in section.rules:
            full_text.append(f"- **{rule.title}**: {rule.description}")
        full_text.append("")
        
    return "\n".join(full_text)