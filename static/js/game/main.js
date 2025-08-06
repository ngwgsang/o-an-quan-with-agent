import { api } from '../services/api.js';
import * as renderer from '../ui/renderer.js';

let gameState = {
    selectedPos: null,
    currentRound: 0,
};

function getEnabledRules() {
    const rules = [];
    if (document.getElementById('rule-e1')?.checked) rules.push('E1');
    if (document.getElementById('rule-e2')?.checked) rules.push('E2');
    if (document.getElementById('rule-e3')?.checked) rules.push('E3');
    if (document.getElementById('rule-e4')?.checked) rules.push('E4');
    if (document.getElementById('rule-e5')?.checked) rules.push('E5');
    return rules;
}

function processApiResponse(data) {
    if (!data || !data.game_state) return;
    const { game_state, game_over, winner, next_turn, action_details, animation_events, human_turn, available_pos } = data;
    gameState.currentRound = game_state.round;

    if (action_details) {
        renderer.addHistoryEntry(action_details, game_state.round, animation_events);
    }
    
    if (animation_events && !human_turn) {
        // Nếu có animation, chạy nó trước, rồi mới cập nhật UI cuối cùng
        renderer.animateEvents(animation_events, data, updateUI);
    } else {
        // Nếu không có animation (ví dụ: lượt của người), cập nhật UI ngay lập tức
        updateUI(data);
    }
}

function updateUI(data, skipBoardRendering = false) {
    if (!data || !data.game_state) return;
    const { game_state, game_over, winner, next_turn, human_turn, available_pos } = data;

    if (!skipBoardRendering) {
        renderer.updateBoard(game_state.board);
    }
    renderer.updateScores(game_state.score.A, game_state.score.B);

    const moveBtn = document.getElementById('move-btn');
    if (game_over) {
        renderer.updateStatus(`Game Over! Winner: ${winner}. (Round ${game_state.round})`);
        if(moveBtn) moveBtn.disabled = true;
        renderer.setHumanInteraction(false);
    } else {
        renderer.updateStatus(`Round ${game_state.round} - Turn: Player ${next_turn}`);
        if(moveBtn) moveBtn.disabled = human_turn === true;
        if (human_turn) {
            renderer.setHumanInteraction(true, available_pos);
        }
    }
}

// Các hàm xử lý sự kiện sẽ được truyền cho events.js
export const gameHandlers = {
    onCellClick: (pos) => {
        gameState.selectedPos = pos;
        renderer.toggleModal('direction-modal', true);
    },

    onDirectionChoice: async (way) => {
        renderer.toggleModal('direction-modal', false);
        renderer.setHumanInteraction(false);
        renderer.updateStatus(`Moving from ${gameState.selectedPos}...`);
        const data = await api.sendHumanMove(gameState.selectedPos, way, getEnabledRules());
        processApiResponse(data);
    },

    onAgentMove: async () => {
        document.getElementById('move-btn').disabled = true;
        renderer.updateStatus('Thinking...');
        const data = await api.requestAgentMove(getEnabledRules());
        processApiResponse(data);
    },

    onReset: async () => {
        if (confirm('Are you sure you want to reset the game?')) {
            renderer.updateStatus('Resetting game...');
            const data = await api.resetGame();
            if (data) {
                document.getElementById('history-log').innerHTML = '';
                document.getElementById('modal-history-content').innerHTML = '';
                updateUI(data);
                alert('Game has been reset!');
            }
        }
    },

    onApplyConfig: async () => {
        if (gameState.currentRound > 0 && !confirm("Game sẽ bắt đầu lại nếu bạn thay đổi cài đặt. Bạn có muốn tiếp tục?")) {
            return;
        }
        
        const getPlayerSettings = (playerNum) => {
            const type = document.getElementById(`player${playerNum}`).value;
            return {
                type: type,
                model: type === 'agent' ? document.getElementById(`model-select-${playerNum}`)?.value : null,
                temperature: type === 'agent' ? parseFloat(document.getElementById(`temperature-value-${playerNum}`)?.value) : null,
                maxTokens: type === 'agent' ? parseInt(document.getElementById(`max-tokens-value-${playerNum}`)?.value) : null,
                topP: type === 'agent' ? parseFloat(document.getElementById(`top-p-value-${playerNum}`)?.value) : null,
                thinkingMode: type === 'agent' ? document.getElementById(`thinking-mode-${playerNum}`)?.checked : null,
            };
        };

        const settings = { player1: getPlayerSettings(1), player2: getPlayerSettings(2) };
        const response = await api.applySettings(settings);
        if (response) {
            alert(response.message);
            document.getElementById('history-log').innerHTML = '';
            document.getElementById('modal-history-content').innerHTML = '';
            updateUI(response);
            renderer.toggleSidebar(false); // Thu gọn sidebar sau khi apply
        }
    },
    
    onExportHistory: () => {
        const historyEntries = Array.from(document.getElementById('modal-history-content').querySelectorAll('div.p-2'));
        const jsonHistory = historyEntries.map(entry => ({
            roundInfo: entry.querySelector('span')?.textContent?.trim() || "",
            time: entry.querySelectorAll('span')?.[1]?.textContent?.trim() || "",
            move: entry.querySelector('p.font-semibold')?.textContent?.trim() || "",
            reason: entry.querySelector('p.text-xs')?.textContent?.trim() || "",
            details: Array.from(entry.querySelectorAll('.border-l-2 > div')).map(div => div.textContent.trim())
        }));

        const blob = new Blob([JSON.stringify(jsonHistory, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `game_history_round${gameState.currentRound}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
};

export async function initializeGame() {
    renderer.updateStatus('Fetching initial game state...');
    const data = await api.getGameState();
    if (data) {
        updateUI(data);
    }
}