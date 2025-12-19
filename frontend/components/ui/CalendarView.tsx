/**
 * Calendar View Component
 * Displays calendar events in month, week, or day view
 */

'use client'

import { useState } from 'react'
import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Clock, MapPin, Video } from 'lucide-react'
import { Button } from './Button'
import { Card } from './Card'

type ViewMode = 'month' | 'week' | 'day' | 'list'

interface CalendarEvent {
  id: string
  title: string
  start_time: string
  end_time: string
  description?: string
  location?: string
  is_virtual?: boolean
  video_link?: string
  status?: string
  attendee_emails?: string[]
}

interface CalendarViewProps {
  events: CalendarEvent[]
  onEventClick?: (event: CalendarEvent) => void
  onDateClick?: (date: Date) => void
}

export function CalendarView({ events, onEventClick, onDateClick }: CalendarViewProps) {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [viewMode, setViewMode] = useState<ViewMode>('month')

  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear()
    const month = date.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startingDayOfWeek = firstDay.getDay()

    const days: (Date | null)[] = []
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null)
    }
    
    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day))
    }
    
    return days
  }

  const getEventsForDate = (date: Date) => {
    if (!date) return []
    const dateStr = date.toISOString().split('T')[0]
    return events.filter(event => {
      const eventDate = new Date(event.start_time).toISOString().split('T')[0]
      return eventDate === dateStr
    })
  }

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev)
      if (direction === 'prev') {
        newDate.setMonth(prev.getMonth() - 1)
      } else {
        newDate.setMonth(prev.getMonth() + 1)
      }
      return newDate
    })
  }

  const navigateWeek = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev)
      const days = direction === 'prev' ? -7 : 7
      newDate.setDate(prev.getDate() + days)
      return newDate
    })
  }

  const navigateDay = (direction: 'prev' | 'next') => {
    setCurrentDate(prev => {
      const newDate = new Date(prev)
      const days = direction === 'prev' ? -1 : 1
      newDate.setDate(prev.getDate() + days)
      return newDate
    })
  }

  const goToToday = () => {
    setCurrentDate(new Date())
  }

  const formatMonthYear = (date: Date) => {
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  }

  const formatWeekRange = (date: Date) => {
    const startOfWeek = new Date(date)
    startOfWeek.setDate(date.getDate() - date.getDay())
    const endOfWeek = new Date(startOfWeek)
    endOfWeek.setDate(startOfWeek.getDate() + 6)
    
    return `${startOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`
  }

  const formatDay = (date: Date) => {
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
  }

  const isToday = (date: Date | null) => {
    if (!date) return false
    const today = new Date()
    return date.toDateString() === today.toDateString()
  }

  const isCurrentMonth = (date: Date | null) => {
    if (!date) return false
    return date.getMonth() === currentDate.getMonth() && date.getFullYear() === currentDate.getFullYear()
  }

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

  // Month View
  if (viewMode === 'month') {
    const days = getDaysInMonth(currentDate)
    
    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth('prev')}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white min-w-[200px] text-center">
              {formatMonthYear(currentDate)}
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateMonth('next')}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={goToToday}
            >
              Today
            </Button>
          </div>
          <div className="flex gap-2">
            {(['month', 'week', 'day', 'list'] as ViewMode[]).map((mode) => (
              <Button
                key={mode}
                variant={viewMode === mode ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {/* Calendar Grid */}
        <Card>
          <div className="p-4">
            {/* Week day headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {weekDays.map(day => (
                <div key={day} className="text-center text-sm font-semibold text-gray-600 dark:text-gray-400 py-2">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar days */}
            <div className="grid grid-cols-7 gap-1">
              {days.map((date, index) => {
                const dayEvents = getEventsForDate(date || new Date())
                const isTodayDate = isToday(date)
                const isCurrentMonthDate = isCurrentMonth(date)

                return (
                  <div
                    key={index}
                    className={`min-h-[100px] border border-gray-200 dark:border-gray-700 rounded-lg p-2 ${
                      isTodayDate
                        ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-300 dark:border-primary-700'
                        : isCurrentMonthDate
                        ? 'bg-white dark:bg-gray-800'
                        : 'bg-gray-50 dark:bg-gray-900/50'
                    } ${date ? 'cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700' : ''}`}
                    onClick={() => date && onDateClick && onDateClick(date)}
                  >
                    {date && (
                      <>
                        <div
                          className={`text-sm font-medium mb-1 ${
                            isTodayDate
                              ? 'text-primary-700 dark:text-primary-400'
                              : isCurrentMonthDate
                              ? 'text-gray-900 dark:text-white'
                              : 'text-gray-400 dark:text-gray-500'
                          }`}
                        >
                          {date.getDate()}
                        </div>
                        <div className="space-y-1">
                          {dayEvents.slice(0, 3).map(event => (
                            <div
                              key={event.id}
                              onClick={(e) => {
                                e.stopPropagation()
                                onEventClick && onEventClick(event)
                              }}
                              className="text-xs p-1 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 truncate cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/50"
                              title={event.title}
                            >
                              {new Date(event.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} {event.title}
                            </div>
                          ))}
                          {dayEvents.length > 3 && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              +{dayEvents.length - 3} more
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </Card>
      </div>
    )
  }

  // Week View
  if (viewMode === 'week') {
    const startOfWeek = new Date(currentDate)
    startOfWeek.setDate(currentDate.getDate() - currentDate.getDay())
    const weekDays = Array.from({ length: 7 }, (_, i) => {
      const date = new Date(startOfWeek)
      date.setDate(startOfWeek.getDate() + i)
      return date
    })

    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateWeek('prev')}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white min-w-[250px] text-center">
              {formatWeekRange(currentDate)}
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateWeek('next')}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={goToToday}
            >
              Today
            </Button>
          </div>
          <div className="flex gap-2">
            {(['month', 'week', 'day', 'list'] as ViewMode[]).map((mode) => (
              <Button
                key={mode}
                variant={viewMode === mode ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {/* Week Grid */}
        <Card>
          <div className="p-4">
            <div className="grid grid-cols-7 gap-4">
              {weekDays.map((date, index) => {
                const dayEvents = getEventsForDate(date)
                const isTodayDate = isToday(date)

                return (
                  <div
                    key={index}
                    className={`min-h-[400px] border rounded-lg p-3 ${
                      isTodayDate
                        ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-300 dark:border-primary-700'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <div className="mb-3">
                      <div className={`text-sm font-medium ${
                        isTodayDate
                          ? 'text-primary-700 dark:text-primary-400'
                          : 'text-gray-900 dark:text-white'
                      }`}>
                        {date.toLocaleDateString('en-US', { weekday: 'short' })}
                      </div>
                      <div className={`text-lg font-bold ${
                        isTodayDate
                          ? 'text-primary-700 dark:text-primary-400'
                          : 'text-gray-900 dark:text-white'
                      }`}>
                        {date.getDate()}
                      </div>
                    </div>
                    <div className="space-y-2">
                      {dayEvents.map(event => (
                        <div
                          key={event.id}
                          onClick={() => onEventClick && onEventClick(event)}
                          className="p-2 rounded bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 cursor-pointer hover:bg-blue-200 dark:hover:bg-blue-900/50"
                        >
                          <div className="text-xs font-medium truncate">{event.title}</div>
                          <div className="text-xs opacity-75">
                            {new Date(event.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </Card>
      </div>
    )
  }

  // Day View
  if (viewMode === 'day') {
    const dayEvents = getEventsForDate(currentDate)
    const isTodayDate = isToday(currentDate)

    return (
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateDay('prev')}
            >
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white min-w-[300px] text-center">
              {formatDay(currentDate)}
            </h2>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigateDay('next')}
            >
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={goToToday}
            >
              Today
            </Button>
          </div>
          <div className="flex gap-2">
            {(['month', 'week', 'day', 'list'] as ViewMode[]).map((mode) => (
              <Button
                key={mode}
                variant={viewMode === mode ? 'primary' : 'outline'}
                size="sm"
                onClick={() => setViewMode(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </Button>
            ))}
          </div>
        </div>

        {/* Day Events */}
        <Card>
          <div className="p-6">
            {dayEvents.length === 0 ? (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                No events scheduled for this day
              </div>
            ) : (
              <div className="space-y-4">
                {dayEvents
                  .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                  .map(event => (
                    <div
                      key={event.id}
                      onClick={() => onEventClick && onEventClick(event)}
                      className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                            {event.title}
                          </h3>
                          <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                            <div className="flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {new Date(event.start_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} - {new Date(event.end_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                            </div>
                            {event.location && (
                              <div className="flex items-center gap-1">
                                {event.is_virtual ? (
                                  <Video className="w-4 h-4" />
                                ) : (
                                  <MapPin className="w-4 h-4" />
                                )}
                                {event.location}
                              </div>
                            )}
                          </div>
                          {event.description && (
                            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                              {event.description}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </Card>
      </div>
    )
  }

  // List View (default fallback)
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-end gap-2">
        {(['month', 'week', 'day', 'list'] as ViewMode[]).map((mode) => (
          <Button
            key={mode}
            variant={viewMode === mode ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setViewMode(mode)}
          >
            {mode.charAt(0).toUpperCase() + mode.slice(1)}
          </Button>
        ))}
      </div>
      <Card>
        <div className="p-6">
          {events.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <CalendarIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p>No events scheduled</p>
            </div>
          ) : (
            <div className="space-y-4">
              {events
                .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
                .map(event => (
                  <div
                    key={event.id}
                    onClick={() => onEventClick && onEventClick(event)}
                    className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                          {event.title}
                        </h3>
                        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {new Date(event.start_time).toLocaleString('en-US', { 
                              month: 'short', 
                              day: 'numeric', 
                              hour: 'numeric', 
                              minute: '2-digit' 
                            })} - {new Date(event.end_time).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}
                          </div>
                          {event.location && (
                            <div className="flex items-center gap-1">
                              {event.is_virtual ? (
                                <Video className="w-4 h-4" />
                              ) : (
                                <MapPin className="w-4 h-4" />
                              )}
                              {event.location}
                            </div>
                          )}
                        </div>
                        {event.description && (
                          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                            {event.description}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          )}
        </div>
      </Card>
    </div>
  )
}

