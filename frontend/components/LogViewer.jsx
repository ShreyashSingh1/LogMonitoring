import { useState, useEffect, useMemo } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Pagination,
  IconButton,
  Collapse
} from '@mui/material'
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  CheckCircle as SuccessIcon
} from '@mui/icons-material'
import { format } from 'date-fns'
import ReactJson from 'react18-json-view'
import { useSocket } from '../contexts/SocketContext'
import { logService } from '../services/api'

const LogViewer = () => {
  const { logs: liveLogs, connected } = useSocket()
  const [logs, setLogs] = useState([])
  const [filteredLogs, setFilteredLogs] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const [levelFilter, setLevelFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [selectedLog, setSelectedLog] = useState(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [expandedRows, setExpandedRows] = useState(new Set())
  
  const itemsPerPage = 50

  useEffect(() => {
    fetchLogs()
  }, [])

  useEffect(() => {
    // Merge live logs with fetched logs
    if (liveLogs.length > 0) {
      setLogs(prevLogs => {
        const newLogs = [...liveLogs, ...prevLogs]
        // Remove duplicates based on content and timestamp
        const uniqueLogs = newLogs.filter((log, index, self) => 
          index === self.findIndex(l => 
            l.raw_content === log.raw_content && l.timestamp === log.timestamp
          )
        )
        return uniqueLogs.slice(0, 1000) // Keep only last 1000 logs
      })
    }
  }, [liveLogs])

  useEffect(() => {
    filterLogs()
  }, [logs, searchTerm, levelFilter, sourceFilter])

  const fetchLogs = async () => {
    try {
      setLoading(true)
      const data = await logService.getLogs({ limit: 500 })
      setLogs(data)
    } catch (error) {
      console.error('Error fetching logs:', error)
    } finally {
      setLoading(false)
    }
  }

  const filterLogs = () => {
    let filtered = logs

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(log =>
        log.message?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        log.raw_content?.toLowerCase().includes(searchTerm.toLowerCase())
      )
    }

    // Filter by level
    if (levelFilter !== 'all') {
      filtered = filtered.filter(log => log.level === levelFilter)
    }

    // Filter by source
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(log => log.source === sourceFilter)
    }

    setFilteredLogs(filtered)
    setPage(1) // Reset to first page when filters change
  }

  const handleLogClick = (log) => {
    setSelectedLog(log)
    setDialogOpen(true)
  }

  const handleRowExpand = (index) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedRows(newExpanded)
  }

  const getLogLevelIcon = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return <ErrorIcon color="error" fontSize="small" />
      case 'warn':
      case 'warning':
        return <WarningIcon color="warning" fontSize="small" />
      case 'info':
        return <InfoIcon color="info" fontSize="small" />
      default:
        return <SuccessIcon color="success" fontSize="small" />
    }
  }

  const getLogLevelColor = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return 'error'
      case 'warn':
      case 'warning':
        return 'warning'
      case 'info':
        return 'info'
      default:
        return 'success'
    }
  }

  const getRowClass = (level) => {
    switch (level?.toLowerCase()) {
      case 'error':
        return 'log-entry-error'
      case 'warn':
      case 'warning':
        return 'log-entry-warn'
      case 'info':
        return 'log-entry-info'
      default:
        return ''
    }
  }

  // Get unique sources and levels for filters
  const uniqueSources = [...new Set(logs.map(log => log.source).filter(Boolean))]
  const uniqueLevels = [...new Set(logs.map(log => log.level).filter(Boolean))]

  // Pagination
  const paginatedLogs = useMemo(() => {
    const startIndex = (page - 1) * itemsPerPage
    return filteredLogs.slice(startIndex, startIndex + itemsPerPage)
  }, [filteredLogs, page, itemsPerPage])

  const totalPages = Math.ceil(filteredLogs.length / itemsPerPage)

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Log Viewer
      </Typography>

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Search logs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>

            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Level</InputLabel>
                <Select
                  value={levelFilter}
                  label="Level"
                  onChange={(e) => setLevelFilter(e.target.value)}
                >
                  <MenuItem value="all">All Levels</MenuItem>
                  {uniqueLevels.map(level => (
                    <MenuItem key={level} value={level}>{level}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Source</InputLabel>
                <Select
                  value={sourceFilter}
                  label="Source"
                  onChange={(e) => setSourceFilter(e.target.value)}
                >
                  <MenuItem value="all">All Sources</MenuItem>
                  {uniqueSources.map(source => (
                    <MenuItem key={source} value={source}>{source}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={4}>
              <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={fetchLogs}
                  disabled={loading}
                >
                  Refresh
                </Button>
                <Chip
                  icon={<FilterIcon />}
                  label={`${filteredLogs.length} logs`}
                  color="primary"
                  variant="outlined"
                />
                {connected && (
                  <Chip
                    label="Live"
                    color="success"
                    size="small"
                  />
                )}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} sx={{ maxHeight: '70vh' }}>
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell></TableCell>
                  <TableCell>Level</TableCell>
                  <TableCell>Source</TableCell>
                  <TableCell>Message</TableCell>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {paginatedLogs.map((log, index) => (
                  <>
                    <TableRow
                      key={index}
                      className={getRowClass(log.level)}
                      sx={{ cursor: 'pointer' }}
                      hover
                    >
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleRowExpand(index)}
                        >
                          {expandedRows.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {getLogLevelIcon(log.level)}
                          <Chip
                            label={log.level}
                            size="small"
                            color={getLogLevelColor(log.level)}
                            sx={{ ml: 1 }}
                          />
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={log.source}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            maxWidth: 400,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {log.message}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" color="textSecondary">
                          {format(new Date(log.timestamp), 'MMM dd, HH:mm:ss')}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => handleLogClick(log)}
                        >
                          Details
                        </Button>
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
                        <Collapse in={expandedRows.has(index)} timeout="auto" unmountOnExit>
                          <Box sx={{ margin: 1, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
                            <Typography variant="subtitle2" gutterBottom>
                              Raw Content:
                            </Typography>
                            <Typography
                              variant="body2"
                              component="pre"
                              sx={{
                                whiteSpace: 'pre-wrap',
                                fontFamily: 'monospace',
                                fontSize: '0.875rem',
                                backgroundColor: '#fff',
                                p: 1,
                                borderRadius: 1,
                                border: '1px solid #e0e0e0'
                              }}
                            >
                              {log.raw_content}
                            </Typography>
                            {log.file_path && (
                              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                                File: {log.file_path}
                              </Typography>
                            )}
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Pagination */}
          {totalPages > 1 && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Pagination
                count={totalPages}
                page={page}
                onChange={(e, newPage) => setPage(newPage)}
                color="primary"
              />
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Log Details Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Log Details
        </DialogTitle>
        <DialogContent>
          {selectedLog && (
            <Box>
              <ReactJson
                src={selectedLog}
                theme="rjv-default"
                collapsed={1}
                enableClipboard={true}
                displayDataTypes={false}
                displayObjectSize={false}
                indentWidth={2}
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default LogViewer 