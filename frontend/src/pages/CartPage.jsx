import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

function CartPage({ user, setCartCount, authReady = true }) {
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [orderForm, setOrderForm] = useState({ shipping_name: '', shipping_phone: '', shipping_address: '', note: '' });
  const [showCheckout, setShowCheckout] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!authReady) return;
    if (!user) { setLoading(false); return; }
    fetchCart();
  }, [user, authReady]);

  const fetchCart = async () => {
    try { const data = await api.getCart(); setCart(data); setCartCount(data.total_items || 0); }
    catch { setError('Không thể tải giỏ hàng.'); }
    finally { setLoading(false); }
  };

  const handleUpdateQuantity = async (itemId, qty) => {
    try { const data = await api.updateCartItem(itemId, qty); setCart(data); setCartCount(data.total_items || 0); }
    catch { setError('Không thể cập nhật.'); }
  };

  const handleRemoveItem = async (itemId) => {
    try { const data = await api.removeCartItem(itemId); setCart(data); setCartCount(data.total_items || 0); }
    catch { setError('Không thể xóa sản phẩm.'); }
  };

  const handleCheckout = async (e) => {
    e.preventDefault(); setSubmitting(true); setError('');
    try {
      const order = await api.createOrder(orderForm);
      await api.createPayment({ order_id: order.id, method: 'cod' });
      let clearedCart = null;
      try {
        clearedCart = await api.clearCart();
      } catch {
        clearedCart = null;
      }
      setMessage('Đặt hàng thành công!');
      setCart(clearedCart || { ...cart, items: [], total_items: 0, total_price: '0.00' });
      setCartCount(0); setShowCheckout(false);
      setTimeout(() => navigate('/orders'), 2000);
    } catch (err) { setError(err.error || 'Đặt hàng thất bại.'); }
    finally { setSubmitting(false); }
  };

  if (!authReady) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;

  if (!user) return (
    <div className="cart-page"><div className="container"><div className="empty-state">
      <div className="icon">🔒</div><h3>Vui lòng đăng nhập để xem giỏ hàng</h3>
      <p style={{ marginBottom: 'var(--space-xl)' }}>Bạn cần đăng nhập để quản lý giỏ hàng.</p>
      <Link to="/login" className="btn btn-primary">Đăng nhập</Link>
    </div></div></div>
  );

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;
  const items = cart?.items || [];

  return (
    <div className="cart-page">
      <div className="container fade-in">
        {/* Breadcrumb */}
        <div className="breadcrumb">
          <Link to="/">Trang chủ</Link>
          <span className="breadcrumb-sep">/</span>
          <span>Giỏ hàng</span>
        </div>

        <h1 className="page-title">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: 10, verticalAlign: 'middle'}}>
            <circle cx="9" cy="20" r="1"></circle>
            <circle cx="18" cy="20" r="1"></circle>
            <path d="M2 3h2l2.7 11.5a2 2 0 0 0 2 1.5h8.9a2 2 0 0 0 1.9-1.4L22 7H6"></path>
          </svg>
          Giỏ hàng {items.length > 0 && <span className="page-title-sub">({cart.total_items} sản phẩm)</span>}
        </h1>
        {message && <div className="alert alert-success">{message}</div>}
        {error && <div className="alert alert-error">{error}</div>}
        {items.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🛒</div><h3>Giỏ hàng trống</h3>
            <p style={{ marginBottom: 'var(--space-xl)' }}>Bạn chưa thêm sản phẩm nào.</p>
            <Link to="/products" className="btn btn-primary">Xem sản phẩm</Link>
          </div>
        ) : (
          <div className="two-col-layout">
            <div>
              {items.map((item) => (
                <div className="cart-item" key={item.id}>
                  <div className="cart-item-image"><img src={item.product_image_url || 'https://placehold.co/200x200/f8fafc/334155?text=SP'} alt={item.product_name} /></div>
                  <div className="cart-item-info">
                    <h3>{item.product_name}</h3>
                    <div className="price">{formatVND(item.product_price)}</div>
                    <div className="cart-item-actions">
                      <div className="quantity-control">
                        <button onClick={() => handleUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}>−</button>
                        <span>{item.quantity}</span>
                        <button onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}>+</button>
                      </div>
                      <button className="btn btn-secondary btn-sm" onClick={() => handleRemoveItem(item.id)} style={{ color: 'var(--color-danger)' }}>Xóa</button>
                    </div>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '1.1rem', whiteSpace: 'nowrap', color: 'var(--color-primary)' }}>{formatVND(item.subtotal)}</div>
                </div>
              ))}
            </div>
            <div className="cart-summary">
              {!showCheckout ? (
                <>
                  <h3>Tóm tắt đơn hàng</h3>
                  <div className="cart-summary-row"><span>Tạm tính</span><span>{formatVND(cart.total_price)}</span></div>
                  <div className="cart-summary-row"><span>Phí vận chuyển</span><span style={{ color: 'var(--color-success)' }}>Miễn phí</span></div>
                  <div className="cart-summary-row total"><span>Tổng cộng</span><span>{formatVND(cart.total_price)}</span></div>
                  <button className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 'var(--space-lg)' }} onClick={() => setShowCheckout(true)} id="checkout-button">Tiến hành thanh toán →</button>
                </>
              ) : (
                <>
                  <h3>Thông tin giao hàng</h3>
                  <form onSubmit={handleCheckout}>
                    <div className="form-group"><label>Họ và tên</label><input type="text" className="form-control" required value={orderForm.shipping_name} onChange={(e) => setOrderForm({ ...orderForm, shipping_name: e.target.value })} /></div>
                    <div className="form-group"><label>Số điện thoại</label><input type="tel" className="form-control" required value={orderForm.shipping_phone} onChange={(e) => setOrderForm({ ...orderForm, shipping_phone: e.target.value })} /></div>
                    <div className="form-group"><label>Địa chỉ</label><textarea className="form-control" rows="3" required value={orderForm.shipping_address} onChange={(e) => setOrderForm({ ...orderForm, shipping_address: e.target.value })} /></div>
                    <div className="form-group"><label>Ghi chú</label><input type="text" className="form-control" value={orderForm.note} onChange={(e) => setOrderForm({ ...orderForm, note: e.target.value })} /></div>
                    <div className="cart-summary-row total"><span>Tổng cộng</span><span>{formatVND(cart.total_price)}</span></div>
                    <button type="submit" className="btn btn-primary btn-lg" style={{ width: '100%', marginTop: 'var(--space-md)' }} disabled={submitting}>{submitting ? 'Đang xử lý...' : '💳 Đặt hàng (COD)'}</button>
                    <button type="button" className="btn btn-secondary" style={{ width: '100%', marginTop: 'var(--space-sm)' }} onClick={() => setShowCheckout(false)}>← Quay lại</button>
                  </form>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default CartPage;
