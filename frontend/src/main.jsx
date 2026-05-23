import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AlertTriangle, Bot, CheckCircle2, FileText, Gauge, Search, ShieldCheck, Workflow } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import './styles.css';

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

function StatCard({ title, value, subtitle, icon: Icon }) {
  return (
    <div className="card stat-card">
      <div className="stat-icon"><Icon size={22} /></div>
      <div>
        <p className="muted">{title}</p>
        <h2>{value}</h2>
        <span>{subtitle}</span>
      </div>
    </div>
  );
}

function App() {
  const [summary, setSummary] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [ragQuery, setRagQuery] = useState('approval threshold for high value duplicate invoices');
  const [ragAnswer, setRagAnswer] = useState(null);
  const [demoResult, setDemoResult] = useState(null);
  const [loading, setLoading] = useState(false);

  async function refresh() {
    const [s, inv, wf] = await Promise.all([
      api('/api/v1/dashboard/summary'),
      api('/api/v1/invoices'),
      api('/api/v1/workflows'),
    ]);
    setSummary(s); setInvoices(inv); setWorkflows(wf);
  }

  useEffect(() => { refresh().catch(console.error); }, []);

  async function runDemo() {
    setLoading(true);
    const raw_text = `Invoice Number: INV-DEMO-${Date.now().toString().slice(-5)}\nVendor ID: V-FAC-001\nVendor Name: Northstar Facilities Pvt Ltd\nPO Number: PO-2025-001\nInvoice Date: 2025-06-18\nDue Date: 2025-07-18\nCurrency: INR\nSubtotal: 125000\nTax: 22500\nTotal: 147500\nITEM|Quarterly facility audit and cleaning controls|qty=1|unit=125000|amount=125000|gl=GL-620|cc=CC-FINOPS`;
    try {
      const result = await api('/api/v1/workflows/run', { method: 'POST', body: JSON.stringify({ raw_text, priority: 'high' }) });
      setDemoResult(result);
      await refresh();
    } finally { setLoading(false); }
  }

  async function askRag() {
    const result = await api('/api/v1/rag/query', { method: 'POST', body: JSON.stringify({ query: ragQuery, top_k: 4 }) });
    setRagAnswer(result);
  }

  const chartData = useMemo(() => invoices.slice(0, 10).map(x => ({ invoice: x.invoice_id, risk: x.risk_score, compliance: x.compliance_score })), [invoices]);

  return (
    <main>
      <section className="hero">
        <div>
          <div className="ey-chip"><ShieldCheck size={16}/> EY-style clean-room demo</div>
          <h1>AI Enterprise Audit & Invoice Compliance Platform</h1>
          <p>Multi-agent invoice validation, PO reconciliation, RAG policy evidence, fraud detection, audit trail generation, and observability.</p>
        </div>
        <button className="primary" onClick={runDemo} disabled={loading}>{loading ? 'Running...' : 'Run invoice workflow'}</button>
      </section>

      <section className="grid four">
        <StatCard title="Invoices" value={summary?.invoice_count ?? '-'} subtitle="processed and seeded" icon={FileText} />
        <StatCard title="Workflows" value={summary?.workflow_count ?? '-'} subtitle="state-machine executions" icon={Workflow} />
        <StatCard title="Avg risk" value={summary?.avg_risk_score ?? '-'} subtitle="fraud intelligence" icon={AlertTriangle} />
        <StatCard title="Compliance" value={summary?.avg_compliance_score ?? '-'} subtitle="policy decision score" icon={CheckCircle2} />
      </section>

      <section className="grid two">
        <div className="card">
          <h3><Gauge size={18}/> Risk and compliance trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="invoice" hide />
              <YAxis />
              <Tooltip />
              <Bar dataKey="risk" />
              <Bar dataKey="compliance" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3><Search size={18}/> RAG compliance query</h3>
          <textarea value={ragQuery} onChange={e => setRagQuery(e.target.value)} />
          <button className="secondary" onClick={askRag}>Ask policy engine</button>
          {ragAnswer && <div className="rag-answer"><b>Answer:</b> {ragAnswer.answer}<br/><b>Confidence:</b> {ragAnswer.confidence}</div>}
        </div>
      </section>

      {demoResult && <section className="card result">
        <h3><Bot size={18}/> Latest workflow result</h3>
        <pre>{JSON.stringify({ workflow_id: demoResult.workflow_id, invoice_id: demoResult.invoice_id, status: demoResult.status, fraud: demoResult.fraud, compliance: demoResult.compliance }, null, 2)}</pre>
      </section>}

      <section className="card">
        <h3>Recent invoices</h3>
        <div className="table">
          <div className="row head"><span>Invoice</span><span>Vendor</span><span>Total</span><span>Status</span><span>Risk</span></div>
          {invoices.map(inv => <div className="row" key={inv.invoice_id}><span>{inv.invoice_id}</span><span>{inv.vendor}</span><span>{inv.total}</span><span>{inv.status}</span><span>{inv.risk_score}</span></div>)}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
