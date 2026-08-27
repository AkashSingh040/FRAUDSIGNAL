import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { casesApi } from '../services/api';
import { Search, ArrowRight, Filter, Download, BoxSelect } from 'lucide-react';

const RiskCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    casesApi.list()
      .then(res => {
        const sorted = res.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        setCases(sorted);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getRiskColor = (score) => {
    if (score >= 70) return 'text-danger';
    if (score >= 30) return 'text-warning';
    return 'text-success';
  };
  
  const getRiskLevelBadge = (score) => {
    if (score >= 70) return <span className="badge badge-high">HIGH</span>;
    if (score >= 30) return <span className="badge badge-medium">MEDIUM</span>;
    return <span className="badge badge-low">LOW</span>;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
  };

  const filteredCases = cases.filter(c => 
    c.case_id.toLowerCase().includes(searchTerm.toLowerCase()) || 
    (c.transaction_id && c.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="flex-col gap-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="page-title">Risk Cases</h1>
          <p className="page-subtitle">All investigated transactions</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-outline text-xs">
            <Filter size={14} /> Filter
          </button>
          <button className="btn btn-outline text-xs">
            <Download size={14} /> Export CSV
          </button>
        </div>
      </div>
      
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', backgroundColor: 'var(--bg-base)' }}>
          <div className="search-input-wrapper">
            <Search />
            <input 
              type="text" 
              placeholder="Search case ID, transaction..." 
              className="form-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th style={{ width: '40px' }}><BoxSelect size={14} className="text-muted" /></th>
                <th>Case / Transaction</th>
                <th>Risk Score</th>
                <th>Risk Level</th>
                <th>Status</th>
                <th>Amount</th>
                <th>Time</th>
                <th style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ padding: '48px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Loading cases...
                  </td>
                </tr>
              ) : filteredCases.length === 0 ? (
                <tr>
                  <td colSpan="8" style={{ padding: '64px 16px', textAlign: 'center' }}>
                    <div className="flex-col items-center justify-center">
                      <ShieldAlert size={48} className="text-muted mb-4 opacity-50" />
                      <div className="text-primary font-semibold mb-2">No risk cases found</div>
                      <div className="text-muted text-sm">Transactions will appear here when payment activity is received.</div>
                    </div>
                  </td>
                </tr>
              ) : (
                filteredCases.map(c => (
                  <tr key={c.case_id}>
                    <td>
                      <input type="checkbox" style={{ accentColor: 'var(--primary)' }} />
                    </td>
                    <td>
                      <div className="font-mono text-xs font-semibold text-primary mb-1">{c.case_id}</div>
                      <div className="font-mono text-xs text-muted">{c.transaction_id || 'pay_unknown'}</div>
                    </td>
                    <td>
                      <div className="flex items-center">
                        <span className={`font-mono font-bold ${getRiskColor(c.risk_score)}`}>{c.risk_score}</span>
                        <span className="text-xs text-muted ml-1">/ 100</span>
                      </div>
                    </td>
                    <td>
                      {getRiskLevelBadge(c.risk_score)}
                    </td>
                    <td>
                      <span className="badge badge-neutral">
                        {c.status}
                      </span>
                    </td>
                    <td className="font-mono text-xs">
                      {formatCurrency(c.evidence?.observed_amount || 0)}
                    </td>
                    <td className="text-xs text-muted">
                      {new Date(c.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <Link to={`/cases/${c.case_id}`} className="btn btn-outline text-xs" style={{ padding: '6px 12px' }}>
                        Investigate <ArrowRight size={14} />
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// We need to import ShieldAlert for the empty state since it's used above but wasn't imported.
import { ShieldAlert } from 'lucide-react';

export default RiskCases;
