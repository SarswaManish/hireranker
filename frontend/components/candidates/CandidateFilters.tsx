'use client';

import { useState, useCallback } from 'react';
import { Search, SlidersHorizontal, X } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { CandidateFilters as FiltersType, Recommendation } from '@/types';
import { cn } from '@/lib/utils';

const RECOMMENDATIONS: { value: Recommendation; label: string; color: string }[] = [
  { value: 'strong_yes', label: 'Strong Yes', color: 'bg-emerald-100 text-emerald-800 border-emerald-300' },
  { value: 'yes', label: 'Yes', color: 'bg-blue-100 text-blue-800 border-blue-300' },
  { value: 'maybe', label: 'Maybe', color: 'bg-amber-100 text-amber-800 border-amber-300' },
  { value: 'no', label: 'No', color: 'bg-red-100 text-red-800 border-red-300' },
];

interface CandidateFiltersProps {
  filters: FiltersType;
  onFiltersChange: (filters: FiltersType) => void;
}

export default function CandidateFilters({ filters, onFiltersChange }: CandidateFiltersProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [scoreRange, setScoreRange] = useState<number[]>([
    filters.min_score ?? 0,
    filters.max_score ?? 100,
  ]);

  const toggleRecommendation = useCallback(
    (rec: Recommendation) => {
      const current = filters.recommendations || [];
      const newRecs = current.includes(rec)
        ? current.filter((r) => r !== rec)
        : [...current, rec];
      onFiltersChange({ ...filters, recommendations: newRecs.length ? newRecs : undefined, page: 1 });
    },
    [filters, onFiltersChange]
  );

  const handleSearchChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      onFiltersChange({ ...filters, search: e.target.value || undefined, page: 1 });
    },
    [filters, onFiltersChange]
  );

  const handleScoreRangeCommit = (vals: number[]) => {
    setScoreRange(vals);
    onFiltersChange({
      ...filters,
      min_score: vals[0] > 0 ? vals[0] : undefined,
      max_score: vals[1] < 100 ? vals[1] : undefined,
      page: 1,
    });
  };

  const handleSkillsChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onFiltersChange({ ...filters, skills: e.target.value || undefined, page: 1 });
  };

  const clearFilters = () => {
    setScoreRange([0, 100]);
    onFiltersChange({ page: 1 });
  };

  const hasActiveFilters =
    filters.search ||
    (filters.recommendations && filters.recommendations.length > 0) ||
    filters.min_score != null ||
    filters.max_score != null ||
    filters.skills;

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 space-y-4">
      {/* Main row */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <Input
            placeholder="Search candidates by name or email..."
            value={filters.search || ''}
            onChange={handleSearchChange}
            className="pl-9"
          />
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className={cn(showAdvanced && 'bg-indigo-50 border-indigo-300 text-indigo-700')}
        >
          <SlidersHorizontal className="w-4 h-4 mr-1.5" />
          Filters
          {hasActiveFilters && (
            <span className="ml-1.5 w-2 h-2 rounded-full bg-indigo-600" />
          )}
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={clearFilters} className="text-gray-500">
            <X className="w-4 h-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Recommendation chips (always visible) */}
      <div className="flex flex-wrap gap-2">
        {RECOMMENDATIONS.map((rec) => {
          const isActive = (filters.recommendations || []).includes(rec.value);
          return (
            <button
              key={rec.value}
              type="button"
              onClick={() => toggleRecommendation(rec.value)}
              className={cn(
                'px-3 py-1 text-xs font-semibold rounded-full border transition-all',
                isActive
                  ? rec.color
                  : 'bg-white border-gray-200 text-gray-500 hover:border-gray-300'
              )}
            >
              {rec.label}
            </button>
          );
        })}
      </div>

      {/* Advanced filters */}
      {showAdvanced && (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-gray-100">
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Score Range: {scoreRange[0]} – {scoreRange[1]}
            </label>
            <Slider
              min={0}
              max={100}
              step={5}
              value={scoreRange}
              onValueChange={setScoreRange}
              onValueCommit={handleScoreRangeCommit}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
              Filter by Skills
            </label>
            <Input
              placeholder="e.g. React, Python"
              value={filters.skills || ''}
              onChange={handleSkillsChange}
            />
          </div>
        </div>
      )}
    </div>
  );
}
