'use client';

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { Zap, Loader2, AlertCircle } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { reviewApi } from '@/lib/api';
import ReviewReport from '@/components/review/ReviewReport';
import { Button } from '@/components/ui/button';

export default function ReviewReportPage() {
  const params = useParams();
  const token = params.token as string;

  const { data: report, isLoading, error } = useQuery({
    queryKey: ['review', token],
    queryFn: () => reviewApi.getReport(token),
    enabled: !!token,
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white">
      {/* Nav */}
      <nav className="bg-white/80 backdrop-blur-sm border-b border-gray-100 sticky top-0 z-50">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-gray-900">HireRanker</span>
          </Link>
          <Link href="/review">
            <Button variant="outline" size="sm">Analyze Another Resume</Button>
          </Link>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Your Full Resume Report</h1>
          <p className="text-gray-500 mt-1">Detailed AI analysis of your resume against the job description</p>
        </div>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-indigo-500 mb-3" />
            <p className="text-gray-500">Loading your report...</p>
          </div>
        ) : error ? (
          <div className="bg-white rounded-2xl border border-red-200 p-8 text-center">
            <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-3" />
            <h3 className="font-semibold text-gray-700 mb-1">Report Not Found</h3>
            <p className="text-sm text-gray-500 mb-4">
              This report link may have expired or is invalid.
            </p>
            <Link href="/review">
              <Button>Analyze a New Resume</Button>
            </Link>
          </div>
        ) : report ? (
          <ReviewReport report={report} />
        ) : null}
      </div>
    </div>
  );
}
