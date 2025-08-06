import { initializeEventListeners } from './ui/events.js';
import { initializeGame, gameHandlers } from './game/main.js';

// Đảm bảo DOM đã được tải hoàn tất trước khi chạy code
document.addEventListener('DOMContentLoaded', () => {
    // Truyền các hàm xử lý từ tầng logic vào tầng event
    initializeEventListeners(gameHandlers);
    
    // Khởi tạo trạng thái game ban đầu
    initializeGame();

    console.log("Game application initialized.");
});