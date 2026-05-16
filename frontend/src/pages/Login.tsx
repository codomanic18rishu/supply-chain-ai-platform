import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

export default function Login() {
  const navigate = useNavigate();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);

    try {
      const response = await api.post('/auth/login', {
        username,
        password,
      });

      localStorage.setItem(
        'access_token',
        response.data.access_token
      );

      alert('Login successful!');
      navigate('/');
    } catch (error: any) {
      let message = 'Login failed';

      const detail = error?.response?.data?.detail;

      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail)) {
        message = detail
          .map((item) => item.msg || JSON.stringify(item))
          .join('\n');
      } else if (detail) {
        message = JSON.stringify(detail, null, 2);
      } else if (error?.message) {
        message = error.message;
      }

      alert(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className='min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-6'>
      <div className='w-full max-w-md rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl p-8 shadow-2xl text-white'>
        <p className='text-cyan-300 text-sm font-medium mb-2'>
          Welcome Back
        </p>

        <h1 className='text-3xl font-bold mb-6'>
          Sign In
        </h1>

        <div className='space-y-4'>
          <input
            type='text'
            placeholder='Username'
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className='w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 outline-none text-white'
          />

          <input
            type='password'
            placeholder='Password'
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className='w-full rounded-xl bg-white/5 border border-white/10 px-4 py-3 outline-none text-white'
          />

          <button
            onClick={handleLogin}
            disabled={loading}
            className='w-full rounded-xl bg-cyan-500 hover:bg-cyan-400 transition py-3 font-semibold text-slate-950 disabled:opacity-50'
          >
            {loading ? 'Signing In...' : 'Sign In'}
          </button>

          <p className='text-sm text-slate-300 text-center'>
            Don't have an account?{' '}
            <Link to='/signup' className='text-cyan-300 hover:underline'>
              Create Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

