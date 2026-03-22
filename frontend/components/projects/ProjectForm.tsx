'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Plus, ChevronRight, ChevronLeft, Loader2, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useCreateProject } from '@/hooks/useProjects';
import { cn } from '@/lib/utils';

const schema = z.object({
  name: z.string().min(2, 'Project name is required'),
  company: z.string().min(2, 'Company name is required'),
  role_title: z.string().min(2, 'Role title is required'),
  job_description: z.string().min(50, 'Please provide a detailed job description'),
  must_have_skills: z.array(z.string()).min(1, 'Add at least one must-have skill'),
  nice_to_have_skills: z.array(z.string()),
  min_experience_years: z.coerce.number().optional(),
  required_location: z.string().optional(),
  required_degree: z.string().optional(),
  max_notice_period_days: z.coerce.number().optional(),
});

type FormValues = z.infer<typeof schema>;

const STEPS = [
  { id: 1, label: 'Basic Info' },
  { id: 2, label: 'Job Description' },
  { id: 3, label: 'Requirements' },
  { id: 4, label: 'Filters' },
  { id: 5, label: 'Review' },
];

function TagInput({
  value,
  onChange,
  placeholder,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState('');

  const add = () => {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
      setInput('');
    }
  };

  const remove = (tag: string) => {
    onChange(value.filter((t) => t !== tag));
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              add();
            }
          }}
          placeholder={placeholder || 'Add skill and press Enter'}
          className="flex-1"
        />
        <Button type="button" variant="outline" size="sm" onClick={add}>
          <Plus className="w-4 h-4" />
        </Button>
      </div>
      {value.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {value.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-50 text-indigo-700 text-sm rounded-full border border-indigo-200"
            >
              {tag}
              <button type="button" onClick={() => remove(tag)} className="hover:text-indigo-900">
                <X className="w-3 h-3" />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProjectForm() {
  const [step, setStep] = useState(1);
  const router = useRouter();
  const createProject = useCreateProject();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    trigger,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      must_have_skills: [],
      nice_to_have_skills: [],
    },
  });

  const watchedValues = watch();

  const validateStep = async (currentStep: number) => {
    const fieldsByStep: Record<number, (keyof FormValues)[]> = {
      1: ['name', 'company', 'role_title'],
      2: ['job_description'],
      3: ['must_have_skills'],
      4: [],
    };
    const fields = fieldsByStep[currentStep] || [];
    if (fields.length === 0) return true;
    return await trigger(fields);
  };

  const nextStep = async () => {
    const valid = await validateStep(step);
    if (valid) setStep((s) => Math.min(s + 1, STEPS.length));
  };

  const prevStep = () => setStep((s) => Math.max(s - 1, 1));

  const onSubmit = async (data: FormValues) => {
    try {
      const project = await createProject.mutateAsync(data);
      router.push(`/projects/${project.id}/import`);
    } catch (err) {
      // handled by mutation
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-8">
        {STEPS.map((s, i) => (
          <div key={s.id} className="flex items-center gap-2">
            <div
              className={cn(
                'flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold transition-colors',
                step === s.id
                  ? 'bg-indigo-600 text-white'
                  : step > s.id
                  ? 'bg-emerald-500 text-white'
                  : 'bg-gray-100 text-gray-400'
              )}
            >
              {step > s.id ? <Check className="w-4 h-4" /> : s.id}
            </div>
            <span
              className={cn(
                'text-sm font-medium hidden sm:block',
                step === s.id ? 'text-gray-900' : 'text-gray-400'
              )}
            >
              {s.label}
            </span>
            {i < STEPS.length - 1 && (
              <ChevronRight className="w-4 h-4 text-gray-300 mx-1" />
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Basic Information</h2>
              <p className="text-sm text-gray-500">Tell us about the position you're hiring for</p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="name">Project Name *</Label>
              <Input
                id="name"
                placeholder="e.g. Senior Frontend Engineer – Q2 2025"
                {...register('name')}
                className={errors.name ? 'border-red-400' : ''}
              />
              {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="company">Company *</Label>
              <Input
                id="company"
                placeholder="e.g. Acme Corp"
                {...register('company')}
                className={errors.company ? 'border-red-400' : ''}
              />
              {errors.company && <p className="text-xs text-red-500">{errors.company.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="role_title">Role Title *</Label>
              <Input
                id="role_title"
                placeholder="e.g. Senior Software Engineer"
                {...register('role_title')}
                className={errors.role_title ? 'border-red-400' : ''}
              />
              {errors.role_title && (
                <p className="text-xs text-red-500">{errors.role_title.message}</p>
              )}
            </div>
          </div>
        )}

        {/* Step 2: Job Description */}
        {step === 2 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Job Description</h2>
              <p className="text-sm text-gray-500">
                Paste your full job description. Our AI uses this to evaluate candidates.
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="job_description">Job Description *</Label>
              <Textarea
                id="job_description"
                placeholder="We are looking for a Senior Software Engineer to join our team...

Responsibilities:
- Lead technical design and architecture
- Write clean, scalable code
...

Requirements:
- 5+ years of experience
- Proficiency in React, TypeScript, Node.js
..."
                {...register('job_description')}
                className={cn(
                  'min-h-[320px] font-mono text-sm',
                  errors.job_description ? 'border-red-400' : ''
                )}
              />
              {errors.job_description && (
                <p className="text-xs text-red-500">{errors.job_description.message}</p>
              )}
              <p className="text-xs text-gray-400">
                {watchedValues.job_description?.length || 0} characters (minimum 50)
              </p>
            </div>
          </div>
        )}

        {/* Step 3: Requirements / Skills */}
        {step === 3 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Skills & Requirements</h2>
              <p className="text-sm text-gray-500">
                Define must-have and nice-to-have skills for the role.
              </p>
            </div>
            <div className="space-y-2">
              <Label>Must-Have Skills *</Label>
              <p className="text-xs text-gray-500">
                Candidates missing these skills will score significantly lower.
              </p>
              <TagInput
                value={watchedValues.must_have_skills || []}
                onChange={(v) => setValue('must_have_skills', v)}
                placeholder="e.g. React, TypeScript — press Enter to add"
              />
              {errors.must_have_skills && (
                <p className="text-xs text-red-500">{errors.must_have_skills.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label>Nice-to-Have Skills</Label>
              <p className="text-xs text-gray-500">
                These improve a candidate's score but are not required.
              </p>
              <TagInput
                value={watchedValues.nice_to_have_skills || []}
                onChange={(v) => setValue('nice_to_have_skills', v)}
                placeholder="e.g. GraphQL, Docker"
              />
            </div>
          </div>
        )}

        {/* Step 4: Filters */}
        {step === 4 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Candidate Filters</h2>
              <p className="text-sm text-gray-500">
                Optional hard filters applied before scoring.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="min_exp">Min. Experience (years)</Label>
                <Input
                  id="min_exp"
                  type="number"
                  min="0"
                  max="30"
                  placeholder="e.g. 3"
                  {...register('min_experience_years')}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="notice">Max Notice Period (days)</Label>
                <Input
                  id="notice"
                  type="number"
                  min="0"
                  placeholder="e.g. 30"
                  {...register('max_notice_period_days')}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="location">Required Location</Label>
                <Input
                  id="location"
                  placeholder="e.g. New York, NY"
                  {...register('required_location')}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="degree">Required Degree</Label>
                <Input
                  id="degree"
                  placeholder="e.g. Bachelor's"
                  {...register('required_degree')}
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Review */}
        {step === 5 && (
          <div className="space-y-5">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-1">Review & Create</h2>
              <p className="text-sm text-gray-500">Confirm your project details before creating.</p>
            </div>
            <div className="bg-gray-50 rounded-xl border border-gray-200 p-5 space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Project
                </p>
                <p className="font-semibold text-gray-900">{watchedValues.name}</p>
                <p className="text-sm text-gray-500">
                  {watchedValues.role_title} at {watchedValues.company}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                  Job Description
                </p>
                <p className="text-sm text-gray-700 line-clamp-3">
                  {watchedValues.job_description}
                </p>
              </div>
              {(watchedValues.must_have_skills?.length ?? 0) > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Must-Have Skills
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {watchedValues.must_have_skills?.map((s) => (
                      <span
                        key={s}
                        className="px-2.5 py-1 bg-red-50 text-red-700 text-xs rounded-full border border-red-200"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {(watchedValues.nice_to_have_skills?.length ?? 0) > 0 && (
                <div>
                  <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Nice-to-Have Skills
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {watchedValues.nice_to_have_skills?.map((s) => (
                      <span
                        key={s}
                        className="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs rounded-full border border-indigo-200"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {createProject.error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {(createProject.error as any)?.response?.data?.detail ||
                  'Failed to create project. Please try again.'}
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
          <Button
            type="button"
            variant="outline"
            onClick={prevStep}
            disabled={step === 1}
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Previous
          </Button>

          {step < STEPS.length ? (
            <Button type="button" onClick={nextStep}>
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          ) : (
            <Button type="submit" disabled={createProject.isPending}>
              {createProject.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Check className="w-4 h-4 mr-1" />
                  Create Project
                </>
              )}
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
