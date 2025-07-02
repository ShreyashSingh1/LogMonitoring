import { useState, useEffect } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { format, subDays, startOfDay, endOfDay } from 'date-fns'
import { useSocket } from '../contexts/SocketContext'
import { logService } from '../services/api'

const Analytics = () => {
  const { logs: liveLogs } = useSocket()
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('24h')
  const [chartData, setChartData] = useState([])
  const [sourceStats, setSourceStats] = useState([])
  const [errorTrends, setErrorTrends] = useState([])

  useEffect(() => {
    fetchAnalytics()
  }, [timeRange])

  useEffect(() => {
    if (liveLogs.length > 0) {
      updateRealTimeAnalytics()
    }
  }, [liveLogs])

  const fetchAnalytics = async () => {
    try {
      setLoading(true)
      const data = await logService.getStats()
      setStats(data)
      generateChartData()
    } catch (error) {
      console.error('Error fetching analytics:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateRealTimeAnalytics = () => {
    generateChartData()
    generateSourceStats()
    generateErrorTrends()
  }

  const generateChartData = () => {
    const now = new Date()
    let intervals = []
    let intervalCount = 24
    let intervalDuration = 60 * 60 * 1000 // 1 hour

    switch (timeRange) {
      case '1h':
        intervalCount = 12
        intervalDuration = 5 * 60 * 1000 // 5 minutes
        break
      case '24h':
        intervalCount = 24
        intervalDuration = 60 * 60 * 1000 // 1 hour
        break
      case '7d':
        intervalCount = 7
        intervalDuration = 24 * 60 * 60 * 1000 // 1 day
        break
      case '30d':
        intervalCount = 30
        intervalDuration = 24 * 60 * 60 * 1000 // 1 day
        break
    }

    // Create time intervals
    for (let i = intervalCount - 1; i >= 0; i--) {
      const time = new Date(now.getTime() - i * intervalDuration)
      intervals.push({
        time: timeRange === '7d' || timeRange === '30d' 
          ? format(time, 'MMM dd') 
          : format(time, 'HH:mm'),
        errors: 0,
        warnings: 0,
        info: 0,
        total: 0
      })
    }

    // Count logs by interval
    liveLogs.forEach(log => {
      const logTime = new Date(log.timestamp)
      const timeDiff = now - logTime
      const intervalIndex = Math.floor(timeDiff / intervalDuration)
      
      if (intervalIndex >= 0 && intervalIndex < intervalCount) {
        const interval = intervals[intervalCount - 1 - intervalIndex]
        if (interval) {
          interval.total++
          const level = log.level?.toLowerCase()
          if (level === 'error') interval.errors++
          else if (level === 'warn' || level === 'warning') interval.warnings++
          else interval.info++
        }
      }
    })

    setChartData(intervals)
  }

  const generateSourceStats = () => {
    const sources = {}
    liveLogs.forEach(log => {
      if (log.source) {
        if (!sources[log.source]) {
          sources[log.source] = { name: log.source, total: 0, errors: 0, warnings: 0 }
        }
        sources[log.source].total++
        const level = log.level?.toLowerCase()
        if (level === 'error') sources[log.source].errors++
        else if (level === 'warn' || level === 'warning') sources[log.source].warnings++
      }
    })

    setSourceStats(Object.values(sources))
  }

  const generateErrorTrends = () => {
    const trends = []
    const now = new Date()
    
    for (let i = 6; i >= 0; i--) {
      const day = subDays(now, i)
      const dayStart = startOfDay(day)
      const dayEnd = endOfDay(day)
      
      const dayLogs = liveLogs.filter(log => {
        const logTime = new Date(log.timestamp)
        return logTime >= dayStart && logTime <= dayEnd
      })

      const errors = dayLogs.filter(log => log.level?.toLowerCase() === 'error').length
      const warnings = dayLogs.filter(log => log.level?.toLowerCase() === 'warn' || log.level?.toLowerCase() === 'warning').length

      trends.push({
        date: format(day, 'MMM dd'),
        errors,
        warnings,
        total: dayLogs.length
      })
    }

    setErrorTrends(trends)
  }

  const levelDistribution = [
    {
      name: 'Error',
      value: stats.level_distribution?.error || 0,
      color: '#f44336'
    },
    {
      name: 'Warning',
      value: (stats.level_distribution?.warn || 0) + (stats.level_distribution?.warning || 0),
      color: '#ff9800'
    },
    {
      name: 'Info',
      value: stats.level_distribution?.info || 0,
      color: '#2196f3'
    }
  ]

  const topErrors = liveLogs
    .filter(log => log.level?.toLowerCase() === 'error')
    .reduce((acc, log) => {
      const key = log.message?.substring(0, 100) || 'Unknown error'
      acc[key] = (acc[key] || 0) + 1
      return acc
    }, {})

  const topErrorsList = Object.entries(topErrors)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10)
    .map(([message, count]) => ({ message, count }))

  if (loading) {
    return (
      <Box sx={{ width: '100%', mt: 2 }}>
        <LinearProgress />
        <Typography sx={{ mt: 2 }}>Loading analytics...</Typography>
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Analytics
      </Typography>

      {/* Time Range Selector */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="1h">Last Hour</MenuItem>
              <MenuItem value="24h">Last 24 Hours</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
              <MenuItem value="30d">Last 30 Days</MenuItem>
            </Select>
          </FormControl>
        </CardContent>
      </Card>

      <Grid container spacing={3}>
        {/* Log Volume Chart */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Log Volume Over Time
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="total"
                    stackId="1"
                    stroke="#2196f3"
                    fill="#2196f3"
                    fillOpacity={0.6}
                    name="Total"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Log Level Distribution */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Log Level Distribution
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={levelDistribution}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    dataKey="value"
                  >
                    {levelDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Trends */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Error Trends (7 Days)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={errorTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="errors"
                    stroke="#f44336"
                    name="Errors"
                    strokeWidth={3}
                  />
                  <Line
                    type="monotone"
                    dataKey="warnings"
                    stroke="#ff9800"
                    name="Warnings"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Source Statistics */}
        <Grid item xs={12} lg={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Logs by Source
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sourceStats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="total" fill="#2196f3" name="Total" />
                  <Bar dataKey="errors" fill="#f44336" name="Errors" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Top Errors */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Frequent Errors
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Error Message</TableCell>
                      <TableCell align="right">Count</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {topErrorsList.map((error, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Typography
                            variant="body2"
                            sx={{
                              maxWidth: 600,
                              overflow: 'hidden',
                              textOverflow: 'ellipsis',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {error.message}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" color="error">
                            {error.count}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}

export default Analytics 