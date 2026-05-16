import { useState } from 'react';
import api from '../services/api';

interface CSVUploadProps {
  onForecast: (data: number[]) => void;
  onInsights: (text: string) => void;
}

export default function CSVUpload({
  onForecast,
  onInsights,
}: CSVUploadProps) {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);

    try {
      // Step 1: Generate forecast
      const forecastResponse = await api.post(
        '/upload-forecast/?periods=7',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      const forecast = forecastResponse.data.forecast;
      onForecast(forecast);

      // Step 2: Generate AI insights
      const insightsResponse = await api.post(
        '/insights/',
        {
          forecast,
        }
      );

      onInsights(insightsResponse.data.insights);
    } catch (error: any) {
      console.error('Upload error:', error);

      const message =
        error?.response?.data?.detail ||
        error?.message ||
        'Upload failed';

      alert(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-2xl">
      <h2 className="text-2xl font-semibold mb-4">
        Upload CSV File
      </h2>

      <input
        type="file"
        accept=".csv"
        onChange={handleUpload}
        className="mb-4 block w-full text-sm"
      />

      {loading && (
        <p className="text-cyan-300">
          Processing forecast and AI insights...
        </p>
      )}
    </div>
  );
}
