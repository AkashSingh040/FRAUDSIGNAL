import React, { useEffect, useState } from 'react';
import { dashboardApi, riskApi } from '../services/api';
import { ShieldAlert, ShieldCheck, Activity, Users } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Dashboard = () => {
  const [summary, setSummary] = useState(null);
  const [modelStatus, setModelStatus] = useState(null);

  useEffect(() => {
    dashboardApi.getSummary().then(res => setSummary(res.data)).catch(console.error);
    riskApi.getStatus().then(res => setModelStatus(res.data)).catch(console.error);
  }, []);

  if (!summary) return <div className="text-muted">Loading dashboard...</div>;

  const data = [
    { name: 'Low Risk', value: summary.total_transactions - summary.medium_risk - summary.high_risk, fill: '#10b981' },
    { name: 'Medium Risk', value: summary.medium_risk, fill: '#f59e0b' },
    { name: 'High Risk', value: summary.high_risk, fill: '#ef4444' },
  ];

  return (
    <div className="flex-col gap-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="page-title mb-4">Risk Overview</h1>
          <p className="text-muted mt-4">Real-time payment intelligence</p>
        </div>
        {modelStatus && (
          <div className={`badge ${modelStatus.trained ? 'badge-low' : 'badge-medium'}`}>
            Model Status: {modelStatus.trained ? 'TRAINED (IEEE-CIS)' : 'RULES FALLBACK (NO DATA)'}
          </div>
        )}
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
        <StatCard title="Total Transactions" value={summary.total_transactions} icon={<Activity className="text-primary" />} />
        <StatCard title="Open Investigations" value={summary.open_investigations} icon={<Users className="text-success" />} />
        <StatCard title="High Risk Rate" value={`${((summary.high_risk / Math.max(summary.total_transactions, 1)) * 100).toFixed(1)}%`} icon={<ShieldAlert className="text-danger" />} />
        <StatCard title="Confirmed Fraud" value={summary.confirmed_fraud} icon={<ShieldCheck className="text-warning" />} />
      </div>

      <div className="glass-panel card">
        <h2 className="card-title mb-4">Risk Distribution</h2>
        <div style={{ height: '300px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#2b2f3a" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="value" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, icon }) => (
  <div className="glass-panel card flex items-center">
    <div style={{ marginRight: '16px' }}>
      {icon}
    </div>
    <div className="stat-card">
      <p className="stat-label">{title}</p>
      <h3 className="stat-value">{value}</h3>
    </div>
  </div>
);

export default Dashboard;
