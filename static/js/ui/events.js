import { toggleModal, toggleSidebar } from './renderer.js';

// Các hàm xử lý (handlers) sẽ được truyền từ tầng logic vào
let handlers = {};

function setupDirectionAnimationListeners() {
    const clockwiseBtn = document.querySelector('button[data-way="clockwise"]');
    const counterClockwiseBtn = document.querySelector('button[data-way="counter_clockwise"]');
    const animationOverlay = document.getElementById('animation-overlay');
    if (!clockwiseBtn || !counterClockwiseBtn || !animationOverlay) return;

    const pathDataClockwise = "M 15,25 L 85,25 Q 95,25 95,35 L 95,65 Q 95,75 85,75 L 15,75 Q 5,75 5,65 L 5,35 Q 5,25 15,25 Z";
    const pathDataCounterClockwise = "M 85,25 L 15,25 Q 5,25 5,35 L 5,65 Q 5,75 15,75 L 85,75 Q 95,75 95,65 L 95,35 Q 95,25 85,25 Z";
    const arrowShape = "M0,-5 L10,0 L0,5 Z";

    const createAnimationElement = (pathData, id) => {
        const wrapper = document.createElement('div');
        wrapper.id = id;
        wrapper.classList.add('hidden', 'w-full', 'h-full');
        wrapper.innerHTML = `<svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="${pathData}" fill="none" stroke="#f59e0b" stroke-width="1.5" stroke-dasharray="5 5" stroke-linecap="round"/><path d="${arrowShape}" fill="#f59e0b"><animateMotion dur="4s" repeatCount="indefinite" path="${pathData}" rotate="auto" /></path></svg>`;
        return wrapper;
    };

    const clockwiseAnimation = createAnimationElement(pathDataClockwise, 'anim-clockwise');
    const counterClockwiseAnimation = createAnimationElement(pathDataCounterClockwise, 'anim-counter-clockwise');
    animationOverlay.appendChild(clockwiseAnimation);
    animationOverlay.appendChild(counterClockwiseAnimation);

    const showAnimation = (direction) => {
        animationOverlay.classList.remove('hidden');
        clockwiseAnimation.classList.toggle('hidden', direction !== 'clockwise');
        counterClockwiseAnimation.classList.toggle('hidden', direction === 'clockwise');
    };
    const hideAnimation = () => animationOverlay.classList.add('hidden');

    clockwiseBtn.addEventListener('mouseenter', () => showAnimation('clockwise'));
    clockwiseBtn.addEventListener('mouseleave', hideAnimation);
    counterClockwiseBtn.addEventListener('mouseenter', () => showAnimation('counter_clockwise'));
    counterClockwiseBtn.addEventListener('mouseleave', hideAnimation);
}

// --- PHẦN SỬA LỖI ---
// Hàm này đã được khôi phục lại logic validation
function syncRangeAndNumber(rangeId, numberId) {
    const range = document.getElementById(rangeId);
    const number = document.getElementById(numberId);
    const applyButton = document.getElementById("apply-config");

    if (!range || !number || !applyButton) return;

    function validateInput() {
        const numValue = parseFloat(number.value);
        if (isNaN(numValue) || numValue < parseFloat(range.min) || numValue > parseFloat(range.max)) {
            number.setCustomValidity(`Nhập trong khoảng ${range.min} - ${range.max}`);
            number.reportValidity(); // Hiển thị thông báo lỗi của trình duyệt
            applyButton.disabled = true;
        } else {
            number.setCustomValidity(''); // Xóa thông báo lỗi
            applyButton.disabled = false;
        }
    }

    range.addEventListener('input', () => {
        number.value = range.value;
        validateInput();
    });

    number.addEventListener('input', () => {
        const numValue = parseFloat(number.value);
        if (!isNaN(numValue) && numValue >= parseFloat(range.min) && numValue <= parseFloat(range.max)) {
            range.value = number.value;
        }
        validateInput();
    });

    validateInput(); // Chạy validation lần đầu khi tải trang
}
// --- KẾT THÚC PHẦN SỬA LỖI ---

export function initializeEventListeners(eventHandlers) {
    handlers = eventHandlers;

    // Các nút chính
    document.getElementById('move-btn')?.addEventListener('click', () => handlers.onAgentMove());
    document.getElementById('reset-btn')?.addEventListener('click', () => handlers.onReset());
    document.getElementById('apply-config')?.addEventListener('click', () => handlers.onApplyConfig());

    // Các ô cờ
    document.querySelectorAll('.game-cell').forEach(cell => {
        if (cell.id && (cell.id.startsWith('A') || cell.id.startsWith('B')) && cell.id.length === 2) {
             cell.addEventListener('click', () => handlers.onCellClick(cell.id));
        }
    });

    // Các nút chọn hướng
    document.querySelectorAll('.direction-btn').forEach(btn => {
        btn.addEventListener('click', () => handlers.onDirectionChoice(btn.dataset.way));
    });

    // Modal và Sidebar
    document.getElementById('open-history-btn')?.addEventListener('click', () => toggleModal('history-modal', true));
    document.getElementById('close-history-modal')?.addEventListener('click', () => toggleModal('history-modal', false));
    document.getElementById('history-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'history-modal') toggleModal('history-modal', false);
    });
    document.getElementById('expand-sidebar-btn')?.addEventListener('click', () => toggleSidebar(true));
    document.getElementById('export-history-json')?.addEventListener('click', () => handlers.onExportHistory());

    // Cài đặt người chơi
    document.getElementById('player1')?.addEventListener('change', (e) => {
        document.getElementById('agent-config-1').classList.toggle('hidden', e.target.value !== 'agent');
    });
    document.getElementById('player2')?.addEventListener('change', (e) => {
        document.getElementById('agent-config-2').classList.toggle('hidden', e.target.value !== 'agent');
    });

    // Đồng bộ input range và number
    syncRangeAndNumber('temperature-1', 'temperature-value-1');
    syncRangeAndNumber('max-tokens-1', 'max-tokens-value-1');
    syncRangeAndNumber('top-p-1', 'top-p-value-1');
    syncRangeAndNumber('temperature-2', 'temperature-value-2');
    syncRangeAndNumber('max-tokens-2', 'max-tokens-value-2');
    syncRangeAndNumber('top-p-2', 'top-p-value-2');

    setupDirectionAnimationListeners();
}