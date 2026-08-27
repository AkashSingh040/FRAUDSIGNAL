import React, { useEffect, useState } from 'react';
import { dashboardApi, riskApi, casesApi } from '../services/api';
import { ShieldAlert, Activity, Users, Shield, ArrowRight, AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Link } from 'react-router-dom';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);
  const [recentCases, setRecentCases] = useState([]);

  useEffect(() => {
    dashboardApi.getSummary().then(res => setSummary(res.data)).catch(console.error);
    riskApi.getStatus().then(res => setModelStatus(res.data)).catch(console.error);
    casesApi.list().then(res => {
      // Sort by newest first
      const sorted = res.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      setRecentCases(sorted);
    }).catch(console.error);
  }, []);

  if (!summary) return <div className="text-muted text-sm mt-4">Loading risk intelligence data...</div>;

  const total = summary.total_transactions;
  const highRiskRate = total > 0 ? ((summary.high_risk / total) * 100).toFixed(1) : 0;

  // Pie chart data
  const pieData = [
    { name: 'Low Risk', value: total - summary.medium_risk - summary.high_risk, color: 'var(--success)' },
    { name: 'Medium Risk', value: summary.medium_risk, color: 'var(--warning)' },
    { name: 'High Risk', value: summary.high_risk, color: 'var(--danger)' },
  ];

  // Derive mock activity time-series from recent cases or generate a flatline if none
  const generateActivityData = () => {
    if (recentCases.length === 0) return Array.from({length: 10}, (_, i) => ({ time: `T-${10-i}`, count: 0 }));
    // Group by minute (mock approach for visual density)
    return recentCases.slice(0, 10).reverse().map((c, i) => ({
      time: new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      risk: c.risk_score
    }));
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
  };

  const getRiskColor = (score) => {
    if (score >= 70) return 'text-danger';
    if (score >= 30) return 'text-warning';
    return 'text-success';
  };

  return (
    <div className="flex-col gap-4">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h1 className="page-title">Risk Intelligence</h1>
          <p className="page-subtitle">Real-time payment and fraud monitoring</p>
        </div>
        {modelStatus && (
          <div className="flex flex-col items-end gap-2">
            <span className="text-xs text-muted font-bold">MODEL STATUS</span>
            <div className={`badge ${modelStatus.trained ? 'badge-neutral' : 'badge-medium'}`}>
              <span className={`pulse-dot ${modelStatus.trained ? 'live' : ''}`}></span>
              {modelStatus.trained ? 'TRAINED (LightGBM)' : 'RULES FALLBACK'}
            </div>
          </div>
        )}
      </div>

      <div className="grid-4">
        <StatCard title="Total Transactions" value={summary.total_transactions} icon={<Activity size={18} className="text-primary" />} />
        <StatCard title="Open Investigations" value={summary.open_investigations} icon={<Users size={18} className="text-warning" />} />
        <StatCard title="High Risk Rate" value={`${highRiskRate}%`} icon={<ShieldAlert size={18} className="text-danger" />} />
        <StatCard title="Confirmed Fraud" value={summary.confirmed_fraud} icon={<Shield size={18} className="text-success" />} />
      </div>

      <div className="grid-charts">
        {/* Risk Activity Chart */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Risk Activity</h2>
          </div>
          <div style={{ height: '220px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={generateActivityData()}>
                <defs>
                  <linearGradient id="colorRisk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border-color)" />
                <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="var(--text-muted)" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="risk" stroke="var(--primary)" fillOpacity={1} fill="url(#colorRisk)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution Chart */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">Risk Distribution</h2>
          </div>
          <div style={{ height: '220px', position: 'relative' }}>
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
              <div className="font-mono" style={{ fontSize: '1.5rem', fontWeight: 600 }}>{total}</div>
              <div className="text-xs text-muted">Total</div>
            </div>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                  stroke="none"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid-charts">
        {/* Live Transactions Table */}
        <div className="card">
          <div className="card-header">
            <h2 className="card-title flex items-center gap-2">
              <span className="pulse-dot live"></span> Live Transactions
            </h2>
            <Link to="/cases" className="text-xs text-primary hover:underline">View All</Link>
          </div>
          <div className="table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Transaction</th>
                  <th>Amount</th>
                  <th>Risk Score</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {recentCases.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center text-muted py-8 text-sm">
                      Waiting for incoming transactions...
                    </td>
                  </tr>
                ) : (
                  recentCases.slice(0, 5).map(c => (
                    <tr key={c.case_id}>
                      <td className="font-mono text-xs">{c.transaction_id || 'pay_unknown'}</td>
                      <td className="font-mono text-xs">{formatCurrency(c.metadata?.amount / 100 || 0)}</td>
                      <td>
                        <span className={`font-mono font-bold ${getRiskColor(c.risk_score)}`}>
                          {c.risk_score}
                        </span>
                      </td>
                      <td>
                        <span className="badge badge-neutral">{c.status}</span>
                      </td>
                      <td>
                        <Link to={`/cases/${c.case_id}`} className="text-primary hover:text-primary-hover transition">
                          <ArrowRight size={16} />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="card flex-col gap-4">
          <div className="card-header" style={{ marginBottom: 0 }}>
            <h2 className="card-title">Recent Alerts</h2>
          </div>
          <div className="flex-col gap-2 overflow-y-auto" style={{ maxHeight: '300px' }}>
            {recentCases.filter(c => c.risk_score >= 70).slice(0, 4).map(c => (
              <div key={`alert-${c.case_id}`} className="flex items-start gap-3 p-3" style={{ backgroundColor: 'var(--bg-base)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
                <AlertTriangle size={16} className="text-danger mt-1 flex-shrink-0" />
                <div>
                  <div className="text-xs font-bold text-danger mb-1">HIGH RISK TRANSACTION</div>
                  <div className="text-xs text-muted mb-1 font-mono">Tx: {c.transaction_id}</div>
                  <div className="text-xs text-secondary">Risk score {c.risk_score} detected.</div>
                </div>
              </div>
            ))}
            {recentCases.filter(c => c.risk_score < 30).slice(0, 1).map(c => (
               <div key={`alert-${c.case_id}`} className="flex items-start gap-3 p-3" style={{ backgroundColor: 'var(--bg-base)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
               <CheckCircle size={16} className="text-success mt-1 flex-shrink-0" />
               <div>
                 <div className="text-xs font-bold text-success mb-1">PAYMENT CLEARED</div>
                 <div className="text-xs text-muted mb-1 font-mono">Tx: {c.transaction_id}</div>
                 <div className="text-xs text-secondary">Cleared auto-approval.</div>
               </div>
             </div>
            ))}
            {recentCases.length === 0 && (
              <div className="text-xs text-muted text-center p-4">No recent alerts.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon }) => (
  <div className="stat-card">
    <div className="stat-header">
      <span className="stat-label">{title}</span>
      {icon}
    </div>
    <div className="stat-value">{value}</div>
  </div>
);

export default Dashboard;
