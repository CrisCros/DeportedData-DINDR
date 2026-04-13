import { Alert, Paper, Stack, Text, Title } from '@mantine/core';

type EmploymentLineChartProps = {
  years: number[];
  values: number[];
};

export function EmploymentLineChart({ years, values }: EmploymentLineChartProps) {
  if (!years.length || !values.length) {
    return (
      <Alert color="yellow" title="Sin datos">
        No hay serie temporal disponible.
      </Alert>
    );
  }

  const width = 860;
  const height = 320;
  const padding = 36;
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = Math.max(max - min, 1);

  const points = values.map((value, index) => {
    const x = padding + (index * (width - padding * 2)) / Math.max(values.length - 1, 1);
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  });

  return (
    <Paper withBorder radius="lg" p="md" className="glass-card">
      <Stack gap="sm">
        <div>
          <Title order={3}>Evolución anual del empleo deportivo</Title>
          <Text c="dimmed" size="sm">
            Valores absolutos en miles de personas.
          </Text>
        </div>
        <div style={{ overflowX: 'auto' }}>
          <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', minWidth: 540, height: 320 }}>
            <polyline fill="none" stroke="#06b6d4" strokeWidth="4" points={points.join(' ')} />
            {values.map((value, index) => {
              const x = padding + (index * (width - padding * 2)) / Math.max(values.length - 1, 1);
              const y = height - padding - ((value - min) / range) * (height - padding * 2);
              return (
                <g key={`${years[index]}-${value}`}>
                  <circle cx={x} cy={y} r="4" fill="#0891b2" />
                  <text x={x} y={height - 10} textAnchor="middle" fontSize="11" fill="#64748b">
                    {years[index]}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>
      </Stack>
    </Paper>
  );
}
