# core/memory.py (tạo file mới)
from collections import deque
from typing import Dict, Any, List

class ShortTermMemory:
    """
    Quản lý bộ nhớ ngắn hạn cho agent dưới dạng một cửa sổ trượt.
    Lưu trữ các cặp (suy nghĩ, hành động) từ các lượt gần đây.
    """
    def __init__(self, mem_size):
        """
        Khởi tạo bộ nhớ với một kích thước cửa sổ nhất định.
        
        Args:
            mem_size (int): Số lượng lượt đi gần nhất cần lưu trữ.
        """
        if mem_size <= 0:
            raise ValueError("Window size must be a positive integer.")
        self.memory = deque(maxlen=mem_size)

    def add_memory(self, round_num: int, thought: str, action: Dict[str, Any]):
        """
        Thêm một ký ức mới vào bộ nhớ.
        Ký ức bao gồm vòng đấu, suy nghĩ và hành động đã thực hiện.
        
        Args:
            round_num (int): Số thứ tự của vòng đấu.
            thought (str): Suy nghĩ/lý do của agent cho hành động.
            action (Dict[str, Any]): Hành động mà agent đã chọn.
        """
        # Đảm bảo chỉ lưu những thông tin cần thiết và gọn gàng
        simplified_action = {
            "position": action.get("pos"),
            "direction": action.get("way")
        }
        
        memory_entry = {
            "round": round_num,
            "thought": thought,
            "action": simplified_action
        }
        self.memory.append(memory_entry)

    def get_context(self) -> List[str]:
        """
        Lấy và định dạng các ký ức gần đây để đưa vào prompt.
        Trình bày theo thứ tự từ mới nhất đến cũ nhất.
        
        Returns:
            str: Một chuỗi định dạng chứa các ký ức gần đây.
        """
        if not self.memory:
            return []

        # Sắp xếp các ký ức từ mới nhất đến cũ nhất
        recent_memories = reversed(self.memory)
        
        context_lines = []
        for mem in recent_memories:
            line = (
                f"- Round {mem.get('round', '?')}: Chose {mem['action']['position']} ({mem['action']['direction']}) because \"{mem['thought']}\"."
            )
            context_lines.append(line)
            
        return context_lines

    def __str__(self) -> str:
        return self.get_context()