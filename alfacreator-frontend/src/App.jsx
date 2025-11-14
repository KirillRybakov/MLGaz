// src/App.jsx
import React from 'react';
import { Routes, Route, NavLink, Outlet, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';

import Header from './components/Header';
import ProtectedRoute from './components/ProtectedRoute'; // Убедитесь, что этот файл создан

// Импортируем все страницы
import PromoGenerator from './modules/PromoGenerator';
import AnalyticsDashboard from './modules/AnalyticsDashboard';
import DocumentGenerator from './modules/DocumentGenerator';
import SmartAnalytics from './modules/SmartAnalytics';
import LoginPage from './modules/LoginPage';
import RegisterPage from './modules/RegisterPage';

// Компонент-обертка для страниц, требующих навигацию
const AppLayout = () => {
  const navButtonClasses = ({ isActive }) =>
    `px-4 py-2 font-semibold rounded-md transition-colors ${
      isActive ? 'bg-red-600 text-white' : 'text-gray-600 hover:bg-red-100'
    }`;

  return (
    <main className="container mx-auto p-4 md:p-6">
      <div className="mb-6 flex flex-wrap justify-center gap-2 md:gap-4">
        <NavLink to="/promo" className={navButtonClasses}>Генератор Промо</NavLink>
        <NavLink to="/analytics" className={navButtonClasses}>Аналитика CSV</NavLink>
        <NavLink to="/documents" className={navButtonClasses}>Шаблоны</NavLink>
        <NavLink to="/smart-analytics" className={navButtonClasses}>Умная Аналитика</NavLink>
      </div>
      <div className="max-w-6xl mx-auto">
        <Outlet /> {/* Здесь будет отображаться контент текущего роута */}
      </div>
    </main>
  );
};


function App() {
  return (
    <div>
      <Toaster position="top-center" reverseOrder={false} />
      <Header />
      <Routes>
        {/* Публичные роуты */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        
        {/* Защищенные роуты с общей навигацией */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          {/* Перенаправляем с главной на первую страницу */}
          <Route index element={<Navigate to="/promo" replace />} /> 
          <Route path="promo" element={<PromoGenerator />} />
          <Route path="analytics" element={<AnalyticsDashboard />} />
          <Route path="documents" element={<DocumentGenerator />} />
          <Route path="smart-analytics" element={<SmartAnalytics />} />
        </Route>

        {/* Роут для ненайденных страниц */}
        <Route path="*" element={<h1>404: Страница не найдена</h1>} />
      </Routes>
    </div>
  );
}

export default App;