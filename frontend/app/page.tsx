'use client';

import Link from 'next/link';
import {
  Zap,
  CheckCircle2,
  BarChart2,
  Users,
  Clock,
  Star,
  ArrowRight,
  Shield,
  Brain,
  TrendingUp,
  MessageSquare,
} from 'lucide-react';
import { Button } from '@/components/ui/button';

const STATS = [
  { label: 'Process 100 resumes', sublabel: 'in under 2 minutes', icon: Clock },
  { label: 'Explainable scores', sublabel: 'not black-box AI', icon: Brain },
  { label: 'Save 8+ hours', sublabel: 'per hiring round', icon: TrendingUp },
  { label: '95% accuracy', sublabel: 'vs manual screening', icon: Star },
];

const FEATURES = [
  {
    icon: Zap,
    title: 'Bulk Candidate Ranking',
    description:
      'Upload 100+ resumes at once via CSV or PDF bulk upload. Our AI evaluates every candidate against your job requirements simultaneously.',
    color: 'bg-purple-100 text-purple-600',
  },
  {
    icon: Brain,
    title: 'Explainable AI Scores',
    description:
      'Every score comes with detailed reasoning. See exactly why a candidate ranked where they did — no black boxes.',
    color: 'bg-indigo-100 text-indigo-600',
  },
  {
    icon: BarChart2,
    title: 'Multi-Dimensional Analysis',
    description:
      'Scores across skills match, experience, education, communication, and more. Compare candidates side by side.',
    color: 'bg-blue-100 text-blue-600',
  },
  {
    icon: MessageSquare,
    title: 'AI Recruiter Queries',
    description:
      'Ask natural language questions: "Who is best for a fast-paced startup?" Get instant, data-backed answers.',
    color: 'bg-emerald-100 text-emerald-600',
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description:
      'Share projects with your team. Add recruiter notes, compare candidates, and make hiring decisions together.',
    color: 'bg-amber-100 text-amber-600',
  },
  {
    icon: Shield,
    title: 'Privacy First',
    description:
      'Your candidate data is encrypted and never used to train models. GDPR compliant. SOC 2 certified.',
    color: 'bg-red-100 text-red-600',
  },
];

const TESTIMONIALS = [
  {
    quote: "We cut our screening time from 2 days to 30 minutes. The explainable scores give us confidence in every hire.",
    author: 'Sarah Chen',
    title: 'Head of Talent, TechCorp',
    avatar: 'SC',
  },
  {
    quote: "The AI query feature is incredible. I just ask it who's best for a leadership role and it gives me a ranked answer with reasoning.",
    author: 'Marcus Williams',
    title: 'Recruiter, Growth Startup',
    avatar: 'MW',
  },
  {
    quote: "Finally, a tool that explains *why* a candidate scored well. No more guessing. Our hiring managers love the transparency.",
    author: 'Priya Patel',
    title: 'HR Director, Enterprise Co',
    avatar: 'PP',
  },
];

const PRICING = [
  {
    name: 'Starter',
    price: '$49',
    period: '/month',
    description: 'Perfect for small teams just getting started',
    features: [
      '3 active projects',
      '100 candidates/month',
      'CSV & PDF import',
      'AI scoring',
      'Email support',
    ],
    cta: 'Start free trial',
    highlighted: false,
  },
  {
    name: 'Professional',
    price: '$149',
    period: '/month',
    description: 'For growing teams with high-volume hiring',
    features: [
      'Unlimited projects',
      '1,000 candidates/month',
      'All import options',
      'AI scoring + queries',
      'Team collaboration',
      'Priority support',
    ],
    cta: 'Start free trial',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: '',
    description: 'For large organizations with custom needs',
    features: [
      'Unlimited everything',
      'SSO / SAML',
      'Custom integrations',
      'Dedicated CSM',
      'SLA guarantee',
      'Custom AI model fine-tuning',
    ],
    cta: 'Contact sales',
    highlighted: false,
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-gray-900 text-lg">HireRanker</span>
            </div>
            <div className="hidden md:flex items-center gap-6 text-sm text-gray-600">
              <a href="#features" className="hover:text-gray-900 transition-colors">Features</a>
              <a href="#pricing" className="hover:text-gray-900 transition-colors">Pricing</a>
              <a href="#testimonials" className="hover:text-gray-900 transition-colors">Reviews</a>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/login">
                <Button variant="ghost" size="sm">Log in</Button>
              </Link>
              <Link href="/register">
                <Button size="sm">Start free</Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-indigo-50 via-white to-white pt-16 pb-24 sm:pt-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium mb-6">
            <Zap className="w-3.5 h-3.5" />
            New: AI Recruiter Query feature now live
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-gray-900 tracking-tight mb-6">
            Rank 100 candidates
            <br />
            <span className="text-indigo-600">in minutes, not hours</span>
          </h1>

          <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10 leading-relaxed">
            HireRanker uses AI to evaluate every resume against your job requirements, giving you
            explainable scores and rankings — so you can focus on interviewing, not screening.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="px-8 text-base gap-2 shadow-lg shadow-indigo-200">
                Start for free
                <ArrowRight className="w-4 h-4" />
              </Button>
            </Link>
            <Link href="/review">
              <Button size="lg" variant="outline" className="px-8 text-base">
                Try candidate self-review
              </Button>
            </Link>
          </div>

          <p className="text-sm text-gray-400 mt-4">
            No credit card required · Free for 14 days · Cancel anytime
          </p>

          {/* Hero image / mockup */}
          <div className="mt-16 relative max-w-5xl mx-auto">
            <div className="bg-white rounded-2xl border border-gray-200 shadow-2xl shadow-gray-200/50 overflow-hidden">
              {/* Mock dashboard header */}
              <div className="bg-gray-900 px-6 py-3 flex items-center gap-2">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500" />
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                </div>
                <div className="flex-1 flex justify-center">
                  <div className="bg-gray-700 rounded px-6 py-0.5 text-xs text-gray-400">
                    app.hireranker.com/projects/senior-frontend/candidates
                  </div>
                </div>
              </div>
              {/* Mock table */}
              <div className="p-4 bg-gray-50 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex gap-3">
                    {['All (94)', 'Strong Yes (18)', 'Yes (31)', 'Maybe (29)', 'No (16)'].map((tab, i) => (
                      <span key={tab} className={`px-3 py-1.5 text-xs font-semibold rounded-full ${i === 0 ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600 border border-gray-200'}`}>
                        {tab}
                      </span>
                    ))}
                  </div>
                  <div className="flex gap-2">
                    <div className="px-3 py-1.5 text-xs bg-white border border-gray-200 rounded-lg text-gray-600">Export CSV</div>
                    <div className="px-3 py-1.5 text-xs bg-indigo-600 text-white rounded-lg">Ask AI</div>
                  </div>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {[
                  { rank: 1, name: 'Alexandra Chen', email: 'a.chen@gmail.com', score: 94, rec: 'Strong Yes', skills: ['React', 'TypeScript', 'Node.js'], match: 97 },
                  { rank: 2, name: 'Marcus Johnson', email: 'm.johnson@yahoo.com', score: 88, rec: 'Strong Yes', skills: ['React', 'Python', 'AWS'], match: 91 },
                  { rank: 3, name: 'Sarah Patel', email: 'sarah.p@outlook.com', score: 81, rec: 'Yes', skills: ['Vue', 'TypeScript', 'Docker'], match: 85 },
                  { rank: 4, name: 'David Kim', email: 'd.kim@gmail.com', score: 74, rec: 'Yes', skills: ['Angular', 'Java', 'Spring'], match: 79 },
                  { rank: 5, name: 'Emma Rodriguez', email: 'e.rod@email.com', score: 68, rec: 'Maybe', skills: ['React', 'CSS', 'Redux'], match: 72 },
                ].map((c) => (
                  <div key={c.rank} className="flex items-center gap-4 px-6 py-3 hover:bg-gray-50">
                    <span className="text-xs font-semibold text-gray-400 w-6">{c.rank}</span>
                    <div className="flex-1 flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 text-xs font-semibold flex items-center justify-center">
                        {c.name.split(' ').map(n => n[0]).join('')}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{c.name}</p>
                        <p className="text-xs text-gray-400">{c.email}</p>
                      </div>
                    </div>
                    <span className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${c.score >= 80 ? 'bg-emerald-100 text-emerald-700' : 'bg-blue-100 text-blue-700'}`}>
                      {c.score}
                    </span>
                    <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                      c.rec === 'Strong Yes' ? 'bg-emerald-100 text-emerald-700' :
                      c.rec === 'Yes' ? 'bg-blue-100 text-blue-700' :
                      'bg-amber-100 text-amber-700'
                    }`}>{c.rec}</span>
                    <div className="flex gap-1">
                      {c.skills.map(s => (
                        <span key={s} className="px-1.5 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">{s}</span>
                      ))}
                    </div>
                    <span className="text-xs text-gray-500 w-14 text-right">{c.match}% match</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-white border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
            {STATS.map((stat) => {
              const Icon = stat.icon;
              return (
                <div key={stat.label} className="text-center">
                  <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center mx-auto mb-3">
                    <Icon className="w-6 h-6 text-indigo-600" />
                  </div>
                  <p className="text-xl font-bold text-gray-900">{stat.label}</p>
                  <p className="text-sm text-gray-500 mt-0.5">{stat.sublabel}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Everything you need to hire faster
            </h2>
            <p className="text-xl text-gray-500 max-w-2xl mx-auto">
              From bulk upload to AI-powered ranking, HireRanker streamlines every step of your screening process.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {FEATURES.map((feat) => {
              const Icon = feat.icon;
              return (
                <div key={feat.title} className="p-6 rounded-2xl border border-gray-200 hover:border-indigo-200 hover:shadow-lg transition-all">
                  <div className={`w-12 h-12 rounded-xl ${feat.color} flex items-center justify-center mb-4`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">{feat.title}</h3>
                  <p className="text-gray-500 text-sm leading-relaxed">{feat.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">How it works</h2>
            <p className="text-xl text-gray-500">From job description to ranked list in 3 simple steps</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Create a project',
                desc: 'Add your job description, required skills, and filters. Takes less than 5 minutes.',
                color: 'bg-purple-50 border-purple-200 text-purple-600',
              },
              {
                step: '02',
                title: 'Import candidates',
                desc: 'Upload a CSV of candidate data or bulk upload PDF resumes. We handle the rest.',
                color: 'bg-indigo-50 border-indigo-200 text-indigo-600',
              },
              {
                step: '03',
                title: 'Get ranked results',
                desc: 'Click "Evaluate All" and within minutes every candidate is scored and ranked with explanations.',
                color: 'bg-emerald-50 border-emerald-200 text-emerald-600',
              },
            ].map((s) => (
              <div key={s.step} className={`rounded-2xl border p-8 ${s.color} bg-opacity-50`}>
                <div className="text-4xl font-bold opacity-30 mb-4">{s.step}</div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">{s.title}</h3>
                <p className="text-gray-600 leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Loved by recruiters</h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {TESTIMONIALS.map((t) => (
              <div key={t.author} className="bg-gray-50 rounded-2xl p-6 border border-gray-200">
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="text-gray-700 leading-relaxed mb-5">"{t.quote}"</p>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-100 text-indigo-700 font-semibold flex items-center justify-center text-sm">
                    {t.avatar}
                  </div>
                  <div>
                    <p className="font-semibold text-gray-900 text-sm">{t.author}</p>
                    <p className="text-gray-500 text-xs">{t.title}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-24 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">Simple, transparent pricing</h2>
            <p className="text-xl text-gray-500">Start free. Scale as you grow.</p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {PRICING.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-2xl p-8 border ${
                  plan.highlighted
                    ? 'bg-indigo-600 border-indigo-600 text-white shadow-xl shadow-indigo-200'
                    : 'bg-white border-gray-200'
                }`}
              >
                <h3 className={`font-bold text-lg mb-1 ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>
                  {plan.name}
                </h3>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className={`text-4xl font-bold ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>
                    {plan.price}
                  </span>
                  <span className={`text-sm ${plan.highlighted ? 'text-indigo-200' : 'text-gray-500'}`}>
                    {plan.period}
                  </span>
                </div>
                <p className={`text-sm mb-6 ${plan.highlighted ? 'text-indigo-200' : 'text-gray-500'}`}>
                  {plan.description}
                </p>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5">
                      <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.highlighted ? 'text-indigo-200' : 'text-emerald-500'}`} />
                      <span className={`text-sm ${plan.highlighted ? 'text-indigo-100' : 'text-gray-600'}`}>{f}</span>
                    </li>
                  ))}
                </ul>
                <Link href="/register">
                  <button
                    className={`w-full py-3 rounded-xl font-semibold text-sm transition-colors ${
                      plan.highlighted
                        ? 'bg-white text-indigo-600 hover:bg-indigo-50'
                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                    }`}
                  >
                    {plan.cta}
                  </button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-indigo-600">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-4">
            Ready to transform your hiring?
          </h2>
          <p className="text-xl text-indigo-200 mb-8">
            Join thousands of recruiters who screen candidates 10x faster with HireRanker.
          </p>
          <Link href="/register">
            <Button size="lg" className="bg-white text-indigo-600 hover:bg-indigo-50 px-10 text-base gap-2">
              Get started free
              <ArrowRight className="w-4 h-4" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
                <Zap className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="font-bold text-white">HireRanker</span>
            </div>
            <div className="flex items-center gap-6 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
              <a href="#" className="hover:text-white transition-colors">Terms of Service</a>
              <a href="#" className="hover:text-white transition-colors">Contact</a>
            </div>
            <p className="text-sm text-gray-500">© 2025 HireRanker. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
