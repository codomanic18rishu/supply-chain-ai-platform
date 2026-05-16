import Sidebar from "../components/Sidebar";
import Dashboard from "./Dashboard";

export default function ForecastPage() {
  return (
    <div className="flex">
      <Sidebar />
      <div className="flex-1">
        <Dashboard />
      </div>
    </div>
  );
}
