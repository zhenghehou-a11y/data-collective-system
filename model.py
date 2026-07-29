# models.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()
engine = create_engine('sqlite:///projects.db', connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(bind=engine)

class Project(Base):
    """项目主表 - 独立管理每个项目"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # ===== 项目基本信息（来自你的前端界面） =====
    project_name = Column(String(200), nullable=False, index=True)     # 项目名称
    project_type = Column(String(50))                                  # 项目类型：软件开发/硬件集成等
    project_budget = Column(Float)                                     # 项目预算（万元）
    project_duration = Column(Integer)                                 # 项目周期（月）
    manpower_requirement = Column(Integer)                             # 需求人数（人月）
    
    # ===== 客户信息（仅作记录，不关联） =====
    customer_name = Column(String(200))                                # 客户公司名称
    contact_person = Column(String(100))                               # 联系人
    contact_phone = Column(String(20))                                 # 联系电话
    customer_industry = Column(String(50))                             # 客户行业
    company_scale = Column(String(50))                                 # 公司规模
    
    # ===== 项目详情 =====
    requirement_description = Column(Text)                             # 项目需求描述
    special_requirements = Column(Text)                                # 补充说明/特殊要求
    payment_method = Column(String(50))                                # 付款方式
    
    # ===== 项目评估 =====
    score = Column(Float)                                              # AI评分
    risk_level = Column(String(20), default="中")                      # 风险等级：低/中/高
    
    # ===== 决策字段 =====
    decision = Column(String(20), default="待评估")                    # 可以接 / 谨慎谈 / 直接拒绝
    decision_reason = Column(Text)                                     # 决策理由
    
    # ===== 文件上传 =====
    upload_file_name = Column(String(200))                             # 上传的文件名
    file_content = Column(Text)                                        # 文件解析内容
    
    # ===== 系统字段 =====
    remark = Column(Text)                                              # 备注
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_deleted = Column(Boolean, default=False)                        # 软删除标记

# 创建表
Base.metadata.create_all(engine)
print("数据库初始化完成！")
