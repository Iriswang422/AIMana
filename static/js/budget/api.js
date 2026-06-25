// 预算API封装
const BudgetAPI = {
    async getTree() {
        const response = await fetch('/api/budget/tree');
        return response.json();
    },

    async addOwner(name, feishuGroup = null) {
        const response = await fetch('/api/budget/owner', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, feishu_group: feishuGroup })
        });
        return response.json();
    },

    async addCategory(ownerId, name) {
        const response = await fetch('/api/budget/category', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ owner_id: ownerId, name })
        });
        return response.json();
    },

    async addItem(categoryId, itemName, originalBudget = 0, currentBudget = 0) {
        const response = await fetch('/api/budget/item', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category_id: categoryId,
                item_name: itemName,
                original_budget: originalBudget,
                current_budget: currentBudget
            })
        });
        return response.json();
    },

    async updateItem(itemId, currentBudget, changedBy = null) {
        const response = await fetch(`/api/budget/item/${itemId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_budget: currentBudget, changed_by: changedBy })
        });
        return response.json();
    },

    async uploadActuals(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/budget/actuals/upload', {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    async previewUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/budget/preview-upload', {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    async getActuals(itemId) {
        const response = await fetch(`/api/budget/actuals/${itemId}`);
        return response.json();
    },

    async updateActual(itemId, month, actualAmount, reason = null) {
        const response = await fetch(`/api/budget/actuals/${itemId}/${month}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ actual_amount: actualAmount, reason })
        });
        return response.json();
    },

    async getAnalysis(month = null, riskLevel = null) {
        const params = new URLSearchParams();
        if (month) params.append('month', month);
        if (riskLevel) params.append('level', riskLevel);

        const response = await fetch(`/api/budget/analysis?${params}`);
        return response.json();
    },

    async getRiskSummary() {
        const response = await fetch('/api/budget/risk-summary');
        return response.json();
    },

    async getRiskItems(level = null) {
        const params = level ? `?level=${level}` : '';
        const response = await fetch(`/api/budget/risk-items${params}`);
        return response.json();
    },

    async getRiskRules() {
        const response = await fetch('/api/budget/risk-rules');
        return response.json();
    },

    async updateRiskRules(rules) {
        const response = await fetch('/api/budget/risk-rules', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ rules })
        });
        return response.json();
    },

    async getChangeLog(itemId = null) {
        const params = itemId ? `?item_id=${itemId}` : '';
        const response = await fetch(`/api/budget/change-log${params}`);
        return response.json();
    },

    async getPermissions() {
        const response = await fetch('/api/budget/permissions');
        return response.json();
    },

    async addPermission(userId, role = 'viewer', ownerId = null, feishuGroup = null) {
        const response = await fetch('/api/budget/permissions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                role,
                owner_id: ownerId,
                feishu_group: feishuGroup
            })
        });
        return response.json();
    },

    async initSample() {
        const response = await fetch('/api/budget/init-sample', { method: 'POST' });
        return response.json();
    }
};
