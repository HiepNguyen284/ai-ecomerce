import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api.js';
import { formatVND } from '../utils/currency.js';

const ORDER_STATUS_OPTIONS = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled'];

const STATUS_LABELS = {
  pending: 'Chờ xử lý',
  confirmed: 'Đã xác nhận',
  processing: 'Đang xử lý',
  shipped: 'Đang giao',
  delivered: 'Đã giao',
  cancelled: 'Đã hủy',
};

const STATUS_COLORS = {
  pending: '#f59e0b',
  confirmed: '#3b82f6',
  processing: '#06b6d4',
  shipped: '#f97316',
  delivered: '#059669',
  cancelled: '#ef4444',
};

const PRODUCT_FORM_TEMPLATE = {
  name: '',
  slug: '',
  description: '',
  category: '',
  price: '',
  compare_price: '',
  stock: '0',
  rating: '4.50',
  num_reviews: '0',
  image_url: '',
  is_active: true,
};

function normalizeList(payload) {
  if (Array.isArray(payload)) return payload;
  if (payload && Array.isArray(payload.results)) return payload.results;
  return [];
}

function getUserDisplayName(customer) {
  const name = `${customer.first_name || ''} ${customer.last_name || ''}`.trim();
  if (name) return name;
  if (customer.username) return customer.username;
  return customer.email || 'N/A';
}

function buildStats(products, orders, customers) {
  const revenue = orders.reduce((sum, order) => sum + Number(order.total_amount || 0), 0);
  return {
    products: products.length,
    orders: orders.length,
    users: customers.length,
    revenue,
  };
}

function parseErrorMessage(err, fallbackMessage) {
  if (!err) return fallbackMessage;
  if (err.error) return err.error;
  if (err.detail) return err.detail;
  if (typeof err === 'string') return err;
  return fallbackMessage;
}

function toNumberString(value, defaultValue = '0') {
  if (value === null || value === undefined || value === '') return defaultValue;
  return String(value);
}

function createFormFromProduct(product) {
  return {
    name: product.name || '',
    slug: product.slug || '',
    description: product.description || '',
    category: product.category || '',
    price: toNumberString(product.price, ''),
    compare_price: product.compare_price ? toNumberString(product.compare_price, '') : '',
    stock: toNumberString(product.stock, '0'),
    rating: toNumberString(product.rating, '4.50'),
    num_reviews: toNumberString(product.num_reviews, '0'),
    image_url: product.image_url || '',
    is_active: Boolean(product.is_active),
  };
}

function AdminPage({ user, authReady = true }) {
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({ products: 0, orders: 0, users: 0, revenue: 0 });

  const [products, setProducts] = useState([]);
  const [orders, setOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [categories, setCategories] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState(null);

  const [productSearch, setProductSearch] = useState('');
  const [orderSearch, setOrderSearch] = useState('');
  const [orderStatusFilter, setOrderStatusFilter] = useState('all');
  const [customerSearch, setCustomerSearch] = useState('');

  const [productForm, setProductForm] = useState(PRODUCT_FORM_TEMPLATE);
  const [editingProductId, setEditingProductId] = useState(null);
  const [productSubmitting, setProductSubmitting] = useState(false);
  const [isProductPanelOpen, setIsProductPanelOpen] = useState(false);

  const [orderDrafts, setOrderDrafts] = useState({});
  const [orderUpdatingId, setOrderUpdatingId] = useState(null);
  const [customerUpdatingId, setCustomerUpdatingId] = useState(null);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'products', label: 'Sản phẩm' },
    { id: 'orders', label: 'Đơn hàng' },
    { id: 'customers', label: 'Khách hàng' },
  ];

  useEffect(() => {
    if (!notice) return undefined;
    const timer = setTimeout(() => setNotice(null), 3000);
    return () => clearTimeout(timer);
  }, [notice]);

  const applyStats = (nextProducts, nextOrders, nextCustomers) => {
    setStats(buildStats(nextProducts, nextOrders, nextCustomers));
  };

  const resetProductForm = (categoryId = '') => {
    setEditingProductId(null);
    setProductForm({ ...PRODUCT_FORM_TEMPLATE, category: categoryId });
  };

  const syncOrderDrafts = (nextOrders) => {
    const drafts = {};
    nextOrders.forEach((order) => {
      drafts[order.id] = order.status;
    });
    setOrderDrafts(drafts);
  };

  const loadAdminData = async () => {
    setLoading(true);
    setError('');

    try {
      const [productResult, orderResult, customerResult, categoryResult] = await Promise.allSettled([
        api.getAdminProducts(),
        api.getAdminOrders(),
        api.getAdminUsers(),
        api.getCategories(),
      ]);

      const nextProducts = productResult.status === 'fulfilled' ? normalizeList(productResult.value) : [];
      const nextOrders = orderResult.status === 'fulfilled' ? normalizeList(orderResult.value) : [];
      const nextCustomers = customerResult.status === 'fulfilled' ? normalizeList(customerResult.value) : [];
      const nextCategories = categoryResult.status === 'fulfilled' ? normalizeList(categoryResult.value) : [];

      setProducts(nextProducts);
      setOrders(nextOrders);
      setCustomers(nextCustomers);
      setCategories(nextCategories);
      syncOrderDrafts(nextOrders);
      applyStats(nextProducts, nextOrders, nextCustomers);

      setProductForm((prev) => ({
        ...prev,
        category: prev.category || nextCategories[0]?.id || '',
      }));

      const failedSources = [];
      if (productResult.status === 'rejected') failedSources.push('sản phẩm');
      if (orderResult.status === 'rejected') failedSources.push('đơn hàng');
      if (customerResult.status === 'rejected') failedSources.push('khách hàng');
      if (categoryResult.status === 'rejected') failedSources.push('danh mục');

      if (failedSources.length > 0) {
        setError(`Không thể tải đầy đủ dữ liệu: ${failedSources.join(', ')}.`);
      }
    } catch {
      setError('Không thể tải dữ liệu quản trị.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!authReady) {
      return;
    }
    if (!user) {
      navigate('/login');
      return;
    }
    if (!user.is_staff) {
      setLoading(false);
      setError('Tài khoản của bạn không có quyền truy cập trang quản trị.');
      return;
    }
    loadAdminData();
  }, [user, authReady]);

  const handleStartCreateProduct = () => {
    resetProductForm(categories[0]?.id || '');
    setIsProductPanelOpen(true);
  };

  const handleStartEditProduct = (product) => {
    setEditingProductId(product.id);
    setProductForm(createFormFromProduct(product));
    setActiveTab('products');
    setIsProductPanelOpen(true);
  };

  const handleCloseProductPanel = () => {
    setIsProductPanelOpen(false);
    resetProductForm(categories[0]?.id || '');
  };

  const handleProductFieldChange = (field, value) => {
    setProductForm((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleSubmitProduct = async (e) => {
    e.preventDefault();
    setError('');

    if (!productForm.name.trim()) {
      setError('Tên sản phẩm là bắt buộc.');
      return;
    }
    if (!productForm.category) {
      setError('Vui lòng chọn danh mục sản phẩm.');
      return;
    }

    const payload = {
      name: productForm.name.trim(),
      description: productForm.description.trim(),
      category: productForm.category,
      price: productForm.price || '0',
      compare_price: productForm.compare_price ? productForm.compare_price : null,
      stock: Number(productForm.stock || 0),
      rating: Number(productForm.rating || 0),
      num_reviews: Number(productForm.num_reviews || 0),
      image_url: productForm.image_url.trim(),
      is_active: Boolean(productForm.is_active),
    };

    if (productForm.slug.trim()) {
      payload.slug = productForm.slug.trim();
    }

    try {
      setProductSubmitting(true);
      if (editingProductId) {
        const updated = await api.updateAdminProduct(editingProductId, payload);
        setProducts((prev) => {
          const next = prev.map((product) => (product.id === updated.id ? updated : product));
          applyStats(next, orders, customers);
          return next;
        });
        setNotice({ type: 'success', text: 'Đã cập nhật sản phẩm.' });
      } else {
        const created = await api.createAdminProduct(payload);
        setProducts((prev) => {
          const next = [created, ...prev];
          applyStats(next, orders, customers);
          return next;
        });
        setNotice({ type: 'success', text: 'Đã tạo sản phẩm mới.' });
      }

      resetProductForm(categories[0]?.id || '');
      setIsProductPanelOpen(false);
    } catch (err) {
      setError(parseErrorMessage(err, 'Không thể lưu sản phẩm.'));
    } finally {
      setProductSubmitting(false);
    }
  };

  const handleDeleteProduct = async (product) => {
    const confirmed = window.confirm(`Xóa sản phẩm "${product.name}"?`);
    if (!confirmed) return;

    try {
      await api.deleteAdminProduct(product.id);
      setProducts((prev) => {
        const next = prev.filter((item) => item.id !== product.id);
        applyStats(next, orders, customers);
        return next;
      });
      if (editingProductId === product.id) {
        resetProductForm(categories[0]?.id || '');
        setIsProductPanelOpen(false);
      }
      setNotice({ type: 'success', text: 'Đã xóa sản phẩm.' });
    } catch (err) {
      setError(parseErrorMessage(err, 'Không thể xóa sản phẩm.'));
    }
  };

  const handleSaveOrderStatus = async (orderId) => {
    const nextStatus = orderDrafts[orderId];
    if (!nextStatus) return;

    try {
      setOrderUpdatingId(orderId);
      const updatedOrder = await api.updateAdminOrderStatus(orderId, nextStatus);
      setOrders((prev) => prev.map((order) => (order.id === orderId ? updatedOrder : order)));
      setNotice({ type: 'success', text: 'Đã cập nhật trạng thái đơn hàng.' });
    } catch (err) {
      setError(parseErrorMessage(err, 'Không thể cập nhật trạng thái đơn hàng.'));
    } finally {
      setOrderUpdatingId(null);
    }
  };

  const handleToggleCustomerFlag = async (customer, field) => {
    try {
      setCustomerUpdatingId(customer.id);
      const updatedCustomer = await api.updateAdminUser(customer.id, { [field]: !customer[field] });
      setCustomers((prev) => {
        const next = prev.map((item) => (item.id === updatedCustomer.id ? updatedCustomer : item));
        applyStats(products, orders, next);
        return next;
      });
      setNotice({ type: 'success', text: 'Đã cập nhật khách hàng.' });
    } catch (err) {
      setError(parseErrorMessage(err, 'Không thể cập nhật khách hàng.'));
    } finally {
      setCustomerUpdatingId(null);
    }
  };

  const filteredProducts = useMemo(() => {
    const keyword = productSearch.trim().toLowerCase();
    if (!keyword) return products;
    return products.filter((product) => {
      return (
        product.name?.toLowerCase().includes(keyword)
        || product.slug?.toLowerCase().includes(keyword)
        || product.category_name?.toLowerCase().includes(keyword)
      );
    });
  }, [products, productSearch]);

  const filteredOrders = useMemo(() => {
    const keyword = orderSearch.trim().toLowerCase();
    return orders.filter((order) => {
      const passStatus = orderStatusFilter === 'all' || order.status === orderStatusFilter;
      if (!passStatus) return false;
      if (!keyword) return true;

      const orderCode = order.id?.toLowerCase().includes(keyword);
      const shippingName = (order.shipping_name || '').toLowerCase().includes(keyword);
      const shippingPhone = (order.shipping_phone || '').toLowerCase().includes(keyword);
      return orderCode || shippingName || shippingPhone;
    });
  }, [orders, orderSearch, orderStatusFilter]);

  const customersWithStats = useMemo(() => {
    const statsByUserId = {};

    orders.forEach((order) => {
      const key = order.user_id || 'unknown';
      if (!statsByUserId[key]) {
        statsByUserId[key] = {
          orderCount: 0,
          totalSpent: 0,
          lastOrderAt: null,
        };
      }
      statsByUserId[key].orderCount += 1;
      statsByUserId[key].totalSpent += Number(order.total_amount || 0);

      const currentDate = order.created_at ? new Date(order.created_at) : null;
      if (currentDate && (!statsByUserId[key].lastOrderAt || currentDate > statsByUserId[key].lastOrderAt)) {
        statsByUserId[key].lastOrderAt = currentDate;
      }
    });

    const knownCustomers = customers.map((customer) => ({
      ...customer,
      ...statsByUserId[customer.id],
      orderCount: statsByUserId[customer.id]?.orderCount || 0,
      totalSpent: statsByUserId[customer.id]?.totalSpent || 0,
      lastOrderAt: statsByUserId[customer.id]?.lastOrderAt || null,
    }));

    const knownIds = new Set(knownCustomers.map((customer) => customer.id));
    const unknownCustomers = Object.entries(statsByUserId)
      .filter(([userId]) => !knownIds.has(userId))
      .map(([userId, extra]) => ({
        id: userId,
        email: '',
        username: `user-${userId.slice(0, 8)}`,
        first_name: '',
        last_name: '',
        phone: '',
        address: '',
        is_staff: false,
        is_active: true,
        ...extra,
      }));

    const merged = [...knownCustomers, ...unknownCustomers];
    const keyword = customerSearch.trim().toLowerCase();

    return merged
      .filter((customer) => {
        if (!keyword) return true;
        const displayName = getUserDisplayName(customer).toLowerCase();
        return (
          displayName.includes(keyword)
          || (customer.email || '').toLowerCase().includes(keyword)
          || (customer.phone || '').toLowerCase().includes(keyword)
        );
      })
      .sort((a, b) => b.totalSpent - a.totalSpent);
  }, [customers, orders, customerSearch]);

  if (!authReady) {
    return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;
  }

  if (!user) {
    return null;
  }

  if (!user.is_staff) {
    return (
      <div className="section" style={{ paddingTop: '100px', minHeight: '100vh' }}>
        <div className="container">
          <div className="empty-state">
            <div className="icon">⛔</div>
            <h3>Bạn không có quyền truy cập trang quản trị</h3>
            <p style={{ marginBottom: 'var(--space-xl)' }}>Vui lòng liên hệ quản trị viên hệ thống để được cấp quyền.</p>
            <Link to="/" className="btn btn-primary">Quay về trang chủ</Link>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;
  }

  return (
    <div style={{ paddingTop: '80px', minHeight: '100vh', display: 'flex' }}>
      <aside style={{
        width: '260px',
        background: 'var(--color-bg-secondary)',
        borderRight: '1px solid var(--color-border)',
        padding: 'var(--space-xl) 0',
        position: 'fixed',
        top: '70px',
        bottom: 0,
        overflowY: 'auto',
        zIndex: 10,
      }}>
        <div style={{ padding: '0 var(--space-lg)', marginBottom: 'var(--space-xl)' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--color-primary-light)' }}>Quản trị hệ thống</h3>
          <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', marginTop: '4px' }}>Customer, Product, Order Management</p>
        </div>

        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            style={{
              display: 'block',
              width: '100%',
              padding: 'var(--space-md) var(--space-lg)',
              textAlign: 'left',
              background: activeTab === tab.id ? 'rgba(37, 99, 235, 0.1)' : 'transparent',
              color: activeTab === tab.id ? 'var(--color-primary-dark)' : 'var(--color-text-secondary)',
              borderLeft: activeTab === tab.id ? '3px solid var(--color-primary)' : '3px solid transparent',
              fontSize: '0.95rem',
              fontWeight: activeTab === tab.id ? 700 : 500,
              transition: 'all 0.2s',
            }}
          >
            {tab.label}
          </button>
        ))}

        <div style={{ padding: 'var(--space-xl) var(--space-lg)', borderTop: '1px solid var(--color-border)', marginTop: 'var(--space-xl)' }}>
          <button className="btn btn-secondary btn-sm" style={{ width: '100%', marginBottom: 'var(--space-sm)' }} onClick={loadAdminData}>
            Làm mới dữ liệu
          </button>
          <Link to="/" className="btn btn-secondary btn-sm" style={{ width: '100%' }}>Về trang chủ</Link>
        </div>
      </aside>

      <main style={{ marginLeft: '260px', flex: 1, padding: 'var(--space-2xl)' }}>
        {notice && (
          <div className={`alert ${notice.type === 'success' ? 'alert-success' : 'alert-error'}`} style={{ marginBottom: 'var(--space-lg)' }}>
            {notice.text}
          </div>
        )}

        {error && (
          <div className="alert alert-error" style={{ marginBottom: 'var(--space-lg)' }}>
            {error}
          </div>
        )}

        {activeTab === 'dashboard' && <DashboardTab stats={stats} orders={orders} />}

        {activeTab === 'products' && (
          <ProductsTab
            rows={filteredProducts}
            categories={categories}
            productSearch={productSearch}
            setProductSearch={setProductSearch}
            productForm={productForm}
            editingProductId={editingProductId}
            productSubmitting={productSubmitting}
            isPanelOpen={isProductPanelOpen}
            onFieldChange={handleProductFieldChange}
            onSubmit={handleSubmitProduct}
            onStartCreate={handleStartCreateProduct}
            onStartEdit={handleStartEditProduct}
            onClosePanel={handleCloseProductPanel}
            onDelete={handleDeleteProduct}
          />
        )}

        {activeTab === 'orders' && (
          <OrdersTab
            rows={filteredOrders}
            orderDrafts={orderDrafts}
            orderSearch={orderSearch}
            setOrderSearch={setOrderSearch}
            orderStatusFilter={orderStatusFilter}
            setOrderStatusFilter={setOrderStatusFilter}
            orderUpdatingId={orderUpdatingId}
            onDraftChange={(orderId, nextStatus) => {
              setOrderDrafts((prev) => ({ ...prev, [orderId]: nextStatus }));
            }}
            onSaveStatus={handleSaveOrderStatus}
          />
        )}

        {activeTab === 'customers' && (
          <CustomersTab
            rows={customersWithStats}
            customerSearch={customerSearch}
            setCustomerSearch={setCustomerSearch}
            customerUpdatingId={customerUpdatingId}
            onToggleFlag={handleToggleCustomerFlag}
          />
        )}
      </main>
    </div>
  );
}

function DashboardTab({ stats, orders }) {
  const recentOrders = orders.slice(0, 6);
  const cardStyle = {
    background: 'var(--gradient-card)',
    border: '1px solid var(--color-border)',
    borderRadius: 'var(--radius-lg)',
    padding: 'var(--space-xl)',
  };

  return (
    <div className="fade-in">
      <h2 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: 'var(--space-2xl)' }}>Dashboard</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0, 1fr))', gap: 'var(--space-lg)', marginBottom: 'var(--space-2xl)' }}>
        <div style={cardStyle}><div style={{ color: 'var(--color-text-muted)', marginBottom: 6 }}>Sản phẩm</div><div style={{ fontSize: '1.7rem', fontWeight: 800 }}>{stats.products}</div></div>
        <div style={cardStyle}><div style={{ color: 'var(--color-text-muted)', marginBottom: 6 }}>Đơn hàng</div><div style={{ fontSize: '1.7rem', fontWeight: 800 }}>{stats.orders}</div></div>
        <div style={cardStyle}><div style={{ color: 'var(--color-text-muted)', marginBottom: 6 }}>Khách hàng</div><div style={{ fontSize: '1.7rem', fontWeight: 800 }}>{stats.users}</div></div>
        <div style={cardStyle}><div style={{ color: 'var(--color-text-muted)', marginBottom: 6 }}>Doanh thu</div><div style={{ fontSize: '1.7rem', fontWeight: 800 }}>{formatVND(stats.revenue)}</div></div>
      </div>

      <div style={{ ...cardStyle, padding: 'var(--space-lg)', overflowX: 'auto' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 'var(--space-md)' }}>Đơn hàng gần đây</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Mã đơn</th>
              <th style={thStyle}>Khách hàng</th>
              <th style={thStyle}>Tổng tiền</th>
              <th style={thStyle}>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {recentOrders.map((order) => (
              <tr key={order.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}><code>{order.id.slice(0, 8)}</code></td>
                <td style={tdStyle}>{order.shipping_name || order.user_id?.slice(0, 8)}</td>
                <td style={tdStyle}><strong>{formatVND(order.total_amount)}</strong></td>
                <td style={tdStyle}>
                  <span style={{
                    padding: '0.2rem 0.65rem',
                    borderRadius: '999px',
                    color: STATUS_COLORS[order.status] || 'var(--color-text-secondary)',
                    background: `${STATUS_COLORS[order.status] || '#64748b'}15`,
                    border: `1px solid ${STATUS_COLORS[order.status] || '#64748b'}40`,
                    fontSize: '0.82rem',
                    fontWeight: 700,
                  }}>
                    {STATUS_LABELS[order.status] || order.status}
                  </span>
                </td>
              </tr>
            ))}
            {recentOrders.length === 0 && (
              <tr><td style={tdStyle} colSpan={4}>Chưa có đơn hàng.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProductsTab({
  rows,
  categories,
  productSearch,
  setProductSearch,
  productForm,
  editingProductId,
  productSubmitting,
  isPanelOpen,
  onFieldChange,
  onSubmit,
  onStartCreate,
  onStartEdit,
  onClosePanel,
  onDelete,
}) {
  const handleClosePanel = () => {
    if (productSubmitting) return;
    onClosePanel();
  };

  return (
    <div className="fade-in" style={{ position: 'relative' }}>
      <div style={{
        background: 'var(--gradient-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-lg)',
        overflowX: 'auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Quản lý sản phẩm</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
            <span style={{ color: 'var(--color-text-muted)' }}>{rows.length} sản phẩm</span>
            <button className="btn btn-primary btn-sm" onClick={onStartCreate}>+ Thêm sản phẩm</button>
          </div>
        </div>

        <input
          className="form-control"
          placeholder="Tìm theo tên, slug hoặc danh mục"
          value={productSearch}
          onChange={(e) => setProductSearch(e.target.value)}
          style={{ maxWidth: '420px', marginBottom: 'var(--space-lg)' }}
        />

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Sản phẩm</th>
              <th style={thStyle}>Danh mục</th>
              <th style={thStyle}>Giá</th>
              <th style={thStyle}>Kho</th>
              <th style={thStyle}>Trạng thái</th>
              <th style={thStyle}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((product) => (
              <tr key={product.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                    <img src={product.image_url || 'https://placehold.co/48x48/f8fafc/334155?text=SP'} alt={product.name}
                      style={{ width: 48, height: 48, borderRadius: 8, objectFit: 'cover', border: '1px solid var(--color-border)' }} />
                    <div>
                      <div style={{ fontWeight: 700 }}>{product.name}</div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{product.slug}</div>
                    </div>
                  </div>
                </td>
                <td style={tdStyle}>{product.category_name}</td>
                <td style={tdStyle}>
                  <div style={{ fontWeight: 700 }}>{formatVND(product.price)}</div>
                  {product.compare_price && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', textDecoration: 'line-through' }}>
                      {formatVND(product.compare_price)}
                    </div>
                  )}
                </td>
                <td style={tdStyle}>{product.stock}</td>
                <td style={tdStyle}>
                  <span style={{
                    color: product.is_active ? 'var(--color-success)' : 'var(--color-danger)',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                  }}>
                    {product.is_active ? 'Hoạt động' : 'Ẩn'}
                  </span>
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', gap: '0.4rem' }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => onStartEdit(product)}>Sửa</button>
                    <button className="btn btn-secondary btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => onDelete(product)}>Xóa</button>
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td style={tdStyle} colSpan={6}>Không có sản phẩm phù hợp.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {isPanelOpen && (
        <div
          style={{
            position: 'fixed',
            top: '70px',
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(15, 23, 42, 0.35)',
            zIndex: 60,
            display: 'flex',
            justifyContent: 'flex-end',
          }}
          onClick={handleClosePanel}
        >
          <div
            style={{
              width: 'min(520px, 100vw)',
              height: '100%',
              background: 'var(--color-bg-primary)',
              borderLeft: '1px solid var(--color-border)',
              padding: 'var(--space-lg)',
              overflowY: 'auto',
              boxShadow: '-18px 0 40px rgba(15, 23, 42, 0.22)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 800 }}>{editingProductId ? 'Chỉnh sửa sản phẩm' : 'Thêm sản phẩm'}</h3>
              <button className="btn btn-secondary btn-sm" onClick={handleClosePanel} disabled={productSubmitting}>Đóng</button>
            </div>

            <form onSubmit={onSubmit}>
              <div className="form-group">
                <label>Tên sản phẩm</label>
                <input className="form-control" value={productForm.name} onChange={(e) => onFieldChange('name', e.target.value)} required />
              </div>

              <div className="form-group">
                <label>Slug (tùy chọn)</label>
                <input className="form-control" value={productForm.slug} onChange={(e) => onFieldChange('slug', e.target.value)} placeholder="tu-dong-neu-bo-trong" />
              </div>

              <div className="form-group">
                <label>Danh mục</label>
                <select className="form-control" value={productForm.category} onChange={(e) => onFieldChange('category', e.target.value)} required>
                  <option value="">Chọn danh mục</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>{category.name}</option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-sm)' }}>
                <div className="form-group">
                  <label>Giá bán</label>
                  <input type="number" className="form-control" min="0" step="1000" value={productForm.price} onChange={(e) => onFieldChange('price', e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Giá gốc</label>
                  <input type="number" className="form-control" min="0" step="1000" value={productForm.compare_price} onChange={(e) => onFieldChange('compare_price', e.target.value)} />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-sm)' }}>
                <div className="form-group">
                  <label>Tồn kho</label>
                  <input type="number" className="form-control" min="0" value={productForm.stock} onChange={(e) => onFieldChange('stock', e.target.value)} required />
                </div>
                <div className="form-group">
                  <label>Đánh giá</label>
                  <input type="number" className="form-control" min="0" max="5" step="0.01" value={productForm.rating} onChange={(e) => onFieldChange('rating', e.target.value)} />
                </div>
              </div>

              <div className="form-group">
                <label>Số lượt đánh giá</label>
                <input type="number" className="form-control" min="0" value={productForm.num_reviews} onChange={(e) => onFieldChange('num_reviews', e.target.value)} />
              </div>

              <div className="form-group">
                <label>Ảnh sản phẩm (URL)</label>
                <input className="form-control" value={productForm.image_url} onChange={(e) => onFieldChange('image_url', e.target.value)} />
              </div>

              <div className="form-group">
                <label>Mô tả</label>
                <textarea rows={3} className="form-control" value={productForm.description} onChange={(e) => onFieldChange('description', e.target.value)} />
              </div>

              <div className="form-group" style={{ marginBottom: 'var(--space-md)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    type="checkbox"
                    checked={productForm.is_active}
                    onChange={(e) => onFieldChange('is_active', e.target.checked)}
                  />
                  Sản phẩm đang hoạt động
                </label>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-sm)', marginTop: 'var(--space-lg)' }}>
                <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={handleClosePanel} disabled={productSubmitting}>
                  Hủy
                </button>
                <button type="submit" className="btn btn-primary" style={{ flex: 1 }} disabled={productSubmitting}>
                  {productSubmitting ? 'Đang lưu...' : editingProductId ? 'Lưu thay đổi' : 'Tạo sản phẩm'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function OrdersTab({
  rows,
  orderDrafts,
  orderSearch,
  setOrderSearch,
  orderStatusFilter,
  setOrderStatusFilter,
  orderUpdatingId,
  onDraftChange,
  onSaveStatus,
}) {
  return (
    <div className="fade-in">
      <div style={{
        background: 'var(--gradient-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-lg)',
        overflowX: 'auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Quản lý đơn hàng</h2>
          <span style={{ color: 'var(--color-text-muted)' }}>{rows.length} đơn hàng</span>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-sm)', marginBottom: 'var(--space-lg)', flexWrap: 'wrap' }}>
          <input
            className="form-control"
            placeholder="Tìm theo mã đơn, tên hoặc SĐT"
            value={orderSearch}
            onChange={(e) => setOrderSearch(e.target.value)}
            style={{ maxWidth: '360px' }}
          />
          <select className="form-control" value={orderStatusFilter} onChange={(e) => setOrderStatusFilter(e.target.value)} style={{ maxWidth: '220px' }}>
            <option value="all">Tất cả trạng thái</option>
            {ORDER_STATUS_OPTIONS.map((status) => (
              <option key={status} value={status}>{STATUS_LABELS[status]}</option>
            ))}
          </select>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Mã đơn</th>
              <th style={thStyle}>Khách hàng</th>
              <th style={thStyle}>Sản phẩm</th>
              <th style={thStyle}>Tổng tiền</th>
              <th style={thStyle}>Trạng thái</th>
              <th style={thStyle}>Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((order) => (
              <tr key={order.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}><code style={{ fontSize: '0.8rem' }}>{order.id.slice(0, 8)}</code></td>
                <td style={tdStyle}>
                  <div style={{ fontWeight: 600 }}>{order.shipping_name || '-'}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{order.shipping_phone || ''}</div>
                </td>
                <td style={tdStyle}>
                  {(order.items || []).slice(0, 3).map((item) => (
                    <div key={item.id} style={{ fontSize: '0.82rem' }}>{item.product_name} x{item.quantity}</div>
                  ))}
                  {(order.items || []).length > 3 && (
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>+{order.items.length - 3} sản phẩm</div>
                  )}
                </td>
                <td style={tdStyle}><strong>{formatVND(order.total_amount)}</strong></td>
                <td style={tdStyle}>
                  <select
                    className="form-control"
                    value={orderDrafts[order.id] || order.status}
                    onChange={(e) => onDraftChange(order.id, e.target.value)}
                    style={{ minWidth: '160px' }}
                  >
                    {ORDER_STATUS_OPTIONS.map((status) => (
                      <option key={status} value={status}>{STATUS_LABELS[status]}</option>
                    ))}
                  </select>
                </td>
                <td style={tdStyle}>
                  <button
                    className="btn btn-primary btn-sm"
                    disabled={orderUpdatingId === order.id}
                    onClick={() => onSaveStatus(order.id)}
                  >
                    {orderUpdatingId === order.id ? 'Đang lưu...' : 'Lưu'}
                  </button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td style={tdStyle} colSpan={6}>Không tìm thấy đơn hàng phù hợp.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CustomersTab({ rows, customerSearch, setCustomerSearch, customerUpdatingId, onToggleFlag }) {
  return (
    <div className="fade-in">
      <div style={{
        background: 'var(--gradient-card)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-lg)',
        overflowX: 'auto',
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-md)', gap: 'var(--space-md)', flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Quản lý khách hàng</h2>
          <span style={{ color: 'var(--color-text-muted)' }}>{rows.length} khách hàng</span>
        </div>

        <input
          className="form-control"
          placeholder="Tìm theo tên, email, số điện thoại"
          value={customerSearch}
          onChange={(e) => setCustomerSearch(e.target.value)}
          style={{ maxWidth: '420px', marginBottom: 'var(--space-lg)' }}
        />

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              <th style={thStyle}>Khách hàng</th>
              <th style={thStyle}>Liên hệ</th>
              <th style={thStyle}>Đơn hàng</th>
              <th style={thStyle}>Chi tiêu</th>
              <th style={thStyle}>Role</th>
              <th style={thStyle}>Trạng thái</th>
              <th style={thStyle}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((customer) => (
              <tr key={customer.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={tdStyle}>
                  <div style={{ fontWeight: 700 }}>{getUserDisplayName(customer)}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{customer.username || customer.id.slice(0, 8)}</div>
                </td>
                <td style={tdStyle}>
                  <div>{customer.email || '-'}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{customer.phone || '-'}</div>
                </td>
                <td style={tdStyle}>{customer.orderCount || 0}</td>
                <td style={tdStyle}><strong>{formatVND(customer.totalSpent || 0)}</strong></td>
                <td style={tdStyle}>
                  <span style={{
                    color: customer.is_staff ? 'var(--color-primary-dark)' : 'var(--color-text-secondary)',
                    fontWeight: 700,
                  }}>
                    {customer.is_staff ? 'Admin' : 'Customer'}
                  </span>
                </td>
                <td style={tdStyle}>
                  <span style={{
                    color: customer.is_active ? 'var(--color-success)' : 'var(--color-danger)',
                    fontWeight: 700,
                  }}>
                    {customer.is_active ? 'Active' : 'Blocked'}
                  </span>
                </td>
                <td style={tdStyle}>
                  <div style={{ display: 'flex', gap: '0.45rem' }}>
                    <button
                      className="btn btn-secondary btn-sm"
                      disabled={customerUpdatingId === customer.id}
                      onClick={() => onToggleFlag(customer, 'is_staff')}
                    >
                      {customer.is_staff ? 'Bỏ admin' : 'Cấp admin'}
                    </button>
                    <button
                      className="btn btn-secondary btn-sm"
                      style={{ color: customer.is_active ? 'var(--color-danger)' : 'var(--color-success)' }}
                      disabled={customerUpdatingId === customer.id}
                      onClick={() => onToggleFlag(customer, 'is_active')}
                    >
                      {customer.is_active ? 'Khóa' : 'Mở khóa'}
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td style={tdStyle} colSpan={7}>Không tìm thấy khách hàng phù hợp.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const thStyle = {
  padding: '0.75rem 1rem',
  textAlign: 'left',
  fontSize: '0.82rem',
  fontWeight: 700,
  color: 'var(--color-text-muted)',
  textTransform: 'uppercase',
  letterSpacing: '0.5px',
};

const tdStyle = {
  padding: '0.75rem 1rem',
  fontSize: '0.9rem',
  color: 'var(--color-text-primary)',
  verticalAlign: 'top',
};

export default AdminPage;
