import { useState } from "react";

export default function SettingsPage() {
  const [apiUrl, setApiUrl] = useState(
    localStorage.getItem("apiUrl") ||
      "https://supply-chain-ai-platform.onrender.com"
  );

  const saveSettings = () => {
    localStorage.setItem("apiUrl", apiUrl);
    alert("Settings saved successfully!");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white p-10">
      <h1 className="text-4xl font-bold mb-6">Settings</h1>

      <div className="max-w-2xl bg-slate-900 p-6 rounded-2xl">
        <label className="block text-lg mb-2">Backend API URL</label>
        <input
          type="text"
          value={apiUrl}
          onChange={(e) => setApiUrl(e.target.value)}
          className="w-full p-3 rounded-lg bg-slate-800 border border-slate-700 mb-4"
        />

        <button
          onClick={saveSettings}
          className="bg-blue-600 hover:bg-blue-700 px-6 py-3 rounded-lg font-semibold"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
}
