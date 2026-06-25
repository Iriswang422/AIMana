from flask import Blueprint, request, jsonify, current_app

rules_bp = Blueprint('rules', __name__)

@rules_bp.route('/api/rules', methods=['POST'])
def create_rule():
    data = request.json

    rule_model = current_app.config['RULE_MODEL']
    rule_id = rule_model.save(
        name=data['name'],
        conditions=data['conditions'],
        logic_operator=data.get('logic_operator', 'AND'),
        description=data.get('description', '')
    )

    return jsonify({
        'success': True,
        'rule_id': rule_id
    })

@rules_bp.route('/api/rules', methods=['GET'])
def get_rules():
    rule_model = current_app.config['RULE_MODEL']
    rules = rule_model.get_all()
    return jsonify({'rules': rules})

@rules_bp.route('/api/rules/<int:rule_id>', methods=['GET'])
def get_rule(rule_id):
    rule_model = current_app.config['RULE_MODEL']
    rule = rule_model.get_by_id(rule_id)

    if not rule:
        return jsonify({'error': '规则不存在'}), 404

    return jsonify({'rule': rule})

@rules_bp.route('/api/rules/<int:rule_id>', methods=['PUT'])
def update_rule(rule_id):
    data = request.json
    rule_model = current_app.config['RULE_MODEL']

    rule = rule_model.get_by_id(rule_id)
    if not rule:
        return jsonify({'error': '规则不存在'}), 404

    rule_model.update(
        rule_id=rule_id,
        name=data['name'],
        conditions=data['conditions'],
        logic_operator=data.get('logic_operator', 'AND'),
        description=data.get('description', '')
    )

    return jsonify({'success': True})

@rules_bp.route('/api/rules/<int:rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    rule_model = current_app.config['RULE_MODEL']

    rule = rule_model.get_by_id(rule_id)
    if not rule:
        return jsonify({'error': '规则不存在'}), 404

    rule_model.delete(rule_id)
    return jsonify({'success': True})
