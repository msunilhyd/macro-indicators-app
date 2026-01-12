'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { DataPoint } from '@/lib/api';

interface ChartProps {
  data: DataPoint[];
  name: string;
  unit: string | null;
}

export default function Chart({ data, name, unit }: ChartProps) {
  const chartData = data.map((dp) => {
    const date = new Date(dp.date);
    // If date is January 1st, show only the year (year-only data)
    const formattedDate = date.getMonth() === 0 && date.getDate() === 1
      ? date.getFullYear().toString()
      : date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
    
    return {
      date: formattedDate,
      value: dp.value,
      fullDate: dp.date,
    };
  });

  const formatYAxis = (value: number) => {
    if (unit === '%') return `${value}%`;
    if (unit?.includes('USD')) return `$${value.toLocaleString()}`;
    return value.toLocaleString();
  };

  return (
    <div className="w-full h-[400px] bg-white rounded-lg shadow-md p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <YAxis
            tickFormatter={formatYAxis}
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={{ stroke: '#e5e7eb' }}
          />
          <Tooltip
            formatter={(value) => [formatYAxis(value as number), name]}
            labelFormatter={(label) => `Date: ${label}`}
            contentStyle={{
              backgroundColor: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="value"
            name={name}
            stroke="#2563eb"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
