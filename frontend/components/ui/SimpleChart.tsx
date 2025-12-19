/**
 * Simple Chart Components
 * Lightweight chart components using SVG (no external dependencies)
 */

'use client'

interface BarChartProps {
  data: Array<{ label: string; value: number; color?: string }>
  height?: number
  showValues?: boolean
}

export function BarChart({ data, height = 120, showValues = true }: BarChartProps) {
  const maxValue = Math.max(...data.map(d => d.value), 1)
  const barWidth = 100 / data.length

  return (
    <div className="w-full flex items-end justify-center" style={{ height: `${height}px` }}>
      <svg viewBox={`0 0 100 ${height}`} className="w-full h-full max-w-[300px]">
        {data.map((item, index) => {
          const barHeight = maxValue > 0 ? (item.value / maxValue) * (height - 25) : 0
          const x = (index * barWidth) + (barWidth * 0.15)
          const width = barWidth * 0.7
          const y = height - barHeight - 20
          const color = item.color || '#0ea5e9'

          return (
            <g key={index}>
              <rect
                x={x}
                y={y}
                width={width}
                height={barHeight}
                fill={color}
                rx="2"
                className="hover:opacity-80 transition-opacity"
              />
              {showValues && item.value > 0 && (
                <text
                  x={x + width / 2}
                  y={y - 5}
                  textAnchor="middle"
                  fontSize="9"
                  fontWeight="600"
                  fill="currentColor"
                  className="text-gray-700 dark:text-gray-300"
                >
                  {item.value}
                </text>
              )}
              <text
                x={x + width / 2}
                y={height - 5}
                textAnchor="middle"
                fontSize="8"
                fill="currentColor"
                className="text-gray-600 dark:text-gray-400"
              >
                {item.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

interface LineChartProps {
  data: Array<{ label: string; value: number }>
  height?: number
  color?: string
}

export function LineChart({ data, height = 200, color = '#0ea5e9' }: LineChartProps) {
  const maxValue = Math.max(...data.map(d => d.value), 1)
  const stepX = 100 / (data.length - 1 || 1)
  const chartHeight = height - 30

  const points = data.map((item, index) => {
    const x = index * stepX
    const y = chartHeight - (item.value / maxValue) * chartHeight + 10
    return `${x},${y}`
  }).join(' ')

  return (
    <div className="w-full">
      <svg viewBox={`0 0 100 ${height}`} className="w-full h-auto">
        <polyline
          points={points}
          fill="none"
          stroke={color}
          strokeWidth="2"
          className="drop-shadow-sm"
        />
        {data.map((item, index) => {
          const x = index * stepX
          const y = chartHeight - (item.value / maxValue) * chartHeight + 10

          return (
            <g key={index}>
              <circle
                cx={x}
                cy={y}
                r="2"
                fill={color}
                className="hover:r-3 transition-all"
              />
              <text
                x={x}
                y={height - 2}
                textAnchor="middle"
                fontSize="7"
                fill="currentColor"
                className="text-gray-600 dark:text-gray-400"
              >
                {item.label}
              </text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

interface PieChartProps {
  data: Array<{ label: string; value: number; color?: string }>
  size?: number
  showLegend?: boolean
}

interface DonutChartProps {
  data: Array<{ label: string; value: number; color?: string }>
  size?: number
  showLegend?: boolean
}

export function PieChart({ data, size = 150, showLegend = true }: PieChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  let currentAngle = -90 // Start at top

  const segments = data.map((item, index) => {
    const percentage = (item.value / total) * 100
    const angle = (item.value / total) * 360
    const startAngle = currentAngle
    const endAngle = currentAngle + angle
    currentAngle = endAngle

    const startAngleRad = (startAngle * Math.PI) / 180
    const endAngleRad = (endAngle * Math.PI) / 180
    const radius = size / 2 - 10

    const x1 = size / 2 + radius * Math.cos(startAngleRad)
    const y1 = size / 2 + radius * Math.sin(startAngleRad)
    const x2 = size / 2 + radius * Math.cos(endAngleRad)
    const y2 = size / 2 + radius * Math.sin(endAngleRad)

    const largeArcFlag = angle > 180 ? 1 : 0

    const pathData = [
      `M ${size / 2} ${size / 2}`,
      `L ${x1} ${y1}`,
      `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      'Z'
    ].join(' ')

    const color = item.color || ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]

    return (
      <g key={index}>
        <path
          d={pathData}
          fill={color}
          className="hover:opacity-80 transition-opacity"
        />
      </g>
    )
  })

  return (
    <div className="w-full flex items-center justify-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto max-w-[180px]">
        {segments}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={size / 2 - 10}
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          className="text-gray-200 dark:text-gray-700"
        />
      </svg>
      {showLegend && (
        <div className="ml-4 space-y-2">
          {data.map((item, index) => {
            const percentage = ((item.value / total) * 100).toFixed(1)
            const color = item.color || ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]
            
            return (
              <div key={index} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: color }}
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {item.label}: {percentage}%
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

export function DonutChart({ data, size = 150, showLegend = true }: DonutChartProps) {
  const total = data.reduce((sum, item) => sum + item.value, 0)
  let currentAngle = -90
  const innerRadius = size / 2 - 20
  const outerRadius = size / 2 - 10

  const segments = data.map((item, index) => {
    const angle = (item.value / total) * 360
    const startAngle = currentAngle
    const endAngle = currentAngle + angle
    currentAngle = endAngle

    const startAngleRad = (startAngle * Math.PI) / 180
    const endAngleRad = (endAngle * Math.PI) / 180

    const x1 = size / 2 + outerRadius * Math.cos(startAngleRad)
    const y1 = size / 2 + outerRadius * Math.sin(startAngleRad)
    const x2 = size / 2 + outerRadius * Math.cos(endAngleRad)
    const y2 = size / 2 + outerRadius * Math.sin(endAngleRad)

    const x3 = size / 2 + innerRadius * Math.cos(endAngleRad)
    const y3 = size / 2 + innerRadius * Math.sin(endAngleRad)
    const x4 = size / 2 + innerRadius * Math.cos(startAngleRad)
    const y4 = size / 2 + innerRadius * Math.sin(startAngleRad)

    const largeArcFlag = angle > 180 ? 1 : 0

    const pathData = [
      `M ${x1} ${y1}`,
      `A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      `L ${x3} ${y3}`,
      `A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x4} ${y4}`,
      'Z'
    ].join(' ')

    const color = item.color || ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]

    return (
      <g key={index}>
        <path
          d={pathData}
          fill={color}
          className="hover:opacity-80 transition-opacity"
        />
      </g>
    )
  })

  return (
    <div className="w-full flex items-center justify-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-auto max-w-[180px]">
        {segments}
      </svg>
      {showLegend && (
        <div className="ml-4 space-y-2">
          {data.map((item, index) => {
            const percentage = ((item.value / total) * 100).toFixed(1)
            const color = item.color || ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][index % 5]
            
            return (
              <div key={index} className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: color }}
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {item.label}: {percentage}%
                </span>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

