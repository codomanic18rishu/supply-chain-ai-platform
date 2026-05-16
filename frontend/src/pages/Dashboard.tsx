import { useState } from 'react';
import { Link } from 'react-router-dom';

import Sidebar from '../components/Sidebar';
import KPIcard from '../components/KPIcard';
import CSVUpload from '../components/CSVUpload';
import ForecastChart from '../components/ForecastChart';

export default function Dashboard() {
  const [forecast, setForecast] = useState<number[]>([]);
  const [insights, setInsights] = useState<string>(
    'Upload a CSV file to generate AI-powered business insights.'
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white flex">
      <Sidebar />

      <main className="flex-1 p-8 lg:p-10 overflow-auto">
        {/* Hero Section */}
        <div className="relative mb-10 overflow-hidden rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-cyan-500/10 via-indigo-500/10 to-purple-500/10" />

          <div className="relative z-10">
            <p className="text-cyan-300 text-sm font-medium mb-2">
              AI-Powered Supply Chain Intelligence
            </p>

            <h1 className="text-4xl lg:text-5xl font-bold leading-tight mb-4">
              Predict Demand.
              <br />
              Optimize Inventory.
            </h1>

            <p className="text-slate-300 max-w-3xl text-lg leading-relaxed">
              Upload CSV files, train machine learning models, and generate
              real-time forecasts with advanced analytics and AI-generated
              business insights.
            </p>

            <div className="mt-6 flex gap-4">
              <Link
                to="/login"
                className="rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white hover:bg-white/10 transition"
              >
                Login
              </Link>

              <Link
                to="/signup"
                className="rounded-xl bg-cyan-500 px-5 py-3 text-sm font-semibold text-slate-950 hover:bg-cyan-400 transition"
              >
                Sign Up
              </Link>
            </div>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-10">
          <KPIcard title="Forecast Accuracy" value="93%" />
          <KPIcard title="Predicted Demand" value="279.6" />
          <KPIcard title="Stockout Risk" value="Low" />
          <KPIcard title="Revenue Impact" value="+12.4%" />
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Forecast Chart */}
          <div className="xl:col-span-2">
            {forecast.length > 0 ? (
              <ForecastChart forecast={forecast} />
            ) : (
              <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl">
                <h2 className="text-2xl font-semibold mb-4">
                  Demand Forecast Overview
                </h2>
                <p className="text-slate-300">
                  Upload a CSV file to generate and visualize forecasts.
                </p>
              </div>
            )}
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            <CSVUpload
              onForecast={setForecast}
              onInsights={setInsights}
            />

            <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-2xl">
              <h2 className="text-2xl font-semibold mb-4">
                AI Insights
              </h2>

              <pre className="whitespace-pre-wrap text-slate-300 font-sans leading-relaxed">
                {insights}
              </pre>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
