import { api } from '../services/api.js';
import * as renderer from '../ui/renderer.js';

let gameState = {
    selectedPos: null,
    currentRound: 0,
    isAutoMode: false, // Thêm trạng thái cho chế độ Auto
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
        
        // Show agent dialog if it's an agent's move
        if (!human_turn) {
            const onDialogClose = () => {
                 if (animation_events) {
                    renderer.animateEvents(animation_events, data, updateUI);
                } else {
                    updateUI(data);
                }
            }
            renderer.showAgentDialog(action_details, data.thoughts, gameState.isAutoMode, onDialogClose);
            return; // Stop further processing until dialog is closed
        }
    }
    
    // This part will now be called from the onDialogClose callback for agent moves
    if (animation_events && !human_turn) {
        // This logic is moved to the onDialogClose callback
    } else {
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
        renderer.setHumanInteraction(human_turn, available_pos);
    }

    // Logic tự động click nút Move
    if (gameState.isAutoMode && !game_over && !human_turn) {
        setTimeout(() => {
            document.getElementById('move-btn')?.click();
        }, 1000); // Đợi 1 giây trước khi đi nước tiếp theo
    }
}

export const gameHandlers = {
    onCellClick: (pos) => {
        // Tự động tắt chế độ auto nếu người dùng tương tác
        if (gameState.isAutoMode) {
            document.getElementById('auto-toggle').checked = false;
            gameState.isAutoMode = false;
        }
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
        const moveBtn = document.getElementById('move-btn');
        if (moveBtn) moveBtn.disabled = true;
        renderer.updateStatus('Thinking...');
        const data = await api.requestAgentMove(getEnabledRules());
        processApiResponse(data);
    },

    onReset: async () => {
        if (confirm('Are you sure you want to reset the game?')) {
            renderer.updateStatus('Resetting game...');
            // Tắt chế độ Auto khi reset
            document.getElementById('auto-toggle').checked = false;
            gameState.isAutoMode = false;
            
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
        
        // Tắt chế độ Auto khi áp dụng cài đặt mới
        document.getElementById('auto-toggle').checked = false;
        gameState.isAutoMode = false;

        const getPlayerSettings = (playerNum) => {
            const type = document.getElementById(`player${playerNum}`).value;
            if (type === 'human' || type === 'random_agent') {
                return { type: type };
            }
            return {
                type: type,
                model: document.getElementById(`model-select-${playerNum}`)?.value,
                temperature: parseFloat(document.getElementById(`temperature-1`).value),
                maxTokens: parseInt(document.getElementById(`max-tokens-1`).value),
                topP: parseFloat(document.getElementById(`top-p-1`).value),
                topK: parseInt(document.getElementById(`top-k-1`).value),
            };
        };

        const settings = { player1: getPlayerSettings(1), player2: getPlayerSettings(2) };
        const response = await api.applySettings(settings);
        if (response) {
            alert(response.message);
            document.getElementById('history-log').innerHTML = '';
            document.getElementById('modal-history-content').innerHTML = '';
            updateUI(response);
            renderer.toggleSidebar(false);
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
    },

    // Thêm handler cho nút Auto
    onToggleAutoMode: (enabled) => {
        gameState.isAutoMode = enabled;
        // Nếu bật auto và đến lượt agent, bắt đầu đi
        const moveBtn = document.getElementById('move-btn');
        if (enabled && moveBtn && !moveBtn.disabled) {
            gameHandlers.onAgentMove();
        }
    }
};

async function populateEndpoints() {
    const endpoints = await api.getEndpoints(); 
    if (endpoints) {
        const select1 = document.getElementById('model-select-1');
        const select2 = document.getElementById('model-select-2');
        select1.innerHTML = '';
        select2.innerHTML = '';
        endpoints.forEach(endpoint => {
            const option1 = new Option(endpoint.name, endpoint.endpoint);
            const option2 = new Option(endpoint.name, endpoint.endpoint);
            select1.add(option1);
            select2.add(option2);
        });
    }
}

export async function initializeGame() {
    renderer.updateStatus('Fetching initial game state...');
    await populateEndpoints();
    const data = await api.getGameState();
    if (data) {
        updateUI(data);
    }
}