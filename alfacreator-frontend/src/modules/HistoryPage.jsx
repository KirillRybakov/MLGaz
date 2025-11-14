// modules/HistoryPage.jsx
import React, { useState, useEffect } from 'react';
import { getHistory } from '../api/apiClient';
import Loader from '../components/Loader';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Маленькие компоненты для отображения разных типов истории
const PromoHistoryItem = ({ item }) => (
  <>
    <h4 className="font-semibold text-gray-600">Входные данные:</h4>
    <p className="text-sm text-gray-500">Продукт: {item.input_data.product_description}, Аудитория: {item.input_data.audience}</p>
    <h4 className="font-semibold text-gray-600 mt-2">Сгенерированные посты:</h4>
    <ul className="list-disc list-inside space-y-1 mt-1">
      {item.output_data.results.map((text, i) => <li key={i}>{text}</li>)}
    </ul>
  </>
);

const AnalyticsHistoryItem = ({ item }) => (
  <>
    <h4 className="font-semibold text-gray-600">Входные данные:</h4>
    <p className="text-sm text-gray-500">Файл: {item.input_data.filename}</p>
    <h4 className="font-semibold text-gray-600 mt-2">Выводы ИИ:</h4>
    <p className="p-2 bg-green-50 rounded-md">{item.output_data.insights}</p>
    <div style={{ width: '100%', height: 200 }} className="mt-2">
      <ResponsiveContainer>
        <LineChart data={item.output_data.chart_data.labels.map((l, i) => ({ name: l, value: item.output_data.chart_data.values[i] }))}>
          <CartesianGrid strokeDasharray="3 3" /> <XAxis dataKey="name" /> <YAxis /> <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#ef4444" name="Продажи" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  </>
);

const DocumentHistoryItem = ({ item }) => (
  <>
    <h4 className="font-semibold text-gray-600">Входные данные:</h4>
    <p className="text-sm text-gray-500">Шаблон: {item.input_data.template_name}</p>
    <h4 className="font-semibold text-gray-600 mt-2">Сгенерированный документ:</h4>
    <pre className="whitespace-pre-wrap font-mono text-xs bg-gray-50 p-2 rounded-md max-h-40 overflow-y-auto">{item.output_data.generated_text}</pre>
  </>
);

const HistoryPage = () => {
  const [history, setHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await getHistory();
        setHistory(response.data);
      } catch (error) {
        toast.error("Не удалось загрузить историю.");
      } finally {
        setIsLoading(false);
      }
    };
    fetchHistory();
  }, []);

  const renderItem = (item) => {
    switch (item.request_type) {
      case 'promo': return <PromoHistoryItem item={item} />;
      case 'analytics': return <AnalyticsHistoryItem item={item} />;
      case 'document': return <DocumentHistoryItem item={item} />;
      default: return null;
    }
  };

  const getTitle = (type) => {
      switch (type) {
          case 'promo': return "Генерация Промо";
          case 'analytics': return "Аналитика";
          case 'document': return "Генерация Документа";
          default: return "Запись";
      }
  }

  if (isLoading) return <Loader text="Загрузка истории..." />;
  if (history.length === 0) return <p className="text-center text-gray-500">Ваша история запросов пуста.</p>;

  return (
    <div className="space-y-4">
      {history.map(item => (
        <div key={item.id} className="bg-white p-4 rounded-lg shadow-md">
          <div className="flex justify-between items-center mb-2 border-b pb-2">
            <h3 className="text-lg font-bold text-gray-800">{getTitle(item.request_type)}</h3>
            <span className="text-xs text-gray-400">{new Date(item.created_at).toLocaleString('ru-RU')}</span>
          </div>
          {renderItem(item)}
        </div>
      ))}
    </div>
  );
};

export default HistoryPage;