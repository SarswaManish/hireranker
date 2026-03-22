'use client';

import { useParams, useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Loader2, Trash2, Save } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import Header from '@/components/layout/Header';
import { useProject, useUpdateProject, useDeleteProject } from '@/hooks/useProjects';
import { useEffect } from 'react';

const schema = z.object({
  name: z.string().min(2),
  company: z.string().min(2),
  role_title: z.string().min(2),
  job_description: z.string().min(50),
});

type FormValues = z.infer<typeof schema>;

export default function ProjectSettingsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const { data: project, isLoading } = useProject(projectId);
  const updateProject = useUpdateProject(projectId);
  const deleteProject = useDeleteProject();

  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (project) {
      reset({
        name: project.name,
        company: project.company,
        role_title: project.role_title,
        job_description: project.job_description,
      });
    }
  }, [project, reset]);

  const onSubmit = async (data: FormValues) => {
    await updateProject.mutateAsync(data);
  };

  const handleDelete = async () => {
    if (confirm('Delete this project permanently? All candidates will be lost.')) {
      await deleteProject.mutateAsync(projectId);
      router.push('/projects');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header title="Project Settings" subtitle={project?.name} />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          <form onSubmit={handleSubmit(onSubmit)} className="bg-white rounded-xl border border-gray-200 p-6 space-y-5">
            <h2 className="font-semibold text-gray-900">Basic Information</h2>

            <div className="space-y-2">
              <Label>Project Name</Label>
              <Input {...register('name')} className={errors.name ? 'border-red-400' : ''} />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Company</Label>
                <Input {...register('company')} className={errors.company ? 'border-red-400' : ''} />
              </div>
              <div className="space-y-2">
                <Label>Role Title</Label>
                <Input {...register('role_title')} className={errors.role_title ? 'border-red-400' : ''} />
              </div>
            </div>

            <div className="space-y-2">
              <Label>Job Description</Label>
              <Textarea
                {...register('job_description')}
                className={`min-h-[200px] ${errors.job_description ? 'border-red-400' : ''}`}
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-gray-100">
              {updateProject.isSuccess && (
                <p className="text-sm text-emerald-600">Changes saved!</p>
              )}
              <div className="flex gap-3 ml-auto">
                <Button type="submit" disabled={!isDirty || updateProject.isPending} className="gap-2">
                  {updateProject.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Save Changes
                </Button>
              </div>
            </div>
          </form>

          {/* Danger zone */}
          <div className="bg-white rounded-xl border border-red-200 p-6">
            <h2 className="font-semibold text-red-700 mb-2">Danger Zone</h2>
            <p className="text-sm text-gray-500 mb-4">
              Permanently delete this project and all its candidates. This action cannot be undone.
            </p>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteProject.isPending}
              className="gap-2"
            >
              {deleteProject.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              Delete Project
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
