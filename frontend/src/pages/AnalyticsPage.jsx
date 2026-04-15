import { useEffect, useState, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

/* ─── helpers ─── */
function pct(v) { return `${(v * 100).toFixed(1)}%`; }

function churnLabel(risk) {
  if (risk >= 0.7) return { text: 'Cao', cls: 'risk-high' };
  if (risk >= 0.3) return { text: 'TB', cls: 'risk-med' };
  return { text: 'Thấp', cls: 'risk-low' };
}

function miniBar(value, max, color) {
  const w = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div className="an-mini-bar">
      <div className="an-mini-bar-fill" style={{ width: `${w}%`, background: color }} />
    </div>
  );
}

/* ─── Main ─── */
export default function AnalyticsPage({ user, authReady = true }) {
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [dash, setDash] = useState(null);
  const [segments, setSegments] = useState([]);
  const [churnData, setChurnData] = useState(null);
  const [rfmData, setRfmData] = useState(null);
  const [categoryData, setCategoryData] = useState([]);
  const [customers, setCustomers] = useState({ results: [], count: 0 });
  const [custPage, setCustPage] = useState(1);
  const [custSort, setCustSort] = useState('-monetary');
  const [custFilter, setCustFilter] = useState('all');
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const tabs = [
    { id: 'overview', label: 'Tổng quan', icon: '📊' },
    { id: 'segments', label: 'Phân khúc', icon: '🏷️' },
    { id: 'churn', label: 'Rủi ro rời bỏ', icon: '⚠️' },
    { id: 'rfm', label: 'Phân tích RFM', icon: '📈' },
    { id: 'categories', label: 'Danh mục', icon: '📦' },
    { id: 'customers', label: 'Khách hàng', icon: '👤' },
  ];

  /* ─── load data ─── */
  useEffect(() => {
    if (!authReady) return;
    if (!user) { navigate('/login'); return; }
    loadAll();
  }, [user, authReady]);

  async function loadAll() {
    setLoading(true);
    try {
      const [d, s, ch, rfm, cat] = await Promise.allSettled([
        api.getAnalyticsDashboard(),
        api.getAnalyticsSegments(),
        api.getAnalyticsChurnChart(),
        api.getAnalyticsRFMChart(),
        api.getAnalyticsCategories(),
      ]);
      if (d.status === 'fulfilled') setDash(d.value);
      if (s.status === 'fulfilled') setSegments(Array.isArray(s.value) ? s.value : []);
      if (ch.status === 'fulfilled') setChurnData(ch.value);
      if (rfm.status === 'fulfilled') setRfmData(rfm.value);
      if (cat.status === 'fulfilled') setCategoryData(Array.isArray(cat.value) ? cat.value : []);
    } catch { /* silent */ }
    setLoading(false);
  }

  useEffect(() => {
    if (tab === 'customers') loadCustomers();
  }, [tab, custPage, custSort, custFilter]);

  async function loadCustomers() {
    try {
      const params = `page=${custPage}&sort=${custSort}${custFilter !== 'all' ? `&churn_risk=${custFilter}` : ''}&page_size=15`;
      const res = await api.getAnalyticsCustomers(params);
      setCustomers(res);
    } catch { /* silent */ }
  }

  async function openCustomerDetail(customerId) {
    setDetailLoading(true);
    try {
      const detail = await api.getAnalyticsCustomerDetail(customerId);
      setSelectedCustomer(detail);
    } catch { setSelectedCustomer(null); }
    setDetailLoading(false);
  }

  /* ─── guards ─── */
  if (!authReady) return <div className="loading-spinner" style={{ paddingTop: 150 }}><div className="spinner" /></div>;
  if (!user) return null;

  if (loading) {
    return (
      <div className="an-layout">
        <div className="loading-spinner" style={{ paddingTop: 150, width: '100%' }}><div className="spinner" /></div>
      </div>
    );
  }

  const d = dash || {};

  return (
    <div className="an-layout">
      {/* Sidebar */}
      <aside className={`admin-sidebar ${sidebarCollapsed ? 'admin-sidebar--collapsed' : ''}`}>
        <div className="admin-sidebar-header">
          <div className="admin-sidebar-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="26" height="26">
              <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 002 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0022 16z" />
              <polyline points="7.5 4.21 12 6.81 16.5 4.21" /><polyline points="7.5 19.79 7.5 14.6 3 12" />
              <polyline points="21 12 16.5 14.6 16.5 19.79" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" />
              <line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
            {!sidebarCollapsed && <span>AI Analytics</span>}
          </div>
          <button className="admin-sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)}>
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
        </div>
        <nav className="admin-sidebar-nav">
          {tabs.map(t => (
            <button key={t.id} onClick={() => { setTab(t.id); setSelectedCustomer(null); }}
              className={`admin-sidebar-item${tab === t.id ? ' admin-sidebar-item--active' : ''}`} title={t.label}>
              <span className="admin-sidebar-icon">{t.icon}</span>
              {!sidebarCollapsed && <span className="admin-sidebar-label">{t.label}</span>}
            </button>
          ))}
        </nav>
        <div className="admin-sidebar-footer">
          <Link to="/admin" className="admin-sidebar-item" title="Quản trị">
            <span className="admin-sidebar-icon">⚙️</span>
            {!sidebarCollapsed && <span className="admin-sidebar-label">Quản trị</span>}
          </Link>
          <Link to="/" className="admin-sidebar-item" title="Trang chủ">
            <span className="admin-sidebar-icon">🏪</span>
            {!sidebarCollapsed && <span className="admin-sidebar-label">Trang chủ</span>}
          </Link>
        </div>
      </aside>

      {/* Main content */}
      <div className={`admin-content ${sidebarCollapsed ? 'admin-content--expanded' : ''}`}>
        <header className="admin-topbar">
          <div className="admin-topbar-left">
            <h1 className="admin-topbar-title">{tabs.find(t => t.id === tab)?.label || 'Analytics'}</h1>
            <span className="an-topbar-sub">Deep Learning Customer Behavior Analysis</span>
          </div>
          <div className="admin-topbar-right">
            <button className="btn btn-secondary btn-sm" onClick={loadAll} title="Làm mới">🔄 Làm mới</button>
            <div className="admin-topbar-user">
              <div className="admin-topbar-avatar">{(user.first_name || user.username || 'A').charAt(0).toUpperCase()}</div>
              <span>{user.first_name || user.username}</span>
            </div>
          </div>
        </header>

        <div className="admin-content-body">
          {tab === 'overview' && <OverviewTab d={d} segments={d.segments || []} />}
          {tab === 'segments' && <SegmentsTab segments={segments} dashSegments={d.segments || []} />}
          {tab === 'churn' && <ChurnTab data={churnData} atRisk={d.at_risk_customers || []} />}
          {tab === 'rfm' && <RFMTab data={rfmData} />}
          {tab === 'categories' && <CategoriesTab data={categoryData} />}
          {tab === 'customers' && (
            <CustomersTab
              customers={customers} page={custPage} setPage={setCustPage}
              sort={custSort} setSort={setCustSort} filter={custFilter} setFilter={setCustFilter}
              selectedCustomer={selectedCustomer} detailLoading={detailLoading}
              onSelectCustomer={openCustomerDetail} onCloseDetail={() => setSelectedCustomer(null)}
            />
          )}
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  Overview Tab                                      */
/* ══════════════════════════════════════════════════ */
function OverviewTab({ d, segments }) {
  const cards = [
    { label: 'Tổng khách hàng', value: d.total_customers?.toLocaleString() || 0, icon: '👥', color: '#6366f1', sub: `${d.total_events?.toLocaleString() || 0} sự kiện` },
    { label: 'CLV trung bình', value: formatVND(d.avg_clv || 0), icon: '💎', color: '#10b981', sub: `Max: ${formatVND(d.max_clv || 0)}` },
    { label: 'Rủi ro rời bỏ TB', value: pct(d.avg_churn_risk || 0), icon: '⚠️', color: '#f59e0b', sub: `${d.churn_distribution?.high || 0} KH nguy cơ cao` },
    { label: 'Doanh thu dự đoán', value: formatVND(d.total_predicted_revenue || 0), icon: '📈', color: '#ef4444', sub: 'Tổng CLV dự đoán' },
  ];

  return (
    <div className="fade-in">
      {/* Stat cards */}
      <div className="an-stat-grid">
        {cards.map(c => (
          <div key={c.label} className="an-stat-card">
            <div className="an-stat-icon" style={{ background: `${c.color}18`, color: c.color }}>{c.icon}</div>
            <div className="an-stat-info">
              <div className="an-stat-label">{c.label}</div>
              <div className="an-stat-value">{c.value}</div>
              <div className="an-stat-sub">{c.sub}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="an-grid-2">
        {/* Segments donut */}
        <div className="an-card">
          <div className="an-card-header"><h3>Phân khúc khách hàng</h3></div>
          <div className="an-card-body">
            {segments.length > 0 ? (
              <div className="an-donut-section">
                <DonutChart data={segments.map(s => ({ name: s.name_vi || s.name, value: s.customer_count, color: s.color }))} />
                <div className="an-legend">
                  {segments.map(s => (
                    <div key={s.segment_id} className="an-legend-item">
                      <span className="an-legend-dot" style={{ background: s.color }} />
                      <span className="an-legend-label">{s.name_vi || s.name}</span>
                      <span className="an-legend-value">{s.customer_count}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : <div className="an-empty">Chưa có dữ liệu phân khúc</div>}
          </div>
        </div>

        {/* Churn distribution */}
        <div className="an-card">
          <div className="an-card-header"><h3>Phân bố rủi ro rời bỏ</h3></div>
          <div className="an-card-body">
            <div className="an-churn-bars">
              {[
                { label: 'Thấp (<30%)', value: d.churn_distribution?.low || 0, color: '#10b981' },
                { label: 'Trung bình (30-70%)', value: d.churn_distribution?.medium || 0, color: '#f59e0b' },
                { label: 'Cao (>70%)', value: d.churn_distribution?.high || 0, color: '#ef4444' },
              ].map(b => (
                <div key={b.label} className="an-churn-bar-row">
                  <div className="an-churn-bar-label">{b.label}</div>
                  <div className="an-churn-bar-track">
                    <div className="an-churn-bar-fill" style={{
                      width: `${d.total_customers ? (b.value / d.total_customers * 100) : 0}%`,
                      background: b.color
                    }} />
                  </div>
                  <div className="an-churn-bar-value">{b.value}</div>
                </div>
              ))}
            </div>

            <div className="an-rfm-summary" style={{ marginTop: '1.5rem' }}>
              <h4 style={{ marginBottom: '0.75rem', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>RFM Trung bình</h4>
              <div className="an-rfm-cards">
                <div className="an-rfm-card">
                  <div className="an-rfm-card-label">Recency</div>
                  <div className="an-rfm-card-value">{d.rfm_summary?.avg_recency?.toFixed(0) || 0}</div>
                  <div className="an-rfm-card-unit">ngày</div>
                </div>
                <div className="an-rfm-card">
                  <div className="an-rfm-card-label">Frequency</div>
                  <div className="an-rfm-card-value">{d.rfm_summary?.avg_frequency?.toFixed(1) || 0}</div>
                  <div className="an-rfm-card-unit">đơn</div>
                </div>
                <div className="an-rfm-card">
                  <div className="an-rfm-card-label">Monetary</div>
                  <div className="an-rfm-card-value">{formatVND(d.rfm_summary?.avg_monetary || 0)}</div>
                  <div className="an-rfm-card-unit">tổng chi</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top spenders & at risk */}
      <div className="an-grid-2">
        <div className="an-card">
          <div className="an-card-header"><h3>🏆 Top khách hàng VIP</h3></div>
          <div className="an-card-body an-card-body--table">
            <table className="an-table"><thead><tr><th>#</th><th>Phân khúc</th><th>Tổng chi</th><th>CLV</th></tr></thead>
              <tbody>
                {(d.top_spenders || []).map((c, i) => (
                  <tr key={c.customer_id}>
                    <td><span className="an-rank">{i + 1}</span></td>
                    <td><span className="an-seg-badge" style={{ background: `${segColor(c.segment_name)}20`, color: segColor(c.segment_name) }}>{c.segment_name}</span></td>
                    <td><strong>{formatVND(c.monetary)}</strong></td>
                    <td>{formatVND(c.predicted_clv)}</td>
                  </tr>
                ))}
                {(!d.top_spenders || d.top_spenders.length === 0) && <tr><td colSpan={4} className="an-empty">Chưa có dữ liệu</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
        <div className="an-card">
          <div className="an-card-header"><h3>🚨 Khách hàng có nguy cơ rời bỏ</h3></div>
          <div className="an-card-body an-card-body--table">
            <table className="an-table"><thead><tr><th>Phân khúc</th><th>Nguy cơ</th><th>Tần suất</th><th>Lần cuối</th></tr></thead>
              <tbody>
                {(d.at_risk_customers || []).map(c => (
                  <tr key={c.customer_id}>
                    <td><span className="an-seg-badge" style={{ background: `${segColor(c.segment_name)}20`, color: segColor(c.segment_name) }}>{c.segment_name}</span></td>
                    <td><span className={`an-risk-badge ${churnLabel(c.churn_risk).cls}`}>{pct(c.churn_risk)}</span></td>
                    <td>{c.frequency} đơn</td>
                    <td>{c.recency_days} ngày trước</td>
                  </tr>
                ))}
                {(!d.at_risk_customers || d.at_risk_customers.length === 0) && <tr><td colSpan={4} className="an-empty">Không có</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Model info */}
      {d.recent_training && (
        <div className="an-card an-model-card">
          <div className="an-card-header"><h3>🧠 Mô hình Deep Learning</h3></div>
          <div className="an-card-body">
            <div className="an-model-grid">
              <div className="an-model-item"><span className="an-model-label">Phiên bản</span><span className="an-model-value">{d.recent_training.version}</span></div>
              <div className="an-model-item"><span className="an-model-label">Model</span><span className="an-model-value">{d.recent_training.model_name}</span></div>
              <div className="an-model-item"><span className="an-model-label">Loss</span><span className="an-model-value">{d.recent_training.final_loss?.toFixed(6)}</span></div>
              <div className="an-model-item"><span className="an-model-label">Samples</span><span className="an-model-value">{d.recent_training.num_samples}</span></div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  Segments Tab                                      */
/* ══════════════════════════════════════════════════ */
function SegmentsTab({ segments, dashSegments }) {
  const segs = segments.length > 0 ? segments : dashSegments;
  const maxMonetary = Math.max(...segs.map(s => parseFloat(s.avg_monetary || 0)), 1);

  return (
    <div className="fade-in">
      <div className="an-seg-grid">
        {segs.map(s => (
          <div key={s.segment_id || s.id} className="an-seg-card" style={{ borderTopColor: s.color }}>
            <div className="an-seg-card-header">
              <span className="an-seg-card-icon" style={{ background: `${s.color}18`, color: s.color }}>{s.icon === 'crown' ? '👑' : s.icon === 'heart' ? '❤️' : s.icon === 'trending-up' ? '📈' : s.icon === 'alert-triangle' ? '⚠️' : s.icon === 'moon' ? '🌙' : '👥'}</span>
              <div>
                <h3 className="an-seg-card-name">{s.name_vi || s.name}</h3>
                <p className="an-seg-card-desc">{s.description_vi || s.description}</p>
              </div>
            </div>
            <div className="an-seg-card-stats">
              <div className="an-seg-stat"><span className="an-seg-stat-value">{s.customer_count}</span><span className="an-seg-stat-label">Khách hàng</span></div>
              <div className="an-seg-stat"><span className="an-seg-stat-value">{formatVND(s.avg_clv || 0)}</span><span className="an-seg-stat-label">CLV TB</span></div>
              <div className="an-seg-stat"><span className="an-seg-stat-value">{formatVND(s.avg_monetary || 0)}</span><span className="an-seg-stat-label">Chi tiêu TB</span></div>
              <div className="an-seg-stat"><span className="an-seg-stat-value">{pct(s.avg_churn_risk || 0)}</span><span className="an-seg-stat-label">Nguy cơ rời</span></div>
            </div>
            {miniBar(parseFloat(s.avg_monetary || 0), maxMonetary, s.color)}
            {s.top_categories && s.top_categories.length > 0 && (
              <div className="an-seg-cats">
                <span className="an-seg-cats-label">Top danh mục:</span>
                {s.top_categories.slice(0, 3).map(c => (
                  <span key={c.name} className="an-seg-cat-tag">{c.name}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  Churn Tab                                         */
/* ══════════════════════════════════════════════════ */
function ChurnTab({ data, atRisk }) {
  if (!data) return <div className="an-empty">Đang tải dữ liệu...</div>;

  const maxCount = Math.max(...(data.histogram || []).map(h => h.count), 1);

  return (
    <div className="fade-in">
      <div className="an-card">
        <div className="an-card-header"><h3>📊 Phân bố Churn Risk (Histogram)</h3></div>
        <div className="an-card-body">
          <div className="an-histogram">
            {(data.histogram || []).map((bin, i) => (
              <div key={i} className="an-hist-bar-col">
                <div className="an-hist-count">{bin.count}</div>
                <div className="an-hist-bar" style={{
                  height: `${(bin.count / maxCount) * 180}px`,
                  background: bin.low >= 0.7 ? '#ef4444' : bin.low >= 0.3 ? '#f59e0b' : '#10b981',
                }} />
                <div className="an-hist-label">{bin.range}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="an-card" style={{ marginTop: '1.5rem' }}>
        <div className="an-card-header"><h3>Churn trung bình theo phân khúc</h3></div>
        <div className="an-card-body">
          <div className="an-churn-segment-grid">
            {(data.by_segment || []).map(s => (
              <div key={s.segment} className="an-churn-seg-card">
                <div className="an-churn-seg-name" style={{ color: s.color }}>{s.segment}</div>
                <div className="an-churn-seg-value">{pct(s.avg_churn)}</div>
                <div className="an-churn-seg-bar">
                  <div style={{ width: `${s.avg_churn * 100}%`, height: '6px', borderRadius: 3, background: s.color }} />
                </div>
                <div className="an-churn-seg-count">{s.count} khách</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {atRisk.length > 0 && (
        <div className="an-card" style={{ marginTop: '1.5rem' }}>
          <div className="an-card-header"><h3>🚨 Khách hàng nguy cơ cao nhất</h3></div>
          <div className="an-card-body an-card-body--table">
            <table className="an-table">
              <thead><tr><th>Email</th><th>Phân khúc</th><th>Churn Risk</th><th>Tần suất</th><th>Tổng chi</th></tr></thead>
              <tbody>
                {atRisk.map(c => (
                  <tr key={c.customer_id}>
                    <td>{c.customer_email || c.customer_id?.slice(0, 12)}</td>
                    <td><span className="an-seg-badge" style={{ background: `${segColor(c.segment_name)}20`, color: segColor(c.segment_name) }}>{c.segment_name}</span></td>
                    <td><span className={`an-risk-badge ${churnLabel(c.churn_risk).cls}`}>{pct(c.churn_risk)}</span></td>
                    <td>{c.frequency}</td>
                    <td>{formatVND(c.monetary)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  RFM Tab                                           */
/* ══════════════════════════════════════════════════ */
function RFMTab({ data }) {
  if (!data) return <div className="an-empty">Đang tải dữ liệu...</div>;

  const dist = data.distribution || {};
  const scatter = data.scatter || [];
  const maxF = Math.max(...scatter.map(s => s.frequency), 1);
  const maxR = Math.max(...scatter.map(s => s.recency), 1);

  return (
    <div className="fade-in">
      <div className="an-grid-3">
        {[
          { label: 'Recency (Ngày gần nhất)', data: dist.recency, unit: 'ngày', color: '#6366f1' },
          { label: 'Frequency (Tần suất)', data: dist.frequency, unit: 'đơn', color: '#10b981' },
          { label: 'Monetary (Giá trị)', data: dist.monetary, unit: '₫', color: '#f59e0b' },
        ].map(m => (
          <div key={m.label} className="an-rfm-metric-card" style={{ borderLeftColor: m.color }}>
            <h4>{m.label}</h4>
            <div className="an-rfm-metric-stats">
              <div><span className="an-rfm-metric-num">{m.data?.mean != null ? (m.unit === '₫' ? formatVND(m.data.mean) : m.data.mean) : '—'}</span><span>TB</span></div>
              <div><span className="an-rfm-metric-num">{m.data?.median != null ? (m.unit === '₫' ? formatVND(m.data.median) : m.data.median) : '—'}</span><span>Median</span></div>
              <div><span className="an-rfm-metric-num">{m.data?.max != null ? (m.unit === '₫' ? formatVND(m.data.max) : m.data.max) : '—'}</span><span>Max</span></div>
            </div>
          </div>
        ))}
      </div>

      <div className="an-card" style={{ marginTop: '1.5rem' }}>
        <div className="an-card-header"><h3>Biểu đồ R × F (kích thước = Monetary)</h3></div>
        <div className="an-card-body">
          <div className="an-scatter-wrap">
            <div className="an-scatter-y-label">Frequency ↑</div>
            <div className="an-scatter-area">
              {scatter.slice(0, 200).map((pt, i) => {
                const x = (pt.recency / maxR) * 100;
                const y = 100 - (pt.frequency / maxF) * 100;
                const size = Math.max(6, Math.min(Math.sqrt(pt.monetary / 1000000) * 4, 30));
                const color = segColor(pt.segment);
                return (
                  <div key={i} className="an-scatter-dot" title={`R:${pt.recency}d F:${pt.frequency} M:${formatVND(pt.monetary)}`}
                    style={{ left: `${x}%`, top: `${y}%`, width: size, height: size, background: color, opacity: 0.7 }} />
                );
              })}
            </div>
            <div className="an-scatter-x-label">Recency (ngày) →</div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  Categories Tab                                    */
/* ══════════════════════════════════════════════════ */
function CategoriesTab({ data }) {
  const maxRevenue = Math.max(...data.map(c => c.revenue), 1);

  return (
    <div className="fade-in">
      <div className="an-card">
        <div className="an-card-header"><h3>📦 Phân tích danh mục sản phẩm</h3></div>
        <div className="an-card-body an-card-body--table">
          <table className="an-table">
            <thead><tr><th>Danh mục</th><th>Doanh thu</th><th>Đơn hàng</th><th>Khách hàng</th><th>Giá trị TB</th><th style={{ width: 120 }}>Tỷ trọng</th></tr></thead>
            <tbody>
              {data.map((cat, i) => (
                <tr key={cat.category}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="an-rank">{i + 1}</span>
                      <strong>{cat.category}</strong>
                    </div>
                  </td>
                  <td><strong>{formatVND(cat.revenue)}</strong></td>
                  <td>{cat.purchases}</td>
                  <td>{cat.customers}</td>
                  <td>{formatVND(cat.avg_amount)}</td>
                  <td>{miniBar(cat.revenue, maxRevenue, catColors[i % catColors.length])}</td>
                </tr>
              ))}
              {data.length === 0 && <tr><td colSpan={6} className="an-empty">Chưa có dữ liệu</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  Customers Tab                                     */
/* ══════════════════════════════════════════════════ */
function CustomersTab({ customers, page, setPage, sort, setSort, filter, setFilter, selectedCustomer, detailLoading, onSelectCustomer, onCloseDetail }) {
  const rows = customers.results || [];

  return (
    <div className="fade-in" style={{ position: 'relative' }}>
      <div className="an-card">
        <div className="an-card-header">
          <h3>Danh sách khách hàng ({customers.count || 0})</h3>
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <select className="form-control" value={filter} onChange={e => { setFilter(e.target.value); setPage(1); }}
              style={{ width: 'auto', fontSize: '0.82rem' }}>
              <option value="all">Tất cả</option>
              <option value="high">Nguy cơ cao</option>
              <option value="medium">Nguy cơ TB</option>
              <option value="low">Nguy cơ thấp</option>
            </select>
            <select className="form-control" value={sort} onChange={e => { setSort(e.target.value); setPage(1); }}
              style={{ width: 'auto', fontSize: '0.82rem' }}>
              <option value="-monetary">Chi tiêu ↓</option>
              <option value="monetary">Chi tiêu ↑</option>
              <option value="-churn_risk">Rủi ro ↓</option>
              <option value="-predicted_clv">CLV ↓</option>
              <option value="-frequency">Tần suất ↓</option>
            </select>
          </div>
        </div>
        <div className="an-card-body an-card-body--table">
          <table className="an-table">
            <thead><tr>
              <th>Phân khúc</th><th>Tổng chi</th><th>Tần suất</th><th>Recency</th>
              <th>Churn Risk</th><th>CLV dự đoán</th><th></th>
            </tr></thead>
            <tbody>
              {rows.map(c => {
                const ch = churnLabel(c.churn_risk);
                return (
                  <tr key={c.customer_id} className="an-table-row-clickable" onClick={() => onSelectCustomer(c.customer_id)}>
                    <td><span className="an-seg-badge" style={{ background: `${segColor(c.segment_name)}20`, color: segColor(c.segment_name) }}>{c.segment_name || 'N/A'}</span></td>
                    <td><strong>{formatVND(c.monetary)}</strong></td>
                    <td>{c.frequency}</td>
                    <td>{c.recency_days}d</td>
                    <td><span className={`an-risk-badge ${ch.cls}`}>{pct(c.churn_risk)}</span></td>
                    <td>{formatVND(c.predicted_clv)}</td>
                    <td><button className="btn btn-secondary btn-sm">Chi tiết</button></td>
                  </tr>
                );
              })}
              {rows.length === 0 && <tr><td colSpan={7} className="an-empty">Không tìm thấy khách hàng</td></tr>}
            </tbody>
          </table>
        </div>
        {/* Pagination */}
        {customers.total_pages > 1 && (
          <div className="an-pagination">
            <button className="btn btn-secondary btn-sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Trước</button>
            <span>Trang {page} / {customers.total_pages}</span>
            <button className="btn btn-secondary btn-sm" disabled={page >= customers.total_pages} onClick={() => setPage(p => p + 1)}>Sau →</button>
          </div>
        )}
      </div>

      {/* Customer Detail Panel */}
      {(selectedCustomer || detailLoading) && (
        <div className="admin-panel-overlay" onClick={onCloseDetail}>
          <div className="an-detail-panel" onClick={e => e.stopPropagation()}>
            {detailLoading ? (
              <div className="loading-spinner"><div className="spinner" /></div>
            ) : selectedCustomer ? (
              <>
                <div className="admin-panel-header">
                  <h3>Chi tiết khách hàng</h3>
                  <button className="admin-panel-close" onClick={onCloseDetail}>✕</button>
                </div>
                <div className="an-detail-body">
                  <div className="an-detail-section">
                    <h4>Thông tin chung</h4>
                    <div className="an-detail-grid">
                      <div><span className="an-detail-label">Email</span><span>{selectedCustomer.customer_email || '—'}</span></div>
                      <div><span className="an-detail-label">Phân khúc</span><span className="an-seg-badge" style={{ background: `${segColor(selectedCustomer.segment_name)}20`, color: segColor(selectedCustomer.segment_name) }}>{selectedCustomer.segment_name}</span></div>
                      <div><span className="an-detail-label">Churn Risk</span><span className={`an-risk-badge ${churnLabel(selectedCustomer.churn_risk || 0).cls}`}>{pct(selectedCustomer.churn_risk || 0)}</span></div>
                      <div><span className="an-detail-label">CLV dự đoán</span><span>{formatVND(selectedCustomer.predicted_clv || 0)}</span></div>
                    </div>
                  </div>
                  <div className="an-detail-section">
                    <h4>Hành vi mua sắm</h4>
                    <div className="an-detail-grid">
                      <div><span className="an-detail-label">Tổng chi</span><span>{formatVND(selectedCustomer.monetary || 0)}</span></div>
                      <div><span className="an-detail-label">Tần suất</span><span>{selectedCustomer.frequency || 0} đơn</span></div>
                      <div><span className="an-detail-label">AOV</span><span>{formatVND(selectedCustomer.avg_order_value || 0)}</span></div>
                      <div><span className="an-detail-label">Recency</span><span>{selectedCustomer.recency_days || 0} ngày</span></div>
                      <div><span className="an-detail-label">SP đã mua</span><span>{selectedCustomer.unique_products_bought || 0}</span></div>
                      <div><span className="an-detail-label">Tỉ lệ hủy</span><span>{pct(selectedCustomer.cancelled_order_ratio || 0)}</span></div>
                    </div>
                  </div>
                  {selectedCustomer.top_categories && selectedCustomer.top_categories.length > 0 && (
                    <div className="an-detail-section">
                      <h4>Danh mục yêu thích</h4>
                      <div className="an-detail-tags">
                        {selectedCustomer.top_categories.map(c => <span key={c} className="an-seg-cat-tag">{c}</span>)}
                      </div>
                    </div>
                  )}
                  {selectedCustomer.recent_events && selectedCustomer.recent_events.length > 0 && (
                    <div className="an-detail-section">
                      <h4>Hoạt động gần đây</h4>
                      <div className="an-events-list">
                        {selectedCustomer.recent_events.slice(0, 10).map(e => (
                          <div key={e.id} className="an-event-row">
                            <span className={`an-event-type an-event-${e.event_type}`}>{eventLabel(e.event_type)}</span>
                            <span className="an-event-product">{e.product_name || '—'}</span>
                            <span className="an-event-amount">{e.amount > 0 ? formatVND(e.amount) : ''}</span>
                            <span className="an-event-time">{new Date(e.timestamp).toLocaleDateString('vi-VN')}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

/* ══════════════════════════════════════════════════ */
/*  Shared Components                                 */
/* ══════════════════════════════════════════════════ */
function DonutChart({ data }) {
  const total = data.reduce((s, d) => s + d.value, 0);
  if (total === 0) return <div className="an-empty">Không có dữ liệu</div>;

  let startAngle = 0;
  const arcs = data.map(d => {
    const angle = (d.value / total) * 360;
    const arc = { ...d, startAngle, angle };
    startAngle += angle;
    return arc;
  });

  function describeArc(cx, cy, r, start, angle) {
    const startRad = (start - 90) * Math.PI / 180;
    const endRad = (start + angle - 90) * Math.PI / 180;
    const x1 = cx + r * Math.cos(startRad);
    const y1 = cy + r * Math.sin(startRad);
    const x2 = cx + r * Math.cos(endRad);
    const y2 = cy + r * Math.sin(endRad);
    const large = angle > 180 ? 1 : 0;
    return `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${large} 1 ${x2} ${y2} Z`;
  }

  return (
    <svg viewBox="0 0 200 200" className="an-donut-svg">
      {arcs.map((a, i) => (
        <path key={i} d={describeArc(100, 100, 85, a.startAngle, Math.max(a.angle - 1, 0.5))}
          fill={a.color} opacity={0.85}>
          <title>{a.name}: {a.value}</title>
        </path>
      ))}
      <circle cx="100" cy="100" r="50" fill="var(--color-bg-primary)" />
      <text x="100" y="96" textAnchor="middle" fontSize="22" fontWeight="700" fill="var(--color-text-primary)">{total}</text>
      <text x="100" y="114" textAnchor="middle" fontSize="10" fill="var(--color-text-muted)">khách hàng</text>
    </svg>
  );
}

/* ─── Lookup helpers ─── */
const SEG_COLORS = { 'VIP Champions': '#f59e0b', 'Loyal Customers': '#10b981', 'Potential Growers': '#6366f1', 'At Risk': '#f97316', 'Hibernating': '#64748b' };
const catColors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316', '#ec4899', '#14b8a6', '#84cc16', '#a855f7', '#e11d48'];

function segColor(name) {
  if (!name) return '#6366f1';
  for (const [key, color] of Object.entries(SEG_COLORS)) {
    if (name.includes(key)) return color;
  }
  // fallback: hash-based
  let hash = 0;
  for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
  return catColors[Math.abs(hash) % catColors.length];
}

function eventLabel(type) {
  const map = { view: 'Xem', add_to_cart: 'Giỏ hàng', purchase: 'Mua', cancel: 'Hủy', search: 'Tìm kiếm', review: 'Đánh giá' };
  return map[type] || type;
}
