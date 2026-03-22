'use client';

import { useState } from 'react';
import { Candidate } from '@/types';
import RecommendationBadge from './RecommendationBadge';
import { getScoreColor } from '@/lib/utils';
import { CheckCircle2, AlertTriangle, AlertOctagon, Minus } from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useRecruiterQuery } from '@/hooks/useEvaluations';

interface CompareViewProps {
  candidates: Candidate[];
  projectId: string;
}

interface CandidatePanelProps {
  candidate: Candidate | undefined;
  label: string;
  candidates: Candidate[];
  onSelect: (id: string) => void;
}

function CandidatePanel({ candidate, label, candidates, onSelect }: CandidatePanelProps) {
  return (
    <div className="flex-1 min-w-0 space-y-4">
      <div>
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{label}</p>
        <Select onValueChange={onSelect} value={candidate?.id || ''}>
          <SelectTrigger>
            <SelectValue placeholder="Select a candidate" />
          </SelectTrigger>
          <SelectContent>
            {candidates.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {candidate && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">{candidate.name}</h3>
              <p className="text-sm text-gray-500">{candidate.email}</p>
              {candidate.current_title && (
                <p className="text-xs text-gray-500 mt-0.5">{candidate.current_title}</p>
              )}
            </div>
            <div className="flex flex-col items-end gap-1">
              {candidate.recommendation && (
                <RecommendationBadge recommendation={candidate.recommendation} size="sm" />
              )}
              {candidate.score != null && (
                <span className={`text-xl font-bold px-2 py-0.5 rounded ${getScoreColor(candidate.score)}`}>
                  {Math.round(candidate.score)}
                </span>
              )}
            </div>
          </div>

          {candidate.skills && candidate.skills.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">Skills</p>
              <div className="flex flex-wrap gap-1">
                {candidate.skills.slice(0, 8).map((s) => (
                  <span key={s} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {candidate.strengths && candidate.strengths.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-emerald-700 mb-2 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                Strengths
              </p>
              <ul className="space-y-1">
                {candidate.strengths.slice(0, 3).map((s, i) => (
                  <li key={i} className="text-xs text-gray-700 flex items-start gap-1.5">
                    <span className="text-emerald-500 mt-0.5">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {candidate.weaknesses && candidate.weaknesses.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-amber-700 mb-2 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                Weaknesses
              </p>
              <ul className="space-y-1">
                {candidate.weaknesses.slice(0, 3).map((w, i) => (
                  <li key={i} className="text-xs text-gray-700 flex items-start gap-1.5">
                    <span className="text-amber-500 mt-0.5">•</span>
                    {w}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {candidate.red_flags && candidate.red_flags.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-red-700 mb-2 flex items-center gap-1">
                <AlertOctagon className="w-3.5 h-3.5" />
                Red Flags
              </p>
              <ul className="space-y-1">
                {candidate.red_flags.slice(0, 2).map((f, i) => (
                  <li key={i} className="text-xs text-red-700 flex items-start gap-1.5">
                    <span className="mt-0.5">•</span>
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function CompareView({ candidates, projectId }: CompareViewProps) {
  const [candidateAId, setCandidateAId] = useState<string>(candidates[0]?.id || '');
  const [candidateBId, setCandidateBId] = useState<string>(candidates[1]?.id || '');
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const recuriterQuery = useRecruiterQuery();

  const candidateA = candidates.find((c) => c.id === candidateAId);
  const candidateB = candidates.find((c) => c.id === candidateBId);

  // Build chart data from score breakdowns
  const chartData = candidateA?.score_breakdown?.map((dim) => {
    const bDim = candidateB?.score_breakdown?.find((d) => d.dimension === dim.dimension);
    return {
      name: dim.dimension.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      [candidateA?.name || 'A']: dim.score,
      [candidateB?.name || 'B']: bDim?.score || 0,
    };
  }) || [];

  const handleAskAI = async () => {
    if (!aiQuery.trim()) return;
    try {
      const res = await recuriterQuery.mutateAsync({
        question: aiQuery,
        project_id: projectId,
        candidate_ids: [candidateAId, candidateBId].filter(Boolean),
      });
      setAiResponse(res.answer);
    } catch (e) {
      setAiResponse('Unable to get AI response. Please try again.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Two-column comparison */}
      <div className="flex gap-6">
        <CandidatePanel
          candidate={candidateA}
          label="Candidate A"
          candidates={candidates}
          onSelect={setCandidateAId}
        />

        <div className="flex items-start pt-8">
          <div className="w-8 flex items-center justify-center">
            <Minus className="w-4 h-4 text-gray-300" />
          </div>
        </div>

        <CandidatePanel
          candidate={candidateB}
          label="Candidate B"
          candidates={candidates}
          onSelect={setCandidateBId}
        />
      </div>

      {/* Score comparison chart */}
      {chartData.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Score Comparison</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={120} />
              <Tooltip />
              <Legend />
              <Bar dataKey={candidateA?.name || 'A'} fill="#6366f1" radius={[0, 4, 4, 0]} />
              <Bar dataKey={candidateB?.name || 'B'} fill="#10b981" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Ask AI */}
      <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-5">
        <h3 className="font-semibold text-indigo-900 mb-3">Ask AI to Compare</h3>
        <div className="flex gap-3">
          <input
            type="text"
            value={aiQuery}
            onChange={(e) => setAiQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAskAI()}
            placeholder="e.g. Who is better for a fast-paced startup environment?"
            className="flex-1 px-4 py-2 rounded-lg border border-indigo-300 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <Button onClick={handleAskAI} disabled={recuriterQuery.isPending}>
            {recuriterQuery.isPending ? 'Asking...' : 'Ask AI'}
          </Button>
        </div>
        {aiResponse && (
          <div className="mt-4 p-4 bg-white rounded-lg border border-indigo-200">
            <p className="text-sm text-gray-700 leading-relaxed">{aiResponse}</p>
          </div>
        )}
      </div>
    </div>
  );
}
