import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api.js';

function LoginPage({ onLogin }) {
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true); setError('');
    try {
      const data = await api.login(form);
      onLogin(data.user, data.token);
      navigate('/');
    } catch (err) {
      setError(err.error || 'Thông tin đăng nhập không hợp lệ.');
    } finally { setLoading(false); }
  };

  return (
    <div className="auth-page">
      <div className="auth-card fade-in">
        <h2>Chào mừng trở lại</h2>
        <p className="subtitle">Đăng nhập vào tài khoản ShopVerse của bạn</p>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input type="email" id="email" className="form-control" placeholder="email@example.com" required
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
          </div>
          <div className="form-group">
            <label htmlFor="password">Mật khẩu</label>
            <input type="password" id="password" className="form-control" placeholder="Nhập mật khẩu" required
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={loading} id="signin-submit">
            {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
          </button>
        </form>
        <div className="auth-footer">Chưa có tài khoản? <Link to="/register">Tạo tài khoản</Link></div>
      </div>
    </div>
  );
}

export default LoginPage;
