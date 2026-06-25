const BudgetApp = {
    currentTab: 'budget',
    filters: { project: '', tag: '', owner: '' },
    data: [],

    init() {
        this.bindEvents();
        this.loadFilterOptions();
        this.loadTabData();
    },

    bindEvents() {
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });

        const importBtn = document.getElementById('import-btn');
        if (importBtn) importBtn.addEventListener('click', () => {
            document.getElementById('import-modal').style.display = 'flex';
        });

        const refreshBtn = document.getElementById('refresh-btn');
        if (refreshBtn) refreshBtn.addEventListener('click', () => this.loadTabData());

        ['project', 'tag', 'owner'].forEach(f => {
            const el = document.getElementById(`filter-${f}`);
            if (el) el.addEventListener('change', () => {
                this.filters[f] = el.value;
                this.loadTabData();
            });
        });

        const previewBtn = document.getElementById('preview-btn');
        if (previewBtn) previewBtn.addEventListener('click', () => this.handlePreview());

        const confirmBtn = document.getElementById('confirm-import-btn');
        if (confirmBtn) confirmBtn.addEventListener('click', () => this.handleImport());

        const saveReasonBtn = document.getElementById('save-reason-btn');
        if (saveReasonBtn) saveReasonBtn.addEventListener('click', () => this.saveReason());
    },

    switchTab(tab) {
        this.currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `${tab}-tab`));
        document.getElementById('risk-summary').style.display = tab === 'comparison' ? 'flex' : 'none';
        this.loadTabData();
    },

    async loadFilterOptions() {
        const res = await BudgetAPI.getFilterOptions();
        if (!res.success) return;
        const opts = res.data;
        this._populateSelect('filter-project', opts.projects || []);
        this._populateSelect('filter-tag', opts.tags || []);
        this._populateSelect('filter-owner', opts.owners || []);
    },

    _populateSelect(id, values) {
        const sel = document.getElementById(id);
        if (!sel) return;
        const current = sel.value;
        const label = sel.options[0].textContent;
        sel.innerHTML = `<option value="">${label}</option>`;
        values.forEach(v => {
            const opt = document.createElement('option');
            opt.value = v;
            opt.textContent = v;
            sel.appendChild(opt);
        });
        sel.value = current;
    },

    async loadTabData() {
        const params = {};
        if (this.filters.project) params.project = this.filters.project;
        if (this.filters.tag) params.tag = this.filters.tag;
        if (this.filters.owner) params.owner = this.filters.owner;

        if (this.currentTab === 'budget') {
            const res = await BudgetAPI.getBudgetData(params);
            if (res.success) {
                this.data = res.data;
                this.renderBudgetTable();
            }
        } else if (this.currentTab === 'comparison') {
            const res = await BudgetAPI.getComparisonData(params);
            if (res.success) {
                this.data = res.data;
                this.renderComparisonTable();
                this.loadRiskSummary();
            }
        } else if (this.currentTab === 'actuals') {
            const res = await BudgetAPI.getActualsData(params);
            if (res.success) {
                this.data = res.data;
                this.renderActualsTable();
            }
        }
    },

    async loadRiskSummary() {
        const res = await BudgetAPI.getRiskSummary();
        if (!res.success) return;
        const d = res.data;
        const el = document.getElementById('risk-summary');
        el.innerHTML = `
            <div class="risk-card risk-p0"><span class="risk-label">P0 超支</span><span class="risk-count">${d.P0 || 0}</span></div>
            <div class="risk-card risk-p1"><span class="risk-label">P1 未用满</span><span class="risk-count">${d.P1 || 0}</span></div>
            <div class="risk-card risk-p2"><span class="risk-label">P2 未使用</span><span class="risk-count">${d.P2 || 0}</span></div>
            <div class="risk-card risk-p3"><span class="risk-label">P3 预算内</span><span class="risk-count">${d.P3 || 0}</span></div>
        `;
    },

    // ===== Table Rendering =====

    renderBudgetTable() {
        const table = document.getElementById('budget-table');
        const thead = table.querySelector('thead tr');
        const tbody = table.querySelector('tbody');

        const baseHeaders = ['项目', 'Tag', '业务场景', '供应商', '明细', '负责人'];
        const monthHeaders = [];
        for (let m = 1; m <= 12; m++) monthHeaders.push(`${m}月预算`);
        const allHeaders = [...baseHeaders, ...monthHeaders, '合计'];

        thead.innerHTML = allHeaders.map(h => `<th>${h}</th>`).join('');

        tbody.innerHTML = this.data.map(row => {
            const base = [
                this._esc(row.project), this._esc(row.tag), this._esc(row.business_scene),
                this._esc(row.vendor), this._esc(row.detail), this._esc(row.owner)
            ];
            const months = [];
            for (let m = 1; m <= 12; m++) {
                const val = row.monthly[`month_${m}`] || 0;
                months.push(`<td class="editable" data-item-id="${row.id}" data-month="${m}" data-type="budget">${this._fmt(val)}</td>`);
            }
            return `<tr>${base.map(b => `<td class="base-col">${b}</td>`).join('')}${months.join('')}<td class="total total-col">${this._fmt(row.total)}</td></tr>`;
        }).join('');

        tbody.querySelectorAll('.editable').forEach(td => {
            td.addEventListener('click', () => this.editCell(td));
        });
    },

    renderComparisonTable() {
        const table = document.getElementById('comparison-table');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');

        // Two-row header: base cols + month groups (预算/实际/差异)
        let headerRow1 = '<tr><th rowspan="2">项目</th><th rowspan="2">Tag</th><th rowspan="2">业务场景</th><th rowspan="2">负责人</th>';
        let headerRow2 = '<tr>';
        for (let m = 1; m <= 12; m++) {
            headerRow1 += `<th colspan="3">${m}月</th>`;
            headerRow2 += '<th>预算</th><th>实际</th><th>差异</th>';
        }
        headerRow1 += '<th rowspan="2">合计差异</th></tr>';
        headerRow2 += '</tr>';
        thead.innerHTML = headerRow1 + headerRow2;

        tbody.innerHTML = this.data.map(row => {
            const base = [
                this._esc(row.project), this._esc(row.tag),
                this._esc(row.business_scene), this._esc(row.owner)
            ];
            const months = [];
            for (let m = 1; m <= 12; m++) {
                const md = row.monthly[`month_${m}`] || {};
                const riskClass = md.risk ? `risk-${md.risk.toLowerCase()}` : '';
                const hasReason = md.reason ? ' has-reason' : '';
                months.push(
                    `<td>${this._fmt(md.budget)}</td>`,
                    `<td class="editable${hasReason}" data-item-id="${row.id}" data-month="${m}" data-type="actual" title="${md.reason ? '点击查看/编辑理由' : '点击编辑'}">${this._fmt(md.actual)}</td>`,
                    `<td class="${riskClass}">${this._fmt(md.diff)}</td>`
                );
            }
            const diffClass = row.total_diff > 0 ? 'risk-p0' : (row.total_diff < 0 ? 'risk-p2' : '');
            return `<tr>${base.map(b => `<td class="base-col">${b}</td>`).join('')}${months.join('')}<td class="${diffClass} total-col">${this._fmt(row.total_diff)}</td></tr>`;
        }).join('');

        tbody.querySelectorAll('.editable').forEach(td => {
            td.addEventListener('click', () => this.editActualCell(td));
        });
    },

    editActualCell(td) {
        const itemId = td.dataset.itemId;
        const month = parseInt(td.dataset.month);
        const oldVal = this._parseNum(td.textContent);

        const row = this.data.find(r => r.id == itemId);
        const md = row ? (row.monthly[`month_${month}`] || {}) : {};

        const input = document.createElement('input');
        input.type = 'number';
        input.value = oldVal;
        input.className = 'cell-input';
        td.textContent = '';
        td.appendChild(input);
        input.focus();
        input.select();

        const save = async () => {
            const newVal = parseFloat(input.value) || 0;
            await BudgetAPI.updateActual(itemId, month, newVal, md.reason || null);
            this.loadTabData();
        };

        input.addEventListener('blur', save);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { input.blur(); }
            if (e.key === 'Escape') { td.textContent = this._fmt(oldVal); }
        });
    },

    renderActualsTable() {
        const table = document.getElementById('actuals-table');
        const thead = table.querySelector('thead tr');
        const tbody = table.querySelector('tbody');

        const baseHeaders = ['项目', 'Tag', '业务场景', '供应商', '明细', '负责人'];
        const monthHeaders = [];
        for (let m = 1; m <= 12; m++) monthHeaders.push(`${m}月实际`);
        const allHeaders = [...baseHeaders, ...monthHeaders, '合计'];

        thead.innerHTML = allHeaders.map(h => `<th>${h}</th>`).join('');

        tbody.innerHTML = this.data.map(row => {
            const base = [
                this._esc(row.project), this._esc(row.tag), this._esc(row.business_scene),
                this._esc(row.vendor), this._esc(row.detail), this._esc(row.owner)
            ];
            const months = [];
            for (let m = 1; m <= 12; m++) {
                const val = row.monthly[`month_${m}`] || 0;
                months.push(`<td class="editable" data-item-id="${row.id}" data-month="${m}" data-type="actual">${this._fmt(val)}</td>`);
            }
            return `<tr>${base.map(b => `<td class="base-col">${b}</td>`).join('')}${months.join('')}<td class="total total-col">${this._fmt(row.total)}</td></tr>`;
        }).join('');

        tbody.querySelectorAll('.editable').forEach(td => {
            td.addEventListener('click', () => this.editCell(td));
        });
    },

    // ===== Cell Editing =====

    editCell(td) {
        const itemId = td.dataset.itemId;
        const month = parseInt(td.dataset.month);
        const type = td.dataset.type;
        const oldVal = this._parseNum(td.textContent);

        const input = document.createElement('input');
        input.type = 'number';
        input.value = oldVal;
        input.className = 'cell-input';
        td.textContent = '';
        td.appendChild(input);
        input.focus();
        input.select();

        const save = async () => {
            const newVal = parseFloat(input.value) || 0;
            td.textContent = this._fmt(newVal);
            if (newVal === oldVal) return;

            if (type === 'budget') {
                await BudgetAPI.updateBudget(itemId, month, newVal);
            } else {
                await BudgetAPI.updateActual(itemId, month, newVal);
            }
            this.loadTabData();
        };

        input.addEventListener('blur', save);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { input.blur(); }
            if (e.key === 'Escape') { td.textContent = this._fmt(oldVal); }
        });
    },

    // ===== Reason Modal =====

    _reasonContext: null,

    showReasonModal(itemId, month) {
        this._reasonContext = { itemId, month };
        const row = this.data.find(r => r.id == itemId);
        const md = row ? (row.monthly[`month_${month}`] || {}) : {};
        document.getElementById('reason-context').textContent =
            `${row ? row.detail : ''} - ${month}月`;
        document.getElementById('reason-input').value = md.reason || '';
        document.getElementById('reason-modal').style.display = 'flex';
    },

    async saveReason() {
        if (!this._reasonContext) return;
        const { itemId, month } = this._reasonContext;
        const reason = document.getElementById('reason-input').value;
        await BudgetAPI.updateReason(itemId, month, reason);
        document.getElementById('reason-modal').style.display = 'none';
        this.loadTabData();
    },

    // ===== Import =====

    async handlePreview() {
        const fileInput = document.getElementById('import-file');
        if (!fileInput.files.length) { alert('请选择文件'); return; }

        const res = await BudgetAPI.previewImport(fileInput.files[0]);
        const el = document.getElementById('import-preview');
        if (res.success) {
            el.innerHTML = `
                <div class="preview-info">
                    <p>明细数: <strong>${res.items_count}</strong></p>
                    <p>预算记录: <strong>${res.budget_records}</strong></p>
                    <p>实际记录: <strong>${res.actual_records}</strong></p>
                    <p>项目: ${(res.projects || []).join(', ')}</p>
                    <p>负责人: ${(res.owners || []).join(', ')}</p>
                </div>
            `;
        } else {
            el.innerHTML = `<div class="error">${res.error}</div>`;
        }
    },

    async handleImport() {
        const fileInput = document.getElementById('import-file');
        if (!fileInput.files.length) { alert('请选择文件'); return; }
        if (!confirm('导入将覆盖现有数据，确定继续？')) return;

        const statusEl = document.getElementById('import-status');
        statusEl.textContent = '导入中...';

        const res = await BudgetAPI.importExcel(fileInput.files[0]);
        if (res.success) {
            statusEl.innerHTML = `<div class="success">导入成功！明细${res.items_count}条，预算${res.budget_records}条，实际${res.actual_records}条</div>`;
            document.getElementById('import-modal').style.display = 'none';
            fileInput.value = '';
            document.getElementById('import-preview').innerHTML = '';
            document.getElementById('import-status').innerHTML = '';
            this.loadFilterOptions();
            this.loadTabData();
        } else {
            statusEl.innerHTML = `<div class="error">导入失败：${res.error}</div>`;
        }
    },

    // ===== Utilities =====

    _fmt(val) {
        if (val === 0 || val === null || val === undefined) return '-';
        return Number(val).toLocaleString('zh-CN', { maximumFractionDigits: 2 });
    },

    _parseNum(str) {
        if (!str || str === '-') return 0;
        return parseFloat(str.replace(/,/g, '')) || 0;
    },

    _esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
};

document.addEventListener('DOMContentLoaded', () => BudgetApp.init());
