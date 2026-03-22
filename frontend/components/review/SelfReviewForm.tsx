'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2, Upload, FileText, Zap } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { reviewApi } from '@/lib/api';
import { SelfReviewPreview } from '@/types';
import { cn } from '@/lib/utils';

interface SelfReviewFormProps {
  onPreviewReady: (preview: SelfReviewPreview) => void;
}

export default function SelfReviewForm({ onPreviewReady }: SelfReviewFormProps) {
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
    multiple: false,
    onDrop: (files) => setResumeFile(files[0] || null),
  });

  const handleSubmit = async () => {
    if (!resumeFile || !jobDescription.trim()) {
      setError('Please upload your resume and paste the job description.');
      return;
    }
    setError('');
    setIsLoading(true);
    try {
      const preview = await reviewApi.submit(resumeFile, jobDescription);
      onPreviewReady(preview);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Resume upload */}
      <div className="space-y-2">
        <label className="text-sm font-semibold text-gray-700">Your Resume</label>
        <div
          {...getRootProps()}
          className={cn(
            'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
            isDragActive
              ? 'border-indigo-400 bg-indigo-50'
              : resumeFile
              ? 'border-emerald-400 bg-emerald-50'
              : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
          )}
        >
          <input {...getInputProps()} />
          {resumeFile ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="w-8 h-8 text-emerald-600" />
              <div className="text-left">
                <p className="font-medium text-emerald-700">{resumeFile.name}</p>
                <p className="text-xs text-emerald-600">
                  {(resumeFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="w-8 h-8 mx-auto mb-2 text-gray-400" />
              <p className="font-medium text-gray-700">
                {isDragActive ? 'Drop your resume here' : 'Upload your resume'}
              </p>
              <p className="text-sm text-gray-500 mt-1">PDF or DOCX — drag & drop or click</p>
            </>
          )}
        </div>
      </div>

      {/* Job description */}
      <div className="space-y-2">
        <label className="text-sm font-semibold text-gray-700">Job Description</label>
        <Textarea
          placeholder="Paste the full job description here...

Example:
We are looking for a Senior Software Engineer to join our growing team. You will be responsible for designing, building, and maintaining high-quality software applications.

Requirements:
- 5+ years of software development experience
- Strong proficiency in JavaScript/TypeScript
- Experience with React and Node.js
..."
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          className="min-h-[200px]"
        />
        <p className="text-xs text-gray-400">{jobDescription.length} characters</p>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <Button
        className="w-full text-base h-12 gap-2"
        onClick={handleSubmit}
        disabled={isLoading || !resumeFile || !jobDescription.trim()}
      >
        {isLoading ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing your resume...
          </>
        ) : (
          <>
            <Zap className="w-5 h-5" />
            Get My Score
          </>
        )}
      </Button>
    </div>
  );
}
