import { useNavigate } from "react-router-dom";

const menuItems = [
  { name: "Dashboard", path: "/" },
  { name: "Forecast", path: "/" },
  { name: "CSV Upload", path: "/" },
  { name: "AI Insights", path: "/" },
  { name: "History", path: "/history" },
  { name: "Settings", path: "/" },
];

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <div className="w-64 min-h-screen bg-slate-900 text-white p-6">
      <h1 className="text-3xl font-bold mb-8">Supply Chain AI</h1>

      <div className="space-y-4">
        {menuItems.map((item) => (
          <button
            key={item.name}
            onClick={() => navigate(item.path)}
            className="w-full text-left px-4 py-3 rounded-xl hover:bg-blue-600 transition"
          >
            {item.name}
          </button>
        ))}
      </div>
    </div>
  );
}
