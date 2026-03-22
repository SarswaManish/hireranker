'use client';

import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { ImportResult } from '@/types';
import { Progress } from '@/components/ui/progress';

interface ImportProgressProps {
  progress?: number;
  result?: ImportResult;
  isImporting?: boolean;
}

export default function ImportProgress({ progress, result, isImporting }: ImportProgressProps) {
  if (result) {
    return (
      <div className="rounded-xl border p-5 space-y-3">
        <div className="flex items-center gap-2">
          {result.failed === 0 ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          ) : (
            <AlertCircle className="w-5 h-5 text-amber-600" />
          )}
          <h3 className="font-semibold text-gray-900">Import Complete</h3>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="bg-emerald-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-emerald-700">{result.imported}</p>
            <p className="text-xs text-emerald-600">Imported</p>
          </div>
          {result.failed > 0 && (
            <div className="bg-red-50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-red-700">{result.failed}</p>
              <p className="text-xs text-red-600">Failed</p>
            </div>
          )}
        </div>

        {result.errors.length > 0 && (
          <div className="space-y-1">
            <p className="text-xs font-semibold text-gray-500">Errors:</p>
            {result.errors.slice(0, 5).map((err, i) => (
              <p key={i} className="text-xs text-red-600 bg-red-50 px-3 py-1 rounded">
                {err}
              </p>
            ))}
          </div>
        )}
      </div>
    );
  }

  if (isImporting) {
    return (
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
          <h3 className="font-semibold text-blue-700">Importing...</h3>
        </div>
        {progress != null && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs text-blue-600">
              <span>Uploading files</span>
              <span>{progress}%</span>
            </div>
            <Progress value={progress} />
          </div>
        )}
      </div>
    );
  }

  return null;
}
