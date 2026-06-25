// API封装
const ReportAPI = {
    async listReports(status = null) {
        const params = status ? `?status=${status}` : '';
        const response = await fetch(`/api/report/list${params}`);
        return response.json();
    },

    async uploadReport(file, period, title = '') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('period', period);
        if (title) formData.append('title', title);

        const response = await fetch('/api/report/upload', {
            method: 'POST',
            body: formData
        });
        return response.json();
    },

    async getSummary(period) {
        const response = await fetch(`/api/report/${period}/summary`);
        return response.json();
    },

    async getBudget(period) {
        const response = await fetch(`/api/report/${period}/budget`);
        return response.json();
    },

    async getProjects(period, project = null) {
        const params = project ? `?project=${project}` : '';
        const response = await fetch(`/api/report/${period}/projects${params}`);
        return response.json();
    },

    async getProjectDetail(period, projectName) {
        const response = await fetch(`/api/report/${period}/project/${projectName}`);
        return response.json();
    },

    async getRevenue(period, project = null) {
        const params = project ? `?project=${project}` : '';
        const response = await fetch(`/api/report/${period}/revenue${params}`);
        return response.json();
    },

    async getCost(period, project = null) {
        const params = project ? `?project=${project}` : '';
        const response = await fetch(`/api/report/${period}/cost${params}`);
        return response.json();
    },

    async getContingency(period) {
        const response = await fetch(`/api/report/${period}/contingency`);
        return response.json();
    },

    async comparePeriods(period1, period2) {
        const response = await fetch(`/api/report/compare?from=${period1}&to=${period2}`);
        return response.json();
    },

    async publishReport(period) {
        const response = await fetch(`/api/report/${period}/publish`, {
            method: 'POST'
        });
        return response.json();
    },

    async unpublishReport(period) {
        const response = await fetch(`/api/report/${period}/unpublish`, {
            method: 'POST'
        });
        return response.json();
    },

    async deleteReport(period) {
        const response = await fetch(`/api/report/${period}/delete`, {
            method: 'DELETE'
        });
        return response.json();
    }
};
