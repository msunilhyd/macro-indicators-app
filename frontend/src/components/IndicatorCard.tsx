'use client';

import Link from 'next/link';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { formatValue, formatDate } from '@/lib/api';
import MiniChart from './MiniChart';

interface IndicatorCardProps {
  name: string;
  slug: string;
  categorySlug: string;
  unit: string | null;
  latestValue: number | null;
  latestDate: string | null;
  changePercent: number | null;
  sparkline?: number[];
}

export default function IndicatorCard({
  name,
  slug,
  categorySlug,
  unit,
  latestValue,
  latestDate,
  changePercent,
  sparkline = [],
}: IndicatorCardProps) {
  const isPositive = changePercent !== null && changePercent > 0;
  const isNegative = changePercent !== null && changePercent < 0;

  return (
    <Link href={`/indicator/${slug}`}>
      <div className="bg-white rounded-lg shadow-md p-5 hover:shadow-lg transition-shadow cursor-pointer border border-gray-100">
        <div className="flex justify-between items-start mb-3">
          <h3 className="font-semibold text-gray-800 text-sm leading-tight line-clamp-2">
            {name}
          </h3>
          <div className="flex items-center ml-2">
            {isPositive && <TrendingUp className="h-4 w-4 text-green-500" />}
            {isNegative && <TrendingDown className="h-4 w-4 text-red-500" />}
            {!isPositive && !isNegative && <Minus className="h-4 w-4 text-gray-400" />}
          </div>
        </div>

        <div className="flex items-end justify-between">
          <div>
            <p className="text-2xl font-bold text-gray-900">
              {formatValue(latestValue, unit)}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {formatDate(latestDate)}
            </p>
          </div>

          {changePercent !== null && (
            <div
              className={`text-sm font-medium px-2 py-1 rounded ${
                isPositive
                  ? 'bg-green-100 text-green-700'
                  : isNegative
                  ? 'bg-red-100 text-red-700'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              {isPositive ? '+' : ''}
              {changePercent.toFixed(2)}%
            </div>
          )}
        </div>

        {sparkline.length > 0 && (
          <div className="mt-3 h-12">
            <MiniChart data={sparkline} isPositive={isPositive} />
          </div>
        )}
      </div>
    </Link>
  );
}
