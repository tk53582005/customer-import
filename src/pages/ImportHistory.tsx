import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface ImportRecord {
  id: number;
  filename: string;
  status: string;
  total_rows: number;
  inserted_count: number;
  error_count: number;
  candidate_count: number;
  created_at: string;
}

export default function ImportHistory() {
  const navigate = useNavigate();
  const [imports, setImports] = useState<ImportRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchImports();
  }, []);

  const fetchImports = async () => {
    try {
      const response = await fetch('/api/import-history');
      const data = await response.json();
      setImports(data);
    } catch (error) {
      console.error('Error fetching imports:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800',
      processing: 'bg-blue-100 text-blue-800',
      failed: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ja-JP');
  };

  if (loading) {
    return <div className="p-8">読み込み中...</div>;
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">インポート履歴</h1>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ファイル名</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ステータス</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">総行数</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">成功</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">エラー</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">重複候補</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">実行日時</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {imports.map((imp) => (
              <tr key={imp.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{imp.id}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{imp.filename}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusBadge(imp.status)}`}>
                    {imp.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{imp.total_rows}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-green-600">{imp.inserted_count}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600">{imp.error_count}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-yellow-600">{imp.candidate_count}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{formatDate(imp.created_at)}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  {imp.candidate_count > 0 && (
                    <button
                      onClick={() => navigate(`/duplicates/${imp.id}`)}
                      className="text-blue-600 hover:text-blue-800"
                    >
                      重複解決
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {imports.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          インポート履歴がありません
        </div>
      )}
    </div>
  );
}
