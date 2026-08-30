import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { casesApi } from '../services/api';
import { Search, ArrowRight, Filter, Download, BoxSelect } from 'lucide-react';

const RiskCases = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [searchTerm, setSearchTerm] = useState(searchParams.get('q') || "");
  const [filterLevel, setFilterLevel] = useState(searchParams.get('level') || "ALL");
  const [filterStatus, setFilterStatus] = useState(searchParams.get('status') || "ALL");

  useEffect(() => {
    const q = searchParams.get('q') || "";
    if (q !== searchTerm) {
      setSearchTerm(q);
    }
  }, [searchParams]);

  const handleSearchChange = (e) => {
    const val = e.target.value;
    setSearchTerm(val);
    updateSearchParams({ q: val || null });
  };

  const handleLevelChange = (e) => {
    const val = e.target.value;
    setFilterLevel(val);
    updateSearchParams({ level: val !== "ALL" ? val : null });
  };

  const handleStatusChange = (e) => {
    const val = e.target.value;
    setFilterStatus(val);
    updateSearchParams({ status: val !== "ALL" ? val : null });
  };

  const updateSearchParams = (updates) => {
    const newParams = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, val]) => {
      if (val) newParams.set(key, val);
      else newParams.delete(key);
    });
    setSearchParams(newParams);
  };

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

  const filteredCases = cases.filter(c => {
    const matchesSearch = c.case_id.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          (c.transaction_id && c.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()));
    
    let matchesFilter = true;
    if (filterLevel === 'HIGH') matchesFilter = c.risk_score >= 70;
    else if (filterLevel === 'MEDIUM') matchesFilter = c.risk_score >= 30 && c.risk_score < 70;
    else if (filterLevel === 'LOW') matchesFilter = c.risk_score < 30;

    let matchesStatus = true;
    if (filterStatus !== 'ALL') {
      if (filterStatus === 'OPEN_INV') {
        matchesStatus = ['OPEN', 'INVESTIGATING', 'REVIEW'].includes(c.status);
      } else if (filterStatus === 'FRAUD_OR_BLOCKED') {
        matchesStatus = c.status === 'CONFIRMED_FRAUD' || c.final_decision === 'BLOCK' || c.recommended_action === 'BLOCK';
      } else {
        matchesStatus = c.status === filterStatus;
      }
    }

    return matchesSearch && matchesFilter && matchesStatus;
  });

  const handleExportCSV = () => {
    if (filteredCases.length === 0) return;
    
    const headers = ['Case ID', 'Transaction ID', 'Risk Score', 'Risk Level', 'Status', 'Amount', 'Time'];
    const csvRows = [headers.join(',')];
    
    filteredCases.forEach(c => {
      const amount = (c.evidence?.observed_amount || 0).toString();
      const time = new Date(c.created_at).toISOString();
      const riskLevel = c.risk_score >= 70 ? 'HIGH' : c.risk_score >= 30 ? 'MEDIUM' : 'LOW';
      const row = [
        c.case_id,
        c.transaction_id || '',
        c.risk_score,
        riskLevel,
        c.status,
        amount,
        time
      ];
      csvRows.push(row.join(','));
    });
    
    const csvContent = "data:text/csv;charset=utf-8," + csvRows.join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `fraudsignal_cases_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="flex-col gap-4">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="page-title">Risk Cases</h1>
          <p className="page-subtitle">All investigated transactions</p>
        </div>
        <div className="flex gap-2 items-center">
          <div style={{ position: 'relative' }}>
            <select 
              className="btn btn-outline text-xs" 
              value={filterLevel}
              onChange={handleLevelChange}
              style={{ appearance: 'none', paddingRight: '28px', backgroundColor: 'var(--bg-surface)' }}
            >
              <option value="ALL">All Risks</option>
              <option value="HIGH">High Risk</option>
              <option value="MEDIUM">Medium Risk</option>
              <option value="LOW">Low Risk</option>
            </select>
            <Filter size={12} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-muted)' }} />
          </div>
          <div style={{ position: 'relative' }}>
            <select 
              className="btn btn-outline text-xs" 
              value={filterStatus}
              onChange={handleStatusChange}
              style={{ appearance: 'none', paddingRight: '28px', backgroundColor: 'var(--bg-surface)' }}
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN_INV">Active Investigations</option>
              <option value="FRAUD_OR_BLOCKED">Fraud / Blocked</option>
              <option value="OPEN">Open</option>
              <option value="INVESTIGATING">Investigating</option>
              <option value="REVIEW">Review</option>
              <option value="CONFIRMED_FRAUD">Confirmed Fraud</option>
              <option value="FALSE_POSITIVE">False Positive</option>
              <option value="RESOLVED">Resolved</option>
            </select>
            <Filter size={12} style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none', color: 'var(--text-muted)' }} />
          </div>
          <button className="btn btn-outline text-xs" onClick={handleExportCSV}>
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
              onChange={handleSearchChange}
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
