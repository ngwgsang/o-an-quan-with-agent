export async function fetchAPI(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: { 'Content-Type': 'application/json' },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    try {
        const response = await fetch(endpoint, options);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching ${endpoint}:`, error);
        // Có thể thêm logic hiển thị lỗi cho người dùng ở đây
        return null;
    }
}

export const api = {
    getGameState: () => fetchAPI('/api/state'),
    requestAgentMove: (extended_rule) => fetchAPI('/api/move', 'POST', { extended_rule }),
    sendHumanMove: (pos, way, extended_rule) => fetchAPI('/api/human_move', 'POST', { pos, way, extended_rule }),
    resetGame: () => fetchAPI('/api/reset', 'POST'),
    applySettings: (settings) => fetchAPI('/api/settings', 'POST', settings),
};