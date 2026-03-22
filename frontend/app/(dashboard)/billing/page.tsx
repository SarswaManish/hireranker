'use client';

import { useState } from 'react';
import { CheckCircle2, Loader2, CreditCard, Zap, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import Header from '@/components/layout/Header';
import { useQuery } from '@tanstack/react-query';
import { billingApi } from '@/lib/api';
import { formatDate } from '@/lib/utils';

const PLANS = [
  {
    id: 'starter',
    name: 'Starter',
    price: 49,
    period: 'month',
    features: ['3 active projects', '100 candidates/month', 'CSV & PDF import', 'AI scoring', 'Email support'],
  },
  {
    id: 'professional',
    name: 'Professional',
    price: 149,
    period: 'month',
    features: ['Unlimited projects', '1,000 candidates/month', 'All import options', 'AI scoring + queries', 'Team collaboration', 'Priority support'],
    highlighted: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    period: 'month',
    features: ['Unlimited everything', 'SSO / SAML', 'Custom integrations', 'Dedicated CSM', 'SLA guarantee'],
  },
];

export default function BillingPage() {
  const [billingInterval, setBillingInterval] = useState<'monthly' | 'yearly'>('monthly');
  const [isLoading, setIsLoading] = useState<string | null>(null);

  const { data: subscription } = useQuery({
    queryKey: ['subscription'],
    queryFn: () => billingApi.getSubscription(),
  });

  const handleSubscribe = async (planId: string) => {
    if (planId === 'enterprise') {
      window.open('mailto:sales@hireranker.com', '_blank');
      return;
    }
    setIsLoading(planId);
    try {
      const { url } = await billingApi.createCheckoutSession(planId);
      window.location.href = url;
    } catch {
      setIsLoading(null);
    }
  };

  const handleCancel = async () => {
    if (confirm('Cancel your subscription? You will retain access until the end of the billing period.')) {
      await billingApi.cancelSubscription();
    }
  };

  const currentPlanId = subscription?.plan?.id;

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <Header title="Billing" subtitle="Manage your subscription and payment details" />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Current subscription */}
          {subscription && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="font-semibold text-gray-900 mb-1">Current Plan</h2>
                  <div className="flex items-center gap-3">
                    <span className="text-2xl font-bold text-indigo-600">{subscription.plan.name}</span>
                    <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full ${
                      subscription.status === 'active' || subscription.status === 'trialing'
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-red-100 text-red-700'
                    }`}>
                      {subscription.status}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {subscription.cancel_at_period_end
                      ? `Cancels on ${formatDate(subscription.current_period_end)}`
                      : `Renews on ${formatDate(subscription.current_period_end)}`}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <Button variant="outline" size="sm" className="gap-1.5">
                    <CreditCard className="w-4 h-4" />
                    Update Payment
                  </Button>
                  {!subscription.cancel_at_period_end && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancel}
                      className="text-red-600 border-red-200 hover:bg-red-50"
                    >
                      Cancel Plan
                    </Button>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Billing toggle */}
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Choose your plan</h2>
            <div className="inline-flex items-center gap-1 bg-gray-100 rounded-full p-1 mt-2">
              <button
                onClick={() => setBillingInterval('monthly')}
                className={`px-4 py-1.5 text-sm font-medium rounded-full transition-colors ${
                  billingInterval === 'monthly' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingInterval('yearly')}
                className={`px-4 py-1.5 text-sm font-medium rounded-full transition-colors ${
                  billingInterval === 'yearly' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'
                }`}
              >
                Yearly
                <span className="ml-1.5 text-xs text-emerald-600 font-semibold">-20%</span>
              </button>
            </div>
          </div>

          {/* Plan cards */}
          <div className="grid md:grid-cols-3 gap-6">
            {PLANS.map((plan) => {
              const isCurrentPlan = currentPlanId === plan.id;
              const price = plan.price
                ? billingInterval === 'yearly'
                  ? Math.round(plan.price * 0.8)
                  : plan.price
                : null;

              return (
                <div
                  key={plan.id}
                  className={`rounded-2xl p-6 border ${
                    plan.highlighted
                      ? 'bg-indigo-600 border-indigo-600 text-white'
                      : 'bg-white border-gray-200'
                  } ${isCurrentPlan ? 'ring-2 ring-indigo-400' : ''}`}
                >
                  {isCurrentPlan && (
                    <div className="mb-3">
                      <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-full ${
                        plan.highlighted ? 'bg-indigo-500 text-white' : 'bg-indigo-100 text-indigo-700'
                      }`}>
                        Current Plan
                      </span>
                    </div>
                  )}

                  <h3 className={`font-bold text-lg mb-1 ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>
                    {plan.name}
                  </h3>

                  <div className="flex items-baseline gap-1 mb-4">
                    {price ? (
                      <>
                        <span className={`text-4xl font-bold ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>
                          ${price}
                        </span>
                        <span className={`text-sm ${plan.highlighted ? 'text-indigo-200' : 'text-gray-500'}`}>
                          /month
                        </span>
                      </>
                    ) : (
                      <span className={`text-2xl font-bold ${plan.highlighted ? 'text-white' : 'text-gray-900'}`}>
                        Custom
                      </span>
                    )}
                  </div>

                  <ul className="space-y-2.5 mb-6">
                    {plan.features.map((f) => (
                      <li key={f} className="flex items-start gap-2">
                        <CheckCircle2 className={`w-4 h-4 mt-0.5 flex-shrink-0 ${plan.highlighted ? 'text-indigo-200' : 'text-emerald-500'}`} />
                        <span className={`text-sm ${plan.highlighted ? 'text-indigo-100' : 'text-gray-600'}`}>{f}</span>
                      </li>
                    ))}
                  </ul>

                  {isCurrentPlan ? (
                    <div className={`text-center py-2.5 rounded-xl text-sm font-medium ${
                      plan.highlighted ? 'bg-indigo-500 text-indigo-100' : 'bg-gray-100 text-gray-500'
                    }`}>
                      Current Plan
                    </div>
                  ) : (
                    <Button
                      onClick={() => handleSubscribe(plan.id)}
                      disabled={isLoading === plan.id}
                      className={`w-full ${
                        plan.highlighted
                          ? 'bg-white text-indigo-600 hover:bg-indigo-50'
                          : 'bg-indigo-600 text-white hover:bg-indigo-700'
                      }`}
                    >
                      {isLoading === plan.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : plan.price ? (
                        `Upgrade to ${plan.name}`
                      ) : (
                        <span className="flex items-center gap-1.5">
                          Contact Sales
                          <ExternalLink className="w-3.5 h-3.5" />
                        </span>
                      )}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Invoice history placeholder */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="font-semibold text-gray-900 mb-4">Payment History</h2>
            <div className="text-center py-8 text-gray-400">
              <CreditCard className="w-10 h-10 mx-auto mb-2 opacity-30" />
              <p className="text-sm">No invoices yet</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
