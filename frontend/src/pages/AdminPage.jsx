import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api.js';

function AdminPage({ user }) {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({ products: 0, orders: 0, users: 0, revenue: 0 });
  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
    fetchAllData();
  }, [user]);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      const [prodData, orderData] = await Promise.allSettled([
        api.getProducts('page_size=100'),
        api.getOrders(),
      ]);

      const prods = prodData.status === 'fulfilled' ? (prodData.value.results || prodData.value || []) : [];
      const ords = orderData.status === 'fulfilled' ? (Array.isArray(orderData.value) ? orderData.value : orderData.value.results || []) : [];

      setProducts(prods);
      setOrders(ords);

      const totalRevenue = ords.reduce((sum, o) => sum + parseFloat(o.total_amount || 0), 0);
      setStats({
        products: prods.length,
        orders: ords.length,
        users: new Set(ords.map(o => o.user_id)).size || 0,
        revenue: totalRevenue.toFixed(2),
      });
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const statusMap = { pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', processing: 'Đang xử lý', shipped: 'Đang giao', delivered: 'Đã giao', cancelled: 'Đã hủy' };
  const statusColors = { pending: '#ffc107', confirmed: '#8b83ff', processing: '#00d2ff', shipped: '#f7971e', delivered: '#00c9a7', cancelled: '#ff4757' };

  const tabs = [
    { id: 'dashboard', label: '📊 Dashboard', icon: '📊' },
    { id: 'products', label: '📦 Sản phẩm', icon: '📦' },
    { id: 'orders', label: '🛒 Đơn hàng', icon: '🛒' },
    { id: 'customers', label: '👥 Khách hàng', icon: '👥' },
  ];

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;

  return (
    <div style={{ paddingTop: '80px', minHeight: '100vh', display: 'flex' }}>
      {/* Sidebar */}
      <aside style={{
        width: '260px', background: 'var(--color-bg-secondary)', borderRight: '1px solid var(--color-border)',
        padding: 'var(--space-xl) 0', position: 'fixed', top: '70px', bottom: 0, overflowY: 'auto', zIndex: 10,
      }}>
        <div style={{ padding: '0 var(--space-lg)', marginBottom: 'var(--space-xl)' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-primary-light)' }}>⚙ Quản trị</h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>Bảng điều khiển</p>
        </div>
        {tabs.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'block', width: '100%', padding: 'var(--space-md) var(--space-lg)', textAlign: 'left',
              background: activeTab === tab.id ? 'rgba(108, 99, 255, 0.1)' : 'transparent',
              color: activeTab === tab.id ? 'var(--color-primary-light)' : 'var(--color-text-secondary)',
              borderLeft: activeTab === tab.id ? '3px solid var(--color-primary)' : '3px solid transparent',
              fontSize: '0.95rem', fontWeight: activeTab === tab.id ? 600 : 400, transition: 'all 0.2s',
            }}>{tab.label}</button>
        ))}
        <div style={{ padding: 'var(--space-xl) var(--space-lg)', borderTop: '1px solid var(--color-border)', marginTop: 'var(--space-xl)' }}>
          <Link to="/" className="btn btn-secondary btn-sm" style={{ width: '100%' }}>← Về trang chủ</Link>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ marginLeft: '260px', flex: 1, padding: 'var(--space-2xl)' }}>
        {activeTab === 'dashboard' && <DashboardTab stats={stats} orders={orders} />}
        {activeTab === 'products' && <ProductsTab products={products} />}
        {activeTab === 'orders' && <OrdersTab orders={orders} statusMap={statusMap} statusColors={statusColors} />}
        {activeTab === 'customers' && <CustomersTab orders={orders} />}
      </main>
    </div>
  );
}

function DashboardTab({ stats, orders }) {
  const statCards = [
    { label: 'Tổng sản phẩm', value: stats.products, icon: '📦', color: '#6c63ff' },
    { label: 'Tổng đơn hàng', value: stats.orders, icon: '🛒', color: '#00d2ff' },
    { label: 'Khách hàng', value: stats.users, icon: '👥', color: '#ff6b9d' },
    { label: 'Doanh thu', value: `$${stats.revenue}`, icon: '💰', color: '#00c9a7' },
  ];

  const recentOrders = orders.slice(0, 5);

  return (
    <div className="fade-in">
      <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: 'var(--space-2xl)' }}>Dashboard</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-lg)', marginBottom: 'var(--space-2xl)' }}>
        {statCards.map((s) => (
          <div key={s.label} style={{
            background: 'var(--gradient-card)', border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-lg)', padding: 'var(--space-xl)', position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ position: 'absolute', top: 'var(--space-md)', right: 'var(--space-md)', fontSize: '2rem', opacity: 0.3 }}>{s.icon}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: 'var(--space-sm)' }}>{s.label}</div>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: s.color }}>{s.value}</div>
          </div>
        ))}
      </div>

      <div style={{ background: 'var(--gradient-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-xl)' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 'var(--space-lg)' }}>Đơn hàng gần đây</h3>
        {recentOrders.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)' }}>Chưa có đơn hàng nào.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                <th style={thStyle}>Mã đơn</th>
                <th style={thStyle}>Ngày</th>
                <th style={thStyle}>Tổng tiền</th>
                <th style={thStyle}>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((o) => (
                <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={tdStyle}><code>{o.id.slice(0, 8)}</code></td>
                  <td style={tdStyle}>{new Date(o.created_at).toLocaleDateString('vi-VN')}</td>
                  <td style={tdStyle}><strong>${o.total_amount}</strong></td>
                  <td style={tdStyle}>
                    <span style={{ padding: '0.25rem 0.6rem', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600, background: 'rgba(108,99,255,0.1)', color: 'var(--color-primary-light)' }}>
                      {o.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function ProductsTab({ products }) {
  const [search, setSearch] = useState('');
  const filtered = products.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2xl)' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Quản lý sản phẩm</h2>
        <span style={{ color: 'var(--color-text-muted)' }}>{filtered.length} sản phẩm</span>
      </div>
      <input type="text" className="form-control" placeholder="Tìm kiếm sản phẩm..."
        value={search} onChange={(e) => setSearch(e.target.value)}
        style={{ maxWidth: '400px', marginBottom: 'var(--space-xl)' }} />

      <div style={{ background: 'var(--gradient-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Hình ảnh</th>
              <th style={thStyle}>Tên sản phẩm</th>
              <th style={thStyle}>Danh mục</th>
              <th style={thStyle}>Giá</th>
              <th style={thStyle}>Tồn kho</th>
              <th style={thStyle}>Đánh giá</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p) => (
              <tr key={p.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}>
                  <img src={p.image_url || 'https://placehold.co/40x40/1a1a2e/eee?text=SP'} alt={p.name}
                    style={{ width: 40, height: 40, borderRadius: '8px', objectFit: 'cover' }} />
                </td>
                <td style={tdStyle}>
                  <div style={{ fontWeight: 600 }}>{p.name}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{p.slug}</div>
                </td>
                <td style={tdStyle}><span style={{ padding: '0.2rem 0.6rem', background: 'rgba(108,99,255,0.1)', borderRadius: '12px', fontSize: '0.82rem', color: 'var(--color-primary-light)' }}>{p.category_name}</span></td>
                <td style={tdStyle}>
                  <strong>${p.price}</strong>
                  {p.compare_price && <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', textDecoration: 'line-through' }}>${p.compare_price}</div>}
                </td>
                <td style={tdStyle}>
                  <span style={{ color: p.stock > 10 ? 'var(--color-success)' : p.stock > 0 ? 'var(--color-warning)' : 'var(--color-danger)', fontWeight: 600 }}>{p.stock}</span>
                </td>
                <td style={tdStyle}><span style={{ color: 'var(--color-accent-warm)' }}>★</span> {p.rating}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function OrdersTab({ orders, statusMap, statusColors }) {
  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2xl)' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Quản lý đơn hàng</h2>
        <span style={{ color: 'var(--color-text-muted)' }}>{orders.length} đơn hàng</span>
      </div>
      <div style={{ background: 'var(--gradient-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Mã đơn</th>
              <th style={thStyle}>Ngày đặt</th>
              <th style={thStyle}>Sản phẩm</th>
              <th style={thStyle}>Tổng tiền</th>
              <th style={thStyle}>Trạng thái</th>
              <th style={thStyle}>Giao hàng</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}><code style={{ fontSize: '0.85rem' }}>{o.id.slice(0, 8)}</code></td>
                <td style={tdStyle}>{new Date(o.created_at).toLocaleDateString('vi-VN')}</td>
                <td style={tdStyle}>
                  {(o.items || []).map((i) => (
                    <div key={i.id} style={{ fontSize: '0.82rem' }}>{i.product_name} x{i.quantity}</div>
                  ))}
                </td>
                <td style={tdStyle}><strong style={{ color: 'var(--color-primary-light)' }}>${o.total_amount}</strong></td>
                <td style={tdStyle}>
                  <span style={{ padding: '0.25rem 0.6rem', borderRadius: '20px', fontSize: '0.78rem', fontWeight: 600, background: `${statusColors[o.status] || '#6c63ff'}20`, color: statusColors[o.status] || '#6c63ff' }}>
                    {statusMap[o.status] || o.status}
                  </span>
                </td>
                <td style={tdStyle}>
                  <div style={{ fontSize: '0.82rem' }}>{o.shipping_name || '-'}</div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{o.shipping_phone || ''}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {orders.length === 0 && <div style={{ padding: 'var(--space-2xl)', textAlign: 'center', color: 'var(--color-text-muted)' }}>Chưa có đơn hàng nào.</div>}
      </div>
    </div>
  );
}

function CustomersTab({ orders }) {
  // Aggregate customer data from orders
  const customerMap = {};
  orders.forEach((o) => {
    const key = o.user_id || o.shipping_name || 'unknown';
    if (!customerMap[key]) {
      customerMap[key] = { id: key, name: o.shipping_name || 'N/A', phone: o.shipping_phone || '', address: o.shipping_address || '', orderCount: 0, totalSpent: 0 };
    }
    customerMap[key].orderCount += 1;
    customerMap[key].totalSpent += parseFloat(o.total_amount || 0);
    if (o.shipping_name) customerMap[key].name = o.shipping_name;
    if (o.shipping_phone) customerMap[key].phone = o.shipping_phone;
  });
  const customers = Object.values(customerMap).sort((a, b) => b.totalSpent - a.totalSpent);

  return (
    <div className="fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2xl)' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Quản lý khách hàng</h2>
        <span style={{ color: 'var(--color-text-muted)' }}>{customers.length} khách hàng</span>
      </div>
      <div style={{ background: 'var(--gradient-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Khách hàng</th>
              <th style={thStyle}>Số điện thoại</th>
              <th style={thStyle}>Địa chỉ</th>
              <th style={thStyle}>Số đơn</th>
              <th style={thStyle}>Tổng chi tiêu</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                    <div style={{ width: 36, height: 36, borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 700, fontSize: '0.85rem' }}>
                      {c.name.charAt(0).toUpperCase()}
                    </div>
                    <div style={{ fontWeight: 600 }}>{c.name}</div>
                  </div>
                </td>
                <td style={tdStyle}>{c.phone || '-'}</td>
                <td style={tdStyle}><div style={{ fontSize: '0.82rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.address || '-'}</div></td>
                <td style={tdStyle}><span style={{ fontWeight: 600 }}>{c.orderCount}</span></td>
                <td style={tdStyle}><strong style={{ color: 'var(--color-success)' }}>${c.totalSpent.toFixed(2)}</strong></td>
              </tr>
            ))}
          </tbody>
        </table>
        {customers.length === 0 && <div style={{ padding: 'var(--space-2xl)', textAlign: 'center', color: 'var(--color-text-muted)' }}>Chưa có khách hàng nào.</div>}
      </div>
    </div>
  );
}

const thStyle = { padding: '0.75rem 1rem', textAlign: 'left', fontSize: '0.82rem', fontWeight: 600, color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px' };
const tdStyle = { padding: '0.75rem 1rem', fontSize: '0.9rem', color: 'var(--color-text-primary)' };

export default AdminPage;
