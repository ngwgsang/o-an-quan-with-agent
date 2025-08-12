import { toggleModal, toggleSidebar, setupAgentDialog } from './renderer.js';

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

function syncRangeAndLabel(rangeId, labelId) {
    const range = document.getElementById(rangeId);
    const label = document.getElementById(labelId);
    if (!range || !label) return;

    range.addEventListener('input', () => {
        label.textContent = range.value;
    });
}

export function initializeEventListeners(eventHandlers) {
    handlers = eventHandlers;

    // Main buttons
    document.getElementById('move-btn')?.addEventListener('click', () => handlers.onAgentMove());
    document.getElementById('reset-btn')?.addEventListener('click', () => handlers.onReset());
    document.getElementById('apply-config')?.addEventListener('click', () => handlers.onApplyConfig());
    document.getElementById('auto-toggle')?.addEventListener('change', (e) => handlers.onToggleAutoMode(e.target.checked));


    // Game cells
    document.querySelectorAll('.game-cell').forEach(cell => {
        if (cell.id && (cell.id.startsWith('A') || cell.id.startsWith('B')) && cell.id.length === 2) {
             cell.addEventListener('click', () => handlers.onCellClick(cell.id));
        }
    });

    // Direction choice buttons
    document.querySelectorAll('.direction-btn').forEach(btn => {
        btn.addEventListener('click', () => handlers.onDirectionChoice(btn.dataset.way));
    });

    // Modals and Sidebar
    document.getElementById('open-history-btn')?.addEventListener('click', () => toggleModal('history-modal', true));
    document.getElementById('close-history-modal')?.addEventListener('click', () => toggleModal('history-modal', false));
    document.getElementById('history-modal')?.addEventListener('click', (e) => {
        if (e.target.id === 'history-modal') toggleModal('history-modal', false);
    });
    document.getElementById('expand-sidebar-btn')?.addEventListener('click', () => toggleSidebar(true));
    document.getElementById('export-history-json')?.addEventListener('click', () => handlers.onExportHistory());

    // Player settings visibility
    const setupPlayerConfigToggle = () => {
        const player1Select = document.getElementById('player1');
        const player2Select = document.getElementById('player2');
        const agentConfig1 = document.getElementById('agent-config-1');
        const agentConfig2 = document.getElementById('agent-config-2');

        const toggleVisibility = () => {
            if (agentConfig1) agentConfig1.classList.toggle('hidden', player1Select.value !== 'agent');
            if (agentConfig2) agentConfig2.classList.toggle('hidden', player2Select.value !== 'agent');
        };

        player1Select?.addEventListener('change', toggleVisibility);
        player2Select?.addEventListener('change', toggleVisibility);

        // Run on initial load
        toggleVisibility();
    };
    
    setupPlayerConfigToggle();

    // Sync range sliders with labels
    syncRangeAndLabel('temperature-1', 'temperature-label-1');
    syncRangeAndLabel('max-tokens-1', 'max-tokens-label-1');
    syncRangeAndLabel('top-p-1', 'top-p-label-1');
    syncRangeAndLabel('top-k-1', 'top-k-label-1');
    syncRangeAndLabel('temperature-2', 'temperature-label-2');
    syncRangeAndLabel('max-tokens-2', 'max-tokens-label-2');
    syncRangeAndLabel('top-p-2', 'top-p-label-2');
    syncRangeAndLabel('top-k-2', 'top-k-label-2');

    setupDirectionAnimationListeners();
    setupAgentDialog();

}