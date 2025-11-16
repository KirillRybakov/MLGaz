// src/modules/LoginPage.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import toast from 'react-hot-toast';

const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Определяем, куда перенаправить пользователя после входа
  const from = location.state?.from?.pathname || "/";

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Пожалуйста, заполните все поля.');
      return;
    }
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Вход выполнен успешно!');
      navigate(from, { replace: true }); // Перенаправляем на нужную страницу
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Неверный email или пароль.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-2xl shadow-lg">
        <h1 className="text-2xl font-bold text-center text-gray-800">Вход в аккаунт</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* --- ПОЛЕ ДЛЯ EMAIL --- */}
          <div>
            <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-600">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-red-500 outline-none"
              placeholder="you@example.com"
              required
            />
          </div>

          {/* --- ПОЛЕ ДЛЯ ПАРОЛЯ --- */}
          <div>
            <label htmlFor="password" className="block mb-2 text-sm font-medium text-gray-600">Пароль</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-red-500 outline-none"
              placeholder="••••••••"
              required
            />
          </div>

          {/* --- КНОПКА ОТПРАВКИ --- */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-red-600 text-white px-6 py-3 rounded-xl hover:bg-red-700 transition disabled:bg-gray-400"
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
        <p className="text-center text-sm text-gray-600">
          Нет аккаунта?{' '}
          <Link to="/register" className="font-medium text-red-600 hover:underline">
            Зарегистрируйтесь
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;