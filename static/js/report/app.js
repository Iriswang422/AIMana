// 全局状态管理
const DashboardState = {
    currentPeriod: null,
    selectedProject: null,
    reports: [],

    async init() {
        await this.loadReports();
        this.bindEvents();
        if (this.reports.length > 0) {
            this.setPeriod(this.reports[0].period);
        }
    },

    async loadReports() {
        const result = await ReportAPI.listReports();
        if (result.success) {
            this.reports = result.reports;
            this.updatePeriodSelector();
            this.updateReportsTable();
        }
    },

    setPeriod(period) {
        this.currentPeriod = period;
        document.getElementById('period-selector').value = period;
        this.refreshDashboard();
    },

    setProject(project) {
        this.selectedProject = project;
        this.refreshCurrentTab();
    },

    async refreshDashboard() {
        if (!this.currentPeriod) return;
        const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
        await this.loadTabData(activeTab);
    },

    async refreshCurrentTab() {
        const activeTab = document.querySelector('.tab-btn.active').dataset.tab;
        await this.loadTabData(activeTab);
    },

    async loadTabData(tabName) {
        if (!this.currentPeriod) return;

        switch (tabName) {
            case 'summary':
                await this.loadSummary();
                break;
            case 'budget':
                await this.loadBudget();
                break;
            case 'projects':
                await this.loadProjects();
                break;
            case 'revenue':
                await this.loadRevenue();
                break;
            case 'cost':
                await this.loadCost();
                break;
            case 'labor':
                await this.loadLabor();
                break;
            case 'admin':
                await this.loadReports();
                break;
        }
    },

    async loadSummary() {
        const result = await ReportAPI.getSummary(this.currentPeriod);
        if (!result.success) return;

        this.renderKPICards(result.data.kpis);
        this.renderHighlights(result.data.highlights);
    },

    async loadBudget() {
        const result = await ReportAPI.getBudget(this.currentPeriod);
        if (!result.success) return;

        this.renderBudgetOverviewChart(result.data.overview);
        this.renderBudgetProjectsChart(result.data.projects);
        this.renderBudgetTable(result.data);
    },

    async loadProjects() {
        const result = await ReportAPI.getProjects(this.currentPeriod, this.selectedProject);
        if (!result.success) return;

        this.updateProjectFilter(result.data.projects);
        this.renderProjectRadarChart(result.data.projects);
        this.renderProjectsTable(result.data.projects);
    },

    async loadRevenue() {
        const result = await ReportAPI.getRevenue(this.currentPeriod, this.selectedProject);
        if (!result.success) return;

        this.renderRevenueTrendChart(result.data.revenue);
        this.renderCollectionHeatmap(result.data.revenue);
    },

    async loadCost() {
        const result = await ReportAPI.getCost(this.currentPeriod, this.selectedProject);
        if (!result.success) return;

        this.renderCostTreemap(result.data);
        this.renderServerCostChart(result.data.server_cost);
    },

    async loadLabor() {
        const result = await ReportAPI.getCost(this.currentPeriod, this.selectedProject);
        if (!result.success) return;

        this.renderHCChart(result.data.labor_cost);
        this.renderAvgCostChart(result.data.labor_cost);
    },

    renderKPICards(kpis) {
        const container = document.getElementById('kpi-grid');
        container.innerHTML = kpis.map(kpi => {
            const variance = kpi.budget ? ((kpi.actual - kpi.budget) / kpi.budget * 100).toFixed(1) : 0;
            const varianceClass = variance > 0 ? 'positive' : variance < 0 ? 'negative' : 'neutral';

            return `
                <div class="kpi-card">
                    <div class="kpi-label">${kpi.metric_name}</div>
                    <div class="kpi-value">${this.formatNumber(kpi.actual)} ${kpi.unit || ''}</div>
                    <div class="kpi-budget">预算: ${this.formatNumber(kpi.budget)}</div>
                    <div class="kpi-variance ${varianceClass}">
                        ${variance > 0 ? '+' : ''}${variance}%
                    </div>
                </div>
            `;
        }).join('');
    },

    renderHighlights(highlights) {
        const container = document.getElementById('highlights-list');
        container.innerHTML = highlights.map(h => `
            <div class="highlight-item priority-${h.priority}">
                <span class="priority-badge">${this.getPriorityText(h.priority)}</span>
                <span class="highlight-text">${h.text}</span>
            </div>
        `).join('');
    },

    renderBudgetOverviewChart(overview) {
        const chart = echarts.init(document.getElementById('budget-overview-chart'));
        const metrics = Object.keys(overview);

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['实际', '预算'] },
            xAxis: { type: 'category', data: metrics },
            yAxis: { type: 'value' },
            series: [
                {
                    name: '实际',
                    type: 'bar',
                    data: metrics.map(m => overview[m].actual)
                },
                {
                    name: '预算',
                    type: 'bar',
                    data: metrics.map(m => overview[m].budget)
                }
            ]
        });
    },

    renderBudgetProjectsChart(projects) {
        const chart = echarts.init(document.getElementById('budget-projects-chart'));
        const projectNames = projects.map(p => p.project);

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['收入实际', '收入预算', '成本实际', '成本预算'] },
            xAxis: { type: 'category', data: projectNames },
            yAxis: { type: 'value' },
            series: [
                {
                    name: '收入实际',
                    type: 'bar',
                    data: projects.map(p => p.revenue_actual)
                },
                {
                    name: '收入预算',
                    type: 'bar',
                    data: projects.map(p => p.revenue_budget)
                },
                {
                    name: '成本实际',
                    type: 'bar',
                    data: projects.map(p => p.cost_actual)
                },
                {
                    name: '成本预算',
                    type: 'bar',
                    data: projects.map(p => p.cost_budget)
                }
            ]
        });
    },

    renderBudgetTable(data) {
        const tbody = document.querySelector('#budget-table tbody');
        const rows = [];

        // 总体KPI
        Object.keys(data.overview).forEach(metric => {
            const kpi = data.overview[metric];
            const variance = kpi.actual - kpi.budget;
            const achievement = kpi.budget ? (kpi.actual / kpi.budget * 100).toFixed(1) : 0;

            rows.push(`
                <tr>
                    <td>${metric}</td>
                    <td>${this.formatNumber(kpi.actual)}</td>
                    <td>${this.formatNumber(kpi.budget)}</td>
                    <td class="${variance >= 0 ? 'positive' : 'negative'}">
                        ${variance >= 0 ? '+' : ''}${this.formatNumber(variance)}
                    </td>
                    <td>${achievement}%</td>
                </tr>
            `);
        });

        tbody.innerHTML = rows.join('');
    },

    renderProjectRadarChart(projects) {
        const chart = echarts.init(document.getElementById('project-radar-chart'));

        chart.setOption({
            tooltip: {},
            radar: {
                indicator: [
                    { name: '收入达成', max: 150 },
                    { name: '成本控制', max: 150 },
                    { name: 'HC利用率', max: 100 }
                ]
            },
            series: [{
                type: 'radar',
                data: projects.map(p => ({
                    name: p.project,
                    value: [
                        p.revenue_achievement ? p.revenue_achievement * 100 : 0,
                        p.cost_budget ? (1 - (p.cost_actual - p.cost_budget) / p.cost_budget) * 100 : 0,
                        80
                    ]
                }))
            }]
        });
    },

    renderProjectsTable(projects) {
        const tbody = document.querySelector('#projects-table tbody');
        tbody.innerHTML = projects.map(p => `
            <tr>
                <td>${p.project}</td>
                <td>${this.formatNumber(p.revenue_actual)}</td>
                <td>${this.formatNumber(p.revenue_budget)}</td>
                <td>${p.revenue_achievement ? (p.revenue_achievement * 100).toFixed(1) : 0}%</td>
                <td>${this.formatNumber(p.cost_actual)}</td>
                <td>${this.formatNumber(p.cost_budget)}</td>
                <td>${p.headcount || 0}</td>
            </tr>
        `).join('');
    },

    renderRevenueTrendChart(revenue) {
        const chart = echarts.init(document.getElementById('revenue-trend-chart'));
        const months = [...new Set(revenue.map(r => r.month))].sort();
        const projects = [...new Set(revenue.map(r => r.project))];

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: projects },
            xAxis: { type: 'category', data: months },
            yAxis: { type: 'value' },
            series: projects.map(project => ({
                name: project,
                type: 'line',
                stack: '总量',
                areaStyle: {},
                data: months.map(month => {
                    const item = revenue.find(r => r.project === project && r.month === month);
                    return item ? item.revenue_confirmed : 0;
                })
            }))
        });
    },

    renderCollectionHeatmap(revenue) {
        const chart = echarts.init(document.getElementById('collection-heatmap'));
        const months = [...new Set(revenue.map(r => r.month))].sort();
        const projects = [...new Set(revenue.map(r => r.project))];

        const data = [];
        revenue.forEach(r => {
            const x = months.indexOf(r.month);
            const y = projects.indexOf(r.project);
            data.push([x, y, r.collection_rate ? r.collection_rate * 100 : 0]);
        });

        chart.setOption({
            tooltip: {
                position: 'top',
                formatter: p => `${projects[p.value[1]]} ${months[p.value[0]]}<br/>实收率: ${p.value[2].toFixed(1)}%`
            },
            xAxis: { type: 'category', data: months },
            yAxis: { type: 'category', data: projects },
            visualMap: {
                min: 70,
                max: 100,
                calculable: true,
                orient: 'horizontal',
                left: 'center',
                bottom: '0%'
            },
            series: [{
                type: 'heatmap',
                data: data,
                label: { show: true }
            }]
        });
    },

    renderCostTreemap(data) {
        const chart = echarts.init(document.getElementById('cost-treemap'));

        chart.setOption({
            tooltip: {},
            series: [{
                type: 'treemap',
                data: [
                    {
                        name: '服务器费用',
                        value: data.server_cost.reduce((sum, s) => sum + (s.server_cost || 0), 0)
                    },
                    {
                        name: '人力成本',
                        value: data.labor_cost.reduce((sum, l) => sum + (l.hc_actual * l.avg_cost_per_head || 0), 0)
                    }
                ]
            }]
        });
    },

    renderServerCostChart(serverCost) {
        const chart = echarts.init(document.getElementById('server-cost-chart'));
        const months = [...new Set(serverCost.map(s => s.month))].sort();
        const projects = [...new Set(serverCost.map(s => s.project))];

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: [...projects, '预算'] },
            xAxis: { type: 'category', data: months },
            yAxis: { type: 'value' },
            series: [
                ...projects.map(project => ({
                    name: project,
                    type: 'line',
                    data: months.map(month => {
                        const item = serverCost.find(s => s.project === project && s.month === month);
                        return item ? item.server_cost : 0;
                    })
                })),
                {
                    name: '预算',
                    type: 'line',
                    lineStyle: { type: 'dashed' },
                    data: months.map(month => {
                        const item = serverCost.find(s => s.month === month);
                        return item ? item.budget : 0;
                    })
                }
            ]
        });
    },

    renderHCChart(laborCost) {
        const chart = echarts.init(document.getElementById('hc-chart'));
        const months = [...new Set(laborCost.map(l => l.month))].sort();
        const projects = [...new Set(laborCost.map(l => l.project))];

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: projects.map(p => `${p} 实际`, ...projects.map(p => `${p} 预算`)) },
            xAxis: { type: 'category', data: months },
            yAxis: { type: 'value' },
            series: [
                ...projects.map(project => ({
                    name: `${project} 实际`,
                    type: 'bar',
                    data: months.map(month => {
                        const item = laborCost.find(l => l.project === project && l.month === month);
                        return item ? item.hc_actual : 0;
                    })
                })),
                ...projects.map(project => ({
                    name: `${project} 预算`,
                    type: 'bar',
                    data: months.map(month => {
                        const item = laborCost.find(l => l.project === project && l.month === month);
                        return item ? item.hc_budget : 0;
                    })
                }))
            ]
        });
    },

    renderAvgCostChart(laborCost) {
        const chart = echarts.init(document.getElementById('avg-cost-chart'));
        const months = [...new Set(laborCost.map(l => l.month))].sort();
        const projects = [...new Set(laborCost.map(l => l.project))];

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: projects },
            xAxis: { type: 'category', data: months },
            yAxis: { type: 'value' },
            series: projects.map(project => ({
                name: project,
                type: 'line',
                data: months.map(month => {
                    const item = laborCost.find(l => l.project === project && l.month === month);
                    return item ? item.avg_cost_per_head : 0;
                })
            }))
        });
    },

    updatePeriodSelector() {
        const select = document.getElementById('period-selector');
        select.innerHTML = '<option value="">选择期间...</option>' +
            this.reports.map(r => `<option value="${r.period}">${r.period}</option>`).join('');
    },

    updateProjectFilter(projects) {
        const select = document.getElementById('project-filter');
        const projectNames = [...new Set(projects.map(p => p.project))];
        select.innerHTML = '<option value="">全部项目</option>' +
            projectNames.map(name => `<option value="${name}">${name}</option>`).join('');
    },

    updateReportsTable() {
        const tbody = document.querySelector('#reports-table tbody');
        tbody.innerHTML = this.reports.map(r => `
            <tr>
                <td>${r.period}</td>
                <td>${r.title}</td>
                <td><span class="status-badge status-${r.status}">${r.status === 'published' ? '已发布' : '草稿'}</span></td>
                <td>${new Date(r.created_at).toLocaleString('zh-CN')}</td>
                <td>
                    <button class="btn btn-sm" onclick="DashboardApp.publishReport('${r.period}')">
                        ${r.status === 'published' ? '取消发布' : '发布'}
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="DashboardApp.deleteReport('${r.period}')">
                        删除
                    </button>
                </td>
            </tr>
        `).join('');
    },

    async publishReport(period) {
        const report = this.reports.find(r => r.period === period);
        if (!report) return;

        if (report.status === 'published') {
            await ReportAPI.unpublishReport(period);
        } else {
            await ReportAPI.publishReport(period);
        }
        await this.loadReports();
    },

    async deleteReport(period) {
        if (!confirm('确定要删除这个报告吗？')) return;

        await ReportAPI.deleteReport(period);
        await this.loadReports();
    },

    bindEvents() {
        // 期间选择
        document.getElementById('period-selector').addEventListener('change', (e) => {
            if (e.target.value) this.setPeriod(e.target.value);
        });

        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

                e.target.classList.add('active');
                document.getElementById(`${e.target.dataset.tab}-tab`).classList.add('active');

                this.loadTabData(e.target.dataset.tab);
            });
        });

        // 项目筛选
        document.getElementById('project-filter').addEventListener('change', (e) => {
            this.setProject(e.target.value || null);
        });

        // 刷新按钮
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.refreshDashboard();
        });

        // 上传按钮
        document.getElementById('upload-btn').addEventListener('click', () => {
            this.handleUpload();
        });
    },

    async handleUpload() {
        const fileInput = document.getElementById('report-file');
        const periodInput = document.getElementById('report-period');
        const titleInput = document.getElementById('report-title');
        const statusDiv = document.getElementById('upload-status');

        if (!fileInput.files.length) {
            statusDiv.innerHTML = '<div class="error">请选择文件</div>';
            return;
        }

        if (!periodInput.value) {
            statusDiv.innerHTML = '<div class="error">请填写期间</div>';
            return;
        }

        statusDiv.innerHTML = '<div class="info">上传中...</div>';

        try {
            const result = await ReportAPI.uploadReport(
                fileInput.files[0],
                periodInput.value,
                titleInput.value
            );

            if (result.success) {
                statusDiv.innerHTML = '<div class="success">上传成功！</div>';
                fileInput.value = '';
                periodInput.value = '';
                titleInput.value = '';

                await this.loadReports();
                this.setPeriod(result.report.period);
            } else {
                statusDiv.innerHTML = `<div class="error">上传失败：${result.error}</div>`;
            }
        } catch (e) {
            statusDiv.innerHTML = `<div class="error">上传失败：${e.message}</div>`;
        }
    },

    formatNumber(num) {
        if (num === null || num === undefined) return '0';
        return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
    },

    getPriorityText(priority) {
        const map = { high: '高', medium: '中', low: '低' };
        return map[priority] || priority;
    }
};

// 初始化
const DashboardApp = DashboardState;
document.addEventListener('DOMContentLoaded', () => {
    DashboardApp.init();
});
