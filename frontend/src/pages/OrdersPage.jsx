import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';

function OrdersPage({ user }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    api.getOrders().then((data) => setOrders(Array.isArray(data) ? data : data.results || [])).catch(console.error).finally(() => setLoading(false));
  }, [user]);

  const statusMap = { pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', processing: 'Đang xử lý', shipped: 'Đang giao', delivered: 'Đã giao', cancelled: 'Đã hủy' };
  const statusColors = { pending: 'var(--color-warning)', confirmed: 'var(--color-primary-light)', processing: 'var(--color-secondary)', shipped: 'var(--color-accent-warm)', delivered: 'var(--color-success)', cancelled: 'var(--color-danger)' };

  if (!user) return (
    <div className="section" style={{ paddingTop: '100px', minHeight: '100vh' }}><div className="container"><div className="empty-state">
      <div className="icon">🔒</div><h3>Vui lòng đăng nhập để xem đơn hàng</h3>
      <p style={{ marginBottom: 'var(--space-xl)' }}>Bạn cần đăng nhập để xem lịch sử đơn hàng.</p>
      <Link to="/login" className="btn btn-primary">Đăng nhập</Link>
    </div></div></div>
  );

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;

  return (
    <div className="section" style={{ paddingTop: '100px', minHeight: '100vh' }}>
      <div className="container fade-in">
        <div className="section-header" style={{ textAlign: 'left' }}><h2>Đơn hàng của tôi</h2><p>Theo dõi và quản lý đơn hàng</p></div>
        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📦</div><h3>Chưa có đơn hàng</h3>
            <p style={{ marginBottom: 'var(--space-xl)' }}>Bắt đầu mua sắm để xem đơn hàng tại đây.</p>
            <Link to="/products" className="btn btn-primary">Xem sản phẩm</Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-lg)' }}>
            {orders.map((order) => (
              <div key={order.id} style={{ background: 'var(--gradient-card)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-xl)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-lg)', flexWrap: 'wrap', gap: 'var(--space-md)' }}>
                  <div>
                    <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginBottom: '4px' }}>Mã đơn hàng</div>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', fontFamily: 'monospace' }}>{order.id.slice(0, 8)}...</div>
                  </div>
                  <div style={{ padding: '0.35rem 1rem', borderRadius: 'var(--radius-full)', fontSize: '0.82rem', fontWeight: 700, color: statusColors[order.status], background: `${statusColors[order.status]}15`, border: `1px solid ${statusColors[order.status]}30`, textTransform: 'capitalize' }}>
                    {statusMap[order.status] || order.status}
                  </div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                  {(order.items || []).map((item) => (
                    <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-sm) 0', borderBottom: '1px solid var(--color-border)' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
                        <img src={item.product_image_url || 'https://placehold.co/50x50/1a1a2e/eee?text=SP'} alt={item.product_name} style={{ width: 50, height: 50, borderRadius: 'var(--radius-sm)', objectFit: 'cover' }} />
                        <div>
                          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{item.product_name}</div>
                          <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>SL: {item.quantity} × ${item.product_price}</div>
                        </div>
                      </div>
                      <div style={{ fontWeight: 700 }}>${item.subtotal}</div>
                    </div>
                  ))}
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--space-lg)', paddingTop: 'var(--space-md)' }}>
                  <div style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)' }}>
                    {new Date(order.created_at).toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>Tổng: <span style={{ color: 'var(--color-primary-light)' }}>${order.total_amount}</span></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default OrdersPage;
