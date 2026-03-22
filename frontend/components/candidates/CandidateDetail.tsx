'use client';

import { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  MapPin,
  GraduationCap,
  Phone,
  Linkedin,
  Github,
  Globe,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  XCircle,
  Star,
  Briefcase,
  Loader2,
} from 'lucide-react';
import { Candidate } from '@/types';
import RecommendationBadge from './RecommendationBadge';
import ScoreBreakdown from './ScoreBreakdown';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { getScoreColor } from '@/lib/utils';
import { useUpdateCandidateNotes } from '@/hooks/useCandidates';

interface CandidateDetailProps {
  candidate: Candidate;
  projectId: string;
}

export default function CandidateDetail({ candidate, projectId }: CandidateDetailProps) {
  const [notes, setNotes] = useState(candidate.recruiter_notes || '');
  const [notesSaved, setNotesSaved] = useState(false);
  const updateNotes = useUpdateCandidateNotes(projectId, candidate.id);

  const handleSaveNotes = async () => {
    await updateNotes.mutateAsync(notes);
    setNotesSaved(true);
    setTimeout(() => setNotesSaved(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <Link
          href={`/projects/${projectId}/candidates`}
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Rankings
        </Link>

        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-xl flex-shrink-0">
              {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{candidate.name}</h1>
              <p className="text-gray-500">{candidate.email}</p>
              {candidate.current_title && (
                <p className="text-sm text-gray-600 mt-1">
                  {candidate.current_title}
                  {candidate.current_company && ` at ${candidate.current_company}`}
                </p>
              )}
              <div className="flex flex-wrap items-center gap-3 mt-2">
                {candidate.location && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <MapPin className="w-3 h-3" />
                    {candidate.location}
                  </span>
                )}
                {candidate.years_experience != null && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <Briefcase className="w-3 h-3" />
                    {candidate.years_experience}yr exp
                  </span>
                )}
                {candidate.phone && (
                  <span className="flex items-center gap-1 text-xs text-gray-500">
                    <Phone className="w-3 h-3" />
                    {candidate.phone}
                  </span>
                )}
                {candidate.linkedin_url && (
                  <a href={candidate.linkedin_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
                    <Linkedin className="w-3 h-3" />
                    LinkedIn
                  </a>
                )}
                {candidate.github_url && (
                  <a href={candidate.github_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-gray-600 hover:underline">
                    <Github className="w-3 h-3" />
                    GitHub
                  </a>
                )}
                {candidate.portfolio_url && (
                  <a href={candidate.portfolio_url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-gray-600 hover:underline">
                    <Globe className="w-3 h-3" />
                    Portfolio
                  </a>
                )}
              </div>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2 flex-shrink-0">
            {candidate.recommendation && (
              <RecommendationBadge recommendation={candidate.recommendation} size="lg" />
            )}
            {candidate.score != null && (
              <div className={`flex items-center justify-center w-16 h-16 rounded-full text-2xl font-bold ${getScoreColor(candidate.score)}`}>
                {Math.round(candidate.score)}
              </div>
            )}
            {candidate.rank && (
              <p className="text-xs text-gray-500">Rank #{candidate.rank}</p>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList className="w-full justify-start bg-white border border-gray-200 p-1 rounded-xl h-auto">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="scores">Score Breakdown</TabsTrigger>
          <TabsTrigger value="resume">Resume</TabsTrigger>
          <TabsTrigger value="evaluation">Evaluation</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4 space-y-4">
          {candidate.recruiter_takeaway && (
            <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-5">
              <p className="text-xs font-semibold text-indigo-700 uppercase tracking-wider mb-2">
                AI Recruiter Takeaway
              </p>
              <p className="text-gray-800 leading-relaxed">{candidate.recruiter_takeaway}</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Key Skills */}
            {candidate.skills && candidate.skills.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3">Key Skills</h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map((skill) => (
                    <span
                      key={skill}
                      className="px-2.5 py-1 bg-gray-100 text-gray-700 text-sm rounded-lg"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Education */}
            {candidate.education && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <GraduationCap className="w-4 h-4 text-gray-400" />
                  Education
                </h3>
                <p className="text-gray-700">{candidate.education}</p>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Strengths */}
            {candidate.strengths && candidate.strengths.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-emerald-700 mb-3 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Strengths
                </h3>
                <ul className="space-y-2">
                  {candidate.strengths.map((s, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Weaknesses */}
            {candidate.weaknesses && candidate.weaknesses.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-amber-700 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Areas of Concern
                </h3>
                <ul className="space-y-2">
                  {candidate.weaknesses.map((w, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                      <AlertTriangle className="w-4 h-4 text-amber-500 mt-0.5 flex-shrink-0" />
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Red flags */}
            {candidate.red_flags && candidate.red_flags.length > 0 && (
              <div className="bg-red-50 rounded-xl border border-red-200 p-5">
                <h3 className="font-semibold text-red-700 mb-3 flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4" />
                  Red Flags
                </h3>
                <ul className="space-y-2">
                  {candidate.red_flags.map((f, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-red-700">
                      <AlertOctagon className="w-4 h-4 mt-0.5 flex-shrink-0" />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing requirements */}
            {candidate.missing_requirements && candidate.missing_requirements.length > 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                  <XCircle className="w-4 h-4 text-gray-400" />
                  Missing Requirements
                </h3>
                <ul className="space-y-2">
                  {candidate.missing_requirements.map((m, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                      <XCircle className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                      {m}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Notable projects */}
          {candidate.notable_projects && candidate.notable_projects.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                <Star className="w-4 h-4 text-amber-500" />
                Notable Projects
              </h3>
              <ul className="space-y-2">
                {candidate.notable_projects.map((p, i) => (
                  <li key={i} className="text-sm text-gray-700 flex items-start gap-2">
                    <span className="text-amber-500">•</span>
                    {p}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </TabsContent>

        {/* Score Breakdown Tab */}
        <TabsContent value="scores" className="mt-4">
          {candidate.score_breakdown && candidate.score_breakdown.length > 0 ? (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <ScoreBreakdown
                breakdown={candidate.score_breakdown}
                overallScore={candidate.score || 0}
              />
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
              <p className="text-gray-500">No score breakdown available.</p>
              <p className="text-xs text-gray-400 mt-1">Run evaluation to generate scores.</p>
            </div>
          )}
        </TabsContent>

        {/* Resume Tab */}
        <TabsContent value="resume" className="mt-4">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">
              {candidate.resume_filename || 'Resume Text'}
            </h3>
            {candidate.resume_text ? (
              <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono bg-gray-50 rounded-lg p-4 max-h-[600px] overflow-y-auto leading-relaxed">
                {candidate.resume_text}
              </pre>
            ) : (
              <p className="text-gray-500">No resume text available.</p>
            )}
          </div>
        </TabsContent>

        {/* Evaluation Tab */}
        <TabsContent value="evaluation" className="mt-4 space-y-4">
          {candidate.confidence_level && (
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="font-semibold text-gray-900 mb-2">Confidence Level</h3>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                candidate.confidence_level === 'high'
                  ? 'bg-emerald-100 text-emerald-700'
                  : candidate.confidence_level === 'medium'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-red-100 text-red-700'
              }`}>
                {candidate.confidence_level.charAt(0).toUpperCase() + candidate.confidence_level.slice(1)} Confidence
              </span>
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Recruiter Notes</h3>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add your notes about this candidate..."
              className="min-h-[120px]"
            />
            <div className="flex items-center justify-between mt-3">
              <p className="text-xs text-gray-400">
                Private notes visible only to your team
              </p>
              <Button
                size="sm"
                onClick={handleSaveNotes}
                disabled={updateNotes.isPending}
              >
                {updateNotes.isPending ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : notesSaved ? (
                  'Saved!'
                ) : (
                  'Save Notes'
                )}
              </Button>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
