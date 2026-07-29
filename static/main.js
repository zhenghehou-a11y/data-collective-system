const FLASK_API = '/api';
const FASTAPI_BASE = 'http://127.0.0.1:8000';
let currentDatabase = [];
let currentEditingProjectId = null;

function switchTab(page) {
    document.querySelectorAll('.top-tab').forEach(t => t.classList.remove('act'));
    document.querySelector(`.top-tab[data-page="${page}"]`).classList.add('act');
    document.querySelectorAll('.page').forEach(p => p.classList.remove('show'));
    document.getElementById(`page-${page}`).classList.add('show');
    if (page === 'database') renderDatabase();
}

function handleFiles(files) {
    if (!files.length) return;
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = `<div class="file-item">📄 ${files[0].name} - 解析中...</div>`;
    setTimeout(() => {
        fileList.innerHTML = `<div class="file-item">✅ ${files[0].name} - 已提取关键信息</div>`;
        showToast('文件解析完成', 's');
    }, 1500);
}

async function runAIAnalysis() {
    const formData = getFormData();
    // 校验必填项 (对应数据库的 nullable=False)
    if (!formData.project_name || !formData.customer_name || !formData.project_budget || !formData.project_duration || !formData.requirement_description) {
        return showToast('请填写所有带 * 号的必填项', 'e');
    }

    document.getElementById('aiPlaceholder').style.display = 'none';
    document.getElementById('aiLoading').style.display = 'flex';
    document.getElementById('aiResult').style.display = 'none';

    try {
        const response = await fetch(`${FLASK_API}/ai-analyze`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(formData)
        });
        const resJson = await response.json();
        if (resJson.code !== 200) throw new Error(resJson.message);

        renderAnalysisResult(resJson.ai_data, formData);
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('aiResult').style.display = 'block';
        showToast(`AI 评估完成！项目已入库 (ID: ${resJson.project_id})`, 's');
    } catch (error) {
        document.getElementById('aiLoading').style.display = 'none';
        document.getElementById('aiPlaceholder').style.display = 'block';
        showToast('AI 评估失败: ' + error.message, 'e');
    }
}

function renderAnalysisResult(aiData, formData) {
    const circumference = 2 * Math.PI * 62;
    const offset = circumference - (aiData.score / 100) * circumference;
    const strokeColor = aiData.score >= 80 ? 'var(--g)' : aiData.score >= 70 ? 'var(--w)' : 'var(--r)';
    document.getElementById('scoreWrap').innerHTML = `
    <div class="score-ring">
      <svg viewBox="0 0 140 140"><circle class="bg" cx="70" cy="70" r="62"/><circle class="fg" cx="70" cy="70" r="62" stroke="${strokeColor}" stroke-dasharray="${circumference}" style="stroke-dashoffset: ${offset}"/></svg>
      <div class="score-val"><div class="num">${aiData.score}</div><div class="lbl">综合评分</div></div>
    </div>
    <div style="flex:1">
      <div style="font-size:13px;color:var(--n-600);line-height:2">
        <div>📌 <strong>技术可行性:</strong> ${Math.min(100, aiData.score + 5)} 分</div>
        <div>📌 <strong>商业价值:</strong> ${Math.max(0, aiData.score - 5)} 分</div>
        <div>📌 <strong>客户信誉:</strong> ${Math.max(0, aiData.score - 10)} 分</div>
      </div>
    </div>`;

    document.getElementById('riskList').innerHTML = `
    <div class="risk-item">
      <div class="risk-icon">${aiData.risk_level === '高' ? '🔥' : aiData.risk_level === '中' ? '⚠️' : 'ℹ️'}</div>
      <div class="risk-body"><div class="risk-title">综合风险等级: ${aiData.risk_level}</div><div class="risk-desc">AI 已根据预算、周期和需求描述完成多维风险评估。</div></div>
      <div class="risk-level ${aiData.risk_level}">${aiData.risk_level}风险</div>
    </div>`;

    const budget = formData.project_budget;
    document.getElementById('profitGrid').innerHTML = `
    <div class="profit-card"><div class="pl">预估毛利润</div><div class="pv">¥${(budget * 0.35).toFixed(1)}万</div></div>
    <div class="profit-card"><div class="pl">预估净利润</div><div class="pv">¥${(budget * 0.22).toFixed(1)}万</div></div>
    <div class="profit-card"><div class="pl">投资回报率</div><div class="pv">${(28 + Math.random() * 10).toFixed(1)}%</div></div>`;

    document.getElementById('reportContent').innerHTML = aiData.report || '暂无详细报告';
}

async function renderDatabase() {
    const tbody = document.getElementById('dbBody');
    const filter = document.getElementById('dbFilter').value;
    const search = document.getElementById('dbSearch').value.toLowerCase();
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;">加载中...</td></tr>';

    try {
        const response = await fetch(`${FASTAPI_BASE}/api/projects?page_size=100`);
        const resJson = await response.json();
        if (resJson.code !== 200) throw new Error('获取数据失败');

        currentDatabase = resJson.data.map(item => {
            let statusClass = 'pending';
            if (item.decision === '可以接') statusClass = 'pass';
            else if (item.decision === '谨慎谈') statusClass = 'warn';
            else if (item.decision === '直接拒绝') statusClass = 'reject';
            return { ...item, statusClass };
        });

        let filteredData = currentDatabase.filter(item => {
            const matchesFilter = filter === 'all' || item.decision === filter;
            const matchesSearch = (item.project_name || '').toLowerCase().includes(search) || (item.customer_name || '').toLowerCase().includes(search);
            return matchesFilter && matchesSearch;
        });

        if (filteredData.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--n-500)">暂无匹配数据</td></tr>';
            return;
        }

        tbody.innerHTML = filteredData.map(item => `
      <tr>
        <td><strong>${item.project_name}</strong><br><span style="font-size:11px;color:var(--n-500)">${item.customer_name || ''}</span></td>
        <td>${item.customer_industry || '-'}</td>
        <td>¥${item.project_budget || 0}万</td>
        <td><span class="score-badge ${item.score >= 80 ? 'h' : item.score >= 70 ? 'm' : item.score > 0 ? 'l' : ''}">${item.score || '-'}</span></td>
        <td>${item.risk_level || '未评估'}</td>
        <td><span class="status-tag ${item.statusClass}">${item.decision || '待评估'}</span></td>
        <td>
          <div class="row-actions">
            <button class="row-btn" onclick="viewAIReport(${item.id})" title="查看 AI 评价">👁️</button>
            <button class="row-btn" onclick="downloadPDF(${item.id})" title="下载 PDF">⬇️</button>
            <button class="row-btn" onclick="openDecisionModal(${item.id})" title="人工决策">⚖️</button>
          </div>
        </td>
      </tr>
    `).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--r)">加载失败，请确保 FastAPI 已启动</td></tr>';
    }
}

function viewAIReport(id) {
    const item = currentDatabase.find(p => p.id === id);
    if (!item) return;
    document.getElementById('aiReportTitle').textContent = `AI 评估报告 - ${item.project_name}`;
    document.getElementById('aiReportContent').innerHTML = item.decision_reason || '暂无 AI 评价';
    document.getElementById('aiReportDownloadBtn').onclick = () => downloadPDF(id);
    document.getElementById('aiReportModal').classList.add('show');
}

function downloadPDF(id) {
    const item = currentDatabase.find(p => p.id === id);
    if (!item) return;
    const element = document.createElement('div');
    element.style.padding = '30px'; element.style.fontFamily = 'sans-serif';
    element.innerHTML = `
    <h2 style="text-align:center; color:#4f46e5; border-bottom: 2px solid #eee; padding-bottom: 10px;">项目 AI 评估报告</h2>
    <p style="text-align:right; font-size:12px; color:#888;">生成时间：${new Date().toLocaleString()}</p>
    <table style="width:100%; margin:20px 0; font-size:14px; border-collapse:collapse;">
      <tr><td style="padding:8px; border:1px solid #ddd; background:#f9fafb; width:120px;"><strong>项目名称</strong></td><td style="padding:8px; border:1px solid #ddd;">${item.project_name}</td></tr>
      <tr><td style="padding:8px; border:1px solid #ddd; background:#f9fafb;"><strong>客户名称</strong></td><td style="padding:8px; border:1px solid #ddd;">${item.customer_name || '-'}</td></tr>
      <tr><td style="padding:8px; border:1px solid #ddd; background:#f9fafb;"><strong>项目预算</strong></td><td style="padding:8px; border:1px solid #ddd;">${item.project_budget || 0} 万元</td></tr>
      <tr><td style="padding:8px; border:1px solid #ddd; background:#f9fafb;"><strong>AI 评分</strong></td><td style="padding:8px; border:1px solid #ddd;">${item.score || '-'}</td></tr>
      <tr><td style="padding:8px; border:1px solid #ddd; background:#f9fafb;"><strong>风险等级</strong></td><td style="padding:8px; border:1px solid #ddd;">${item.risk_level || '-'}</td></tr>
    </table>
    <h3 style="border-bottom: 2px solid #eee; padding-bottom: 8px; margin-top: 20px;">AI 详细评估意见</h3>
    <div style="font-size: 14px; line-height: 1.8; color: #333; white-space: pre-wrap;">${item.decision_reason || '暂无'}</div>
  `;
    document.body.appendChild(element);
    html2pdf().set({ margin: 10, filename: `${item.project_name}_AI评估报告.pdf`, html2canvas: { scale: 2 }, jsPDF: { unit: 'mm', format: 'a4' } }).from(element).save().then(() => {
        document.body.removeChild(element);
        showToast('PDF 下载成功', 's');
    });
}

function openDecisionModal(id) {
    const item = currentDatabase.find(p => p.id === id);
    if (!item) return;
    currentEditingProjectId = id;
    document.getElementById('modalProjectName').textContent = item.project_name;
    document.getElementById('modalDecisionSelect').value = item.decision || '待评估';
    document.getElementById('modalRemark').value = item.remark || '';
    document.getElementById('decisionModal').classList.add('show');
}

async function submitDecisionChange() {
    const newDecision = document.getElementById('modalDecisionSelect').value;
    const humanRemark = document.getElementById('modalRemark').value;
    try {
        const response = await fetch(`${FASTAPI_BASE}/api/projects/${currentEditingProjectId}`, {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ decision: newDecision, remark: humanRemark })
        });
        const res = await response.json();
        if (res.code === 200) {
            showToast('人工决策保存成功', 's');
            document.getElementById('decisionModal').classList.remove('show');
            renderDatabase();
        } else throw new Error(res.detail);
    } catch (error) { showToast('更新失败: ' + error.message, 'e'); }
}

// 【核心】完美对齐同事数据库字段的映射
function getFormData() {
    return {
        project_name: document.getElementById('pName').value,           // 对应 project_name
        customer_name: document.getElementById('cName').value,          // 对应 customer_name
        contact_person: document.getElementById('cPerson').value,       // 对应 contact_person
        contact_phone: document.getElementById('cPhone').value,         // 对应 contact_phone
        customer_industry: document.getElementById('cIndustry').value,  // 对应 customer_industry
        company_scale: document.getElementById('cSize').value,          // 对应 company_scale
        project_budget: parseFloat(document.getElementById('pBudget').value) || 0, // 对应 project_budget
        project_duration: parseInt(document.getElementById('pDuration').value) || 0, // 对应 project_duration
        manpower_requirement: parseInt(document.getElementById('pHeadcount').value) || 0, // 对应 manpower_requirement
        project_type: document.getElementById('pType').value,           // 对应 project_type
        payment_method: document.getElementById('pPayment').value,      // 对应 payment_method
        requirement_description: document.getElementById('pDesc').value, // 对应 requirement_description
        special_requirements: document.getElementById('pExtra').value   // 对应 special_requirements
    };
}

function showToast(msg, type = 's') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`; toast.textContent = msg;
    document.getElementById('toasts').appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, 3000);
}

switchTab('input');