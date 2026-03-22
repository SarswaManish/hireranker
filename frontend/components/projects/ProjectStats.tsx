'use client';

import { Users, CheckCircle2, TrendingUp, Clock } from 'lucide-react';
import { ProjectStats as ProjectStatsType } from '@/types';

interface ProjectStatsProps {
  stats: ProjectStatsType;
}

export default function ProjectStats({ stats }: ProjectStatsProps) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-gray-500 text-sm mb-2">
          <Users className="w-4 h-4" />
          <span>Total</span>
        </div>
        <p className="text-2xl font-bold text-gray-900">{stats.total_candidates}</p>
        <p className="text-xs text-gray-500 mt-1">candidates</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-emerald-600 text-sm mb-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Strong Yes</span>
        </div>
        <p className="text-2xl font-bold text-emerald-700">{stats.strong_yes_count}</p>
        <p className="text-xs text-gray-500 mt-1">
          {stats.total_candidates > 0
            ? `${Math.round((stats.strong_yes_count / stats.total_candidates) * 100)}% of total`
            : '—'}
        </p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-blue-600 text-sm mb-2">
          <TrendingUp className="w-4 h-4" />
          <span>Avg Score</span>
        </div>
        <p className="text-2xl font-bold text-gray-900">
          {stats.avg_score > 0 ? Math.round(stats.avg_score) : '—'}
        </p>
        <p className="text-xs text-gray-500 mt-1">out of 100</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-2 text-purple-600 text-sm mb-2">
          <Clock className="w-4 h-4" />
          <span>Evaluated</span>
        </div>
        <p className="text-2xl font-bold text-gray-900">{stats.evaluated_candidates}</p>
        <p className="text-xs text-gray-500 mt-1">
          {stats.evaluation_progress > 0
            ? `${Math.round(stats.evaluation_progress)}% complete`
            : 'not started'}
        </p>
      </div>
    </div>
  );
}
