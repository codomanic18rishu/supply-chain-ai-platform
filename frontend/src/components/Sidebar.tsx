import { useNavigate } from 'react-router-dom';

export default function Sidebar() {
  const navigate = useNavigate();

  const items = [
    { label: 'Dashboard', path: '/' },
    { label: 'Forecast', path: '/' },
    { label: 'CSV Upload', path: '/' },
    { label: 'AI Insights', path: '/' },
    { label: 'History', path: '/history' },
    { label: 'Settings', path: '/' },
  ];

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  return (
    <aside className='hidden lg:flex w-72 flex-col border-r border-white/10 bg-black/20 backdrop-blur-xl p-8'>
      <h1 className='text-2xl font-bold text-white mb-10'>
        Supply Chain AI
      </h1>

      <nav className='space-y-2 flex-1'>
        {items.map((item, index) => (
          <button
            key={item.label}
            onClick={() => navigate(item.path)}
            className={
              index === 0
                ? 'w-full text-left rounded-xl px-4 py-3 cursor-pointer transition bg-cyan-500/20 text-cyan-300'
                : 'w-full text-left rounded-xl px-4 py-3 cursor-pointer transition text-slate-300 hover:bg-white/5'
            }
          >
            {item.label}
          </button>
        ))}
      </nav>

      <button
        onClick={handleLogout}
        className='mt-6 w-full rounded-xl bg-red-500/20 text-red-300 hover:bg-red-500/30 transition px-4 py-3 font-semibold'
      >
        Logout
      </button>
    </aside>
  );
}
