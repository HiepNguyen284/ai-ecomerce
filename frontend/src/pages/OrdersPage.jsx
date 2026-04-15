import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

function OrdersPage({ user, authReady = true }) {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authReady) return;
    if (!user) { setLoading(false); return; }
    api.getOrders().then((data) => setOrders(Array.isArray(data) ? data : data.results || [])).catch(console.error).finally(() => setLoading(false));
  }, [user, authReady]);

  const statusMap = { pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', processing: 'Đang xử lý', shipped: 'Đang giao', delivered: 'Đã giao', cancelled: 'Đã hủy' };
  const statusColors = { pending: '#f59e0b', confirmed: '#3b82f6', processing: '#06b6d4', shipped: '#f97316', delivered: '#059669', cancelled: '#ef4444' };

  if (!authReady) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;

  if (!user) return (
    <div className="orders-page"><div className="container"><div className="empty-state">
      <div className="icon">🔒</div><h3>Vui lòng đăng nhập để xem đơn hàng</h3>
      <p style={{ marginBottom: 'var(--space-xl)' }}>Bạn cần đăng nhập để xem lịch sử đơn hàng.</p>
      <Link to="/login" className="btn btn-primary">Đăng nhập</Link>
    </div></div></div>
  );

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;

  return (
    <div className="orders-page">
      <div className="container fade-in">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/">Trang chủ</Link>
          <span className="breadcrumb-sep">/</span>
          <span>Đơn hàng của tôi</span>
        </div>

        <h1 className="page-title">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: 10, verticalAlign: 'middle'}}>
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
          </svg>
          Đơn hàng của tôi
        </h1>
        
        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="icon">📦</div><h3>Chưa có đơn hàng</h3>
            <p style={{ marginBottom: 'var(--space-xl)' }}>Bắt đầu mua sắm để xem đơn hàng tại đây.</p>
            <Link to="/products" className="btn btn-primary">Xem sản phẩm</Link>
          </div>
        ) : (
          <div className="orders-list">
            {orders.map((order) => (
              <div key={order.id} className="order-card">
                <div className="order-card-header">
                  <div className="order-card-id">
                    <span className="order-label">Mã đơn hàng</span>
                    <code>{order.id.slice(0, 8)}...</code>
                  </div>
                  <div className="order-card-date">
                    {new Date(order.created_at).toLocaleDateString('vi-VN', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </div>
                  <span className="order-status-badge" style={{
                    color: statusColors[order.status],
                    background: `${statusColors[order.status]}15`,
                    border: `1px solid ${statusColors[order.status]}30`,
                  }}>
                    {statusMap[order.status] || order.status}
                  </span>
                </div>
                <div className="order-card-items">
                  {(order.items || []).map((item) => (
                    <div key={item.id} className="order-item">
                      <img src={item.product_image_url || 'https://placehold.co/60x60/f8fafc/334155?text=SP'} alt={item.product_name} className="order-item-img" />
                      <div className="order-item-info">
                        <div className="order-item-name">{item.product_name}</div>
                        <div className="order-item-qty">SL: {item.quantity} × {formatVND(item.product_price)}</div>
                      </div>
                      <div className="order-item-subtotal">{formatVND(item.subtotal)}</div>
                    </div>
                  ))}
                </div>
                <div className="order-card-footer">
                  <span>Tổng: <strong style={{ color: 'var(--color-primary)', fontSize: '1.15rem' }}>{formatVND(order.total_amount)}</strong></span>
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
