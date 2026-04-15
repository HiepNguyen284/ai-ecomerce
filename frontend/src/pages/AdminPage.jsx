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

function AdminPage({ user, authReady = true, onLogout }) {
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

  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'products', label: 'Sản phẩm', icon: '📦' },
    { id: 'orders', label: 'Đơn hàng', icon: '🧾' },
    { id: 'customers', label: 'Khách hàng', icon: '👥' },
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

  const handleAdminLogout = () => {
    if (onLogout) onLogout();
    navigate('/login');
  };

  if (!authReady) {
    return <div className="loading-spinner" style={{ paddingTop: '150px' }}><div className="spinner"></div></div>;
  }

  if (!user) {
    return null;
  }

  if (!user.is_staff) {
    return (
      <div className="admin-access-denied">
        <div className="admin-access-denied-card">
          <div className="admin-access-denied-icon">⛔</div>
          <h3>Bạn không có quyền truy cập trang quản trị</h3>
          <p>Vui lòng liên hệ quản trị viên hệ thống để được cấp quyền.</p>
          <Link to="/" className="btn btn-primary">Quay về trang chủ</Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="admin-layout">
        <div className="loading-spinner" style={{ paddingTop: '150px', width: '100%' }}><div className="spinner"></div></div>
      </div>
    );
  }

  return (
    <div className="admin-layout">
      {/* Admin Sidebar */}
      <aside className={`admin-sidebar ${sidebarCollapsed ? 'admin-sidebar--collapsed' : ''}`}>
        <div className="admin-sidebar-header">
          <div className="admin-sidebar-brand">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" width="28" height="28">
              <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"></path>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <path d="M16 10a4 4 0 0 1-8 0"></path>
            </svg>
            {!sidebarCollapsed && <span>ShopVerse Admin</span>}
          </div>
          <button className="admin-sidebar-toggle" onClick={() => setSidebarCollapsed(!sidebarCollapsed)} title="Thu gọn">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
        </div>

        <nav className="admin-sidebar-nav">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`admin-sidebar-item ${activeTab === tab.id ? 'admin-sidebar-item--active' : ''}`}
              title={tab.label}
            >
              <span className="admin-sidebar-icon">{tab.icon}</span>
              {!sidebarCollapsed && <span className="admin-sidebar-label">{tab.label}</span>}
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-footer">
          <button className="admin-sidebar-item" onClick={loadAdminData} title="Làm mới">
            <span className="admin-sidebar-icon">🔄</span>
            {!sidebarCollapsed && <span className="admin-sidebar-label">Làm mới dữ liệu</span>}
          </button>
          <Link to="/" className="admin-sidebar-item" title="Về trang khách hàng">
            <span className="admin-sidebar-icon">🏪</span>
            {!sidebarCollapsed && <span className="admin-sidebar-label">Trang khách hàng</span>}
          </Link>
          <button className="admin-sidebar-item admin-sidebar-item--danger" onClick={handleAdminLogout} title="Đăng xuất">
            <span className="admin-sidebar-icon">🚪</span>
            {!sidebarCollapsed && <span className="admin-sidebar-label">Đăng xuất</span>}
          </button>
        </div>
      </aside>

      {/* Admin Content */}
      <div className={`admin-content ${sidebarCollapsed ? 'admin-content--expanded' : ''}`}>
        {/* Admin Top Bar */}
        <header className="admin-topbar">
          <div className="admin-topbar-left">
            <h1 className="admin-topbar-title">{tabs.find(t => t.id === activeTab)?.label || 'Dashboard'}</h1>
          </div>
          <div className="admin-topbar-right">
            <Link to="/" className="admin-topbar-btn" title="Về trang khách hàng">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                <polyline points="9 22 9 12 15 12 15 22"></polyline>
              </svg>
              Về trang khách hàng
            </Link>
            <div className="admin-topbar-user">
              <div className="admin-topbar-avatar">
                {(user.first_name || user.username || 'A').charAt(0).toUpperCase()}
              </div>
              <span>{user.first_name || user.username}</span>
            </div>
          </div>
        </header>

        <div className="admin-content-body">
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
        </div>
      </div>
    </div>
  );
}

/* ========== Dashboard Tab ========== */
function DashboardTab({ stats, orders }) {
  const recentOrders = orders.slice(0, 8);

  const statCards = [
    { label: 'Sản phẩm', value: stats.products, icon: '📦', color: '#3b82f6' },
    { label: 'Đơn hàng', value: stats.orders, icon: '🧾', color: '#f59e0b' },
    { label: 'Khách hàng', value: stats.users, icon: '👥', color: '#10b981' },
    { label: 'Doanh thu', value: formatVND(stats.revenue), icon: '💰', color: '#ef4444' },
  ];

  return (
    <div className="fade-in">
      <div className="admin-stat-grid">
        {statCards.map((card) => (
          <div className="admin-stat-card" key={card.label}>
            <div className="admin-stat-card-icon" style={{ background: `${card.color}15`, color: card.color }}>
              {card.icon}
            </div>
            <div className="admin-stat-card-info">
              <div className="admin-stat-card-label">{card.label}</div>
              <div className="admin-stat-card-value">{card.value}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="admin-card">
        <div className="admin-card-header">
          <h3>Đơn hàng gần đây</h3>
          <span className="admin-card-badge">{recentOrders.length} đơn</span>
        </div>
        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Mã đơn</th>
                <th>Khách hàng</th>
                <th>Tổng tiền</th>
                <th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {recentOrders.map((order) => (
                <tr key={order.id}>
                  <td><code>{order.id.slice(0, 8)}</code></td>
                  <td>{order.shipping_name || order.user_id?.slice(0, 8)}</td>
                  <td><strong>{formatVND(order.total_amount)}</strong></td>
                  <td>
                    <span className="admin-status-badge" style={{
                      color: STATUS_COLORS[order.status] || '#64748b',
                      background: `${STATUS_COLORS[order.status] || '#64748b'}15`,
                      border: `1px solid ${STATUS_COLORS[order.status] || '#64748b'}40`,
                    }}>
                      {STATUS_LABELS[order.status] || order.status}
                    </span>
                  </td>
                </tr>
              ))}
              {recentOrders.length === 0 && (
                <tr><td colSpan={4} className="admin-table-empty">Chưa có đơn hàng.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ========== Products Tab ========== */
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
      <div className="admin-card">
        <div className="admin-card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <h3>Quản lý sản phẩm</h3>
            <span className="admin-card-badge">{rows.length} sản phẩm</span>
          </div>
          <button className="btn btn-primary btn-sm" onClick={onStartCreate}>+ Thêm sản phẩm</button>
        </div>

        <div style={{ padding: '0 var(--space-lg)', marginBottom: 'var(--space-md)' }}>
          <input
            className="form-control"
            placeholder="Tìm theo tên, slug hoặc danh mục"
            value={productSearch}
            onChange={(e) => setProductSearch(e.target.value)}
            style={{ maxWidth: '420px' }}
          />
        </div>

        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Sản phẩm</th>
                <th>Danh mục</th>
                <th>Giá</th>
                <th>Kho</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((product) => (
                <tr key={product.id}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-sm)' }}>
                      <img src={product.image_url || 'https://placehold.co/48x48/f8fafc/334155?text=SP'} alt={product.name}
                        style={{ width: 44, height: 44, borderRadius: 8, objectFit: 'cover', border: '1px solid var(--color-border)' }} />
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.88rem' }}>{product.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{product.slug}</div>
                      </div>
                    </div>
                  </td>
                  <td>{product.category_name}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{formatVND(product.price)}</div>
                    {product.compare_price && (
                      <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)', textDecoration: 'line-through' }}>
                        {formatVND(product.compare_price)}
                      </div>
                    )}
                  </td>
                  <td>{product.stock}</td>
                  <td>
                    <span className="admin-status-badge" style={{
                      color: product.is_active ? 'var(--color-success)' : 'var(--color-danger)',
                      background: product.is_active ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    }}>
                      {product.is_active ? 'Hoạt động' : 'Ẩn'}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.4rem' }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => onStartEdit(product)}>Sửa</button>
                      <button className="btn btn-secondary btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => onDelete(product)}>Xóa</button>
                    </div>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr><td colSpan={6} className="admin-table-empty">Không có sản phẩm phù hợp.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {isPanelOpen && (
        <div className="admin-panel-overlay" onClick={handleClosePanel}>
          <div className="admin-panel" onClick={(e) => e.stopPropagation()}>
            <div className="admin-panel-header">
              <h3>{editingProductId ? 'Chỉnh sửa sản phẩm' : 'Thêm sản phẩm'}</h3>
              <button className="admin-panel-close" onClick={handleClosePanel} disabled={productSubmitting}>✕</button>
            </div>

            <form onSubmit={onSubmit} className="admin-panel-body">
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

/* ========== Orders Tab ========== */
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
      <div className="admin-card">
        <div className="admin-card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <h3>Quản lý đơn hàng</h3>
            <span className="admin-card-badge">{rows.length} đơn hàng</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-sm)', padding: '0 var(--space-lg)', marginBottom: 'var(--space-md)', flexWrap: 'wrap' }}>
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

        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Mã đơn</th>
                <th>Khách hàng</th>
                <th>Sản phẩm</th>
                <th>Tổng tiền</th>
                <th>Trạng thái</th>
                <th>Cập nhật</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((order) => (
                <tr key={order.id}>
                  <td><code style={{ fontSize: '0.8rem' }}>{order.id.slice(0, 8)}</code></td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{order.shipping_name || '-'}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{order.shipping_phone || ''}</div>
                  </td>
                  <td>
                    {(order.items || []).slice(0, 3).map((item) => (
                      <div key={item.id} style={{ fontSize: '0.82rem' }}>{item.product_name} x{item.quantity}</div>
                    ))}
                    {(order.items || []).length > 3 && (
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>+{order.items.length - 3} sản phẩm</div>
                    )}
                  </td>
                  <td><strong>{formatVND(order.total_amount)}</strong></td>
                  <td>
                    <select
                      className="form-control"
                      value={orderDrafts[order.id] || order.status}
                      onChange={(e) => onDraftChange(order.id, e.target.value)}
                      style={{ minWidth: '150px', fontSize: '0.85rem' }}
                    >
                      {ORDER_STATUS_OPTIONS.map((status) => (
                        <option key={status} value={status}>{STATUS_LABELS[status]}</option>
                      ))}
                    </select>
                  </td>
                  <td>
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
                <tr><td colSpan={6} className="admin-table-empty">Không tìm thấy đơn hàng phù hợp.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ========== Customers Tab ========== */
function CustomersTab({ rows, customerSearch, setCustomerSearch, customerUpdatingId, onToggleFlag }) {
  return (
    <div className="fade-in">
      <div className="admin-card">
        <div className="admin-card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
            <h3>Quản lý khách hàng</h3>
            <span className="admin-card-badge">{rows.length} khách hàng</span>
          </div>
        </div>

        <div style={{ padding: '0 var(--space-lg)', marginBottom: 'var(--space-md)' }}>
          <input
            className="form-control"
            placeholder="Tìm theo tên, email, số điện thoại"
            value={customerSearch}
            onChange={(e) => setCustomerSearch(e.target.value)}
            style={{ maxWidth: '420px' }}
          />
        </div>

        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>Khách hàng</th>
                <th>Liên hệ</th>
                <th>Đơn hàng</th>
                <th>Chi tiêu</th>
                <th>Role</th>
                <th>Trạng thái</th>
                <th>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((customer) => (
                <tr key={customer.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{getUserDisplayName(customer)}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{customer.username || customer.id.slice(0, 8)}</div>
                  </td>
                  <td>
                    <div>{customer.email || '-'}</div>
                    <div style={{ fontSize: '0.78rem', color: 'var(--color-text-muted)' }}>{customer.phone || '-'}</div>
                  </td>
                  <td>{customer.orderCount || 0}</td>
                  <td><strong>{formatVND(customer.totalSpent || 0)}</strong></td>
                  <td>
                    <span className="admin-status-badge" style={{
                      color: customer.is_staff ? '#3b82f6' : '#64748b',
                      background: customer.is_staff ? 'rgba(59, 130, 246, 0.1)' : 'rgba(100, 116, 139, 0.1)',
                    }}>
                      {customer.is_staff ? 'Admin' : 'Customer'}
                    </span>
                  </td>
                  <td>
                    <span className="admin-status-badge" style={{
                      color: customer.is_active ? 'var(--color-success)' : 'var(--color-danger)',
                      background: customer.is_active ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                    }}>
                      {customer.is_active ? 'Active' : 'Blocked'}
                    </span>
                  </td>
                  <td>
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
                <tr><td colSpan={7} className="admin-table-empty">Không tìm thấy khách hàng phù hợp.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default AdminPage;
