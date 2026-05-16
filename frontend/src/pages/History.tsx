import { useEffect, useState } from 'react';
import api from '../services/api';

interface HistoryRecord {
  id: number;
  model_used: string;
  confidence: number;
  forecast: number[];
  insights: string;
  created_at: string;
}

export default function History() {
  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await api.get('/history/');
        setRecords(response.data.history);
      } catch (error) {
        console.error('Failed to load history:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className='min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white p-10'>
        Loading forecast history...
      </div>
    );
  }

  return (
    <div className='min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white p-8 lg:p-10'>
      <h1 className='text-4xl font-bold mb-8'>
        Forecast History
      </h1>

      <div className='space-y-6'>
        {records.map((record) => (
          <div
            key={record.id}
            className='rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-2xl'
          >
            <div className='flex justify-between items-center mb-4'>
              <h2 className='text-2xl font-semibold'>
                Forecast #{record.id}
              </h2>

              <span className='text-sm text-slate-400'>
                {new Date(record.created_at).toLocaleString()}
              </span>
            </div>

            <p className='text-slate-300 mb-2'>
              Model: {record.model_used}
            </p>

            <p className='text-slate-300 mb-4'>
              Confidence: {(record.confidence * 100).toFixed(1)}%
            </p>

            <p className='text-cyan-300 mb-2 font-medium'>
              Forecast Values
            </p>

            <p className='text-slate-300 mb-4'>
              {record.forecast.join(', ')}
            </p>

            <p className='text-cyan-300 mb-2 font-medium'>
              AI Insights
            </p>

            <pre className='whitespace-pre-wrap text-slate-300 font-sans leading-relaxed'>
              {record.insights}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
