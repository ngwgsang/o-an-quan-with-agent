import { api } from '../services/api.js';
import * as renderer from '../ui/renderer.js';

let gameState = {
    selectedPos: null,
    currentRound: 0,
    isAutoMode: false,
    autoMoveTimeout: null,
    lastApiData: null,
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
    gameState.lastApiData = data;
    gameState.currentRound = data.game_state.round;
    
    console.log("DEBUG: ", data);
    

    if (data.action_details) {
        renderer.addHistoryEntry(data.action_details, data.game_state.round, data.animation_events);
        
        // SỬA LỖI: Dựa vào cờ 'show_thinking_dialog' từ API trả về
        if (data.show_thinking_dialog) {
            const onDialogClose = () => {
                 if (data.animation_events) {
                    renderer.animateEvents(data.animation_events, data, updateUI);
                } else {
                    updateUI(data);
                }
            }
            renderer.showAgentDialog(data.action_details, data.action_details.memory_context.reverse(), gameState.isAutoMode, onDialogClose);
            return; // Dừng xử lý và chờ dialog đóng lại
        }
    }
    
    // Nếu không hiển thị dialog, tiếp tục cập nhật giao diện
    if (data.animation_events) {
        renderer.animateEvents(data.animation_events, data, updateUI);
    } else {
        updateUI(data);
    }
}

function updateUI(data, skipBoardRendering = false) {
    if (!data || !data.game_state) return;
    gameState.lastApiData = data;
    const { game_state, game_over, winner, next_turn, human_turn, available_pos } = data;

    if (!skipBoardRendering) {
        renderer.updateBoard(game_state.board);
    }
    renderer.updateScores(game_state.score.A, game_state.score.B);

    const moveBtn = document.getElementById('move-btn');
    const autoToggle = document.getElementById('auto-toggle');

    if (game_over) {
        renderer.updateStatus(`Game Over! Winner: ${winner}. (Round ${game_state.round})`);
        if (moveBtn) moveBtn.disabled = true;
        if (autoToggle) {
            autoToggle.checked = false;
            autoToggle.disabled = true;
        }
        gameState.isAutoMode = false;
        clearTimeout(gameState.autoMoveTimeout);
        renderer.setHumanInteraction(false);
    } else {
        renderer.updateStatus(`Round ${game_state.round} - Turn: Player ${next_turn}`);
        if (moveBtn) {
            moveBtn.disabled = human_turn === true || gameState.isAutoMode === true;
        }
        if (autoToggle) autoToggle.disabled = false;
        renderer.setHumanInteraction(human_turn, available_pos);
    }

    if (gameState.isAutoMode && !game_over && !human_turn) {
        clearTimeout(gameState.autoMoveTimeout);
        gameState.autoMoveTimeout = setTimeout(() => {
            gameHandlers.onAgentMove();
        }, 1000); 
    }
}


const getPersonaSelection = (playerNum) => {
    // Tên của input radio button sẽ là 'persona-player1' hoặc 'persona-player2'
    const selector = `input[name="persona-player${playerNum}"]:checked`;
    const selectedRadio = document.querySelector(selector);
    return selectedRadio ? selectedRadio.value : 'BALANCE'; // Giá trị mặc định phải là giá trị enum
};

export const gameHandlers = {
    onCellClick: (pos) => {
        if (gameState.isAutoMode) {
            const autoToggle = document.getElementById('auto-toggle');
            if (autoToggle) {
                autoToggle.checked = false;
                autoToggle.dispatchEvent(new Event('change'));
            }
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
        renderer.updateStatus('Thinking...');
        const data = await api.requestAgentMove(getEnabledRules());
        processApiResponse(data);
    },

    onReset: async () => {
        if (confirm('Are you sure you want to reset the game?')) {
            renderer.updateStatus('Resetting game...');
            document.getElementById('auto-toggle').checked = false;
            gameHandlers.onToggleAutoMode(false);
            
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
        
        document.getElementById('auto-toggle').checked = false;
        gameHandlers.onToggleAutoMode(false);
        const getPlayerSettings = (playerNum) => {
            const type = document.getElementById(`player${playerNum}`).value;
            if (type === 'human' || type === 'random_agent') {
                return { type: type };
            }
            const persona = getPersonaSelection(playerNum);
            // SỬA LỖI: Bổ sung 'thinkingMode' vào object gửi đi
            
            return {
                type: type,
                model: document.getElementById(`model-select-${playerNum}`)?.value,
                temperature: parseFloat(document.getElementById(`temperature-${playerNum}`).value),
                maxTokens: parseInt(document.getElementById(`max-tokens-value-${playerNum}`).value),
                topP: parseFloat(document.getElementById(`top-p-value-${playerNum}`).value),
                topK: parseInt(document.getElementById(`top-k-value-${playerNum}`).value),
                persona: persona,
                memSize: parseInt(document.getElementById(`mem-size-value-${playerNum}`).value),
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

    onToggleAutoMode: (enabled) => {
        gameState.isAutoMode = enabled;
        
        if (gameState.lastApiData) {
            updateUI(gameState.lastApiData);
        }

        if (!enabled) {
            clearTimeout(gameState.autoMoveTimeout);
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