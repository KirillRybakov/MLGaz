import React, { createContext, useState, useContext, useEffect } from 'react';
import { loginUser, registerUser, getCurrentUserProfile } from '../api/apiClient';
import Loader from '../components/Loader'; // Предполагаем, что у вас есть компонент лоадера

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState(true); // Для первоначальной проверки токена

  useEffect(() => {
    const validateToken = async () => {
      if (token) {
        try {
          const { data } = await getCurrentUserProfile();
          setUser(data);
        } catch (error) {
          console.error("Невалидный токен, выход из системы.");
          logout(); // Если токен есть, но он невалиден
        }
      }
      setLoading(false);
    };
    validateToken();
  }, [token]);

  const login = async (email, password) => {
    const { data } = await loginUser(email, password);
    localStorage.setItem('authToken', data.access_token);
    setToken(data.access_token);
    // useEffect выше сам загрузит данные пользователя после установки токена
  };

  const register = async (email, password) => {
    await registerUser(email, password);
    // После успешной регистрации сразу логиним пользователя
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    setToken(null);
    setUser(null);
  };

  if (loading) {
    return <Loader />; // Показываем лоадер, пока проверяем сессию
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);