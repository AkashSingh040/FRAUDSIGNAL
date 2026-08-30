import React, { useState, useEffect } from 'react';
import { Play, CheckCircle, AlertCircle, Loader, Zap } from 'lucide-react';
import { razorpayApi, riskApi } from '../services/api';

const Simulation = () => {
  const [amount, setAmount] = useState(500);
  const [profile, setProfile] = useState('SAFE');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // null, 'success', 'error'
  const [message, setMessage] = useState('');

  const [seedLoading, setSeedLoading] = useState(false);
  const [seedStatus, setSeedStatus] = useState(null);
  const [seedMessage, setSeedMessage] = useState('');

  // Load Razorpay Script
  useEffect(() => {
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const handleSimulate = async () => {
    setLoading(true);
    setStatus(null);
    setMessage('');
    
    try {
      // 1. Create order on backend
      const res = await razorpayApi.createOrder(amount, profile);
      const { order_id, key_id, amount: orderAmount } = res.data;

      // 2. Initialize Razorpay Checkout
      const options = {
        key: key_id,
        amount: orderAmount,
        currency: 'INR',
        name: 'FraudSignal Demo',
        description: 'Test Transaction',
        order_id: order_id,
        handler: function (response) {
          // 3. Handle success
          setStatus('success');
          setMessage(`Payment successful! Payment ID: ${response.razorpay_payment_id}. The backend webhook is now processing this transaction through the risk engine. Check the Risk Cases page shortly.`);
          setLoading(false);
        },
        prefill: {
          name: 'Demo User',
          email: 'demo@example.com',
          contact: '9999999999'
        },
        theme: {
          color: '#3b82f6' // Match app primary color
        },
        modal: {
          ondismiss: function() {
            setLoading(false);
          }
        }
      };

      const rzp = new window.Razorpay(options);
      
      rzp.on('payment.failed', function (response){
        setStatus('error');
        setMessage(`Payment Failed: ${response.error.description}`);
        setLoading(false);
      });
      
      rzp.open();
    } catch (err) {
      console.error(err);
      setStatus('error');
      setMessage(err.response?.data?.detail || 'Failed to initiate simulation. Ensure backend keys are set.');
    } finally {
      if (status === 'error' || message) {
        setLoading(false);
      }
    }
  };

  const handleSeed = async () => {
    setSeedLoading(true);
    setSeedStatus(null);
    setSeedMessage('');
    try {
      const res = await riskApi.seed();
      setSeedStatus('success');
      setSeedMessage(res.data.message || 'Seeding started successfully.');
    } catch (err) {
      console.error(err);
      setSeedStatus('error');
      setSeedMessage(err.response?.data?.detail || 'Failed to trigger bulk seed.');
    } finally {
      setSeedLoading(false);
    }
  };

  // Add auto amount selection based on profile
  useEffect(() => {
    if (profile === 'SAFE') setAmount(450);
    if (profile === 'MEDIUM') setAmount(15000); // Triggers Elevated Amount
    if (profile === 'HIGH') setAmount(55000); // Triggers Unusually High Amount (> 50k threshold) + Notes
  }, [profile]);

  return (
    <div className="space-y-6">
      <div className="page-header">
        <div>
          <h1 className="text-2xl font-bold">Simulation & Demo</h1>
          <p className="text-muted mt-1">Generate live test transactions and evaluate risk engine responses in real-time.</p>
        </div>
      </div>

      <div className="grid-2">
        {/* Card 1: Live Simulation */}
        <div className="card flex-col h-full">
          <div className="card-header">
            <h2 className="card-title">Live Checkout Simulation</h2>
          </div>
          
          <div className="space-y-4 mb-6 flex-1">
            <div>
              <label className="block text-sm text-muted mb-2">Risk Profile</label>
              <select 
                className="form-input w-full"
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
              >
                <option value="SAFE">Safe (Low Amount, Normal Location)</option>
                <option value="MEDIUM">Suspicious (Elevated Amount &gt; 10k)</option>
                <option value="HIGH">High Risk (Location Mismatch & High Velocity)</option>
              </select>
            </div>
            
            <div className="pt-2">
              <label className="block text-sm text-muted mb-2">Amount (INR)</label>
              <input 
                type="number" 
                className="form-input w-full"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                min="1"
              />
            </div>
          </div>

          <button 
            className="btn btn-primary w-full flex justify-center items-center gap-2 py-3"
            onClick={handleSimulate}
            disabled={loading}
          >
            {loading ? <Loader className="animate-spin" size={18} /> : <Play size={18} />}
            {loading ? 'Processing...' : 'Simulate Payment'}
          </button>

          {status === 'success' && (
            <div className="mt-6 card border animate-fade-in" style={{ borderColor: 'var(--success)' }}>
              <div className="flex items-start gap-4">
                <div className="p-2 rounded-full" style={{ backgroundColor: 'rgba(0, 230, 118, 0.1)' }}>
                  <CheckCircle size={24} className="text-success shrink-0" />
                </div>
                <div>
                  <h4 className="font-bold text-lg text-success mb-1 tracking-wide">Transaction Completed</h4>
                  <p className="text-sm text-muted leading-relaxed">{message}</p>
                </div>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="mt-6 card border animate-fade-in" style={{ borderColor: 'var(--danger)' }}>
              <div className="flex items-start gap-4">
                <div className="p-2 rounded-full" style={{ backgroundColor: 'rgba(255, 71, 87, 0.1)' }}>
                  <AlertCircle size={24} className="text-danger shrink-0" />
                </div>
                <div>
                  <h4 className="font-bold text-lg text-danger mb-1 tracking-wide">Simulation Failed</h4>
                  <p className="text-sm text-muted leading-relaxed">{message}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Card 2: Bulk Seed Database */}
        <div className="card flex-col h-full">
          <div className="card-header">
            <h2 className="card-title">Bulk Demo Seed</h2>
          </div>
          
          <div className="flex-1">
            <p className="text-sm text-muted leading-relaxed mb-6">
              Bypass the Razorpay checkout popup entirely and instantly push <strong className="text-primary">10 highly-randomized transactions</strong> directly into the backend risk engine pipeline.
            </p>
            
            <ul className="text-sm text-muted space-y-3 mb-8">
              <li className="flex items-center gap-2">
                <span className="w-1-5 h-1-5 rounded-full bg-success"></span>
                <strong>5 Safe:</strong> Low amount, local IP.
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1-5 h-1-5 rounded-full bg-warning"></span>
                <strong>3 Medium:</strong> Elevated amounts.
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1-5 h-1-5 rounded-full bg-danger"></span>
                <strong>2 High Risk:</strong> High velocity, foreign IPs.
              </li>
            </ul>
          </div>

          <button 
            className="btn btn-outline w-full flex justify-center items-center gap-2 py-3 border-dashed"
            onClick={handleSeed}
            disabled={seedLoading}
          >
            {seedLoading ? <Loader className="animate-spin" size={18} /> : <Zap size={18} className="text-primary" />}
            {seedLoading ? 'Seeding Database...' : 'Run Bulk Seed Demo'}
          </button>
          
          {seedStatus === 'success' && (
            <div className="mt-6 p-4 rounded card border animate-fade-in flex items-start gap-3" style={{ borderColor: 'rgba(0, 230, 118, 0.3)', backgroundColor: 'rgba(0, 230, 118, 0.05)' }}>
              <CheckCircle size={20} className="text-success shrink-0 mt-0-5" />
              <span className="text-sm font-medium text-success">{seedMessage}</span>
            </div>
          )}
          {seedStatus === 'error' && (
            <div className="mt-6 p-4 rounded card border animate-fade-in flex items-start gap-3" style={{ borderColor: 'rgba(255, 71, 87, 0.3)', backgroundColor: 'rgba(255, 71, 87, 0.05)' }}>
              <AlertCircle size={20} className="text-danger shrink-0 mt-0-5" />
              <span className="text-sm font-medium text-danger">{seedMessage}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Simulation;
