'use client';

import { ScoreBreakdown as ScoreBreakdownType } from '@/types';
import { getScoreBgColor, getScoreTextColor } from '@/lib/utils';
import {
  RadialBarChart,
  RadialBar,
  ResponsiveContainer,
  PolarAngleAxis,
} from 'recharts';

interface ScoreBreakdownProps {
  breakdown: ScoreBreakdownType[];
  overallScore: number;
}

function ScoreDimensionBar({ dimension }: { dimension: ScoreBreakdownType }) {
  const percentage = Math.round((dimension.score / dimension.max_score) * 100);
  const barColor = getScoreBgColor(percentage);
  const textColor = getScoreTextColor(percentage);

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-700 capitalize">
          {dimension.dimension.replace(/_/g, ' ')}
        </span>
        <span className={`text-sm font-bold ${textColor}`}>
          {dimension.score}/{dimension.max_score}
        </span>
      </div>
      <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full ${barColor} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {dimension.reasoning && (
        <p className="text-xs text-gray-500 leading-relaxed">{dimension.reasoning}</p>
      )}
    </div>
  );
}

export default function ScoreBreakdown({ breakdown, overallScore }: ScoreBreakdownProps) {
  const donutData = [{ value: overallScore, fill: overallScore >= 80 ? '#10b981' : overallScore >= 60 ? '#3b82f6' : overallScore >= 40 ? '#f59e0b' : '#ef4444' }];

  return (
    <div className="space-y-6">
      {/* Overall score donut */}
      <div className="flex items-center gap-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
        <div className="relative w-24 h-24 flex-shrink-0">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart
              innerRadius="70%"
              outerRadius="100%"
              data={donutData}
              startAngle={90}
              endAngle={-270}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar dataKey="value" background={{ fill: '#e5e7eb' }} />
            </RadialBarChart>
          </ResponsiveContainer>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xl font-bold text-gray-900">{Math.round(overallScore)}</span>
          </div>
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500">Overall Score</p>
          <p className="text-3xl font-bold text-gray-900">{Math.round(overallScore)}<span className="text-lg text-gray-400">/100</span></p>
          <p className="text-xs text-gray-500 mt-1">
            {overallScore >= 80 ? 'Excellent match' : overallScore >= 60 ? 'Good match' : overallScore >= 40 ? 'Moderate match' : 'Poor match'}
          </p>
        </div>
      </div>

      {/* Dimension bars */}
      <div className="space-y-5">
        {breakdown.map((dim) => (
          <ScoreDimensionBar key={dim.dimension} dimension={dim} />
        ))}
      </div>
    </div>
  );
}
