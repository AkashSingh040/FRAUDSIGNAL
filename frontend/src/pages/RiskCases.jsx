import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { casesApi } from '../services/api';
import { Search, ChevronRight } from 'lucide-react';

const RiskCases = () => {
  const [cases, setCases] = useState([]);

  useEffect(() => {
    casesApi.list().then(res => setCases(res.data)).catch(console.error);
  }, []);

  return (
    <div className="flex-col gap-4">
      <h1 className="page-title">Risk Cases</h1>
      
      <div className="glass-panel">
        <div style={{ padding: '16px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
            <Search style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', width: '16px', height: '16px', color: 'var(--text-muted)' }} />
            <input 
              type="text" 
              placeholder="Search cases..." 
              className="form-input"
              style={{ paddingLeft: '36px' }}
            />
          </div>
        </div>
        
        <div className="table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Case ID / Tx</th>
                <th>Risk Score</th>
                <th>Status</th>
                <th>Time</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {cases.length === 0 ? (
                <tr>
                  <td colSpan="5" style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No risk cases found. Run the simulator to generate some.
                  </td>
                </tr>
              ) : (
                cases.map(c => (
                  <tr key={c.case_id}>
                    <td>
                      <div className="font-semibold" style={{ width: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.case_id}</div>
                      <div className="text-xs text-muted" style={{ width: '150px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{c.transaction_id}</div>
                    </td>
                    <td>
                      <div className="flex items-center">
                        <div style={{
                          width: '8px', height: '8px', borderRadius: '50%', marginRight: '8px',
                          backgroundColor: c.risk_score >= 70 ? 'var(--danger)' : c.risk_score >= 30 ? 'var(--warning)' : 'var(--success)'
                        }} />
                        <span className="font-bold">{c.risk_score}</span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-medium">
                        {c.status}
                      </span>
                    </td>
                    <td className="text-sm text-muted">
                      {new Date(c.created_at).toLocaleString()}
                    </td>
                    <td>
                      <Link to={`/cases/${c.case_id}`} className="flex items-center font-semibold text-primary">
                        Investigate
                        <ChevronRight style={{ width: '16px', height: '16px', marginLeft: '4px' }} />
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

export default RiskCases;
