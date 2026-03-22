'use client';

import { useState, useMemo } from 'react';
import Link from 'next/link';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  SortingState,
} from '@tanstack/react-table';
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  Eye,
  GitCompareArrows,
  Download,
  Loader2,
} from 'lucide-react';
import { Candidate, Recommendation } from '@/types';
import { getScoreColor, getInitials } from '@/lib/utils';
import RecommendationBadge from './RecommendationBadge';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { cn } from '@/lib/utils';

const columnHelper = createColumnHelper<Candidate>();

interface CandidatesTableProps {
  candidates: Candidate[];
  projectId: string;
  isLoading?: boolean;
  selectedIds: string[];
  onSelectToggle: (id: string) => void;
  onExport: () => void;
  onCompare: () => void;
}

function ScoreBadge({ score }: { score: number }) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold',
        getScoreColor(score)
      )}
    >
      {Math.round(score)}
    </span>
  );
}

function SkillChips({ skills }: { skills: string[] }) {
  const display = skills.slice(0, 3);
  const more = skills.length - 3;
  return (
    <div className="flex flex-wrap gap-1">
      {display.map((skill) => (
        <span
          key={skill}
          className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded"
        >
          {skill}
        </span>
      ))}
      {more > 0 && (
        <span className="px-1.5 py-0.5 bg-gray-100 text-gray-500 text-xs rounded">
          +{more}
        </span>
      )}
    </div>
  );
}

export default function CandidatesTable({
  candidates,
  projectId,
  isLoading,
  selectedIds,
  onSelectToggle,
  onExport,
  onCompare,
}: CandidatesTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns = useMemo(
    () => [
      columnHelper.display({
        id: 'select',
        header: () => <span className="text-xs text-gray-400">Compare</span>,
        cell: ({ row }) => (
          <input
            type="checkbox"
            checked={selectedIds.includes(row.original.id)}
            onChange={() => onSelectToggle(row.original.id)}
            className="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
            disabled={selectedIds.length >= 2 && !selectedIds.includes(row.original.id)}
          />
        ),
        size: 60,
      }),
      columnHelper.accessor('rank', {
        header: '#',
        cell: (info) => (
          <span className="text-sm font-semibold text-gray-500">{info.getValue() || '—'}</span>
        ),
        size: 50,
      }),
      columnHelper.accessor('name', {
        header: 'Candidate',
        cell: (info) => {
          const candidate = info.row.original;
          return (
            <div className="flex items-center gap-3">
              <Avatar className="w-8 h-8 flex-shrink-0">
                <AvatarFallback className="text-xs">
                  {getInitials(candidate.name)}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <Link
                  href={`/projects/${projectId}/candidates/${candidate.id}`}
                  className="font-medium text-gray-900 hover:text-indigo-600 truncate block"
                >
                  {candidate.name}
                </Link>
                <p className="text-xs text-gray-500 truncate">{candidate.email}</p>
              </div>
            </div>
          );
        },
        size: 220,
      }),
      columnHelper.accessor('score', {
        header: 'Score',
        cell: (info) => {
          const score = info.getValue();
          return score != null ? <ScoreBadge score={score} /> : <span className="text-gray-300 text-sm">—</span>;
        },
        size: 80,
      }),
      columnHelper.accessor('recommendation', {
        header: 'Recommendation',
        cell: (info) => {
          const rec = info.getValue();
          return rec ? (
            <RecommendationBadge recommendation={rec} size="sm" />
          ) : (
            <span className="text-gray-300 text-sm">Pending</span>
          );
        },
        size: 140,
      }),
      columnHelper.accessor('skills_match_pct', {
        header: 'Skills Match',
        cell: (info) => {
          const pct = info.getValue();
          if (pct == null) return <span className="text-gray-300 text-sm">—</span>;
          return (
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full rounded-full',
                    pct >= 80 ? 'bg-emerald-500' : pct >= 60 ? 'bg-blue-500' : pct >= 40 ? 'bg-amber-500' : 'bg-red-400'
                  )}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-sm text-gray-700">{Math.round(pct)}%</span>
            </div>
          );
        },
        size: 130,
      }),
      columnHelper.accessor('skills', {
        header: 'Top Skills',
        cell: (info) => {
          const skills = info.getValue() || [];
          return skills.length > 0 ? <SkillChips skills={skills} /> : <span className="text-gray-300 text-sm">—</span>;
        },
        size: 200,
        enableSorting: false,
      }),
      columnHelper.accessor('status', {
        header: 'Status',
        cell: (info) => {
          const status = info.getValue();
          const statusStyles: Record<string, string> = {
            pending: 'bg-gray-100 text-gray-600',
            evaluating: 'bg-blue-100 text-blue-700',
            evaluated: 'bg-emerald-100 text-emerald-700',
            error: 'bg-red-100 text-red-600',
          };
          return (
            <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', statusStyles[status] || 'bg-gray-100')}>
              {status === 'evaluating' ? (
                <span className="flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin" />
                  Evaluating
                </span>
              ) : (
                <span className="capitalize">{status}</span>
              )}
            </span>
          );
        },
        size: 100,
      }),
      columnHelper.display({
        id: 'actions',
        header: '',
        cell: ({ row }) => (
          <Link
            href={`/projects/${projectId}/candidates/${row.original.id}`}
            className="inline-flex items-center gap-1 px-2.5 py-1.5 text-xs text-indigo-600 hover:bg-indigo-50 rounded-md transition-colors"
          >
            <Eye className="w-3.5 h-3.5" />
            View
          </Link>
        ),
        size: 70,
      }),
    ],
    [projectId, selectedIds, onSelectToggle]
  );

  const table = useReactTable({
    data: candidates,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    manualSorting: false,
  });

  return (
    <div className="space-y-3">
      {/* Table actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {selectedIds.length === 2 && (
            <Button size="sm" onClick={onCompare} className="gap-1.5">
              <GitCompareArrows className="w-4 h-4" />
              Compare Selected
            </Button>
          )}
          {selectedIds.length > 0 && selectedIds.length < 2 && (
            <p className="text-xs text-gray-500">Select 2 candidates to compare</p>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={onExport} className="gap-1.5">
          <Download className="w-4 h-4" />
          Export CSV
        </Button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id} className="border-b border-gray-200 bg-gray-50">
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap"
                      style={{ width: header.getSize() }}
                    >
                      {header.isPlaceholder ? null : (
                        <div
                          className={cn(
                            'flex items-center gap-1',
                            header.column.getCanSort() && 'cursor-pointer select-none hover:text-gray-700'
                          )}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {header.column.getCanSort() && (
                            <>
                              {header.column.getIsSorted() === 'asc' ? (
                                <ChevronUp className="w-3 h-3" />
                              ) : header.column.getIsSorted() === 'desc' ? (
                                <ChevronDown className="w-3 h-3" />
                              ) : (
                                <ChevronsUpDown className="w-3 h-3 opacity-40" />
                              )}
                            </>
                          )}
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-gray-100">
              {isLoading ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-12 text-center">
                    <Loader2 className="w-6 h-6 animate-spin text-indigo-500 mx-auto mb-2" />
                    <p className="text-sm text-gray-500">Loading candidates...</p>
                  </td>
                </tr>
              ) : table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="px-4 py-12 text-center">
                    <p className="text-gray-500">No candidates found</p>
                    <p className="text-xs text-gray-400 mt-1">Try adjusting your filters</p>
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className={cn(
                      'hover:bg-gray-50 transition-colors',
                      selectedIds.includes(row.original.id) && 'bg-indigo-50'
                    )}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
