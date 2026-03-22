'use client';

import { useState } from 'react';
import { ImportPreview, ColumnMapping } from '@/types';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const FIELD_OPTIONS = [
  { value: 'name', label: 'Full Name *' },
  { value: 'email', label: 'Email *' },
  { value: 'phone', label: 'Phone' },
  { value: 'location', label: 'Location' },
  { value: 'linkedin_url', label: 'LinkedIn URL' },
  { value: 'github_url', label: 'GitHub URL' },
  { value: 'portfolio_url', label: 'Portfolio URL' },
  { value: 'education', label: 'Education' },
  { value: 'years_experience', label: 'Years of Experience' },
  { value: 'current_title', label: 'Current Title' },
  { value: 'current_company', label: 'Current Company' },
  { value: 'skills', label: 'Skills (comma-separated)' },
  { value: 'resume_text', label: 'Resume Text' },
  { value: '__skip__', label: '— Skip this column —' },
];

interface ColumnMapperProps {
  preview: ImportPreview;
  mappings: ColumnMapping[];
  onMappingsChange: (mappings: ColumnMapping[]) => void;
}

export default function ColumnMapper({ preview, mappings, onMappingsChange }: ColumnMapperProps) {
  const getMapping = (col: string) =>
    mappings.find((m) => m.csv_column === col)?.field || '__skip__';

  const setMapping = (csvColumn: string, field: string) => {
    const newMappings = mappings.filter((m) => m.csv_column !== csvColumn);
    if (field !== '__skip__') {
      newMappings.push({ csv_column: csvColumn, field });
    }
    onMappingsChange(newMappings);
  };

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-medium text-gray-700 mb-1">
          Map CSV columns to candidate fields
        </p>
        <p className="text-xs text-gray-500">
          {preview.total_rows} rows detected. Map at least Name and Email.
        </p>
      </div>

      <div className="border border-gray-200 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-1/3">
                CSV Column
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-1/3">
                Maps To
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider w-1/3">
                Sample Value
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {preview.columns.map((col) => (
              <tr key={col} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-mono text-xs text-gray-700">{col}</td>
                <td className="px-4 py-3">
                  <Select value={getMapping(col)} onValueChange={(v) => setMapping(col, v)}>
                    <SelectTrigger className="h-8 text-xs">
                      <SelectValue placeholder="Skip" />
                    </SelectTrigger>
                    <SelectContent>
                      {FIELD_OPTIONS.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500 truncate max-w-[150px]">
                  {preview.sample_rows[0]?.[col] || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Sample data preview */}
      {preview.sample_rows.length > 0 && (
        <details className="group">
          <summary className="text-xs font-medium text-indigo-600 cursor-pointer hover:underline">
            Preview sample data ({preview.sample_rows.length} rows)
          </summary>
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-xs border border-gray-200 rounded-lg overflow-hidden">
              <thead className="bg-gray-50">
                <tr>
                  {preview.columns.map((col) => (
                    <th key={col} className="px-3 py-2 text-left font-medium text-gray-500 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {preview.sample_rows.slice(0, 3).map((row, i) => (
                  <tr key={i}>
                    {preview.columns.map((col) => (
                      <td key={col} className="px-3 py-2 text-gray-600 whitespace-nowrap max-w-[150px] truncate">
                        {row[col] || ''}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}
