import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Shield, Activity, Search, Brain, Webhook, Settings, Database, Server, Bell, User } from 'lucide-react';

const Layout = () => {
  const location = useLocation();

  const isNavActive = (path) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-header">
          <Shield />
          <span>FraudSignal</span>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Overview</div>
          <Link to="/" className={`nav-item ${isNavActive('/') ? 'active' : ''}`}>
            <Activity />
            <span>Dashboard</span>
          </Link>
          <Link to="/cases" className={`nav-item ${isNavActive('/cases') ? 'active' : ''}`}>
            <Shield />
            <span>Risk Cases</span>
          </Link>

          <div className="nav-section-title">Intelligence</div>
          <Link to="#" className="nav-item">
            <Brain />
            <span>Model (M1)</span>
          </Link>
          <Link to="#" className="nav-item">
            <Webhook />
            <span>Webhooks</span>
          </Link>

          <div className="nav-section-title">System</div>
          <Link to="#" className="nav-item">
            <Settings />
            <span>Settings</span>
          </Link>
        </nav>
        
        <div className="sidebar-footer flex-col gap-2">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span>SYSTEM STATUS</span>
            <div className="flex items-center text-success">
              <span className="pulse-dot live" style={{ marginRight: '4px' }}></span>
              LIVE
            </div>
          </div>
          <div className="flex items-center gap-2 mt-2">
            <Server size={12} className="text-muted" />
            <span>API Operational</span>
          </div>
          <div className="flex items-center gap-2">
            <Database size={12} className="text-muted" />
            <span>MongoDB Connected</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <header className="top-header">
          <div className="flex items-center gap-2 text-sm text-muted">
            <span className="font-semibold text-primary">Risk Intelligence</span>
            <span>/</span>
            <span>{location.pathname === '/' ? 'Dashboard' : location.pathname.substring(1)}</span>
          </div>
          
          <div className="search-input-wrapper" style={{ margin: '0 auto' }}>
            <Search />
            <input type="text" placeholder="Search transaction, case ID..." className="form-input" />
          </div>

          <div className="flex items-center gap-4 text-muted">
            <button className="btn btn-outline" style={{ padding: '8px', border: 'none' }}>
              <Bell size={18} />
            </button>
            <button className="btn btn-outline" style={{ padding: '8px', border: 'none' }}>
              <User size={18} />
            </button>
          </div>
        </header>

        <main className="page-container animate-fade-in">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default Layout;