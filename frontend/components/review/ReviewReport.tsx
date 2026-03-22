'use client';

import { SelfReviewReport } from '@/types';
import { CheckCircle2, XCircle, AlertTriangle, ArrowRight, FileText } from 'lucide-react';
import { getScoreColor } from '@/lib/utils';

interface ReviewReportProps {
  report: SelfReviewReport;
}

export default function ReviewReport({ report }: ReviewReportProps) {
  return (
    <div className="space-y-6">
      {/* Score hero */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl p-8 text-white text-center">
        <p className="text-indigo-200 text-sm font-medium mb-2">Your Resume Match Score</p>
        <div className="text-7xl font-bold mb-2">{Math.round(report.score)}</div>
        <div className="text-indigo-200 text-lg">/ 100</div>
        <p className="mt-4 text-indigo-100 max-w-md mx-auto leading-relaxed">
          {report.explanation}
        </p>
      </div>

      {/* ATS Score */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-gray-400" />
            <h3 className="font-semibold text-gray-900">ATS Readability Score</h3>
          </div>
          <span className={`text-lg font-bold px-3 py-1 rounded-lg ${getScoreColor(report.ats_score)}`}>
            {Math.round(report.ats_score)}
          </span>
        </div>
        <p className="text-sm text-gray-500 mt-2">
          {report.ats_score >= 80
            ? 'Your resume is highly readable by ATS systems.'
            : report.ats_score >= 60
            ? 'Your resume is reasonably ATS-friendly with some room for improvement.'
            : 'Your resume may have trouble passing ATS filters — see suggestions below.'}
        </p>
      </div>

      {/* Strengths */}
      {report.strengths && report.strengths.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-emerald-700 mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5" />
            Strengths
          </h3>
          <ul className="space-y-2">
            {report.strengths.map((s, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-gray-700">
                <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Missing skills */}
      {report.missing_skills && report.missing_skills.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-red-700 mb-4 flex items-center gap-2">
            <XCircle className="w-5 h-5" />
            Missing Skills
          </h3>
          <div className="flex flex-wrap gap-2">
            {report.missing_skills.map((skill, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-red-50 text-red-700 text-sm rounded-full border border-red-200"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Weak bullets with rewrites */}
      {report.weak_bullets && report.weak_bullets.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h3 className="font-semibold text-amber-700 mb-4 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Resume Bullet Improvements
          </h3>
          <div className="space-y-4">
            {report.weak_bullets.map((bullet, i) => (
              <div key={i} className="space-y-2">
                <div className="flex items-start gap-2 px-3 py-2 bg-red-50 rounded-lg border border-red-100">
                  <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-700">{bullet.original}</p>
                </div>
                <div className="flex items-start gap-2">
                  <ArrowRight className="w-4 h-4 text-gray-300 mt-0.5 flex-shrink-0" />
                  <div className="flex items-start gap-2 flex-1 px-3 py-2 bg-emerald-50 rounded-lg border border-emerald-100">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                    <p className="text-sm text-emerald-700">{bullet.improved}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Improvement suggestions */}
      {report.improvement_suggestions && report.improvement_suggestions.length > 0 && (
        <div className="bg-indigo-50 rounded-xl border border-indigo-200 p-5">
          <h3 className="font-semibold text-indigo-900 mb-4">Improvement Suggestions</h3>
          <ul className="space-y-2">
            {report.improvement_suggestions.map((tip, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-indigo-800">
                <span className="w-5 h-5 rounded-full bg-indigo-600 text-white text-xs flex items-center justify-center flex-shrink-0 mt-0.5 font-semibold">
                  {i + 1}
                </span>
                {tip}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
