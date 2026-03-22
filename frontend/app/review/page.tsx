'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Zap, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';
import SelfReviewForm from '@/components/review/SelfReviewForm';
import { SelfReviewPreview } from '@/types';
import { Button } from '@/components/ui/button';
import { getScoreColor } from '@/lib/utils';

export default function ReviewPage() {
  const [preview, setPreview] = useState<SelfReviewPreview | null>(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white">
      {/* Nav */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-gray-900">HireRanker</span>
          </Link>
          <Link href="/login">
            <Button variant="ghost" size="sm">Recruiter Login</Button>
          </Link>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-12">
        {!preview ? (
          <>
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-3">
                How well does your resume match this job?
              </h1>
              <p className="text-gray-500 text-lg">
                Upload your resume and paste the job description. Get an AI score in seconds.
              </p>
            </div>

            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
              <SelfReviewForm onPreviewReady={setPreview} />
            </div>
          </>
        ) : (
          <div className="space-y-6">
            {/* Preview result */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8 text-center">
              <p className="text-sm font-medium text-gray-500 mb-2">Your Match Score</p>
              <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full text-3xl font-bold mx-auto mb-4 ${getScoreColor(preview.score)}`}>
                {Math.round(preview.score)}
              </div>
              <p className="text-gray-600 mb-6">{preview.preview_message}</p>

              {/* Teaser strengths */}
              {preview.strengths && preview.strengths.length > 0 && (
                <div className="text-left mb-6">
                  <p className="font-semibold text-gray-700 mb-3">Your top strengths:</p>
                  <ul className="space-y-2">
                    {preview.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Paywall */}
              {preview.payment_required && (
                <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-xl p-6 text-white text-center">
                  <Lock className="w-8 h-8 mx-auto mb-2 opacity-80" />
                  <h3 className="font-bold text-lg mb-1">Unlock Your Full Report</h3>
                  <p className="text-indigo-200 text-sm mb-4">
                    Get detailed feedback, missing skills, weak bullet rewrites, and ATS score.
                  </p>
                  <div className="text-3xl font-bold mb-4">$9.99</div>
                  <Button className="bg-white text-indigo-600 hover:bg-indigo-50 w-full gap-2">
                    <ArrowRight className="w-4 h-4" />
                    Get Full Report
                  </Button>
                  <p className="text-xs text-indigo-300 mt-2">One-time payment. Instant access.</p>
                </div>
              )}
            </div>

            <div className="text-center">
              <button
                onClick={() => setPreview(null)}
                className="text-sm text-gray-400 hover:text-gray-600"
              >
                ← Try another resume
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
