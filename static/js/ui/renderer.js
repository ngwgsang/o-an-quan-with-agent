const sleep = ms => new Promise(res => setTimeout(res, ms));

// --- PHẦN SỬA LỖI: KHÔI PHỤC LOGIC VỊ TRÍ NGẪU NHIÊN ---

function createBubbleElement(piece) {
    const bubble = document.createElement('div');
    // Các class này sẽ được định nghĩa trong dashboard.html để có position: absolute
    const pieceType = piece.startsWith('p') ? 'peasant' : 'mandarin';
    const team = piece.endsWith('_a') ? 'bubble-a' : 'bubble-b';
    bubble.className = `bubble ${pieceType} ${team}`;
    bubble.textContent = pieceType === 'mandarin' ? '🧙‍♂️' : '🧑‍';
    return bubble;
}

/**
 * Thêm một quân cờ vào ô với vị trí ngẫu nhiên.
 * @param {HTMLElement} cellElement - Ô để thêm quân cờ vào.
 * @param {string} piece - Tên của quân cờ (ví dụ: 'peasant_a').
 */
function addBubbleToCell(cellElement, piece) {
    const bubble = createBubbleElement(piece);
    const size = piece.startsWith('p') ? 30 : 60; // Kích thước của quân cờ
    const padding = 5; // Khoảng đệm an toàn từ mép ô

    // Tính toán vị trí ngẫu nhiên cho left và top
    // Điều này đảm bảo quân cờ nằm hoàn toàn bên trong ô
    const randomLeft = padding + Math.random() * (cellElement.clientWidth - size - padding * 2);
    const randomTop = padding + Math.random() * (cellElement.clientHeight - size - padding * 2);

    bubble.style.left = `${randomLeft}px`;
    bubble.style.top = `${randomTop}px`;
    
    cellElement.appendChild(bubble);
}

/**
 * Vẽ lại toàn bộ quân cờ trong một ô.
 * @param {HTMLElement} cellElement - Ô cần vẽ lại.
 * @param {string[]} pieces - Mảng các quân cờ trong ô đó.
 */
function renderBubbles(cellElement, pieces) {
    // Xóa hết các quân cờ cũ trước khi vẽ lại
    cellElement.innerHTML = '';
    pieces.forEach(piece => addBubbleToCell(cellElement, piece));
}

// --- KẾT THÚC PHẦN SỬA LỖI ---


let agentDialogCountdown;

function typeWriter(element, text, onComplete) {
    let i = 0;
    element.innerHTML = ''; // Clear previous text
    const cursor = '<span class="typing-cursor"></span>';
    element.innerHTML = cursor;

    function type() {
        if (i < text.length) {
            element.innerHTML = text.substring(0, i + 1) + cursor;
            i++;
            setTimeout(type, 50); // Adjust typing speed here
        } else {
            // Remove cursor after typing is done
            element.innerHTML = text;
            if (onComplete) onComplete();
        }
    }
    type();
}


export function showAgentDialog(details, memory, isAutoMode, onDialogClose) {
    const dialog = document.getElementById('agent-dialog');
    if (!dialog) return;

    // Populate Reason Tab
    const reasonEl = document.querySelector('#tab-content-reason p');
    typeWriter(reasonEl, details.reason || "No reason provided.");

    // Populate Action Tab
    const actionEl = document.getElementById('tab-content-action');
    const moveAction = details.action || {};
    let actionHtml = `<p class="font-semibold my-1">Move: ${moveAction.pos || 'N/A'} -> ${moveAction.way || 'N/A'}</p>`;
    actionHtml += `<div class="text-xs opacity-80 pl-2 border-l-2 border-slate-500 max-h-48 overflow-y-auto">`;
    if (details.steps) {
        details.steps.forEach(step => { actionHtml += `<div>${step}</div>`; });
    }
    actionHtml += `</div>`;
    actionEl.innerHTML = actionHtml;

    // Populate Memory Tab
    const memoryEl = document.querySelector('#tab-content-memory ul');
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


    toggleModal('agent-dialog', true);
    document.getElementById('minimized-agent-icon').classList.add('hidden');


    const closeBtn = document.getElementById('close-agent-dialog');
    const countdownEl = document.getElementById('agent-countdown');

    const closeDialog = () => {
        clearInterval(agentDialogCountdown);
        toggleModal('agent-dialog', false);
        document.getElementById('minimized-agent-icon').classList.remove('hidden');
        if (onDialogClose) onDialogClose();
    }

    closeBtn.onclick = closeDialog;


    if (isAutoMode) {
        let count = 10;
        countdownEl.textContent = `(Auto-closing in ${count}s)`;
        agentDialogCountdown = setInterval(() => {
            count--;
            countdownEl.textContent = `(Auto-closing in ${count}s)`;
            if (count <= 0) {
                closeDialog();
            }
        }, 1000);
    } else {
        countdownEl.textContent = '';
    }
}


export function setupAgentDialog() {
    // Tab switching logic
    document.querySelectorAll('.tab-btn').forEach(button => {
        button.addEventListener('click', () => {
            const tab = button.dataset.tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            document.getElementById(`tab-content-${tab}`).classList.remove('hidden');
        });
    });

    // Restore dialog from minimized icon
    document.getElementById('minimized-agent-icon').addEventListener('click', () => {
        toggleModal('agent-dialog', true);
        document.getElementById('minimized-agent-icon').classList.add('hidden');
    });

}

function getElementCenter(el) {
    const rect = el.getBoundingClientRect();
    return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

async function animateSingleDrop(fromPos, toPos, piece) {
    const fromCell = document.getElementById(fromPos);
    const toCell = document.getElementById(toPos);
    if (!fromCell || !toCell) return;

    const bubbleToRemove = fromCell.querySelector('.bubble');
    let startRect;

    if (bubbleToRemove) {
        startRect = bubbleToRemove.getBoundingClientRect();
        fromCell.removeChild(bubbleToRemove);
    } else {
        const startCenter = getElementCenter(fromCell);
        startRect = { left: startCenter.x, top: startCenter.y, width: 0, height: 0 };
    }

    const endCenter = getElementCenter(toCell);
    const flyingBubble = createBubbleElement(piece);
    flyingBubble.classList.add('flying-bubble');
    document.body.appendChild(flyingBubble);

    flyingBubble.style.left = `${startRect.left}px`;
    flyingBubble.style.top = `${startRect.top}px`;

    await sleep(10);

    flyingBubble.style.left = `${endCenter.x - flyingBubble.offsetWidth / 2}px`;
    flyingBubble.style.top = `${endCenter.y - flyingBubble.offsetHeight / 2}px`;

    await sleep(250);
    document.body.removeChild(flyingBubble);
    addBubbleToCell(toCell, piece);
}

async function animateCapture(fromPos, team) {
    const fromCell = document.getElementById(fromPos);
    const scoreEl = document.getElementById(team === 'A' ? 'score-a' : 'score-b');
    
    fromCell.classList.add('ring-4', 'ring-red-500', 'transition-all', 'duration-500');
    scoreEl.classList.add('scale-150', 'text-yellow-400', 'transition-all', 'duration-300');
    
    fromCell.innerHTML = '';

    await sleep(500);

    fromCell.classList.remove('ring-4', 'ring-red-500');
    scoreEl.classList.remove('scale-150', 'text-yellow-400');
}

export async function animateEvents(events, finalState, onComplete) {
    document.getElementById('move-btn').disabled = true;
    document.getElementById('reset-btn').disabled = true;
    document.getElementById('apply-config').disabled = true;

    let lastHighlightedCell = null;
    let currentPickupPos = null;

    for (const event of events) {
        switch(event.type) {
            case 'pickup':
                if (lastHighlightedCell) lastHighlightedCell.classList.remove('ring-4', 'ring-yellow-500');
                currentPickupPos = event.pos;
                const pickupCell = document.getElementById(event.pos);
                if (pickupCell) {
                    pickupCell.classList.add('ring-4', 'ring-yellow-500');
                    lastHighlightedCell = pickupCell;
                    await sleep(400);
                }
                break;
            case 'drop':
                await animateSingleDrop(currentPickupPos, event.to_pos, event.piece);
                break;
            case 'capture':
                await animateCapture(event.pos, event.team);
                break;
            case 'score_update':
                document.getElementById('score-a').textContent = event.score.A;
                document.getElementById('score-b').textContent = event.score.B;
                await sleep(300);
                break;
            case 'game_over':
                await sleep(500);
                alert(event.message);
                break;
        }
    }
    
    document.getElementById('reset-btn').disabled = false;
    document.getElementById('apply-config').disabled = false;
    
    if (onComplete) onComplete(finalState, true);
}

export function updateStatus(message) {
    document.getElementById('game-status').textContent = message;
}

export function addHistoryEntry(actionDetails, round, animationEvents) {
    const historyLog = document.getElementById('history-log');
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

export function updateBoard(boardState) {
    Object.keys(boardState).forEach(pos => {
        const cell = document.getElementById(pos);
        if (cell) {
            renderBubbles(cell, boardState[pos]);
            cell.classList.remove('ring-4', 'ring-offset-2', 'ring-purple-500', 'ring-yellow-500', 'ring-red-500');
        }
    });
}

export function updateScores(scoreA, scoreB) {
    document.getElementById('score-a').textContent = scoreA;
    document.getElementById('score-b').textContent = scoreB;
}

export function setHumanInteraction(enable, availablePos = []) {
    document.getElementById('game_board').classList.toggle('human-turn', enable);
    document.querySelectorAll('.game-cell').forEach(cell => {
        cell.classList.remove('selectable');
        cell.onclick = null;
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

export function toggleModal(modalId, show) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.toggle('hidden', !show);
        if (modalId === 'history-modal' && show) {
            document.getElementById('modal-history-content').innerHTML = document.getElementById('history-log').innerHTML;
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