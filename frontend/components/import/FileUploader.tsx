'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, X } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploaderProps {
  accept: Record<string, string[]>;
  multiple?: boolean;
  files: File[];
  onFilesChange: (files: File[]) => void;
  label?: string;
  hint?: string;
}

export default function FileUploader({
  accept,
  multiple = false,
  files,
  onFilesChange,
  label = 'Drop files here',
  hint,
}: FileUploaderProps) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      onFilesChange(multiple ? [...files, ...accepted] : accepted);
    },
    [files, multiple, onFilesChange]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple,
  });

  const removeFile = (index: number) => {
    onFilesChange(files.filter((_, i) => i !== index));
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
          isDragActive
            ? 'border-indigo-400 bg-indigo-50'
            : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
        )}
      >
        <input {...getInputProps()} />
        <Upload
          className={cn(
            'w-10 h-10 mx-auto mb-3',
            isDragActive ? 'text-indigo-500' : 'text-gray-400'
          )}
        />
        <p className="font-medium text-gray-700">
          {isDragActive ? 'Drop files here' : label}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          or{' '}
          <span className="text-indigo-600 font-medium">browse to upload</span>
        </p>
        {hint && <p className="text-xs text-gray-400 mt-2">{hint}</p>}
      </div>

      {files.length > 0 && (
        <div className="space-y-2">
          {files.map((file, i) => (
            <div
              key={i}
              className="flex items-center gap-3 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200"
            >
              <File className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-700 truncate">{file.name}</p>
                <p className="text-xs text-gray-400">{formatSize(file.size)}</p>
              </div>
              <button
                type="button"
                onClick={() => removeFile(i)}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
