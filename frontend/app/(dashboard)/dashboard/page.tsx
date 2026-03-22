'use client';

import Link from 'next/link';
import {
  FolderOpen,
  Users,
  TrendingUp,
  Plus,
  ArrowRight,
  Activity,
  Loader2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import Header from '@/components/layout/Header';
import ProjectCard from '@/components/projects/ProjectCard';
import { useDashboardStats, useProjects, useDeleteProject } from '@/hooks/useProjects';
import { useAuthStore } from '@/store/auth';
import { formatNumber } from '@/lib/utils';

function StatCard({
  icon: Icon,
  label,
  value,
  sublabel,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
  sublabel?: string;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <div className={`w-9 h-9 rounded-lg ${color} flex items-center justify-center`}>
          <Icon className="w-4 h-4 text-white" />
        </div>
      </div>
      <p className="text-3xl font-bold text-gray-900">{value}</p>
      {sublabel && <p className="text-xs text-gray-400 mt-1">{sublabel}</p>}
    </div>
  );
}

export default function DashboardPage() {
  const { user } = useAuthStore();
  const { data: stats, isLoading: statsLoading } = useDashboardStats();
  const { data: projects, isLoading: projectsLoading } = useProjects();
  const deleteProject = useDeleteProject();

  const recentProjects = projects?.slice(0, 6) || [];
  const firstName = user?.name?.split(' ')[0] || 'there';

  const handleDelete = async (id: string) => {
    if (confirm('Delete this project? This cannot be undone.')) {
      await deleteProject.mutateAsync(id);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header
        title={`Good morning, ${firstName}`}
        subtitle="Here's what's happening with your hiring projects"
      />

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
          {statsLoading ? (
            <div className="col-span-4 flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
            </div>
          ) : (
            <>
              <StatCard
                icon={FolderOpen}
                label="Total Projects"
                value={formatNumber(stats?.total_projects || 0)}
                color="bg-indigo-500"
              />
              <StatCard
                icon={Activity}
                label="Active Projects"
                value={formatNumber(stats?.active_projects || 0)}
                sublabel="Currently hiring"
                color="bg-emerald-500"
              />
              <StatCard
                icon={Users}
                label="Total Candidates"
                value={formatNumber(stats?.total_candidates || 0)}
                sublabel="Across all projects"
                color="bg-blue-500"
              />
              <StatCard
                icon={TrendingUp}
                label="Evaluated"
                value={formatNumber(stats?.evaluated_candidates || 0)}
                sublabel={
                  stats?.total_candidates
                    ? `${Math.round((stats.evaluated_candidates / stats.total_candidates) * 100)}% of total`
                    : '—'
                }
                color="bg-purple-500"
              />
            </>
          )}
        </div>

        {/* Recent Projects */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Projects</h2>
            <div className="flex items-center gap-3">
              <Link href="/projects">
                <Button variant="ghost" size="sm" className="gap-1">
                  View all
                  <ArrowRight className="w-3.5 h-3.5" />
                </Button>
              </Link>
              <Link href="/projects/new">
                <Button size="sm" className="gap-1.5">
                  <Plus className="w-4 h-4" />
                  New Project
                </Button>
              </Link>
            </div>
          </div>

          {projectsLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
            </div>
          ) : recentProjects.length === 0 ? (
            <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
              <FolderOpen className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-700 mb-1">No projects yet</h3>
              <p className="text-sm text-gray-500 mb-4">
                Create your first project to start ranking candidates
              </p>
              <Link href="/projects/new">
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Create your first project
                </Button>
              </Link>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 xl:grid-cols-3 gap-4">
              {recentProjects.map((project) => (
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
    </div>
  );
}
