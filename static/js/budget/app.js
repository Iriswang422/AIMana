const BudgetApp = {
    currentTab: 'budget',
    filters: { project: '', tag: '', owner: '', month: '' },
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

        ['project', 'tag', 'owner', 'month'].forEach(f => {
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

        const saveNoteBtn = document.getElementById('save-note-btn');
        if (saveNoteBtn) saveNoteBtn.addEventListener('click', () => this.saveVarianceNote());
    },

    switchTab(tab) {
        this.currentTab = tab;
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.toggle('active', p.id === `${tab}-tab`));
        document.getElementById('risk-summary').style.display = tab === 'comparison' ? 'flex' : 'none';
        document.getElementById('risk-legend').style.display = tab === 'comparison' ? 'flex' : 'none';
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

    _getParams() {
        const params = {};
        if (this.filters.project) params.project = this.filters.project;
        if (this.filters.tag) params.tag = this.filters.tag;
        if (this.filters.owner) params.owner = this.filters.owner;
        if (this.filters.month) params.month = this.filters.month;
        return params;
    },

    async loadTabData() {
        const params = this._getParams();

        if (this.currentTab === 'budget') {
            const res = await BudgetAPI.getBudgetData(params);
            if (res.success) {
                this.data = res.data;
                this.renderBudgetTable();
                this._updateBudgetSummary();
            }
        } else if (this.currentTab === 'comparison') {
            const res = await BudgetAPI.getComparisonData(params);
            if (res.success) {
                this.data = res.data;
                this.renderComparisonTable();
                this._updateComparisonSummary();
                this.loadRiskSummary();
            }
        } else if (this.currentTab === 'actuals') {
            const res = await BudgetAPI.getActualsData(params);
            if (res.success) {
                this.data = res.data;
                this.renderActualsTable();
                this._updateActualsSummary();
            }
        }
    },

    async loadRiskSummary() {
        const params = {};
        if (this.filters.month) params.month = this.filters.month;
        const qs = new URLSearchParams(params).toString();
        const res = await fetch(`/api/budget/risk-summary${qs ? '?' + qs : ''}`).then(r => r.json());
        if (!res.success) return;
        const d = res.data;
        document.getElementById('risk-summary').innerHTML = `
            <div class="risk-card risk-p0"><span class="risk-label">P0 超支</span><span class="risk-count">${d.P0 || 0}</span></div>
            <div class="risk-card risk-p1"><span class="risk-label">P1 未用满</span><span class="risk-count">${d.P1 || 0}</span></div>
            <div class="risk-card risk-p2"><span class="risk-label">P2 未使用</span><span class="risk-count">${d.P2 || 0}</span></div>
            <div class="risk-card risk-p3"><span class="risk-label">P3 预算内</span><span class="risk-count">${d.P3 || 0}</span></div>
        `;
    },

    _updateBudgetSummary() {
        const total = this.data.reduce((s, r) => s + (r.total || 0), 0);
        document.getElementById('budget-summary').innerHTML =
            `<span>共 <strong>${this.data.length}</strong> 条明细</span>
             <span>合计预算: <strong class="total-val">${this._fmt(total)}</strong></span>`;
    },

    _updateComparisonSummary() {
        const totals = this._compTotals();
        const diff = totals.grandActual - totals.grandBudget;
        const diffClass = diff > 0 ? 'risk-p0' : diff < 0 ? 'neg' : '';
        const monthLabel = this.filters.month ? `${this.filters.month}月` : '全年';
        document.getElementById('comparison-summary').innerHTML =
            `<span>${monthLabel} | 共 <strong>${this.data.length}</strong> 条</span>
             <span>合计预算: <strong>${this._fmt(totals.grandBudget)}</strong></span>
             <span>合计实际: <strong>${this._fmt(totals.grandActual)}</strong></span>
             <span>合计差异: <strong class="${diffClass}">${this._fmt(diff)}</strong></span>`;
    },

    _updateActualsSummary() {
        const total = this.data.reduce((s, r) => s + (r.total || 0), 0);
        document.getElementById('actuals-summary').innerHTML =
            `<span>共 <strong>${this.data.length}</strong> 条明细</span>
             <span>合计实际: <strong class="total-val">${this._fmt(total)}</strong></span>`;
    },

    // ===== Table Rendering =====

    renderBudgetTable() {
        const table = document.getElementById('budget-table');
        const thead = table.querySelector('thead tr');
        const tbody = table.querySelector('tbody');
        const tfoot = table.querySelector('tfoot');

        const baseHeaders = ['项目', 'Tag', '业务场景', '供应商', '明细', '负责人'];
        const monthHeaders = [];
        for (let m = 1; m <= 12; m++) monthHeaders.push(`${m}月`);
        const allHeaders = [...baseHeaders, ...monthHeaders, '合计'];
        thead.innerHTML = allHeaders.map(h => `<th>${h}</th>`).join('');

        tbody.innerHTML = this.data.map(row => {
            const base = [row.project, row.tag, row.business_scene, row.vendor, row.detail, row.owner]
                .map(v => `<td class="base-col">${this._esc(v)}</td>`).join('');
            const months = [];
            for (let m = 1; m <= 12; m++) {
                const val = row.monthly[`month_${m}`] || 0;
                const highlight = this.filters.month && parseInt(this.filters.month) === m ? ' highlight-col' : '';
                months.push(`<td class="editable${highlight}" data-item-id="${row.id}" data-month="${m}" data-type="budget">${this._fmt(val)}</td>`);
            }
            return `<tr>${base}${months.join('')}<td class="total total-col">${this._fmt(row.total)}</td></tr>`;
        }).join('');

        const totals = this._calcTotals('budget');
        tfoot.innerHTML = `<tr class="total-row"><td class="base-col" colspan="6">合计</td>${totals.months.map(v => `<td class="total-col">${this._fmt(v)}</td>`).join('')}<td class="total total-col">${this._fmt(totals.grand)}</td></tr>`;

        tbody.querySelectorAll('.editable').forEach(td => {
            td.addEventListener('click', () => this.editCell(td));
        });
    },

    renderComparisonTable() {
        const table = document.getElementById('comparison-table');
        const thead = table.querySelector('thead');
        const tbody = table.querySelector('tbody');
        const tfoot = table.querySelector('tfoot');

        const selMonth = this.filters.month ? parseInt(this.filters.month) : null;
        const monthsToShow = selMonth ? [selMonth] : [1,2,3,4,5,6,7,8,9,10,11,12];

        thead.innerHTML = '';
        const tr1 = document.createElement('tr');
        ['项目','Tag','业务场景','负责人'].forEach(h => {
            const th = document.createElement('th');
            th.className = 'base-col';
            th.rowSpan = 2;
            th.textContent = h;
            tr1.appendChild(th);
        });
        monthsToShow.forEach(m => {
            const th = document.createElement('th');
            th.colSpan = 4;
            if (selMonth === m) th.className = 'highlight-col';
            th.textContent = m + '月';
            tr1.appendChild(th);
        });
        const totalTh = document.createElement('th');
        totalTh.rowSpan = 2;
        totalTh.textContent = '合计差异';
        tr1.appendChild(totalTh);
        thead.appendChild(tr1);

        const tr2 = document.createElement('tr');
        monthsToShow.forEach(m => {
            ['预算','实际','差异','解释'].forEach(h => {
                const th = document.createElement('th');
                if (selMonth === m) th.className = 'highlight-col';
                th.textContent = h;
                tr2.appendChild(th);
            });
        });
        thead.appendChild(tr2);

        tbody.innerHTML = '';
        if (!this.data || !Array.isArray(this.data)) return;

        const frag = document.createDocumentFragment();
        this.data.forEach(row => {
            const tr = document.createElement('tr');
            [row.project, row.tag, row.business_scene, row.owner].forEach(v => {
                const td = document.createElement('td');
                td.className = 'base-col';
                td.textContent = v || '';
                tr.appendChild(td);
            });
            const monthly = row.monthly || {};
            monthsToShow.forEach(m => {
                const md = monthly['month_' + m] || {};
                const hl = selMonth === m;

                const tdB = document.createElement('td');
                if (hl) tdB.className = 'highlight-col';
                tdB.textContent = this._fmt(md.budget);
                tr.appendChild(tdB);

                const tdA = document.createElement('td');
                tdA.className = 'editable' + (hl ? ' highlight-col' : '');
                tdA.dataset.itemId = row.id;
                tdA.dataset.month = m;
                tdA.dataset.type = 'actual';
                tdA.textContent = this._fmt(md.actual);
                tr.appendChild(tdA);

                const tdD = document.createElement('td');
                if (md.risk) tdD.className = 'risk-' + md.risk.toLowerCase();
                if (hl) tdD.className += (tdD.className ? ' ' : '') + 'highlight-col';
                tdD.textContent = this._fmt(md.diff);
                tr.appendChild(tdD);

                const tdN = document.createElement('td');
                tdN.className = 'note-cell' + (md.note ? ' has-note' : '') + (hl ? ' highlight-col' : '');
                tdN.dataset.itemId = row.id;
                tdN.dataset.month = m;
                tdN.title = md.note || '点击添加差异解释';
                tdN.textContent = md.note ? this._truncate(md.note, 20) : '+';
                tr.appendChild(tdN);
            });
            const totalDiff = row.total_diff || 0;
            const tdTotal = document.createElement('td');
            tdTotal.className = 'total-col';
            if (totalDiff > 0) tdTotal.className += ' risk-p0';
            else if (totalDiff < 0) tdTotal.className += ' risk-p2';
            tdTotal.textContent = this._fmt(totalDiff);
            tr.appendChild(tdTotal);

            frag.appendChild(tr);
        });
        tbody.appendChild(frag);

        tfoot.innerHTML = '';
        const totals = this._compTotals();
        const trFoot = document.createElement('tr');
        trFoot.className = 'total-row';
        const tdLabel = document.createElement('td');
        tdLabel.className = 'base-col';
        tdLabel.colSpan = 4;
        tdLabel.textContent = '合计';
        trFoot.appendChild(tdLabel);
        monthsToShow.forEach(m => {
            const hl = selMonth === m;
            [totals.budgets[m], totals.actuals[m], totals.diffs[m]].forEach(v => {
                const td = document.createElement('td');
                if (hl) td.className = 'highlight-col';
                td.textContent = this._fmt(v);
                trFoot.appendChild(td);
            });
            const tdEmpty = document.createElement('td');
            if (hl) tdEmpty.className = 'highlight-col';
            trFoot.appendChild(tdEmpty);
        });
        const tdGrand = document.createElement('td');
        tdGrand.className = 'total-col';
        if (totals.grandDiff > 0) tdGrand.className += ' risk-p0';
        else if (totals.grandDiff < 0) tdGrand.className += ' risk-p2';
        tdGrand.textContent = this._fmt(totals.grandDiff);
        trFoot.appendChild(tdGrand);
        tfoot.appendChild(trFoot);

        tbody.querySelectorAll('.editable').forEach(td => {
            td.addEventListener('click', () => this.editActualCell(td));
        });
        tbody.querySelectorAll('.note-cell').forEach(td => {
            td.addEventListener('click', () => this.showNoteModal(td));
        });
    },

    renderActualsTable() {
        const table = document.getElementById('actuals-table');
        const thead = table.querySelector('thead tr');
        const tbody = table.querySelector('tbody');
        const tfoot = table.querySelector('tfoot');

        const baseHeaders = ['项目', 'Tag', '业务场景', '供应商', '明细', '负责人'];
        const monthHeaders = [];
        for (let m = 1; m <= 12; m++) monthHeaders.push(`${m}月`);
        const allHeaders = [...baseHeaders, ...monthHeaders, '合计'];
        thead.innerHTML = allHeaders.map(h => `<th>${h}</th>`).join('');

        tbody.innerHTML = this.data.map(row => {
            const base = [row.project, row.tag, row.business_scene, row.vendor, row.detail, row.owner]
                .map(v => `<td class="base-col">${this._esc(v)}</td>`).join('');
            const months = [];
            for (let m = 1; m <= 12; m++) {
                const val = row.monthly[`month_${m}`] || 0;
                const hl = this.filters.month && parseInt(this.filters.month) === m ? ' highlight-col' : '';
                months.push(`<td class="editable${hl}" data-item-id="${row.id}" data-month="${m}" data-type="actual">${this._fmt(val)}</td>`);
            }
            return `<tr>${base}${months.join('')}<td class="total total-col">${this._fmt(row.total)}</td></tr>`;
        }).join('');

        const totals = this._calcTotals('actual');
        tfoot.innerHTML = `<tr class="total-row"><td class="base-col" colspan="6">合计</td>${totals.months.map(v => `<td class="total-col">${this._fmt(v)}</td>`).join('')}<td class="total total-col">${this._fmt(totals.grand)}</td></tr>`;

        tbody.querySelectorAll('.editable').forEach(td => {
            td.addEventListener('click', () => this.editCell(td));
        });
    },

    _calcTotals(type) {
        const months = {};
        for (let m = 1; m <= 12; m++) months[m] = 0;
        let grand = 0;
        this.data.forEach(row => {
            for (let m = 1; m <= 12; m++) {
                const val = row.monthly[`month_${m}`] || 0;
                months[m] += val;
                grand += val;
            }
        });
        return { months, grand };
    },

    _compTotals() {
        const budgets = {}, actuals = {}, diffs = {};
        for (let m = 1; m <= 12; m++) { budgets[m] = 0; actuals[m] = 0; diffs[m] = 0; }
        let grandBudget = 0, grandActual = 0;
        const selMonth = this.filters.month ? parseInt(this.filters.month) : null;
        this.data.forEach(row => {
            const monthly = row.monthly || {};
            for (let m = 1; m <= 12; m++) {
                if (selMonth && selMonth !== m) continue;
                const md = monthly['month_' + m] || {};
                budgets[m] += md.budget || 0;
                actuals[m] += md.actual || 0;
                diffs[m] += md.diff || 0;
                grandBudget += md.budget || 0;
                grandActual += md.actual || 0;
            }
        });
        return { budgets, actuals, diffs, grandBudget, grandActual, grandDiff: grandActual - grandBudget };
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
            if (newVal === oldVal) { td.textContent = this._fmt(oldVal); return; }
            if (type === 'budget') {
                await BudgetAPI.updateBudget(itemId, month, newVal);
            } else {
                await BudgetAPI.updateActual(itemId, month, newVal);
            }
            this.loadTabData();
        };

        input.addEventListener('blur', save);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') input.blur();
            if (e.key === 'Escape') { td.textContent = this._fmt(oldVal); }
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
            if (newVal === oldVal) { td.textContent = this._fmt(oldVal); return; }
            await BudgetAPI.updateActual(itemId, month, newVal, md.reason || null);
            this.loadTabData();
        };

        input.addEventListener('blur', save);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') input.blur();
            if (e.key === 'Escape') { td.textContent = this._fmt(oldVal); }
        });
    },

    // ===== Variance Note Modal =====

    _noteContext: null,

    showNoteModal(td) {
        const itemId = td.dataset.itemId;
        const month = parseInt(td.dataset.month);
        const row = this.data.find(r => r.id == itemId);
        const md = row ? (row.monthly[`month_${month}`] || {}) : {};

        this._noteContext = { itemId, month };
        document.getElementById('note-context').textContent =
            `${row ? row.project + ' / ' + row.tag + ' / ' + row.business_scene : ''} - ${month}月`;
        document.getElementById('note-input').value = md.note || '';

        const meta = md.note_updated_by ? `上次编辑: ${md.note_updated_by}` : '';
        document.getElementById('note-meta').textContent = meta;

        document.getElementById('note-modal').style.display = 'flex';
        document.getElementById('note-input').focus();
    },

    async saveVarianceNote() {
        if (!this._noteContext) return;
        const { itemId, month } = this._noteContext;
        const note = document.getElementById('note-input').value;
        await BudgetAPI.updateVarianceNote(itemId, month, note, '');
        document.getElementById('note-modal').style.display = 'none';
        this.loadTabData();
    },

    // ===== Import =====

    async handlePreview() {
        const fileInput = document.getElementById('import-file');
        if (!fileInput.files.length) { alert('请选择文件'); return; }
        const res = await BudgetAPI.previewImport(fileInput.files[0]);
        const el = document.getElementById('import-preview');
        if (res.success) {
            el.innerHTML = `<div class="preview-info">
                <p>明细: <strong>${res.items_count}</strong> 条 | 预算记录: <strong>${res.budget_records}</strong> | 实际记录: <strong>${res.actual_records}</strong></p>
                <p>项目: ${(res.projects || []).join(', ')}</p>
                <p>负责人: ${(res.owners || []).join(', ')}</p>
            </div>`;
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
            statusEl.innerHTML = `<div class="success">导入成功！明细${res.items_count}条</div>`;
            document.getElementById('import-modal').style.display = 'none';
            fileInput.value = '';
            document.getElementById('import-preview').innerHTML = '';
            statusEl.innerHTML = '';
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
    _esc(str) { return str || ''; },
    _truncate(str, len) {
        if (!str) return '';
        return str.length > len ? str.substring(0, len) + '...' : str;
    }
};

document.addEventListener('DOMContentLoaded', () => BudgetApp.init());
