import React, { useState } from 'react';
import { uploadAnalyticsFile, getAnalyticsResult } from '../api/apiClient';
import axios from 'axios';

const SmartAnalytics = () => {
  const [tgLink, setTgLink] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const handleAnalyze = async () => {
    if (!tgLink && !file) {
      setError('Добавьте Telegram / Instagram ссылку или загрузите файл с данными.');
      return;
    }

    setError(null);
    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      if (file) formData.append('file', file);
      if (tgLink) formData.append('link', tgLink);

      const response = await axios.post('/api/v1/analytics/smart', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      console.log('Ответ от сервера:', response.data);
      setResult(response.data);
    } catch (err) {
      console.error('Ошибка при анализе:', err);
      setError('Не удалось выполнить анализ. Проверьте подключение и попробуйте снова.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto mt-10 p-6 bg-white rounded-2xl shadow-lg">
      <h1 className="text-2xl font-bold text-gray-800 mb-4">Умная аналитика</h1>
      <p className="text-gray-600 mb-6">
        Загрузите данные бизнеса (чеки, продажи, аудитория) или укажите ссылку на Telegram / VK / Instagram.
        Система проанализирует вашу аудиторию, тренды и предложит стратегии для роста.
      </p>

      <div className="space-y-4">
        <input
          type="text"
          value={tgLink}
          onChange={(e) => setTgLink(e.target.value)}
          placeholder="Ссылка на Telegram/VK/Instagram"
          className="w-full border border-gray-300 rounded-xl p-3 focus:ring-2 focus:ring-blue-500 outline-none"
        />

        <div>
          <label className="block mb-2 text-gray-600">Загрузить файл с данными (.csv, .xlsx)</label>
          <input
            type="file"
            onChange={(e) => setFile(e.target.files[0])}
            className="w-full text-sm"
          />
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="bg-blue-600 text-white px-6 py-3 rounded-xl hover:bg-blue-700 transition disabled:bg-gray-400"
        >
          {loading ? 'Анализирую...' : 'Запустить анализ'}
        </button>
      </div>

      {error && <p className="mt-4 text-red-600">{error}</p>}

        {result && (
            <div className="mt-8 border-t border-gray-200 pt-6">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">📊 Результаты анализа</h2>
                {/* --- НОВЫЙ БЛОК ДЛЯ КРАТКИХ РЕКОМЕНДАЦИЙ --- */}
                {result.kratkieRekomendatsii && Array.isArray(result.kratkieRekomendatsii) && result.kratkieRekomendatsii.length > 0 && (
                    <div className="mb-6">
                        <h3 className="font-semibold text-gray-700 mb-2">💡 Ключевые рекомендации:</h3>
                        <ul className="list-disc list-inside text-gray-700 space-y-1">
                            {result.kratkieRekomendatsii.map((item, index) => (
                                <li key={index}>{item}</li>
                            ))}
                        </ul>
                    </div>
                )}
                {/* --- БЛОК ДЛЯ ОТОБРАЖЕНИЯ ЦЕЛИ НА НЕДЕЛЮ (ключ изменен на русский) --- */}
                {result.celNaNedelyu && (
                    <div className="mb-6 bg-blue-50 p-4 rounded-lg">
                        <h3 className="font-semibold text-gray-800 mb-2">🎯 Цель на неделю:</h3>
                        <p className="text-gray-700">{result.celNaNedelyu}</p>
                    </div>
                )}
                {/* --- БЛОК ДЛЯ ОТОБРАЖЕНИЯ КОНТЕНТ-ПЛАНА (ключи изменены на русские) --- */}
                {result.kontentPlan && Array.isArray(result.kontentPlan) && result.kontentPlan.length > 0 && (
                    <div>
                        <h3 className="font-semibold text-gray-800 mb-3">🗓️ Контент-план по дням:</h3>
                        <div className="space-y-4">
                            {result.kontentPlan.map((plan, index) => (
                                <div key={index} className="border border-gray-200 p-4 rounded-lg">
                                    <p className="font-bold text-md text-blue-600">{plan.den}</p>
                                    <p className="mt-2"><strong>Тема:</strong> {plan.tema}</p>
                                    <p className="mt-1"><strong>Идея поста:</strong> {plan.ideyaPosta}</p>
                                    <p className="mt-1"><strong>Формат:</strong> {plan.format}</p>
                                    <p className="mt-1"><strong>Призыв к действию:</strong> {plan.prizyvKDeystviyu}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
                {/* --- ПРОВЕРКА, ЕСЛИ ДАННЫЕ ВООБЩЕ НЕ ПРИШЛИ В НУЖНОМ ФОРМАТЕ --- */}
                {!result.kratkieRekomendatsii && !result.kontentPlan && (
                    <p className="text-gray-600">⚠️ Ответ получен, но его структура не распознана.</p>
                )}
            </div>
        )}
    </div>
  );
};

export default SmartAnalytics;
