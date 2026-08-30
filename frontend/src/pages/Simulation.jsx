import React, { useState, useEffect } from 'react';
import { Play, CheckCircle, AlertCircle, Loader } from 'lucide-react';
import { razorpayApi } from '../services/api';

const Simulation = () => {
  const [amount, setAmount] = useState(500);
  const [profile, setProfile] = useState('SAFE');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null); // null, 'success', 'error'
  const [message, setMessage] = useState('');

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

      <div className="panel p-6 max-w-2xl">
        <h2 className="text-lg font-semibold mb-4">Generate Test Transaction</h2>
        
        <div className="space-y-4 mb-6">
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
          
          <div>
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
          className="btn btn-primary w-full flex justify-center items-center gap-2"
          onClick={handleSimulate}
          disabled={loading}
        >
          {loading ? <Loader className="animate-spin" size={18} /> : <Play size={18} />}
          {loading ? 'Processing...' : 'Simulate Payment'}
        </button>

        {status === 'success' && (
          <div className="mt-6 card border" style={{ borderColor: 'var(--success)' }}>
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
          <div className="mt-6 card border" style={{ borderColor: 'var(--danger)' }}>
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
    </div>
  );
};

export default Simulation;
