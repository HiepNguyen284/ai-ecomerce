import { Link, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from '../services/api.js';

function CartPage({ user, setCartCount }) {
  const navigate = useNavigate();
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [orderForm, setOrderForm] = useState({
    shipping_name: '',
    shipping_phone: '',
    shipping_address: '',
    note: '',
  });
  const [showCheckout, setShowCheckout] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    fetchCart();
  }, [user]);

  const fetchCart = async () => {
    try {
      const data = await api.getCart();
      setCart(data);
      setCartCount(data.total_items || 0);
    } catch (err) {
      setError('Failed to load cart.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateQuantity = async (itemId, quantity) => {
    try {
      const data = await api.updateCartItem(itemId, quantity);
      setCart(data);
      setCartCount(data.total_items || 0);
    } catch (err) {
      setError('Failed to update item.');
    }
  };

  const handleRemoveItem = async (itemId) => {
    try {
      const data = await api.removeCartItem(itemId);
      setCart(data);
      setCartCount(data.total_items || 0);
    } catch (err) {
      setError('Failed to remove item.');
    }
  };

  const handleCheckout = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const order = await api.createOrder(orderForm);
      // Auto-pay with COD
      await api.createPayment({ order_id: order.id, method: 'cod' });
      setMessage('Order placed successfully!');
      setCart({ ...cart, items: [], total_items: 0, total_price: '0.00' });
      setCartCount(0);
      setShowCheckout(false);
      setTimeout(() => navigate('/orders'), 2000);
    } catch (err) {
      setError(err.error || 'Failed to place order.');
    } finally {
      setSubmitting(false);
    }
  };

  if (!user) {
    return (
      <div className="cart-page">
        <div className="container">
          <div className="empty-state">
            <div className="icon">🔒</div>
            <h3>Please sign in to view your cart</h3>
            <p style={{ marginBottom: 'var(--space-xl)' }}>You need to be logged in to manage your shopping cart.</p>
            <Link to="/login" className="btn btn-primary">Sign In</Link>
          </div>
        </div>
      </div>
    );
  }

  if (loading) return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;

  const items = cart?.items || [];

  return (
    <div className="cart-page">
      <div className="container fade-in">
        <h1 style={{ fontSize: '2rem', fontWeight: 800, marginBottom: 'var(--space-2xl)' }}>
          Shopping Cart {items.length > 0 && <span style={{ color: 'var(--color-text-muted)', fontSize: '1rem' }}>({cart.total_items} items)</span>}
        </h1>

        {message && <div className="alert alert-success">{message}</div>}
        {error && <div className="alert alert-error">{error}</div>}

        {items.length === 0 ? (
          <div className="empty-state">
            <div className="icon">🛒</div>
            <h3>Your cart is empty</h3>
            <p style={{ marginBottom: 'var(--space-xl)' }}>Looks like you haven't added anything yet.</p>
            <Link to="/products" className="btn btn-primary">Browse Products</Link>
          </div>
        ) : (
          <div className="two-col-layout">
            {/* Cart Items */}
            <div>
              {items.map((item) => (
                <div className="cart-item" key={item.id}>
                  <div className="cart-item-image">
                    <img src={item.product_image_url || `https://placehold.co/200x200/1a1a2e/eee?text=Product`} alt={item.product_name} />
                  </div>
                  <div className="cart-item-info">
                    <h3>{item.product_name}</h3>
                    <div className="price">${item.product_price}</div>
                    <div className="cart-item-actions">
                      <div className="quantity-control">
                        <button onClick={() => handleUpdateQuantity(item.id, Math.max(1, item.quantity - 1))}>−</button>
                        <span>{item.quantity}</span>
                        <button onClick={() => handleUpdateQuantity(item.id, item.quantity + 1)}>+</button>
                      </div>
                      <button
                        className="btn btn-secondary btn-sm"
                        onClick={() => handleRemoveItem(item.id)}
                        style={{ color: 'var(--color-danger)' }}
                      >
                        Remove
                      </button>
                    </div>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '1.1rem', whiteSpace: 'nowrap' }}>
                    ${item.subtotal}
                  </div>
                </div>
              ))}
            </div>

            {/* Summary / Checkout */}
            <div className="cart-summary">
              {!showCheckout ? (
                <>
                  <h3>Order Summary</h3>
                  <div className="cart-summary-row">
                    <span>Subtotal</span>
                    <span>${cart.total_price}</span>
                  </div>
                  <div className="cart-summary-row">
                    <span>Shipping</span>
                    <span style={{ color: 'var(--color-success)' }}>Free</span>
                  </div>
                  <div className="cart-summary-row total">
                    <span>Total</span>
                    <span>${cart.total_price}</span>
                  </div>
                  <button
                    className="btn btn-primary btn-lg"
                    style={{ width: '100%', marginTop: 'var(--space-lg)' }}
                    onClick={() => setShowCheckout(true)}
                    id="checkout-button"
                  >
                    Proceed to Checkout →
                  </button>
                </>
              ) : (
                <>
                  <h3>Shipping Information</h3>
                  <form onSubmit={handleCheckout}>
                    <div className="form-group">
                      <label>Full Name</label>
                      <input
                        type="text"
                        className="form-control"
                        required
                        value={orderForm.shipping_name}
                        onChange={(e) => setOrderForm({ ...orderForm, shipping_name: e.target.value })}
                        id="shipping-name"
                      />
                    </div>
                    <div className="form-group">
                      <label>Phone</label>
                      <input
                        type="tel"
                        className="form-control"
                        required
                        value={orderForm.shipping_phone}
                        onChange={(e) => setOrderForm({ ...orderForm, shipping_phone: e.target.value })}
                        id="shipping-phone"
                      />
                    </div>
                    <div className="form-group">
                      <label>Address</label>
                      <textarea
                        className="form-control"
                        rows="3"
                        required
                        value={orderForm.shipping_address}
                        onChange={(e) => setOrderForm({ ...orderForm, shipping_address: e.target.value })}
                        id="shipping-address"
                      />
                    </div>
                    <div className="form-group">
                      <label>Note (optional)</label>
                      <input
                        type="text"
                        className="form-control"
                        value={orderForm.note}
                        onChange={(e) => setOrderForm({ ...orderForm, note: e.target.value })}
                      />
                    </div>
                    <div className="cart-summary-row total">
                      <span>Total</span>
                      <span>${cart.total_price}</span>
                    </div>
                    <button
                      type="submit"
                      className="btn btn-accent btn-lg"
                      style={{ width: '100%', marginTop: 'var(--space-md)' }}
                      disabled={submitting}
                      id="place-order-button"
                    >
                      {submitting ? 'Processing...' : '💳 Place Order (COD)'}
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ width: '100%', marginTop: 'var(--space-sm)' }}
                      onClick={() => setShowCheckout(false)}
                    >
                      ← Back to Summary
                    </button>
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
