'use client';

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { Upload, FileText, ChevronRight, Loader2, CheckCircle2, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Header from '@/components/layout/Header';
import FileUploader from '@/components/import/FileUploader';
import ColumnMapper from '@/components/import/ColumnMapper';
import ImportProgress from '@/components/import/ImportProgress';
import { importApi } from '@/lib/api';
import { ImportPreview, ImportResult, ColumnMapping } from '@/types';
import { cn } from '@/lib/utils';
import { useProject } from '@/hooks/useProjects';

type ImportMode = 'csv' | 'resumes';

export default function ImportPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;
  const { data: project } = useProject(projectId);

  const [mode, setMode] = useState<ImportMode>('csv');
  const [csvFiles, setCsvFiles] = useState<File[]>([]);
  const [resumeFiles, setResumeFiles] = useState<File[]>([]);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [mappings, setMappings] = useState<ColumnMapping[]>([]);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  const [isImporting, setIsImporting] = useState(false);
  const [importProgress, setImportProgress] = useState(0);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState('');

  const handleCSVPreview = async () => {
    if (!csvFiles[0]) return;
    setIsPreviewLoading(true);
    setError('');
    try {
      const p = await importApi.previewCSV(projectId, csvFiles[0]);
      setPreview(p);
      // Auto-map obvious columns
      const autoMappings: ColumnMapping[] = [];
      const fieldGuesses: Record<string, string[]> = {
        name: ['name', 'full name', 'candidate name'],
        email: ['email', 'email address', 'e-mail'],
        phone: ['phone', 'mobile', 'telephone'],
        location: ['location', 'city', 'address'],
        linkedin_url: ['linkedin', 'linkedin url'],
        github_url: ['github', 'github url'],
        years_experience: ['years experience', 'experience', 'yoe', 'exp'],
        skills: ['skills', 'technologies', 'tech stack'],
        current_title: ['title', 'job title', 'position', 'current title'],
      };
      p.columns.forEach((col) => {
        const colLower = col.toLowerCase().trim();
        for (const [field, guesses] of Object.entries(fieldGuesses)) {
          if (guesses.some((g) => colLower.includes(g))) {
            autoMappings.push({ csv_column: col, field });
            break;
          }
        }
      });
      setMappings(autoMappings);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Failed to preview file');
    } finally {
      setIsPreviewLoading(false);
    }
  };

  const handleCSVImport = async () => {
    if (!csvFiles[0]) return;
    setIsImporting(true);
    setError('');
    try {
      const r = await importApi.importCSV(projectId, csvFiles[0], mappings);
      setResult(r);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  const handleResumeImport = async () => {
    if (resumeFiles.length === 0) return;
    setIsImporting(true);
    setError('');
    try {
      const r = await importApi.importResumes(projectId, resumeFiles, setImportProgress);
      setResult(r);
    } catch (e: any) {
      setError(e?.response?.data?.detail || 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header
        title="Import Candidates"
        subtitle={project ? `Adding candidates to: ${project.name}` : 'Import candidates to your project'}
      />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-2xl mx-auto space-y-6">
          {/* Mode selector */}
          {!result && (
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => { setMode('csv'); setPreview(null); setResult(null); }}
                className={cn(
                  'p-4 rounded-xl border-2 text-left transition-colors',
                  mode === 'csv'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                )}
              >
                <FileText className={cn('w-6 h-6 mb-2', mode === 'csv' ? 'text-indigo-600' : 'text-gray-400')} />
                <p className={cn('font-semibold', mode === 'csv' ? 'text-indigo-700' : 'text-gray-700')}>
                  CSV / XLSX Import
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Upload a spreadsheet with candidate data
                </p>
              </button>
              <button
                onClick={() => { setMode('resumes'); setPreview(null); setResult(null); }}
                className={cn(
                  'p-4 rounded-xl border-2 text-left transition-colors',
                  mode === 'resumes'
                    ? 'border-indigo-500 bg-indigo-50'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                )}
              >
                <Upload className={cn('w-6 h-6 mb-2', mode === 'resumes' ? 'text-indigo-600' : 'text-gray-400')} />
                <p className={cn('font-semibold', mode === 'resumes' ? 'text-indigo-700' : 'text-gray-700')}>
                  Resume Upload
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Bulk upload PDF or DOCX resumes
                </p>
              </button>
            </div>
          )}

          {/* Result */}
          {result && (
            <div className="space-y-4">
              <ImportProgress result={result} />
              <div className="flex gap-3">
                <Link href={`/projects/${projectId}/candidates`} className="flex-1">
                  <Button className="w-full gap-2">
                    <ArrowRight className="w-4 h-4" />
                    View Candidates
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  onClick={() => { setResult(null); setPreview(null); setCsvFiles([]); setResumeFiles([]); }}
                >
                  Import More
                </Button>
              </div>
            </div>
          )}

          {/* CSV mode */}
          {mode === 'csv' && !result && (
            <div className="space-y-4">
              <FileUploader
                accept={{
                  'text/csv': ['.csv'],
                  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
                  'application/vnd.ms-excel': ['.xls'],
                }}
                files={csvFiles}
                onFilesChange={setCsvFiles}
                label="Drop your CSV or XLSX file here"
                hint="Supported: .csv, .xlsx, .xls"
              />

              {csvFiles.length > 0 && !preview && (
                <Button onClick={handleCSVPreview} disabled={isPreviewLoading} className="w-full gap-2">
                  {isPreviewLoading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <ChevronRight className="w-4 h-4" />
                  )}
                  Preview & Map Columns
                </Button>
              )}

              {preview && (
                <>
                  <ColumnMapper
                    preview={preview}
                    mappings={mappings}
                    onMappingsChange={setMappings}
                  />
                  <ImportProgress isImporting={isImporting} progress={importProgress} />
                  {error && (
                    <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                      {error}
                    </div>
                  )}
                  <Button
                    onClick={handleCSVImport}
                    disabled={isImporting}
                    className="w-full gap-2"
                  >
                    {isImporting ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="w-4 h-4" />
                    )}
                    Import {preview.total_rows} Candidates
                  </Button>
                </>
              )}
            </div>
          )}

          {/* Resume mode */}
          {mode === 'resumes' && !result && (
            <div className="space-y-4">
              <FileUploader
                accept={{
                  'application/pdf': ['.pdf'],
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
                  'application/msword': ['.doc'],
                }}
                multiple
                files={resumeFiles}
                onFilesChange={setResumeFiles}
                label="Drop resumes here"
                hint="PDF or DOCX — upload multiple files at once"
              />

              <ImportProgress isImporting={isImporting} progress={importProgress} />

              {error && (
                <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                  {error}
                </div>
              )}

              {resumeFiles.length > 0 && (
                <Button
                  onClick={handleResumeImport}
                  disabled={isImporting}
                  className="w-full gap-2"
                >
                  {isImporting ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  Import {resumeFiles.length} Resume{resumeFiles.length !== 1 ? 's' : ''}
                </Button>
              )}
            </div>
          )}

          {/* Skip link */}
          {!result && (
            <div className="text-center">
              <Link href={`/projects/${projectId}/candidates`} className="text-sm text-gray-400 hover:text-gray-600">
                Skip for now →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
