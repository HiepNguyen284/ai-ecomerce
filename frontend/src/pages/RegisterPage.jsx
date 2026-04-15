import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api.js';

function RegisterPage({ onLogin }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', username: '', first_name: '', last_name: '', password: '', password_confirm: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.password_confirm) { setError('Mật khẩu không khớp.'); return; }
    setLoading(true); setError('');
    try {
      const data = await api.register(form);
      onLogin(data.user, data.token);
      navigate('/');
    } catch (err) {
      const msgs = [];
      if (typeof err === 'object') Object.values(err).forEach((v) => { if (Array.isArray(v)) msgs.push(...v); else if (typeof v === 'string') msgs.push(v); });
      setError(msgs.join(' ') || 'Đăng ký thất bại. Vui lòng thử lại.');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-card fade-in">
        <h2>Tạo tài khoản</h2>
        <p className="subtitle">Tham gia ShopVerse và bắt đầu mua sắm</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-md)' }}>
            <div className="form-group">
              <label htmlFor="first_name">Họ</label>
              <input type="text" id="first_name" className="form-control" placeholder="Nguyễn"
                value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} />
            </div>
            <div className="form-group">
              <label htmlFor="last_name">Tên</label>
              <input type="text" id="last_name" className="form-control" placeholder="Văn A"
                value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
            </div>
          </div>
          <div className="form-group">
            <label htmlFor="username">Tên đăng nhập</label>
            <input type="text" id="username" className="form-control" placeholder="nguyenvana" required
              value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
          </div>
          <div className="form-group">
            <label htmlFor="reg-email">Email</label>
            <input type="email" id="reg-email" className="form-control" placeholder="email@example.com" required
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="form-group">
            <label htmlFor="reg-password">Mật khẩu</label>
            <input type="password" id="reg-password" className="form-control" placeholder="Tối thiểu 8 ký tự" required minLength={8}
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <div className="form-group">
            <label htmlFor="password_confirm">Xác nhận mật khẩu</label>
            <input type="password" id="password_confirm" className="form-control" placeholder="Nhập lại mật khẩu" required
              value={form.password_confirm} onChange={(e) => setForm({ ...form, password_confirm: e.target.value })} />
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={loading} id="register-submit">
            {loading ? 'Đang tạo tài khoản...' : 'Tạo tài khoản'}
          </button>
        </form>
        <div className="auth-footer">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></div>
      </div>
    </div>
  );
}

export default RegisterPage;
