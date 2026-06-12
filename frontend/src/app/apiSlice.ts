import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'
import type { RootState } from './store'
import type {
  ApiResponse,
  PaginatedResponse,
  OverviewStats,
  TimelinePoint,
  SecurityEvent,
  SecurityEventDetail,
  SecurityAlert,
  MLModel,
} from '../types'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = (getState() as RootState).auth.access
      if (token) {
        headers.set('Authorization', `Bearer ${token}`)
      }
      return headers
    },
  }),
  tagTypes: ['Events', 'Alerts', 'Models', 'Stats'],
  endpoints: (builder) => ({
    // Auth
    login: builder.mutation<
      ApiResponse<{ access: string; refresh: string; user: { id: string; username: string; email: string; is_staff: boolean; first_name: string; last_name: string } }>,
      { username: string; password: string }
    >({
      query: (credentials) => ({
        url: '/auth/login/',
        method: 'POST',
        body: credentials,
      }),
    }),

    // Stats
    getOverviewStats: builder.query<ApiResponse<OverviewStats>, void>({
      query: () => '/stats/overview/',
      providesTags: ['Stats'],
    }),

    getThreatTimeline: builder.query<
      ApiResponse<{ timeline: TimelinePoint[]; hours: number }>,
      { hours?: number }
    >({
      query: ({ hours = 24 } = {}) => `/stats/timeline/?hours=${hours}`,
      providesTags: ['Stats'],
    }),

    // Events
    getEvents: builder.query<
      PaginatedResponse<SecurityEvent>,
      {
        page?: number
        page_size?: number
        severity?: string
        is_attack?: boolean
        attack_type?: string
        source_ip?: string
        search?: string
        ordering?: string
      }
    >({
      query: (params = {}) => {
        const searchParams = new URLSearchParams()
        Object.entries(params).forEach(([k, v]) => {
          if (v !== undefined && v !== null && v !== '') {
            searchParams.set(k, String(v))
          }
        })
        return `/events/?${searchParams.toString()}`
      },
      providesTags: ['Events'],
    }),

    getEventDetail: builder.query<ApiResponse<SecurityEventDetail>, string>({
      query: (id) => `/events/${id}/`,
      providesTags: (_result, _error, id) => [{ type: 'Events', id }],
    }),

    classifyRequest: builder.mutation<
      ApiResponse<SecurityEvent>,
      Record<string, unknown>
    >({
      query: (body) => ({
        url: '/events/classify/',
        method: 'POST',
        body,
      }),
      invalidatesTags: ['Events', 'Alerts', 'Stats'],
    }),

    // Alerts
    getAlerts: builder.query<
      PaginatedResponse<SecurityAlert>,
      { page?: number; status?: string; severity?: string }
    >({
      query: (params = {}) => {
        const searchParams = new URLSearchParams()
        Object.entries(params).forEach(([k, v]) => {
          if (v !== undefined && v !== null && v !== '') searchParams.set(k, String(v))
        })
        return `/alerts/?${searchParams.toString()}`
      },
      providesTags: ['Alerts'],
    }),

    resolveAlert: builder.mutation<ApiResponse<SecurityAlert>, { id: string; notes?: string }>({
      query: ({ id, notes }) => ({
        url: `/alerts/${id}/resolve/`,
        method: 'POST',
        body: { notes: notes || '' },
      }),
      invalidatesTags: ['Alerts', 'Stats'],
    }),

    markFalsePositive: builder.mutation<ApiResponse<SecurityAlert>, { id: string; notes?: string }>({
      query: ({ id, notes }) => ({
        url: `/alerts/${id}/false-positive/`,
        method: 'POST',
        body: { notes: notes || '' },
      }),
      invalidatesTags: ['Alerts', 'Stats'],
    }),

    // Models
    getModels: builder.query<ApiResponse<MLModel[]>, void>({
      query: () => '/models/',
      providesTags: ['Models'],
    }),

    retrainModel: builder.mutation<ApiResponse<{ message: string }>, string>({
      query: (id) => ({
        url: `/models/${id}/retrain/`,
        method: 'POST',
      }),
      invalidatesTags: ['Models'],
    }),

    // Export
    exportEvents: builder.query<Blob, { format: string; hours?: number; severity?: string; is_attack?: string }>({
      query: ({ format = 'json', hours = 24, severity, is_attack }) => {
        const params = new URLSearchParams({ format, hours: String(hours) })
        if (severity) params.set('severity', severity)
        if (is_attack) params.set('is_attack', is_attack)
        return `/events/export/?${params.toString()}`
      },
    }),
  }),
})

export const {
  useLoginMutation,
  useGetOverviewStatsQuery,
  useGetThreatTimelineQuery,
  useGetEventsQuery,
  useGetEventDetailQuery,
  useClassifyRequestMutation,
  useGetAlertsQuery,
  useResolveAlertMutation,
  useMarkFalsePositiveMutation,
  useGetModelsQuery,
  useRetrainModelMutation,
} = apiSlice
