import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  forecast: number[];
}

export default function ForecastChart({
  forecast,
}: Props) {
  const data = forecast.map((value, index) => ({
    day: `Day ${index + 1}`,
    value,
  }));

  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-2xl h-[420px]">
      <h2 className="text-2xl font-semibold mb-6">
        Forecast Chart
      </h2>

      <ResponsiveContainer width="100%" height="85%">
        <LineChart data={data}>
          <XAxis dataKey="day" stroke="#94a3b8" />
          <YAxis stroke="#94a3b8" />
          <Tooltip />
          <Line
            type="monotone"
            dataKey="value"
            stroke="#22d3ee"
            strokeWidth={3}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}