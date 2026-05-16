import { useNavigate, useLocation } from "react-router-dom";

const menuItems = [
  { name: "Dashboard", path: "/" },
  { name: "Forecast", path: "/" },
  { name: "CSV Upload", path: "/" },
  { name: "AI Insights", path: "/" },
  { name: "History", path: "/history" },
  { name: "Settings", path: "/settings" },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem("token");
    navigate("/login");
    window.location.reload();
  };

  return (
    <div className="w-64 h-screen bg-slate-900 text-white p-6 flex flex-col justify-between">
      <div>
        <h1 className="text-3xl font-bold mb-8">Supply Chain AI</h1>

        <div className="space-y-4">
          {menuItems.map((item) => (
            <button
              key={item.name}
              onClick={() => navigate(item.path)}
              className={
                "w-full text-left px-4 py-3 rounded-xl transition " +
                (location.pathname === item.path
                  ? "bg-blue-600"
                  : "hover:bg-blue-600")
              }
            >
              {item.name}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleLogout}
        className="w-full text-left px-4 py-3 rounded-xl bg-red-600 hover:bg-red-700 transition font-semibold"
      >
        Logout
      </button>
    </div>
  );
}
