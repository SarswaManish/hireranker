'use client';

import Link from 'next/link';
import { Plus, FolderOpen, Search, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import Header from '@/components/layout/Header';
import ProjectCard from '@/components/projects/ProjectCard';
import { useProjects, useDeleteProject } from '@/hooks/useProjects';
import { ProjectStatus } from '@/types';
import { cn } from '@/lib/utils';

const STATUS_FILTERS: { value: ProjectStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'active', label: 'Active' },
  { value: 'evaluating', label: 'Evaluating' },
  { value: 'completed', label: 'Completed' },
  { value: 'draft', label: 'Draft' },
  { value: 'archived', label: 'Archived' },
];

export default function ProjectsPage() {
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<ProjectStatus | 'all'>('all');
  const { data: projects, isLoading } = useProjects();
  const deleteProject = useDeleteProject();

  const filtered = (projects || []).filter((p) => {
    const matchesSearch =
      !search ||
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.role_title.toLowerCase().includes(search.toLowerCase()) ||
      p.company.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const handleDelete = async (id: string) => {
    if (confirm('Delete this project? This cannot be undone.')) {
      await deleteProject.mutateAsync(id);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header title="Projects" subtitle="Manage all your hiring projects" />

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {/* Controls */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search projects..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <Link href="/projects/new">
            <Button className="gap-1.5">
              <Plus className="w-4 h-4" />
              New Project
            </Button>
          </Link>
        </div>

        {/* Status filters */}
        <div className="flex flex-wrap gap-2">
          {STATUS_FILTERS.map((f) => {
            const count =
              f.value === 'all'
                ? (projects || []).length
                : (projects || []).filter((p) => p.status === f.value).length;

            return (
              <button
                key={f.value}
                onClick={() => setStatusFilter(f.value)}
                className={cn(
                  'px-3 py-1.5 text-sm font-medium rounded-full border transition-colors',
                  statusFilter === f.value
                    ? 'bg-indigo-600 text-white border-indigo-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
                )}
              >
                {f.label}
                <span className="ml-1.5 opacity-70">({count})</span>
              </button>
            );
          })}
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="bg-white rounded-xl border border-dashed border-gray-300 p-16 text-center">
            <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            {search || statusFilter !== 'all' ? (
              <>
                <h3 className="font-semibold text-gray-700 mb-1">No matching projects</h3>
                <p className="text-sm text-gray-500">Try adjusting your search or filters</p>
              </>
            ) : (
              <>
                <h3 className="font-semibold text-gray-700 mb-1">No projects yet</h3>
                <p className="text-sm text-gray-500 mb-4">
                  Create your first project to start ranking candidates
                </p>
                <Link href="/projects/new">
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Create project
                  </Button>
                </Link>
              </>
            )}
          </div>
        ) : (
          <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filtered.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={handleDelete}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
