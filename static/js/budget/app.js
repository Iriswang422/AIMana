// 预算追踪主控制器
const BudgetApp = {
    currentMonth: null,
    currentRiskLevel: null,
    tree: [],

    async init() {
        this.bindEvents();
        await this.loadTree();
        await this.loadAnalysis();
        await this.loadRiskSummary();
        await this.loadRiskRules();
        await this.loadPermissions();
        await this.loadChangeLog();
        await this.loadActualsTable();
    },

    async loadTree() {
        const result = await BudgetAPI.getTree();
        if (result.success) {
            this.tree = result.data;
            this.renderBudgetTree();
        }
    },

    async loadAnalysis() {
        const result = await BudgetAPI.getAnalysis(this.currentMonth, this.currentRiskLevel);
        if (result.success) {
            this.renderAnalysisTable(result.data);
        }
    },

    async loadRiskSummary() {
        const result = await BudgetAPI.getRiskSummary();
        if (result.success) {
            this.renderRiskSummary(result.data);
        }
    },

    async loadRiskRules() {
        const result = await BudgetAPI.getRiskRules();
        if (result.success) {
            this.renderRiskRulesEditor(result.data);
        }
    },

    async loadPermissions() {
        const result = await BudgetAPI.getPermissions();
        if (result.success) {
            this.renderPermissionsTable(result.data);
        }
    },

    async loadChangeLog() {
        const result = await BudgetAPI.getChangeLog();
        if (result.success) {
            this.renderChangeLogTable(result.data);
        }
    },

    // ===== 渲染预算树 =====
    renderBudgetTree() {
        const container = document.getElementById('budget-tree');
        let html = '';

        this.tree.forEach(owner => {
            html += `
                <div class="budget-owner">
                    <div class="owner-header">
                        <h3>${owner.name}</h3>
                        <div class="owner-actions">
                            ${owner.feishu_group ? `<span style="font-size:12px;opacity:0.85">${owner.feishu_group}</span>` : ''}
                            <button class="btn btn-sm" onclick="BudgetApp.addCategoryPrompt(${owner.id})">+ 板块</button>
                        </div>
                    </div>
                    <div class="owner-body">
            `;

            owner.categories.forEach(cat => {
                html += `
                    <div class="budget-category">
                        <div class="category-header">
                            <h4>${cat.name}</h4>
                            <button class="btn btn-sm" onclick="BudgetApp.addItemPrompt(${cat.id})">+ 明细</button>
                        </div>
                        <div class="category-body">
                        <table class="item-table">
                            <thead>
                                <tr>
                                    <th>明细名称</th>
                                    <th style="text-align:right">原预算</th>
                                    <th style="text-align:right">当前预算</th>
                                    <th style="text-align:right">差额</th>
                                    <th style="text-align:right">YTD实际</th>
                                    <th style="text-align:right">YTD差异</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody>
                `;

                cat.items.forEach(item => {
                    const diff = item.current_budget - item.original_budget;
                    const ytdDiff = item.current_budget - (item.ytd_actual || 0);

                    html += `
                        <tr>
                            <td class="item-name">${item.item_name}</td>
                            <td class="num-cell">${this.formatMoney(item.original_budget)}</td>
                            <td class="num-cell">${this.formatMoney(item.current_budget)}</td>
                            <td class="num-cell ${diff >= 0 ? 'positive' : 'negative'}">
                                ${diff >= 0 ? '+' : ''}${this.formatMoney(diff)}
                            </td>
                            <td class="num-cell">${this.formatMoney(item.ytd_actual || 0)}</td>
                            <td class="num-cell ${ytdDiff >= 0 ? 'positive' : 'negative'}">
                                ${ytdDiff >= 0 ? '+' : ''}${this.formatMoney(ytdDiff)}
                            </td>
                            <td class="item-actions">
                                <button class="btn btn-sm" onclick="BudgetApp.editBudget(${item.id}, '${item.item_name.replace(/'/g, "\\'")}', ${item.original_budget}, ${item.current_budget})">编辑</button>
                                <button class="btn btn-sm" onclick="BudgetApp.showChangeLog(${item.id})">记录</button>
                            </td>
                        </tr>
                    `;
                });

                html += `
                            </tbody>
                        </table>
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    // ===== 渲染分析表格 =====
    renderAnalysisTable(data) {
        const tbody = document.querySelector('#analysis-table tbody');
        tbody.innerHTML = data.map(row => {
            const level = (row.risk_level || 'unknown').toLowerCase();
            return `
            <tr>
                <td>${row.owner_name}</td>
                <td>${row.category_name}</td>
                <td>${row.item_name}</td>
                <td class="num-cell">${this.formatMoney(row.budget)}</td>
                <td class="num-cell">${this.formatMoney(row.actual)}</td>
                <td class="num-cell ${row.variance >= 0 ? 'positive' : 'negative'}">
                    ${row.variance >= 0 ? '+' : ''}${this.formatMoney(row.variance)}
                </td>
                <td class="num-cell">${((row.variance_rate || 0) * 100).toFixed(1)}%</td>
                <td><span class="risk-badge risk-${level}">${row.risk_level || '-'}</span></td>
                <td>
                    <input type="text"
                           class="reason-input"
                           value="${row.reason || ''}"
                           onchange="BudgetApp.updateReason(${row.item_id}, '${row.month}', this.value)"
                           placeholder="填写变动理由...">
                </td>
            </tr>
            `;
        }).join('');
    }

    // ===== 渲染风险汇总 =====
    renderRiskSummary(summary) {
        const container = document.getElementById('risk-summary');
        container.innerHTML = `
            <div class="risk-card p0">
                <div class="risk-card-label">P0 超支</div>
                <div class="risk-card-value">${summary.P0 || 0}</div>
                <div class="risk-card-amount">共 ${summary.P0 || 0} 项</div>
            </div>
            <div class="risk-card p1">
                <div class="risk-card-label">P1 未用满</div>
                <div class="risk-card-value">${summary.P1 || 0}</div>
                <div class="risk-card-amount">共 ${summary.P1 || 0} 项</div>
            </div>
            <div class="risk-card p2">
                <div class="risk-card-label">P2 未使用</div>
                <div class="risk-card-value">${summary.P2 || 0}</div>
                <div class="risk-card-amount">共 ${summary.P2 || 0} 项</div>
            </div>
            <div class="risk-card p3">
                <div class="risk-card-label">P3 预算内</div>
                <div class="risk-card-value">${summary.P3 || 0}</div>
                <div class="risk-card-amount">共 ${summary.P3 || 0} 项</div>
            </div>
        `;
    }

    // ===== 渲染风险规则编辑器 =====
    renderRiskRulesEditor(rules) {
        const container = document.getElementById('risk-rules-editor');
        container.innerHTML = rules.map(rule => {
            const levelLower = rule.level.toLowerCase();
            return `
            <div class="rule-row">
                <span class="rule-level risk-${levelLower}">${rule.level}</span>
                <input type="text" class="rule-label" value="${rule.label}" data-field="label" data-level="${rule.level}">
                <select class="rule-condition" data-field="condition_type" data-level="${rule.level}">
                    <option value="over_budget" ${rule.condition_type === 'over_budget' ? 'selected' : ''}>超支</option>
                    <option value="under_used" ${rule.condition_type === 'under_used' ? 'selected' : ''}>未用满</option>
                    <option value="no_usage" ${rule.condition_type === 'no_usage' ? 'selected' : ''}>未使用</option>
                    <option value="within_budget" ${rule.condition_type === 'within_budget' ? 'selected' : ''}>预算内</option>
                </select>
                <input type="number" class="rule-threshold" value="${rule.threshold}" step="0.01" data-field="threshold" data-level="${rule.level}">
                <label class="rule-active">
                    <input type="checkbox" ${rule.is_active ? 'checked' : ''} data-field="is_active" data-level="${rule.level}">
                    启用
                </label>
            </div>
            `;
        }).join('');
    }

    // ===== 渲染权限表格 =====
    renderPermissionsTable(perms) {
        const tbody = document.querySelector('#permissions-table tbody');
        tbody.innerHTML = perms.map(p => `
            <tr>
                <td>${p.user_id}</td>
                <td>${p.role}</td>
                <td>${p.feishu_group || '-'}</td>
            </tr>
        `).join('');
    }

    // ===== 渲染变更记录表格 =====
    renderChangeLogTable(logs) {
        const tbody = document.querySelector('#change-log-table tbody');
        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>${new Date(log.changed_at).toLocaleString('zh-CN')}</td>
                <td>${log.item_id}</td>
                <td>${this.formatMoney(log.old_budget)}</td>
                <td>${this.formatMoney(log.new_budget)}</td>
                <td class="${log.diff >= 0 ? 'positive' : 'negative'}">
                    ${log.diff >= 0 ? '+' : ''}${this.formatMoney(log.diff)}
                </td>
                <td>${log.changed_by || '-'}</td>
            </tr>
        `).join('');
    }

    // ===== 渲染趋势图表 =====
    renderTrendChart(viewType = 'owner') {
        const chart = echarts.init(document.getElementById('trend-chart'));

        const months = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05'];

        let series = [];

        if (viewType === 'owner') {
            // 按负责人汇总
            const ownerData = {};
            this.tree.forEach(owner => {
                ownerData[owner.name] = months.map(() => 0);
                owner.categories.forEach(cat => {
                    cat.items.forEach(item => {
                        item.actuals?.forEach(actual => {
                            const idx = months.indexOf(actual.month);
                            if (idx >= 0) {
                                ownerData[owner.name][idx] += actual.actual_amount;
                            }
                        });
                    });
                });
            });

            series = Object.entries(ownerData).map(([name, data]) => ({
                name,
                type: 'line',
                stack: '总量',
                areaStyle: {},
                data
            }));
        } else {
            // 按板块汇总
            const catData = {};
            this.tree.forEach(owner => {
                owner.categories.forEach(cat => {
                    catData[cat.name] = months.map(() => 0);
                    cat.items.forEach(item => {
                        item.actuals?.forEach(actual => {
                            const idx = months.indexOf(actual.month);
                            if (idx >= 0) {
                                catData[cat.name][idx] += actual.actual_amount;
                            }
                        });
                    });
                });
            });

            series = Object.entries(catData).map(([name, data]) => ({
                name,
                type: 'line',
                stack: '总量',
                areaStyle: {},
                data
            }));
        }

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: series.map(s => s.name) },
            xAxis: { type: 'category', data: months.map(m => m.slice(5) + '月') },
            yAxis: { type: 'value' },
            series
        });
    }

    renderComparisonChart() {
        const chart = echarts.init(document.getElementById('comparison-chart'));

        // 汇总所有预算和实际
        let totalBudget = 0;
        const monthlyActuals = {};

        this.tree.forEach(owner => {
            owner.categories.forEach(cat => {
                cat.items.forEach(item => {
                    totalBudget += item.current_budget / 12; // 月均预算
                    item.actuals?.forEach(actual => {
                        if (!monthlyActuals[actual.month]) monthlyActuals[actual.month] = 0;
                        monthlyActuals[actual.month] += actual.actual_amount;
                    });
                });
            });
        });

        const months = Object.keys(monthlyActuals).sort();
        const budgetLine = months.map(() => totalBudget);
        const actualLine = months.map(m => monthlyActuals[m]);

        chart.setOption({
            tooltip: { trigger: 'axis' },
            legend: { data: ['月均预算', '实际发生'] },
            xAxis: { type: 'category', data: months.map(m => m.slice(5) + '月') },
            yAxis: { type: 'value' },
            series: [
                {
                    name: '月均预算',
                    type: 'line',
                    data: budgetLine,
                    lineStyle: { type: 'dashed' }
                },
                {
                    name: '实际发生',
                    type: 'bar',
                    data: actualLine
                }
            ]
        });
    }

    // ===== 交互操作 =====
    addOwnerPrompt() {
        const name = prompt('负责人姓名：');
        if (name) {
            const group = prompt('飞书群（可选）：');
            BudgetAPI.addOwner(name, group).then(() => this.loadTree());
        }
    },

    addCategoryPrompt(ownerId) {
        const name = prompt('预算板块名称：');
        if (name) {
            BudgetAPI.addCategory(ownerId, name).then(() => this.loadTree());
        }
    },

    addItemPrompt(categoryId) {
        const name = prompt('预算明细名称：');
        if (name) {
            const original = parseFloat(prompt('原预算：', '0')) || 0;
            const current = parseFloat(prompt('当前预算：', original)) || original;
            BudgetAPI.addItem(categoryId, name, original, current).then(() => this.loadTree());
        }
    },

    editBudget(itemId, itemName, originalBudget, currentBudget) {
        document.getElementById('edit-item-name').value = itemName;
        document.getElementById('edit-original-budget').value = originalBudget;
        document.getElementById('edit-current-budget').value = currentBudget;
        document.getElementById('edit-budget-modal').dataset.itemId = itemId;
        document.getElementById('edit-budget-modal').style.display = 'flex';
    },

    async saveBudget() {
        const itemId = parseInt(document.getElementById('edit-budget-modal').dataset.itemId);
        const newBudget = parseFloat(document.getElementById('edit-current-budget').value);
        const changedBy = document.getElementById('edit-changed-by').value;

        if (!newBudget || newBudget < 0) {
            alert('请输入有效的预算金额');
            return;
        }

        const result = await BudgetAPI.updateItem(itemId, newBudget, changedBy);
        if (result.success) {
            document.getElementById('edit-budget-modal').style.display = 'none';
            await this.loadTree();
            await this.loadAnalysis();
            await this.loadChangeLog();
        } else {
            alert('保存失败：' + result.error);
        }
    },

    async showChangeLog(itemId) {
        const result = await BudgetAPI.getChangeLog(itemId);
        if (result.success) {
            const content = document.getElementById('change-log-content');
            if (result.data.length === 0) {
                content.innerHTML = '<p>暂无变更记录</p>';
            } else {
                content.innerHTML = `
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>时间</th>
                                <th>原预算</th>
                                <th>新预算</th>
                                <th>差额</th>
                                <th>操作人</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.data.map(log => `
                                <tr>
                                    <td>${new Date(log.changed_at).toLocaleString('zh-CN')}</td>
                                    <td>${this.formatMoney(log.old_budget)}</td>
                                    <td>${this.formatMoney(log.new_budget)}</td>
                                    <td class="${log.diff >= 0 ? 'positive' : 'negative'}">
                                        ${log.diff >= 0 ? '+' : ''}${this.formatMoney(log.diff)}
                                    </td>
                                    <td>${log.changed_by || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            }
            document.getElementById('change-log-modal').style.display = 'flex';
        }
    },

    async updateReason(itemId, month, reason) {
        await BudgetAPI.updateActual(itemId, month, 0, reason); // 只更新理由
    },

    async handleUpload() {
        const fileInput = document.getElementById('actuals-file');
        const statusDiv = document.getElementById('upload-status');

        if (!fileInput.files.length) {
            statusDiv.innerHTML = '<div class="error">请选择文件</div>';
            return;
        }

        statusDiv.innerHTML = '<div class="info">上传中...</div>';

        const result = await BudgetAPI.uploadActuals(fileInput.files[0]);

        if (result.success) {
            statusDiv.innerHTML = `
                <div class="success">
                    上传成功！匹配 ${result.saved_count}/${result.total_count} 条记录
                    ${result.warnings.length > 0 ? `<br/>警告: ${result.warnings.join('<br/>')}` : ''}
                </div>
            `;
            fileInput.value = '';
            await this.loadTree();
            await this.loadAnalysis();
            await this.loadRiskSummary();
        } else {
            statusDiv.innerHTML = `<div class="error">上传失败：${result.error}</div>`;
        }
    },

    async handlePreview() {
        const fileInput = document.getElementById('actuals-file');
        if (!fileInput.files.length) {
            alert('请先选择文件');
            return;
        }

        const result = await BudgetAPI.previewUpload(fileInput.files[0]);

        if (result.success) {
            const content = document.getElementById('preview-content');
            content.innerHTML = `
                <p>共 ${result.total_rows} 条记录</p>
                <p>唯一值 - 负责人: ${result.unique_values.owners.join(', ')}</p>
                <p>唯一值 - 板块: ${result.unique_values.categories.join(', ')}</p>
                <p>唯一值 - 明细: ${result.unique_values.items.join(', ')}</p>
                <p>唯一值 - 月份: ${result.unique_values.months.join(', ')}</p>
                <h4>前20条预览:</h4>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>负责人</th>
                            <th>板块</th>
                            <th>明细</th>
                            <th>月份</th>
                            <th>实际数</th>
                            <th>理由</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${result.preview.map(row => `
                            <tr>
                                <td>${row.owner}</td>
                                <td>${row.category}</td>
                                <td>${row.item_name}</td>
                                <td>${row.month}</td>
                                <td>${this.formatMoney(row.actual_amount)}</td>
                                <td>${row.reason || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            document.getElementById('preview-modal').style.display = 'flex';
        } else {
            alert('预览失败：' + result.error);
        }
    },

    async saveRiskRules() {
        const rules = [];
        document.querySelectorAll('.rule-row').forEach(row => {
            const level = row.querySelector('.rule-level').textContent;
            const label = row.querySelector('.rule-label').value;
            const conditionType = row.querySelector('.rule-condition').value;
            const threshold = parseFloat(row.querySelector('.rule-threshold').value);
            const isActive = row.querySelector('.rule-active input').checked ? 1 : 0;

            rules.push({ level, label, condition_type: conditionType, threshold, is_active: isActive });
        });

        const result = await BudgetAPI.updateRiskRules(rules);
        if (result.success) {
            alert('风险规则已保存');
            await this.loadAnalysis();
            await this.loadRiskSummary();
        } else {
            alert('保存失败');
        }
    },

    async addPermission() {
        const userId = document.getElementById('perm-user').value;
        const role = document.getElementById('perm-role').value;
        const group = document.getElementById('perm-group').value;

        if (!userId) {
            alert('请输入用户ID');
            return;
        }

        const result = await BudgetAPI.addPermission(userId, role, null, group);
        if (result.success) {
            document.getElementById('perm-user').value = '';
            document.getElementById('perm-group').value = '';
            await this.loadPermissions();
        } else {
            alert('添加失败');
        }
    },

    async initSampleData() {
        if (!confirm('确定要初始化FY26真实数据（1-5月预实对比及原因）吗？')) return;

        const result = await BudgetAPI.initSample();
        if (result.success) {
            alert(result.message);
            await this.loadTree();
            await this.loadAnalysis();
            await this.loadRiskSummary();
            await this.loadChangeLog();
            // 如果趋势图已渲染，刷新
            const trendChart = document.getElementById('trend-chart');
            if (trendChart && trendChart.style.display !== 'none') {
                this.renderTrendChart();
                this.renderComparisonChart();
            }
        } else {
            alert('初始化失败：' + (result.error || ''));
        }
    },

    bindEvents() {
        // 标签页切换
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

                e.target.classList.add('active');
                document.getElementById(`${e.target.dataset.tab}-tab`).classList.add('active');

                // 切换到趋势tab时渲染图表
                if (e.target.dataset.tab === 'trend') {
                    setTimeout(() => {
                        this.renderTrendChart();
                        this.renderComparisonChart();
                    }, 100);
                }
            });
        });

        // 月份筛选
        const mf = document.getElementById('month-filter'); if (mf) mf.addEventListener('change', (e) => {
            this.currentMonth = e.target.value || null;
            this.loadAnalysis();
        });

        // 风险筛选
        document.querySelectorAll('.risk-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.risk-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.currentRiskLevel = e.target.dataset.level || null;
                this.loadAnalysis();
            });
        });

        // 视图切换
        document.querySelectorAll('.toggle-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.toggle-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.renderTrendChart(e.target.dataset.view);
            });
        });

        // 刷新按钮
        const rb = document.getElementById('refresh-btn'); if (rb) rb.addEventListener('click', () => {
            this.loadTree();
            this.loadAnalysis();
            this.loadRiskSummary();
        });

        // 初始化示例数据
        const isb = document.getElementById('init-sample-btn'); if (isb) isb.addEventListener('click', () => {
            this.initSampleData();
        });

        // 添加负责人
        const aob = document.getElementById('add-owner-btn'); if (aob) aob.addEventListener('click', () => {
            this.addOwnerPrompt();
        });

        // 编辑预算
        const sbb = document.getElementById('save-budget-btn'); if (sbb) sbb.addEventListener('click', () => {
            this.saveBudget();
        });

        // 上传实际数
        const ub = document.getElementById('upload-btn'); if (ub) ub.addEventListener('click', () => {
            this.handleUpload();
        });

        // 预览上传
        const pb = document.getElementById('preview-btn'); if (pb) pb.addEventListener('click', () => {
            this.handlePreview();
        });

        // 保存风险规则
        const srb = document.getElementById('save-rules-btn'); if (srb) srb.addEventListener('click', () => {
            this.saveRiskRules();
        });

        // 添加权限
        const apb = document.getElementById('add-perm-btn'); if (apb) apb.addEventListener('click', () => {
            this.addPermission();
        });

        // Excel 导入
        const importBtn = document.getElementById('import-excel-btn');
        if (importBtn) {
            importBtn.addEventListener('click', () => {
                document.getElementById('import-section').style.display = 'block';
            });
        }

        const previewImportBtn = document.getElementById('preview-import-btn');
        if (previewImportBtn) {
            previewImportBtn.addEventListener('click', () => {
                this.handleBudgetImportPreview();
            });
        }

        const confirmImportBtn = document.getElementById('confirm-import-btn');
        if (confirmImportBtn) {
            confirmImportBtn.addEventListener('click', () => {
                this.handleBudgetImport();
            });
        }

        // 实际成本上传
        const previewActualsBtn = document.getElementById('preview-actuals-btn');
        if (previewActualsBtn) {
            previewActualsBtn.addEventListener('click', () => {
                this.handleActualsPreview();
            });
        }

        const uploadActualsBtn = document.getElementById('upload-actuals-btn');
        if (uploadActualsBtn) {
            uploadActualsBtn.addEventListener('click', () => {
                this.handleActualsUpload();
            });
        }
    },

    // ===== Excel 批量导入 =====
    async handleBudgetImportPreview() {
        const fileInput = document.getElementById('budget-import-file');
        const statusDiv = document.getElementById('import-status');

        if (!fileInput.files.length) {
            statusDiv.innerHTML = '<div class="error">请选择文件</div>';
            return;
        }

        statusDiv.innerHTML = '<div class="info">解析中...</div>';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/api/budget/import-preview', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.success) {
                const content = document.getElementById('import-preview-content');
                content.innerHTML = `
                    <p>共 ${result.total_rows} 条记录</p>
                    <p>将创建：${result.owners_count}个负责人, ${result.categories_count}个板块, ${result.items_count}条明细</p>
                    ${result.warnings.length > 0 ? `<div class="warning" style="background:#fff3cd;padding:10px;border-radius:4px;margin:10px 0;">️ ${result.warnings.join('<br/>')}</div>` : ''}
                    <h4>前20条预览:</h4>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>负责人</th>
                                <th>板块</th>
                                <th>明细</th>
                                <th>原预算</th>
                                <th>当前预算</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.preview.map(row => `
                                <tr>
                                    <td>${row.owner}</td>
                                    <td>${row.category}</td>
                                    <td>${row.item_name}</td>
                                    <td>${this.formatMoney(row.original_budget)}</td>
                                    <td>${this.formatMoney(row.current_budget)}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                document.getElementById('import-preview-modal').style.display = 'flex';
                statusDiv.innerHTML = '<div class="success">解析成功，请预览后确认导入</div>';
            } else {
                statusDiv.innerHTML = `<div class="error">解析失败：${result.error}</div>`;
            }
        } catch (e) {
            statusDiv.innerHTML = `<div class="error">请求失败：${e.message}</div>`;
        }
    },

    async handleBudgetImport() {
        const fileInput = document.getElementById('budget-import-file');
        const statusDiv = document.getElementById('import-status');

        if (!fileInput.files.length) {
            statusDiv.innerHTML = '<div class="error">请选择文件</div>';
            return;
        }

        if (!confirm('确定要导入这些数据吗？')) return;

        statusDiv.innerHTML = '<div class="info">导入中...</div>';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/api/budget/import', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.success) {
                statusDiv.innerHTML = `
                    <div class="success">
                        导入成功！<br/>
                        创建：${result.owners_count}个负责人, ${result.categories_count}个板块, ${result.items_count}条明细
                    </div>
                `;
                fileInput.value = '';
                document.getElementById('import-section').style.display = 'none';
                await this.loadTree();
                await this.loadAnalysis();
            } else {
                statusDiv.innerHTML = `<div class="error">导入失败：${result.error}</div>`;
            }
        } catch (e) {
            statusDiv.innerHTML = `<div class="error">请求失败：${e.message}</div>`;
        }
    },

    // ===== 实际成本上传 =====
    async handleActualsPreview() {
        const fileInput = document.getElementById('actuals-upload-file');
        const statusDiv = document.getElementById('actuals-upload-status');

        if (!fileInput.files.length) {
            statusDiv.innerHTML = '<div class="error">请选择文件</div>';
            return;
        }

        statusDiv.innerHTML = '<div class="info">解析中...</div>';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/api/budget/actuals-preview', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.success) {
                const content = document.getElementById('actuals-preview-content');
                content.innerHTML = `
                    <p>共 ${result.total_rows} 条记录</p>
                    <p>匹配成功：${result.matched_count}条，未匹配：${result.unmatched_count}条</p>
                    ${result.warnings.length > 0 ? `<div class="warning" style="background:#fff3cd;padding:10px;border-radius:4px;margin:10px 0;">️ ${result.warnings.join('<br/>')}</div>` : ''}
                    <h4>前20条预览:</h4>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>负责人</th>
                                <th>板块</th>
                                <th>明细</th>
                                <th>月份</th>
                                <th>实际金额</th>
                                <th>理由</th>
                                <th>状态</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${result.preview.map(row => `
                                <tr>
                                    <td>${row.owner}</td>
                                    <td>${row.category}</td>
                                    <td>${row.item_name}</td>
                                    <td>${row.month}</td>
                                    <td>${this.formatMoney(row.actual_amount)}</td>
                                    <td>${row.reason || '-'}</td>
                                    <td>${row.matched ? '<span style="color:green">✓</span>' : '<span style="color:red">✗</span>'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
                document.getElementById('actuals-preview-modal').style.display = 'flex';
                statusDiv.innerHTML = '<div class="success">解析成功，请预览后确认上传</div>';
            } else {
                statusDiv.innerHTML = `<div class="error">解析失败：${result.error}</div>`;
            }
        } catch (e) {
            statusDiv.innerHTML = `<div class="error">请求失败：${e.message}</div>`;
        }
    },

    async handleActualsUpload() {
        const fileInput = document.getElementById('actuals-upload-file');
        const statusDiv = document.getElementById('actuals-upload-status');

        if (!fileInput.files.length) {
            statusDiv.innerHTML = '<div class="error">请选择文件</div>';
            return;
        }

        if (!confirm('确定要上传这些实际数数据吗？')) return;

        statusDiv.innerHTML = '<div class="info">上传中...</div>';

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        try {
            const res = await fetch('/api/budget/actuals-upload', {
                method: 'POST',
                body: formData
            });
            const result = await res.json();

            if (result.success) {
                statusDiv.innerHTML = `
                    <div class="success">
                        上传成功！<br/>
                        匹配：${result.matched_count}条，未匹配：${result.unmatched_count}条
                    </div>
                `;
                fileInput.value = '';
                await this.loadTree();
                await this.loadAnalysis();
                await this.loadRiskSummary();
                await this.loadActualsTable();
            } else {
                statusDiv.innerHTML = `<div class="error">上传失败：${result.error}</div>`;
            }
        } catch (e) {
            statusDiv.innerHTML = `<div class="error">请求失败：${e.message}</div>`;
        }
    },

    async loadActualsTable() {
        try {
            const res = await fetch('/api/budget/actuals-list');
            const result = await res.json();

            if (result.success) {
                const tbody = document.querySelector('#actuals-table tbody');
                tbody.innerHTML = result.data.map(row => `
                    <tr>
                        <td>${row.owner_name}</td>
                        <td>${row.category_name}</td>
                        <td>${row.item_name}</td>
                        <td>${row.month}</td>
                        <td>${this.formatMoney(row.actual_amount)}</td>
                        <td>${row.reason || '-'}</td>
                        <td><span class="risk-badge risk-${(row.risk_level || 'unknown').toLowerCase()}">${row.risk_level || '-'}</span></td>
                    </tr>
                `).join('');
            }
        } catch (e) {
            console.error('加载实际数列表失败:', e);
        }
    },

    formatMoney(num) {
        if (num === null || num === undefined) return '0';
        return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
    }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    BudgetApp.init();
});

