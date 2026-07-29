from fastapi import FastAPI, Depends, HTTPException, Query, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import Optional, List
from model import SessionLocal, Project
from datetime import datetime
import re

app = FastAPI(title="项目评估系统API")

# CORS 配置 (修复了缺失的 # 号)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    # 修复了缺失的缩进
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== Pydantic模型 ==========
class ProjectCreate(BaseModel):
    project_name: str
    project_type: Optional[str] = None
    project_budget: Optional[float] = None
    project_duration: Optional[int] = None
    manpower_requirement: Optional[int] = None
    customer_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    customer_industry: Optional[str] = None
    company_scale: Optional[str] = None
    payment_method: Optional[str] = None
    requirement_description: Optional[str] = None
    special_requirements: Optional[str] = None
    remark: Optional[str] = None

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_type: Optional[str] = None
    project_budget: Optional[float] = None
    project_duration: Optional[int] = None
    manpower_requirement: Optional[int] = None
    customer_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    customer_industry: Optional[str] = None
    company_scale: Optional[str] = None
    payment_method: Optional[str] = None
    requirement_description: Optional[str] = None
    special_requirements: Optional[str] = None
    score: Optional[float] = None
    risk_level: Optional[str] = None
    decision: Optional[str] = None
    decision_reason: Optional[str] = None
    remark: Optional[str] = None

# ========== 1. 获取项目列表 ==========
@app.get("/api/projects")
async def get_projects(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    decision: Optional[str] = Query(None, description="决策筛选"),
    risk_level: Optional[str] = Query(None, description="风险等级筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取项目列表"""
    query = db.query(Project).filter(Project.is_deleted == False)
    
    if keyword:
        query = query.filter(
            or_(
                Project.project_name.contains(keyword),
                Project.customer_name.contains(keyword),
                Project.contact_person.contains(keyword)
            )
        )
    if project_type:
        query = query.filter(Project.project_type == project_type)
    if decision:
        query = query.filter(Project.decision == decision)
    if risk_level:
        query = query.filter(Project.risk_level == risk_level)
        
    total = query.count()
    projects = query.order_by(Project.updated_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    
    return {
        "code": 200,
        "data": [{
            "id": p.id,
            "project_name": p.project_name,
            "project_type": p.project_type,
            "project_budget": p.project_budget,
            "project_duration": p.project_duration,
            "manpower_requirement": p.manpower_requirement,
            "customer_name": p.customer_name,
            "contact_person": p.contact_person,
            "contact_phone": p.contact_phone,
            "customer_industry": p.customer_industry,
            "company_scale": p.company_scale,
            "payment_method": p.payment_method,
            "requirement_description": p.requirement_description[:100] + "..." if p.requirement_description and len(p.requirement_description) > 100 else p.requirement_description,
            "score": p.score,
            "risk_level": p.risk_level,
            "decision": p.decision,
            "decision_reason": p.decision_reason,
            "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M")
        } for p in projects],
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }

# ========== 2. 获取项目详情 ==========
@app.get("/api/projects/{project_id}")
async def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    """获取项目完整详情"""
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return {
        "code": 200,
        "data": {
            "id": project.id,
            "project_name": project.project_name,
            "project_type": project.project_type,
            "project_budget": project.project_budget,
            "project_duration": project.project_duration,
            "manpower_requirement": project.manpower_requirement,
            "customer_name": project.customer_name,
            "contact_person": project.contact_person,
            "contact_phone": project.contact_phone,
            "customer_industry": project.customer_industry,
            "company_scale": project.company_scale,
            "payment_method": project.payment_method,
            "requirement_description": project.requirement_description,
            "special_requirements": project.special_requirements,
            "score": project.score,
            "risk_level": project.risk_level,
            "decision": project.decision,
            "decision_reason": project.decision_reason,
            "upload_file_name": project.upload_file_name,
            "remark": project.remark,
            "created_at": project.created_at.strftime("%Y-%m-%d %H:%M"),
            "updated_at": project.updated_at.strftime("%Y-%m-%d %H:%M")
        }
    }

# ========== 3. 手动创建项目 ==========
@app.post("/api/projects")
async def create_project(data: ProjectCreate, db: Session = Depends(get_db)):
    """手动填写创建项目"""
    new_project = Project(
        project_name=data.project_name,
        project_type=data.project_type,
        project_budget=data.project_budget,
        project_duration=data.project_duration,
        manpower_requirement=data.manpower_requirement,
        customer_name=data.customer_name,
        contact_person=data.contact_person,
        contact_phone=data.contact_phone,
        customer_industry=data.customer_industry,
        company_scale=data.company_scale,
        payment_method=data.payment_method,
        requirement_description=data.requirement_description,
        special_requirements=data.special_requirements,
        remark=data.remark
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"code": 200, "message": "项目创建成功", "project_id": new_project.id}

# ========== 4. 文件上传创建项目 ==========
@app.post("/api/projects/upload")
async def upload_project_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传文件创建项目"""
    content = await file.read()
    try:
        file_text = content.decode('utf-8')
    except:
        file_text = content.decode('gbk', errors='ignore')
        
    def extract_field(pattern, text):
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None
        
    project_name = extract_field(r'(?:项目名称|项目)[：:]\s*([^\n\r]+)', file_text) or file.filename
    customer_name = extract_field(r'(?:客户|客户公司)[：:]\s*([^\n\r]+)', file_text)
    contact = extract_field(r'(?:联系人|联系人员)[：:]\s*([^\n\r]+)', file_text)
    phone = re.search(r'(\d{11})', file_text)
    budget_match = re.search(r'(?:预算|项目预算)[：:]\s*(\d+\.?\d*)', file_text)
    
    new_project = Project(
        project_name=project_name,
        customer_name=customer_name,
        contact_person=contact,
        contact_phone=phone.group(1) if phone else None,
        project_budget=float(budget_match.group(1)) if budget_match else None,
        requirement_description=file_text[:500],
        upload_file_name=file.filename,
        file_content=file_text[:5000]
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return {"code": 200, "message": "文件上传成功", "project_id": new_project.id, "file_name": file.filename}

# ========== 5. 更新项目 ==========
@app.put("/api/projects/{project_id}")
async def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)):
    """更新项目信息"""
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
        
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    project.updated_at = datetime.now()
    db.commit()
    return {"code": 200, "message": "更新成功"}

# ========== 6. 更新决策 ==========
@app.put("/api/projects/{project_id}/decision")
async def update_decision(project_id: int, decision: str, decision_reason: Optional[str] = None, db: Session = Depends(get_db)):
    """更新项目决策"""
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    if decision not in ["可以接", "谨慎谈", "直接拒绝"]:
        raise HTTPException(status_code=400, detail="决策只能是：可以接/谨慎谈/直接拒绝")
        
    project.decision = decision
    if decision_reason:
        project.decision_reason = decision_reason
    project.updated_at = datetime.now()
    db.commit()
    return {"code": 200, "message": f"决策已更新为：{decision}"}

# ========== 8. 获取统计信息 ==========
@app.get("/api/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """获取项目统计"""
    projects = db.query(Project).filter(Project.is_deleted == False).all()
    total = len(projects)
    decision_count = {"可以接": 0, "谨慎谈": 0, "直接拒绝": 0, "待评估": 0}
    total_budget = 0
    total_score = 0
    score_count = 0
    risk_count = {"低": 0, "中": 0, "高": 0}
    
    for p in projects:
        decision_count[p.decision or "待评估"] += 1
        total_budget += (p.project_budget or 0)
        if p.score:
            total_score += p.score
            score_count += 1
        if p.risk_level:
            risk_count[p.risk_level] = risk_count.get(p.risk_level, 0) + 1
            
    return {
        "code": 200,
        "data": {
            "total_projects": total,
            "decision_count": decision_count,
            "total_budget": total_budget,
            "avg_score": round(total_score / score_count, 1) if score_count > 0 else 0,
            "risk_count": risk_count,
            "can_accept": decision_count["可以接"],
            "should_reject": decision_count["直接拒绝"]
        }
    }

# ========== 9. 获取项目类型列表 ==========
@app.get("/api/project-types")
async def get_project_types(db: Session = Depends(get_db)):
    """获取所有项目类型"""
    types = db.query(Project.project_type).filter(
        Project.is_deleted == False,
        Project.project_type.isnot(None)
    ).distinct().all()
    return {"code": 200, "data": [t[0] for t in types if t[0]]}