import Link from 'next/link';
import { Zap, CheckCircle2 } from 'lucide-react';
import RegisterForm from '@/components/auth/RegisterForm';

const BENEFITS = [
  'Free 14-day trial, no credit card',
  'Process 100 resumes in < 2 minutes',
  'Explainable AI scores',
  'Cancel anytime',
];

export default function RegisterPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid lg:grid-cols-2 gap-12 items-start">
        {/* Left: Benefits */}
        <div className="hidden lg:block pt-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-8">
            <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-gray-900">HireRanker</span>
          </Link>
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Hire smarter,<br />not harder
          </h2>
          <p className="text-gray-500 mb-8 leading-relaxed">
            Join thousands of recruiters who use HireRanker to screen candidates 10x faster
            with explainable AI scoring.
          </p>
          <ul className="space-y-3">
            {BENEFITS.map((b) => (
              <li key={b} className="flex items-center gap-2.5 text-gray-700">
                <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                {b}
              </li>
            ))}
          </ul>
        </div>

        {/* Right: Form */}
        <div>
          <div className="text-center mb-6 lg:hidden">
            <Link href="/" className="inline-flex items-center gap-2">
              <div className="w-9 h-9 bg-indigo-600 rounded-xl flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-gray-900">HireRanker</span>
            </Link>
          </div>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Create your account</h1>
            <p className="text-gray-500 mb-6">Start your free 14-day trial</p>
            <RegisterForm />
          </div>

          <p className="text-center text-sm text-gray-500 mt-4">
            Already have an account?{' '}
            <Link href="/login" className="text-indigo-600 font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
