import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { casesApi } from '../services/api';
import { AlertTriangle, CheckCircle, Clock, ShieldBan, ArrowLeft, BrainCircuit, Info, Zap } from 'lucide-react';

const Investigation = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    casesApi.get(caseId)
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, [caseId]);

  const handleDecision = async (decision) => {
    try {
      await casesApi.updateDecision(caseId, decision, "Manual review decision");
      navigate('/cases');
    } catch (err) {
      console.error(err);
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount || 0);
  };

  const getRiskColor = (score) => {
    if (score >= 70) return 'text-danger';
    if (score >= 30) return 'text-warning';
    return 'text-success';
  };

  if (loading) return <div className="text-muted p-8 text-sm">Loading investigation record...</div>;
  if (!data) return <div className="text-danger p-8 text-sm">Failed to load case data.</div>;

  const inv = data.investigation || {};
  const isResolved = data.status === "RESOLVED" || data.status === "CONFIRMED_FRAUD" || data.status === "FALSE_POSITIVE";

  return (
    <div className="flex-col gap-4 pb-12">
      <Link to="/cases" className="flex items-center text-sm font-semibold text-muted mb-2 transition hover:text-primary">
        <ArrowLeft size={16} className="mr-2" /> Back to Risk Cases
      </Link>
      
      <div className="case-header">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="page-title mb-0" style={{ fontSize: '1.25rem' }}>CASE #{data.case_id.split('-')[0].toUpperCase()}</h1>
            <span className={`badge ${data.risk_score >= 70 ? 'badge-high' : data.risk_score >= 30 ? 'badge-medium' : 'badge-low'}`}>
              {data.status}
            </span>
          </div>
          <div className="font-mono text-xs text-muted flex gap-4">
            <span>TX: {data.transaction_id || 'N/A'}</span>
            <span>CUSTOMER: {data.customer_id || 'N/A'}</span>
          </div>
        </div>
        
        <div className="flex-col items-end">
          <div className="text-xs font-bold text-muted mb-1">RISK SCORE</div>
          <div className="flex items-baseline gap-1">
            <span className={`font-mono font-bold ${getRiskColor(data.risk_score)}`} style={{ fontSize: '2rem', lineHeight: '1' }}>
              {data.risk_score}
            </span>
            <span className="text-muted text-sm font-mono">/ 100</span>
          </div>
        </div>
      </div>

      <div className="grid-3-1">
        {/* Left Column */}
        <div className="flex-col gap-4">
          
          {/* AI Investigation Report */}
          <div className="card" style={{ borderTop: '3px solid var(--primary)' }}>
            <h2 className="card-title mb-4 flex items-center gap-2">
              <BrainCircuit size={18} className="text-primary" /> Groq AI Intelligence Report
            </h2>
            
            <div className="flex-col gap-6">
              <div>
                <div className="text-xs font-bold text-muted mb-2">SUMMARY</div>
                <div className="text-sm font-medium leading-relaxed">
                  {inv.summary || "No AI summary generated for this case."}
                </div>
              </div>

              <div className="grid-2">
                <div>
                  <div className="text-xs font-bold text-muted mb-2">EVIDENCE</div>
                  <div className="evidence-list">
                    {(inv.evidence || []).map((e, i) => (
                      <div key={i} className="evidence-item info flex items-start gap-2">
                        <CheckCircle size={14} className="text-primary mt-0.5 flex-shrink-0" />
                        <span>{e}</span>
                      </div>
                    ))}
                    {(!inv.evidence || inv.evidence.length === 0) && <div className="text-xs text-muted">None documented.</div>}
                  </div>
                </div>

                <div>
                  <div className="text-xs font-bold text-muted mb-2">REASONING</div>
                  <div className="evidence-list">
                    {(inv.reasoning || []).map((r, i) => (
                      <div key={i} className="evidence-item flex items-start gap-2">
                        <Info size={14} className="text-warning mt-0.5 flex-shrink-0" />
                        <span>{r}</span>
                      </div>
                    ))}
                    {(!inv.reasoning || inv.reasoning.length === 0) && <div className="text-xs text-muted">None documented.</div>}
                  </div>
                </div>
              </div>

              {inv.uncertainties && inv.uncertainties.length > 0 && (
                <div>
                  <div className="text-xs font-bold text-muted mb-2">UNCERTAINTIES & RISK VECTORS</div>
                  <div className="evidence-list">
                    {inv.uncertainties.map((u, i) => (
                      <div key={i} className="evidence-item critical flex items-start gap-2">
                        <AlertTriangle size={14} className="text-danger mt-0.5 flex-shrink-0" /> 
                        <span className="font-medium text-danger">{u}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Model Metrics */}
          <div className="grid-2 gap-4">
            <div className="card">
              <h2 className="card-title mb-4 flex items-center gap-2">
                <Zap size={16} className="text-warning" /> Risk Signals
              </h2>
              <div className="flex-col gap-2">
                {data.signals && data.signals.length > 0 ? (
                  data.signals.map(s => (
                    <div key={s.signal_id} className="flex justify-between items-center py-2 border-b border-[var(--border-color)] last:border-0">
                      <div>
                        <div className="font-semibold text-sm">{s.title}</div>
                        <div className="text-xs text-muted">{s.description}</div>
                      </div>
                      <span className={`badge ${s.severity === 'HIGH' ? 'badge-high' : 'badge-medium'}`}>
                        {s.severity}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted">No explicit risk signals triggered.</div>
                )}
              </div>
            </div>

            <div className="card">
              <h2 className="card-title mb-4">Model Decision</h2>
              <div className="flex-col gap-2">
                <div className="detail-row">
                  <span className="detail-label">Model Engine</span>
                  <span className="detail-value font-mono text-xs">LightGBM (IEEE-CIS)</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Fraud Probability</span>
                  <span className="detail-value font-mono text-xs">{(data.risk_score / 100).toFixed(4)}</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">Decision Threshold</span>
                  <span className="detail-value font-mono text-xs">0.3000 (Medium)</span>
                </div>
                <div className="detail-row">
                  <span className="detail-label">LLM Investigator</span>
                  <span className="detail-value font-mono text-xs">Groq Llama-3-8b</span>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column - Actions & Details */}
        <div className="flex-col gap-4">
          
          {/* Action Panel */}
          <div className="card flex-col">
            <h2 className="card-title mb-4">Investigation Actions</h2>
            
            <div className="mb-6 p-4 rounded bg-[var(--bg-base)] border border-[var(--border-color)]">
              <div className="text-xs font-bold text-muted mb-2">AI RECOMMENDED ACTION</div>
              <div className="font-bold font-mono text-lg" style={{ color: inv.recommended_action === 'BLOCK' ? 'var(--danger)' : 'var(--primary)' }}>
                {inv.recommended_action || "UNKNOWN"}
              </div>
            </div>

            {isResolved ? (
              <div className="p-4 rounded border border-[var(--border-color)] text-center">
                <div className="text-xs text-muted mb-1">FINAL DECISION</div>
                <div className="font-bold text-success flex items-center justify-center gap-2">
                  <CheckCircle size={16} /> {data.final_decision}
                </div>
              </div>
            ) : (
              <div className="flex-col gap-3">
                <button onClick={() => handleDecision('APPROVE')} className="btn btn-outline hover:bg-[var(--success-bg)] hover:text-success hover:border-[var(--success-border)] w-full py-3 transition-colors duration-200">
                  <CheckCircle size={18} /> Mark as Legitimate
                </button>
                <button onClick={() => handleDecision('MONITOR')} className="btn btn-outline hover:bg-[var(--warning-bg)] hover:text-warning hover:border-[var(--warning-border)] w-full py-3 transition-colors duration-200">
                  <Clock size={18} /> Send to Manual Review
                </button>
                <button onClick={() => handleDecision('BLOCK')} className="btn btn-danger w-full py-3 mt-2">
                  <ShieldBan size={18} /> Confirm Fraud & Block
                </button>
              </div>
            )}
          </div>
          
          {/* Transaction Metadata */}
          <div className="card">
            <h2 className="card-title mb-4">Transaction Details</h2>
            <div className="flex-col">
              <div className="detail-row">
                <span className="detail-label">Amount</span>
                <span className="detail-value font-mono">{formatCurrency(data.metadata?.amount / 100 || 0)}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Currency</span>
                <span className="detail-value font-mono">{data.metadata?.currency || 'INR'}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Timestamp</span>
                <span className="detail-value text-xs">{new Date(data.created_at).toLocaleString()}</span>
              </div>
              <div className="detail-row flex-col gap-1" style={{ alignItems: 'flex-start' }}>
                <span className="detail-label">Razorpay Event</span>
                <span className="detail-value font-mono text-xs break-all bg-[var(--bg-base)] p-2 rounded w-full border border-[var(--border-color)]">
                  payment.captured
                </span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Investigation;
