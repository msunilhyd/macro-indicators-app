'use client';

import { LineChart, Line, ResponsiveContainer } from 'recharts';

interface MiniChartProps {
  data: number[];
  isPositive?: boolean;
}

export default function MiniChart({ data, isPositive = true }: MiniChartProps) {
  const chartData = data.map((value, index) => ({ value, index }));
  const color = isPositive ? '#16a34a' : '#dc2626';

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData}>
        <Line
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
