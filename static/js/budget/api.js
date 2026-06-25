const BudgetAPI = {
    async getBudgetData(params) {
        const qs = new URLSearchParams(params || {}).toString();
        const res = await fetch(`/api/budget/budget-data?${qs}`);
        return res.json();
    },

    async getComparisonData(params) {
        const qs = new URLSearchParams(params || {}).toString();
        const res = await fetch(`/api/budget/comparison-data?${qs}`);
        return res.json();
    },

    async getActualsData(params) {
        const qs = new URLSearchParams(params || {}).toString();
        const res = await fetch(`/api/budget/actuals-data?${qs}`);
        return res.json();
    },

    async getFilterOptions() {
        const res = await fetch('/api/budget/filter-options');
        return res.json();
    },

    async getRiskSummary() {
        const res = await fetch('/api/budget/risk-summary');
        return res.json();
    },

    async importExcel(file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/budget/import-excel', { method: 'POST', body: formData });
        return res.json();
    },

    async previewImport(file) {
        const formData = new FormData();
        formData.append('file', file);
        const res = await fetch('/api/budget/import-preview', { method: 'POST', body: formData });
        return res.json();
    },

    async updateBudget(item_id, month, amount, changed_by) {
        const res = await fetch(`/api/budget/item/${item_id}/budget`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, amount, changed_by })
        });
        return res.json();
    },

    async updateActual(item_id, month, amount, reason, changed_by) {
        const res = await fetch(`/api/budget/item/${item_id}/actual`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, amount, reason, changed_by })
        });
        return res.json();
    },

    async updateReason(item_id, month, reason) {
        const res = await fetch(`/api/budget/item/${item_id}/reason`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, reason })
        });
        return res.json();
    },

    async updateVarianceNote(item_id, month, note, updated_by) {
        const res = await fetch(`/api/budget/item/${item_id}/note`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ month, note, updated_by })
        });
        return res.json();
    },

    async getRiskRules() {
        const res = await fetch('/api/budget/risk-rules');
        return res.json();
    },

    async getChangeLog(item_id) {
        const qs = item_id ? `?item_id=${item_id}` : '';
        const res = await fetch(`/api/budget/change-log${qs}`);
        return res.json();
    }
};
