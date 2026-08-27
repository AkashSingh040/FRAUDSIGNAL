import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { casesApi } from '../services/api';
import { AlertTriangle, CheckCircle, Clock, ShieldBan, ArrowLeft, BrainCircuit, Info, Zap, XCircle, FileJson, Crosshair } from 'lucide-react';

const Investigation = () => {
  const { caseId } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showRawJson, setShowRawJson] = useState(false);

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

  // Determine final decision badge styling
  let finalDecisionIcon = <CheckCircle size={16} />;
  let finalDecisionColor = 'text-success';
  if (data.final_decision === 'BLOCK') {
    finalDecisionIcon = <ShieldBan size={16} />;
    finalDecisionColor = 'text-danger';
  } else if (data.final_decision === 'MONITOR') {
    finalDecisionIcon = <Clock size={16} />;
    finalDecisionColor = 'text-warning';
  }

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
            <div className="flex justify-between items-start mb-6">
              <h2 className="card-title flex items-center gap-2">
                <BrainCircuit size={18} className="text-primary" /> Groq AI Intelligence Report
              </h2>
              {inv.recommended_action && (
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-muted">AI ACTION:</span>
                  <span className={`badge ${inv.recommended_action === 'BLOCK' ? 'badge-high' : inv.recommended_action === 'MONITOR' ? 'badge-medium' : 'badge-low'}`}>
                    {inv.recommended_action}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex-col gap-6">
              <div className="p-4 rounded bg-base border border-color">
                <div className="text-xs font-bold text-muted mb-2 uppercase tracking-wider flex items-center gap-2">
                  <Info size={14} className="text-primary" /> Executive Summary
                </div>
                <div className="text-sm font-medium leading-relaxed">
                  {inv.summary || "No AI summary generated for this case."}
                </div>
              </div>

              <div className="grid-2">
                <div>
                  <div className="text-xs font-bold text-muted mb-3 uppercase tracking-wider">Factual Evidence</div>
                  <div className="flex-col gap-2">
                    {(inv.evidence || []).map((e, i) => (
                      <div key={i} className="p-3 text-sm rounded log-block-evidence flex items-start gap-3">
                        <Crosshair size={14} className="text-primary mt-0-5 flex-shrink-0" />
                        <span className="leading-tight">{e}</span>
                      </div>
                    ))}
                    {(!inv.evidence || inv.evidence.length === 0) && <div className="text-xs text-muted">None documented.</div>}
                  </div>
                </div>

                <div>
                  <div className="text-xs font-bold text-muted mb-3 uppercase tracking-wider">Logical Reasoning</div>
                  <div className="flex-col gap-2">
                    {(inv.reasoning || []).map((r, i) => (
                      <div key={i} className="p-3 text-sm rounded log-block-reasoning flex items-start gap-3">
                        <Info size={14} className="text-warning mt-0-5 flex-shrink-0" />
                        <span className="leading-tight">{r}</span>
                      </div>
                    ))}
                    {(!inv.reasoning || inv.reasoning.length === 0) && <div className="text-xs text-muted">None documented.</div>}
                  </div>
                </div>
              </div>

              {inv.uncertainties && inv.uncertainties.length > 0 && (
                <div className="p-4 rounded log-block-danger">
                  <div className="text-xs font-bold text-danger mb-2 uppercase tracking-wider flex items-center gap-2">
                    <AlertTriangle size={14} /> Uncertainties & Risk Vectors
                  </div>
                  <div className="flex-col gap-2">
                    {inv.uncertainties.map((u, i) => (
                      <div key={i} className="flex items-start gap-2 text-sm text-danger">
                        <span className="mt-1 flex-shrink-0 w-1-5 h-1-5 rounded-full bg-danger"></span>
                        <span>{u}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Model Metrics */}
          <div className="grid-2 gap-4">
            <div className="card h-full">
              <h2 className="card-title mb-4 flex items-center gap-2">
                <Zap size={16} className="text-warning" /> LightGBM Telemetry
              </h2>
              <div className="flex-col gap-3">
                {data.signals && data.signals.length > 0 ? (
                  data.signals.map(s => (
                    <div key={s.signal_id} className="p-3 rounded bg-base border border-color">
                      <div className="flex justify-between items-start mb-1">
                        <div className="font-semibold text-sm">{s.title}</div>
                        <span className={`badge ${s.severity === 'HIGH' ? 'badge-high' : 'badge-medium'}`}>
                          {s.severity}
                        </span>
                      </div>
                      <div className="text-xs text-muted leading-relaxed">{s.description}</div>
                    </div>
                  ))
                ) : (
                  <div className="text-xs text-muted p-3 border border-dashed border-color rounded text-center">No explicit telemetry thresholds breached.</div>
                )}
              </div>
            </div>

            <div className="card h-full flex flex-col">
              <h2 className="card-title mb-4">Detection Engine Specs</h2>
              <div className="flex-col gap-3 flex-1 justify-center">
                <div className="detail-row py-2 border-b border-color">
                  <span className="detail-label">Model Engine</span>
                  <span className="detail-value font-mono text-xs">LightGBM (IEEE-CIS)</span>
                </div>
                <div className="detail-row py-2 border-b border-color">
                  <span className="detail-label">Fraud Probability</span>
                  <span className="detail-value font-mono text-xs text-warning">{(data.risk_score / 100).toFixed(4)}</span>
                </div>
                <div className="detail-row py-2 border-b border-color">
                  <span className="detail-label">Decision Threshold</span>
                  <span className="detail-value font-mono text-xs">0.6000 (Optimized)</span>
                </div>
                <div className="detail-row py-2">
                  <span className="detail-label">LLM Investigator</span>
                  <span className="detail-value font-mono text-xs text-primary">Groq Llama-3-8b</span>
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

            {isResolved ? (
              <div className="p-4 rounded border border-color text-center bg-base">
                <div className="text-xs text-muted mb-2 tracking-wider uppercase">Final Decision Applied</div>
                <div className={`font-bold ${finalDecisionColor} flex items-center justify-center gap-2 text-lg`}>
                  {finalDecisionIcon} {data.final_decision}
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
                <span className="detail-value font-mono">{formatCurrency(data.evidence?.observed_amount || 0)}</span>
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
                <span className="detail-value font-mono text-xs break-all bg-base p-2 rounded w-full border border-color">
                  payment.captured
                </span>
              </div>
            </div>
            
            {/* Raw JSON Viewer */}
            <div className="mt-4 pt-4 border-t border-color">
              <button 
                onClick={() => setShowRawJson(!showRawJson)} 
                className="flex items-center justify-between w-full text-xs font-bold text-muted hover:text-primary transition-colors uppercase tracking-wider"
              >
                <div className="flex items-center gap-2">
                  <FileJson size={14} /> View Raw Payload
                </div>
                <span>{showRawJson ? '-' : '+'}</span>
              </button>
              
              {showRawJson && (
                <div className="mt-3 p-3 bg-black border border-color rounded overflow-x-auto">
                  <pre className="text-[10px] font-mono text-muted m-0">
                    {JSON.stringify(data.metadata || data.evidence, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
};

export default Investigation;
