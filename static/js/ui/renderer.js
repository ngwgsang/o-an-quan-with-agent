// File: renderer.js (NỘI DUNG MỚI HOÀN TOÀN)

const sleep = ms => new Promise(res => setTimeout(res, ms));

// --- CÁC HÀM TẠO VÀ QUẢN LÝ QUÂN CỜ (BUBBLES) ---

function createBubbleElement(piece) {
    const bubble = document.createElement('div');
    const pieceType = piece.startsWith('p') ? 'peasant' : (piece.startsWith('m') ? 'mandarin' : '');
    if (!pieceType) return null;

    const team = piece.endsWith('_a') ? 'bubble-a' : 'bubble-b';
    bubble.className = `bubble ${pieceType} ${team}`;
    bubble.dataset.pieceId = piece + '_' + Date.now() + Math.random(); // ID duy nhất
    bubble.textContent = pieceType === 'mandarin' ? '👲' : '🧑‍🌾';
    return bubble;
}

function addBubbleToCell(cellElement, piece) {
    const bubble = createBubbleElement(piece);
    if (!bubble) return;
    const size = piece.startsWith('p') ? 60 : 100;
    const padding = 5;
    const randomLeft = padding + Math.random() * (cellElement.clientWidth - size - padding * 2);
    const randomTop = padding + Math.random() * (cellElement.clientHeight - size - padding * 2);
    bubble.style.left = `${randomLeft}px`;
    bubble.style.top = `${randomTop}px`;
    cellElement.appendChild(bubble);
}

// --- CÁC HÀM XỬ LÝ ANIMATION ---

async function getElementCenter(el) {
    const rect = el.getBoundingClientRect();
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

async function animateSingleDrop(fromPos, toPos, piece) {
    const fromCell = document.getElementById(fromPos);
    const toCell = document.getElementById(toPos);
    if (!fromCell || !toCell) return;

    // Thay vì xóa bubble bất kỳ, ta lấy bubble cuối cùng trong ô
    const bubbleToRemove = fromCell.querySelector('.bubble:last-child');
    let startRect;

    if (bubbleToRemove) {
        startRect = bubbleToRemove.getBoundingClientRect();
        bubbleToRemove.remove(); // Xóa bubble cụ thể
    } else {
        const startCenter = await getElementCenter(fromCell);
        startRect = { left: startCenter.x, top: startCenter.y, width: 0, height: 0 };
    }

    const endCenter = await getElementCenter(toCell);
    const flyingBubble = createBubbleElement(piece);
    if (!flyingBubble) return;

    flyingBubble.classList.add('flying-bubble');
    document.body.appendChild(flyingBubble);

    flyingBubble.style.left = `${startRect.left}px`;
    flyingBubble.style.top = `${startRect.top}px`;

    await sleep(10);

    flyingBubble.style.left = `${endCenter.x - flyingBubble.offsetWidth / 2}px`;
    flyingBubble.style.top = `${endCenter.y - flyingBubble.offsetHeight / 2}px`;

    await sleep(250);
    if (document.body.contains(flyingBubble)) {
        document.body.removeChild(flyingBubble);
    }
    addBubbleToCell(toCell, piece);
}


async function animateCapture(fromPos, team) {
    const fromCell = document.getElementById(fromPos);
    if (!fromCell) return;

    fromCell.classList.add('ring-4', 'ring-red-500');
    await sleep(500);

    // Xóa tất cả bubble bên trong ô một cách an toàn
    const bubbles = fromCell.querySelectorAll('.bubble');
    bubbles.forEach(b => b.remove());

    await sleep(200);
    fromCell.classList.remove('ring-4', 'ring-red-500');
}


export async function animateEvents(events, finalState, onComplete) {
    const buttons = ['move-btn', 'reset-btn', 'apply-config'];
    buttons.forEach(id => {
        const btn = document.getElementById(id);
        if (btn) btn.disabled = true;
    });

    try {
        let currentPickupPos = null;
        for (const event of events) {
            switch (event.type) {
                case 'pickup':
                    currentPickupPos = event.pos;
                    const pickupCell = document.getElementById(event.pos);
                    if (pickupCell) {
                         pickupCell.classList.add('ring-4', 'ring-yellow-500');
                         await sleep(400);
                         pickupCell.classList.remove('ring-4', 'ring-yellow-500');
                    }
                    break;
                case 'drop':
                    await animateSingleDrop(currentPickupPos, event.to_pos, event.piece);
                    break;
                case 'capture':
                    await animateCapture(event.pos, event.team);
                    break;
                case 'score_update':
                    updateScores(event.score.A, event.score.B);
                    const scoreEl = document.getElementById(event.team === 'A' ? 'score-a' : 'score-b');
                    if(scoreEl) scoreEl.classList.add('scale-150', 'text-yellow-400');
                    await sleep(300);
                    if(scoreEl) scoreEl.classList.remove('scale-150', 'text-yellow-400');
                    break;
                case 'game_over':
                    await sleep(500);
                    alert(event.message);
                    break;
            }
        }
    } finally {
        if (onComplete) {
            onComplete(finalState, false);
        }
    }
}


// --- CÁC HÀM CẬP NHẬT GIAO DIỆN CHÍNH ---

export function updateBoard(boardState) {
    const allCells = document.querySelectorAll('.game-cell');
    allCells.forEach(cell => {
        // Xóa tất cả bubble hiện có
        const bubbles = cell.querySelectorAll('.bubble');
        bubbles.forEach(b => b.remove());

        // Vẽ lại bubble mới từ boardState
        const pos = cell.id;
        if (boardState[pos]) {
            boardState[pos].forEach(piece => addBubbleToCell(cell, piece));
        }
        
        // Xóa hiệu ứng còn sót lại
        cell.classList.remove('ring-4', 'ring-yellow-500', 'ring-red-500');
    });
}


export function updateScores(scoreA, scoreB) {
    const scoreAEl = document.getElementById('score-a');
    const scoreBEl = document.getElementById('score-b');
    if (scoreAEl) scoreAEl.textContent = scoreA;
    if (scoreBEl) scoreBEl.textContent = scoreB;
}

export function updateStatus(message) {
    const statusEl = document.getElementById('game-status');
    if (statusEl) statusEl.textContent = message;
}

export function setHumanInteraction(enable, availablePos = []) {
    const boardEl = document.getElementById('game_board');
    if (boardEl) boardEl.classList.toggle('human-turn', enable);
    
    document.querySelectorAll('.game-cell').forEach(cell => {
        cell.classList.remove('selectable');
    });

    if (enable) {
        updateStatus('Your turn! Please select a cell.');
        availablePos.forEach(pos => {
            const cell = document.getElementById(pos);
            if (cell) {
                cell.classList.add('selectable');
            }
        });
    }
}

export function addHistoryEntry(actionDetails, round, animationEvents) {
    const historyLog = document.getElementById('history-log');
    if (!historyLog) return;
    const entry = document.createElement('div');
    entry.className = 'p-2 rounded border border-slate-600 text-sm';
    const moveAction = actionDetails.action || {};
    const reason = actionDetails.reason;
    let html = `<div class="flex justify-between items-center opacity-70"><span>Round ${round} - Player ${moveAction.pos ? moveAction.pos.charAt(0) : '?'}</span><span>${new Date().toLocaleTimeString()}</span></div><p class="font-semibold my-1">Move: ${moveAction.pos || 'N/A'} -> ${moveAction.way || 'N/A'}</p>`;
    if (reason) html += `<p class="text-xs italic text-cyan-400 my-1">🤔: ${reason}</p>`;
    html += `<div class="text-xs opacity-80 pl-2 border-l-2 border-slate-500 max-h-24 overflow-y-auto">`;
    if (animationEvents) {
        let dropCounter = 0;
        animationEvents.forEach(event => {
            switch (event.type) {
                case 'pickup':
                    dropCounter = 0;
                    html += `<div><strong>Bốc ${event.pieces.length} quân</strong> từ ô ${event.pos}</div>`;
                    break;
                case 'drop':
                    dropCounter++;
                    let pieceType = event.piece.startsWith('p') ? 'Dân' : 'Quan';
                    html += `<div>&nbsp;&nbsp;↳ Rải quân ${pieceType} #${dropCounter} tới ô ${event.to_pos}</div>`;
                    break;
                case 'capture':
                    html += `<div><strong>Ăn ${event.pieces.length} quân</strong> ở ô ${event.pos}</div>`;
                    break;
                case 'game_over':
                    html += `<div class="font-bold text-red-400">${event.message}</div>`;
                    break;
            }
        });
    } else if (actionDetails.steps) {
        actionDetails.steps.forEach(step => { html += `<div>${step}</div>`; });
    }
    html += `</div>`;
    entry.innerHTML = html;
    historyLog.prepend(entry);
}


export function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.toggle('hidden', !show);
        if (modalId === 'history-modal' && show) {
            const modalContent = document.getElementById('modal-history-content');
            const historyLog = document.getElementById('history-log');
            if (modalContent && historyLog) {
                modalContent.innerHTML = historyLog.innerHTML;
            }
        }
    }
}

export function toggleSidebar(expanded) {
    const sidebar = document.getElementById('sidebar');
    const sidebarContent = document.getElementById('sidebar-content-expanded');
    const expandBtn = document.getElementById('expand-sidebar-btn');
    if (sidebar && sidebarContent && expandBtn) {
        sidebar.classList.toggle('w-[20%]', expanded);
        sidebar.classList.toggle('p-4', expanded);
        sidebar.classList.toggle('pr-0', expanded);
        sidebar.classList.toggle('w-16', !expanded);
        sidebar.classList.toggle('p-2', !expanded);
        sidebarContent.classList.toggle('hidden', !expanded);
        expandBtn.classList.toggle('hidden', expanded);
    }
}

// Dialog của Agent - giữ nguyên từ file cũ
let agentDialogCountdown;
function typeWriter(element, text, onComplete) {
    let i = 0;
    element.innerHTML = '';
    const cursor = '<span class="typing-cursor"></span>';
    element.innerHTML = cursor;
    function type() {
        if (i < text.length) {
            element.innerHTML = text.substring(0, i + 1) + cursor;
            i++;
            setTimeout(type, 16);
        } else {
            element.innerHTML = text;
            if (onComplete) onComplete();
        }
    }
    type();
}
export function showAgentDialog(details, memory, isAutoMode, onDialogClose) {
    const dialog = document.getElementById('agent-dialog');
    if (!dialog) return;
    const reasonEl = document.querySelector('#tab-content-reason p');
    if (reasonEl) typeWriter(reasonEl, details.observation + " " + details.reason  || "No reason provided.");
    const actionEl = document.getElementById('tab-content-action');
    if (actionEl) {
        const moveAction = details.action || {};
        let actionHtml = `<p class="font-semibold my-1">Move: ${moveAction.pos || 'N/A'} -> ${moveAction.way || 'N/A'}</p>`;
        actionHtml += `<div class="text-xs opacity-80 pl-2 border-l-2 border-slate-500 max-h-48 overflow-y-auto">`;
        if (details.steps) {
            details.steps.forEach(step => { actionHtml += `<div>${step}</div>`; });
        }
        actionHtml += `</div>`;
        actionEl.innerHTML = actionHtml;
    }
    const memoryEl = document.querySelector('#tab-content-memory ul');
    if (memoryEl) {
        memoryEl.innerHTML = '';
        if (memory && memory.length > 0) {
            memory.forEach(mem => {
                const li = document.createElement('li');
                li.textContent = mem;
                memoryEl.appendChild(li);
            });
        } else {
            memoryEl.innerHTML = '<li>No memories yet.</li>';
        }
    }
    toggleModal('agent-dialog', true);
    const minimizeIcon = document.getElementById('minimized-agent-icon');
    if (minimizeIcon) minimizeIcon.classList.add('hidden');
    const closeBtn = document.getElementById('close-agent-dialog');
    const countdownEl = document.getElementById('agent-countdown');
    const minimizeDialog = () => {
        toggleModal('agent-dialog', false);
        if (minimizeIcon) minimizeIcon.classList.remove('hidden');
    };
    if (closeBtn) closeBtn.onclick = minimizeDialog;
    const proceedWithMove = () => {
        clearInterval(agentDialogCountdown);
        toggleModal('agent-dialog', false);
        if (minimizeIcon) minimizeIcon.classList.add('hidden');
        if (onDialogClose) onDialogClose();
    };
    let count = 20;
    if (countdownEl) {
        countdownEl.textContent = `(Continuing in ${count}s)`;
        if (agentDialogCountdown) clearInterval(agentDialogCountdown);
        agentDialogCountdown = setInterval(() => {
            count--;
            countdownEl.textContent = `(Continuing in ${count}s)`;
            if (count <= 0) {
                proceedWithMove();
            }
        }, 1000);
    }
}
export function setupAgentDialog() {
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            const tab = button.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            document.querySelectorAll('.tab-content').forEach(content => content.classList.add('hidden'));
            const tabContent = document.getElementById(`tab-content-${tab}`);
            if (tabContent) tabContent.classList.remove('hidden');
        });
    });
    const minimizeIcon = document.getElementById('minimized-agent-icon');
    if (minimizeIcon) {
        minimizeIcon.addEventListener('click', () => {
            toggleModal('agent-dialog', true);
            minimizeIcon.classList.add('hidden');
        });
    }
}