import json
import random
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from model import Project, SessionLocal, engine, Base

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@app.route('/')
def index():
    return render_template('index.html')

def mock_ai_analysis(data):
    budget = float(data.get('project_budget', 0))
    duration = float(data.get('project_duration', 0))
    score = random.randint(65, 95)
    risk = "低" if score >= 80 else "中" if score >= 70 else "高"

    report = f"""【项目概述】
项目名称：{data.get('project_name')}
客户名称：{data.get('customer_name')} (行业: {data.get('customer_industry')}, 规模: {data.get('company_scale')})
项目预算：{budget} 万元 | 期望周期：{duration} 个月 | 需求人数：{data.get('manpower_requirement')} 人月

【风险评估】
综合风险等级：{risk}。
主要风险集中在需求范围的明确性和交付时间的紧张程度上。建议在合同中对需求变更流程做出严格规定。

【收益分析】
根据测算，该项目毛利率约为 35%，净利率约为 22%，投资回报率（ROI）良好。

【AI 参谋建议】
AI 已完成多维评估，提供评分与风险参考。最终是否接单，请由人工在“资料库”中进行审批决策。"""

    return {"score": score, "risk_level": risk, "report": report}

@app.route('/api/ai-analyze', methods=['POST'])
def ai_analyze():
    db = next(get_db())
    try:
        data = request.json
        ai_result = mock_ai_analysis(data)
        
        # 【核心】将前端传来的所有字段，完美映射到同事的数据库模型中
        new_project = Project(
            project_name=data.get('project_name', '未命名'),
            customer_name=data.get('customer_name'),
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            customer_industry=data.get('customer_industry'),
            company_scale=data.get('company_scale'),
            project_type=data.get('project_type'),
            project_budget=float(data.get('project_budget', 0)),
            project_duration=int(data.get('project_duration', 0)),
            manpower_requirement=int(data.get('manpower_requirement', 0)),
            payment_method=data.get('payment_method'),
            requirement_description=data.get('requirement_description'),
            special_requirements=data.get('special_requirements'),
            
            # AI 评估字段
            score=ai_result['score'],
            risk_level=ai_result['risk_level'],
            decision="待评估",               
            decision_reason=ai_result['report'] 
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        return jsonify({
            "code": 200, 
            "message": "AI分析完成并入库",
            "project_id": new_project.id,
            "ai_data": ai_result
        })
    except Exception as e:
        db.rollback()
        return jsonify({"code": 500, "message": str(e)}), 500
    finally:
        db.close()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)