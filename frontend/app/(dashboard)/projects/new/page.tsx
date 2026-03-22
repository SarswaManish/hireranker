import Header from '@/components/layout/Header';
import ProjectForm from '@/components/projects/ProjectForm';

export default function NewProjectPage() {
  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header title="Create New Project" subtitle="Set up your hiring project in a few steps" />

      <div className="flex-1 overflow-y-auto p-6">
        <ProjectForm />
      </div>
    </div>
  );
}
