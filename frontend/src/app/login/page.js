'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Login() {
  const [adminCode, setAdminCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (adminCode.trim() === '') {
      setError('請輸入管理員密碼');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/admin/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: adminCode }),
      });

      const data = await response.json();

      if (response.ok) {
        // 儲存認證資訊
        localStorage.setItem('isAdmin', 'true');
        localStorage.setItem('adminToken', data.token);
        localStorage.setItem('adminCode', adminCode);

        // 跳轉到管理頁面
        router.push('/admin');
      } else {
        setError(data.detail || '管理員密碼錯誤');
      }
    } catch (error) {
      console.error('登入錯誤:', error);
      setError('登入失敗，請檢查網路連線');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#0f203e]">
      <div className="w-full max-w-sm px-6">
        <div className="text-center mb-12">
          <h1 className="text-2xl font-bold text-[#92cbf4] tracking-wider">
            管理員介面
          </h1>
        </div>

        <div className="space-y-6">
          <div className="text-left">
            <label className="block text-[#557797] text-sm font-medium mb-4">
              管理員密碼
            </label>

            <input
              type="password"
              value={adminCode}
              onChange={(e) => setAdminCode(e.target.value)}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSubmit(e);
                }
              }}
              className="w-full px-4 py-3 bg-transparent border-2 border-[#294565] rounded-lg
                       text-white placeholder-slate-400 focus:outline-none focus:border-cyan-400
                       transition-colors duration-200"
              placeholder=""
              disabled={isLoading}
            />
          </div>

          {/* Error message */}
          {error && (
            <div className="text-red-400 text-sm text-center bg-red-900/20 border border-red-500/30 rounded-lg p-3">
              {error}
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="w-full py-3 text-md rounded-xl bg-[#81c0e7] text-[#092e58] 
                     hover:bg-[#70b3d9] disabled:bg-gray-500 disabled:cursor-not-allowed 
                     font-bold transition-colors duration-200"
          >
            {isLoading ? '登入中...' : '登入'}
          </button>
        </div>
      </div>
    </div >
  );
}