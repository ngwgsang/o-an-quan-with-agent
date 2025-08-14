**I. LUẬT DI CHUYỂN (MOVEMENT RULES)**
1.  **Bắt đầu**: Chọn 1 trong 5 ô của bạn (ví dụ: A1-A5 cho đội A) phải có quân bên trong. Không được chọn ô Quan (QA, QB).
2.  **Hành động**: Bốc TẤT CẢ quân trong ô đã chọn lên.
3.  **Rải quân**: Rải lần lượt từng quân vào các ô kế tiếp (bao gồm cả ô Quan của đối thủ và của mình).
4.  **Hướng đi**: Bạn có thể chọn rải theo chiều kim đồng hồ (`clockwise`) hoặc ngược chiều kim đồng hồ (`counter_clockwise`).

**II. LUẬT ĂN QUÂN (CAPTURING RULES)**
1.  **Điều kiện ăn**: Sau khi rải hết quân, nếu ô tiếp theo **TRỐNG**, bạn sẽ xét ô kế tiếp nữa. Nếu ô đó có quân, bạn sẽ **ĂN** toàn bộ số quân trong ô đó.
2.  **Ăn dây (Chain Capture)**: Sau khi ăn một ô, nếu ô liền kề tiếp theo lại **TRỐNG** và ô sau nó nữa có quân, bạn được quyền ăn tiếp ô đó. Cứ tiếp tục như vậy cho đến khi không thỏa mãn điều kiện ăn.
3.  **Kết thúc lượt**: Lượt của bạn kết thúc khi không thể ăn được nữa.

**III. CÁC TÌNH HUỐNG ĐẶC BIỆT (SPECIAL CASES)**
1.  **Ô Quan**: Quân trong ô Quan (gọi là Quan) **KHÔNG BAO GIỜ** được bốc lên để rải, chỉ có thể bị ăn.
2.  **Rải tiếp (Scattering Chain)**: Nếu sau khi rải hết quân mà ô tiếp theo **CÓ QUÂN** (không phải ô trống), bạn phải bốc toàn bộ quân ở ô đó lên và **rải tiếp** theo chiều đã chọn ban đầu.
3.  **Hết quân trên sân nhà ("Vay quân")**: Nếu cả 5 ô của bạn đều hết quân, bạn phải dùng 5 quân đã ăn được của mình để đặt vào mỗi ô 1 quân. Nếu không đủ 5 quân để rải, bạn phải vay của đối thủ và trả lại khi tính điểm cuối game.
4.  **Cấm ăn Quan đầu game**: Bạn không được phép ăn Quan ở lượt 1 và 2.

**IV. KẾT THÚC GAME (END OF GAME)**
- Game kết thúc khi cả hai ô Quan đều đã bị ăn hết.
- Hoặc khi đến lượt một người chơi nhưng cả 5 ô của người đó đều không còn quân.

**V. CÁCH TÍNH ĐIỂM (SCORING)**
- Mỗi quân Dân (peasant) bạn ăn được tính là **1 điểm**.
- Mỗi quân Quan (mandarin) bạn ăn được tính là **5 điểm**.
- Người thắng là người có tổng điểm cao hơn sau khi kết thúc game.