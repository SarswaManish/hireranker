import { Recommendation } from '@/types';
import { getRecommendationColor, getRecommendationLabel } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface RecommendationBadgeProps {
  recommendation: Recommendation;
  size?: 'sm' | 'md' | 'lg';
}

export default function RecommendationBadge({
  recommendation,
  size = 'md',
}: RecommendationBadgeProps) {
  const colorClass = getRecommendationColor(recommendation);
  const label = getRecommendationLabel(recommendation);

  return (
    <span
      className={cn(
        'inline-flex items-center font-semibold rounded-full border',
        colorClass,
        size === 'sm' && 'px-2 py-0.5 text-xs',
        size === 'md' && 'px-2.5 py-1 text-xs',
        size === 'lg' && 'px-3 py-1.5 text-sm'
      )}
    >
      {label}
    </span>
  );
}
