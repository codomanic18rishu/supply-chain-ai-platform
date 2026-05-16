interface KPIcardProps {
  title: string;
  value: string;
}

export default function KPIcard({
  title,
  value,
}: KPIcardProps) {
  return (
    <div className="rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-6 shadow-2xl">
      <p className="text-sm text-slate-400 mb-2">{title}</p>
      <p className="text-3xl font-bold text-white">{value}</p>
    </div>
  );
}