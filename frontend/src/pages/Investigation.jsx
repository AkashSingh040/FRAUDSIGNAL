import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { casesApi } from '../services/api';
import { AlertTriangle, CheckCircle, Clock, ShieldBan, ArrowLeft } from 'lucide-react';

const Investigation = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);

  useEffect(() => {
    casesApi.get(caseId).then(res => setData(res.data)).catch(console.error);
  }, [caseId]);

  const handleDecision = async (decision) => {
    try {
      await casesApi.updateDecision(caseId, decision, "Manual review decision");
      navigate('/cases');
    } catch (err) {
      console.error(err);
    }
  };

  if (!data) return <div className="text-muted" style={{ padding: '32px' }}>Loading case...</div>;

  const inv = data.investigation || {};
  const isResolved = data.status === "RESOLVED" || data.status === "CONFIRMED_FRAUD" || data.status === "FALSE_POSITIVE";

  return (
    <div className="flex-col gap-4 pb-12" style={{ maxWidth: '1200px', margin: '0 auto' }}>
      <Link to="/cases" className="flex items-center text-sm font-semibold text-muted mb-4" style={{ transition: 'color 0.2s' }}>
        <ArrowLeft style={{ width: '16px', height: '16px', marginRight: '4px' }} /> Back to Cases
      </Link>
      
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="page-title mb-0">Case Investigation</h1>
          <p className="text-muted text-sm mt-4">ID: {data.case_id}</p>
        </div>
        <div className={`badge ${data.risk_score >= 70 ? 'badge-high pulse' : data.risk_score >= 30 ? 'badge-medium' : 'badge-low'}`} style={{ fontSize: '1rem', padding: '8px 16px' }}>
          Risk Score: {data.risk_score}
        </div>
      </div>

      <div className="grid-3-1">
        {/* Left Column - Investigation Report */}
        <div className="flex-col gap-4">
          <div className="glass-panel card">
            <h2 className="card-title flex items-center mb-4">
              <span style={{ fontSize: '1.2rem', marginRight: '8px' }}>🤖</span>
              AI Investigation Report
            </h2>
            
            <div className="flex-col gap-4">
              <div>
                <h3 className="text-xs font-bold text-muted mb-4" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>Summary</h3>
                <p className="font-semibold" style={{ fontSize: '1.1rem' }}>{inv.summary || "No summary available."}</p>
              </div>
              
              <div>
                <h3 className="text-xs font-bold text-muted mb-4" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>Evidence</h3>
                <div className="evidence-list">
                  {(inv.evidence || []).map((e, i) => (
                    <div key={i} className="evidence-item flex">
                      <CheckCircle style={{ width: '20px', height: '20px', color: 'var(--success)', marginRight: '12px', flexShrink: 0 }} />
                      <span>{e}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold text-muted mb-4" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>Reasoning</h3>
                <div style={{ padding: '16px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)' }}>
                  <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {(inv.reasoning || []).map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                </div>
              </div>
              
              {inv.uncertainties && inv.uncertainties.length > 0 && (
                <div>
                  <h3 className="text-xs font-bold text-muted mb-4" style={{ textTransform: 'uppercase', letterSpacing: '0.05em' }}>Uncertainties</h3>
                  <div className="evidence-list">
                    {inv.uncertainties.map((u, i) => (
                      <div key={i} className="evidence-item critical flex items-center">
                        <AlertTriangle style={{ width: '16px', height: '16px', color: 'var(--danger)', marginRight: '8px' }} /> 
                        <span className="text-sm" style={{ color: 'var(--text-primary)' }}>{u}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="glass-panel card">
            <h2 className="card-title mb-4">Raw Risk Signals</h2>
            <div className="flex-col gap-2">
              {data.signals.map(s => (
                <div key={s.signal_id} style={{ padding: '12px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div className="font-semibold">{s.title}</div>
                    <div className="text-sm text-muted">{s.description}</div>
                  </div>
                  <div className={`badge ${s.severity === 'HIGH' ? 'badge-high' : 'badge-medium'}`}>
                    {s.severity}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - Actions */}
        <div className="flex-col gap-4">
          <div className="glass-panel card">
            <h2 className="card-title mb-4">Decision Engine</h2>
            
            <div style={{ padding: '16px', backgroundColor: 'rgba(0,0,0,0.2)', borderRadius: 'var(--radius-sm)', marginBottom: '24px' }}>
              <div className="text-xs font-bold text-muted mb-4" style={{ textTransform: 'uppercase' }}>AI Recommendation</div>
              <div className="font-bold" style={{ fontSize: '1.25rem' }}>{inv.recommended_action || "UNKNOWN"}</div>
            </div>

            {isResolved ? (
              <div style={{ padding: '16px', backgroundColor: 'var(--success-bg)', color: 'var(--success)', borderRadius: 'var(--radius-sm)', textAlign: 'center', fontWeight: '500' }}>
                Case resolved with decision: {data.final_decision}
              </div>
            ) : (
              <div className="flex-col gap-2">
                <button onClick={() => handleDecision('APPROVE')} className="btn btn-success w-full" style={{ padding: '12px' }}>
                  <CheckCircle style={{ width: '20px', height: '20px' }} /> Approve Transaction
                </button>
                <button onClick={() => handleDecision('MONITOR')} className="btn btn-outline w-full" style={{ padding: '12px', backgroundColor: 'var(--warning-bg)', color: 'var(--warning)', borderColor: 'var(--warning)' }}>
                  <Clock style={{ width: '20px', height: '20px' }} /> Monitor User
                </button>
                <button onClick={() => handleDecision('BLOCK')} className="btn btn-danger w-full" style={{ padding: '12px' }}>
                  <ShieldBan style={{ width: '20px', height: '20px' }} /> Block Transaction
                </button>
              </div>
            )}
          </div>
          
          <div className="glass-panel card">
            <h2 className="card-title mb-4">Transaction Details</h2>
            <div className="text-sm flex-col gap-2">
              <div className="flex justify-between" style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted">Transaction ID</span>
                <span className="font-medium" style={{ maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={data.transaction_id}>{data.transaction_id}</span>
              </div>
              <div className="flex justify-between" style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted">Amount</span>
                <span className="font-bold">{data.evidence?.observed_amount || 'N/A'}</span>
              </div>
              <div className="flex justify-between" style={{ paddingBottom: '8px', borderBottom: '1px solid var(--border-color)' }}>
                <span className="text-muted">Customer</span>
                <span className="font-medium" style={{ maxWidth: '100px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{data.customer_id}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Investigation;
