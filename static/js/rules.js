let availableFields = [];
let conditionCount = 0;

document.addEventListener('DOMContentLoaded', function() {
    loadRulesList();
    addCondition();
});

function addCondition() {
    conditionCount++;
    const container = document.getElementById('conditions-container');
    const row = document.createElement('div');
    row.className = 'condition-row';
    row.id = `condition-${conditionCount}`;

    row.innerHTML = `
        <select class="field-select" id="field-${conditionCount}">
            <option value="">选择字段</option>
        </select>
        <select class="operator-select" id="operator-${conditionCount}">
            <option value="==">等于</option>
            <option value="!=">不等于</option>
            <option value=">">大于</option>
            <option value="<">小于</option>
            <option value=">=">大于等于</option>
            <option value="<=">小于等于</option>
            <option value="contains">包含</option>
            <option value="not_contains">不包含</option>
            <option value="starts_with">开头是</option>
            <option value="ends_with">结尾是</option>
            <option value="is_empty">为空</option>
            <option value="is_not_empty">不为空</option>
        </select>
        <input type="text" class="value-input" id="value-${conditionCount}" placeholder="值">
        <button class="delete-btn" onclick="deleteCondition(${conditionCount})">删除</button>
    `;

    container.appendChild(row);
}

function deleteCondition(id) {
    const row = document.getElementById(`condition-${id}`);
    if (row) {
        row.remove();
    }
}

async function saveRule() {
    const name = document.getElementById('rule-name').value;
    const description = document.getElementById('rule-description').value;
    const logic = document.querySelector('input[name="logic"]:checked').value;

    if (!name) {
        alert('请输入规则名称');
        return;
    }

    const conditions = [];
    const conditionRows = document.querySelectorAll('.condition-row');

    conditionRows.forEach(row => {
        const id = row.id.split('-')[1];
        const field = document.getElementById(`field-${id}`).value;
        const operator = document.getElementById(`operator-${id}`).value;
        const value = document.getElementById(`value-${id}`).value;

        if (field) {
            conditions.push({ field, operator, value });
        }
    });

    if (conditions.length === 0) {
        alert('请至少添加一个筛选条件');
        return;
    }

    try {
        const response = await fetch('/api/rules', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name,
                description,
                conditions,
                logic_operator: logic
            })
        });

        const data = await response.json();

        if (data.success) {
            alert('规则保存成功！');
            document.getElementById('rule-name').value = '';
            document.getElementById('rule-description').value = '';
            document.getElementById('conditions-container').innerHTML = '';
            conditionCount = 0;
            addCondition();
            loadRulesList();
        } else {
            alert('保存失败：' + data.error);
        }
    } catch (error) {
        alert('保存失败：' + error.message);
    }
}

async function loadRulesList() {
    const response = await fetch('/api/rules');
    const data = await response.json();

    const container = document.getElementById('rules-list');
    container.innerHTML = '';

    data.rules.forEach(rule => {
        const item = document.createElement('div');
        item.className = 'rule-item';

        const conditionsText = rule.conditions.map(c =>
            `${c.field} ${c.operator} ${c.value}`
        ).join(` ${rule.logic_operator} `);

        item.innerHTML = `
            <h4>${rule.name}</h4>
            <div class="rule-desc">${rule.description || '无描述'}</div>
            <div class="rule-conditions">条件：${conditionsText}</div>
            <div class="rule-actions">
                <button onclick="editRule(${rule.id})">编辑</button>
                <button class="delete-btn" onclick="deleteRule(${rule.id})">删除</button>
            </div>
        `;

        container.appendChild(item);
    });
}

async function editRule(id) {
    const response = await fetch(`/api/rules/${id}`);
    const data = await response.json();

    if (data.rule) {
        const rule = data.rule;
        document.getElementById('rule-name').value = rule.name;
        document.getElementById('rule-description').value = rule.description || '';

        const logicRadio = document.querySelector(`input[name="logic"][value="${rule.logic_operator}"]`);
        if (logicRadio) logicRadio.checked = true;

        document.getElementById('conditions-container').innerHTML = '';
        conditionCount = 0;

        rule.conditions.forEach(condition => {
            addCondition();
            const id = conditionCount;
            document.getElementById(`field-${id}`).value = condition.field;
            document.getElementById(`operator-${id}`).value = condition.operator;
            document.getElementById(`value-${id}`).value = condition.value;
        });
    }
}

async function deleteRule(id) {
    if (!confirm('确定要删除这个规则吗？')) return;

    try {
        const response = await fetch(`/api/rules/${id}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            loadRulesList();
        } else {
            alert('删除失败：' + data.error);
        }
    } catch (error) {
        alert('删除失败：' + error.message);
    }
}
