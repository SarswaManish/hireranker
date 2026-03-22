'use client';

import Link from 'next/link';
import { Users, Calendar, MoreVertical, Trash2, Settings, BarChart2 } from 'lucide-react';
import { Project } from '@/types';
import { formatRelativeTime, getScoreColor } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

const statusConfig: Record<string, { label: string; variant: 'default' | 'secondary' | 'success' | 'warning' | 'info' | 'destructive' | 'outline' }> = {
  draft: { label: 'Draft', variant: 'secondary' },
  active: { label: 'Active', variant: 'success' },
  evaluating: { label: 'Evaluating', variant: 'info' },
  completed: { label: 'Completed', variant: 'default' },
  archived: { label: 'Archived', variant: 'outline' },
};

interface ProjectCardProps {
  project: Project;
  onDelete?: (id: string) => void;
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const statusCfg = statusConfig[project.status] || statusConfig.draft;
  const evaluationPct =
    project.candidate_count > 0
      ? Math.round((project.evaluated_count / project.candidate_count) * 100)
      : 0;

  return (
    <div className="group bg-white rounded-xl border border-gray-200 p-5 hover:border-indigo-300 hover:shadow-md transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant={statusCfg.variant}>{statusCfg.label}</Badge>
          </div>
          <Link href={`/projects/${project.id}/candidates`}>
            <h3 className="font-semibold text-gray-900 truncate hover:text-indigo-600 transition-colors">
              {project.name}
            </h3>
          </Link>
          <p className="text-sm text-gray-500 truncate">
            {project.role_title} · {project.company}
          </p>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-gray-100 transition-all ml-2">
            <MoreVertical className="w-4 h-4 text-gray-500" />
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem asChild>
              <Link href={`/projects/${project.id}/candidates`} className="flex items-center gap-2">
                <BarChart2 className="w-4 h-4" />
                View candidates
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href={`/projects/${project.id}/settings`} className="flex items-center gap-2">
                <Settings className="w-4 h-4" />
                Settings
              </Link>
            </DropdownMenuItem>
            {onDelete && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={() => onDelete(project.id)}
                  className="text-red-600 focus:text-red-600 focus:bg-red-50 flex items-center gap-2"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete project
                </DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {/* Stats row */}
      <div className="flex items-center gap-4 mt-4 pt-4 border-t border-gray-100">
        <div className="flex items-center gap-1.5 text-sm text-gray-500">
          <Users className="w-4 h-4" />
          <span>{project.candidate_count} candidates</span>
        </div>
        {project.avg_score != null && project.avg_score > 0 && (
          <div className="flex items-center gap-1.5 text-sm">
            <span className="text-gray-500">Avg score</span>
            <span className={`font-semibold px-1.5 py-0.5 rounded text-xs ${getScoreColor(project.avg_score)}`}>
              {Math.round(project.avg_score)}
            </span>
          </div>
        )}
        <div className="flex items-center gap-1 text-xs text-gray-400 ml-auto">
          <Calendar className="w-3 h-3" />
          {formatRelativeTime(project.created_at)}
        </div>
      </div>

      {/* Evaluation progress */}
      {project.candidate_count > 0 && (
        <div className="mt-3">
          <div className="flex items-center justify-between text-xs text-gray-500 mb-1">
            <span>Evaluated</span>
            <span>{project.evaluated_count}/{project.candidate_count}</span>
          </div>
          <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full transition-all"
              style={{ width: `${evaluationPct}%` }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
