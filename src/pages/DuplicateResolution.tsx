import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

interface DuplicateCandidate {
  id: number;
  import_row_id: number;
  existing_customer_id: number;
  existing_customer: {
    id: number;
    full_name: string;
    email: string;
    phone: string;
    address: string;
  };
  new_data: {
    full_name?: string;
    email?: string;
    phone?: string;
    address?: string;
  };
  match_reason: string;
  similarity_score: number;
  resolution: string;
}

export default function DuplicateResolution() {
  const { importId } = useParams<{ importId: string }>();
  const navigate = useNavigate();
  const [candidates, setCandidates] = useState<DuplicateCandidate[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCandidates();
  }, [importId]);

  const fetchCandidates = async () => {
    try {
      const response = await fetch(`/api/duplicates/${importId}`);
      const data = await response.json();
      setCandidates(data);
    } catch (error) {
      console.error('Error fetching candidates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResolve = async (candidateId: number, action: string) => {
    try {
      const response = await fetch(`/api/duplicates/${candidateId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });

      if (response.ok) {
        // 解決済みの候補を削除
        setCandidates(candidates.filter(c => c.id !== candidateId));
      }
    } catch (error) {
      console.error('Error resolving candidate:', error);
    }
  };

  if (loading) {
    return <div className="p-8">読み込み中...</div>;
  }

  if (candidates.length === 0) {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">重複解決</h1>
        <p className="mb-4">解決が必要な重複はありません。</p>
        <button
          onClick={() => navigate('/')}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          ホームに戻る
        </button>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">重複解決 (インポートID: {importId})</h1>
      <p className="mb-6 text-gray-600">{candidates.length}件の重複候補があります</p>

      <div className="space-y-6">
        {candidates.map((candidate) => (
          <div key={candidate.id} className="border rounded-lg p-6 bg-white shadow">
            <div className="grid grid-cols-2 gap-6 mb-4">
              {/* 既存顧客 */}
              <div className="border-r pr-6">
                <h3 className="font-bold text-lg mb-2 text-blue-600">既存顧客</h3>
                <div className="space-y-2">
                  <p><span className="font-semibold">名前:</span> {candidate.existing_customer.full_name}</p>
                  <p><span className="font-semibold">メール:</span> {candidate.existing_customer.email || '(なし)'}</p>
                  <p><span className="font-semibold">電話:</span> {candidate.existing_customer.phone || '(なし)'}</p>
                  <p><span className="font-semibold">住所:</span> {candidate.existing_customer.address || '(なし)'}</p>
                </div>
              </div>

              {/* 新規データ */}
              <div className="pl-6">
                <h3 className="font-bold text-lg mb-2 text-green-600">新規データ</h3>
                <div className="space-y-2">
                  <p><span className="font-semibold">名前:</span> {candidate.new_data.full_name || '(なし)'}</p>
                  <p><span className="font-semibold">メール:</span> {candidate.new_data.email || '(なし)'}</p>
                  <p><span className="font-semibold">電話:</span> {candidate.new_data.phone || '(なし)'}</p>
                  <p><span className="font-semibold">住所:</span> {candidate.new_data.address || '(なし)'}</p>
                </div>
              </div>
            </div>

            {/* マッチ情報 */}
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <p className="text-sm">
                <span className="font-semibold">マッチ理由:</span> {candidate.match_reason}
              </p>
              <p className="text-sm">
                <span className="font-semibold">類似度:</span> {(candidate.similarity_score * 100).toFixed(0)}%
              </p>
            </div>

            {/* アクションボタン */}
            <div className="flex gap-3">
              <button
                onClick={() => handleResolve(candidate.id, 'merged')}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                既存顧客にマージ
              </button>
              <button
                onClick={() => handleResolve(candidate.id, 'created_new')}
                className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
              >
                新規顧客として作成
              </button>
              <button
                onClick={() => handleResolve(candidate.id, 'ignored')}
                className="px-4 py-2 bg-gray-400 text-white rounded hover:bg-gray-500"
              >
                無視
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
