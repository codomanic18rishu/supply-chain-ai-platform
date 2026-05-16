import Sidebar from "../components/Sidebar";

export default function HistoryPage() {
  const downloadPDF = () => {
    window.open(
      "https://supply-chain-ai-platform.onrender.com/report/history.pdf",
      "_blank"
    );
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-white">
      <Sidebar />

      <div className="flex-1 p-10">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold">Forecast History</h1>

          <button
            onClick={downloadPDF}
            className="bg-red-600 hover:bg-red-700 px-6 py-3 rounded-xl font-semibold"
          >
            Download PDF Report
          </button>
        </div>

        <p className="text-slate-300">
          View all previously generated forecasts and export them as a PDF report.
        </p>
      </div>
    </div>
  );
}
