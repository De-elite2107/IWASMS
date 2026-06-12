// IWASMS TypeScript interfaces

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'normal';
export type AlertStatus = 'open' | 'investigating' | 'resolved' | 'false_positive';

export interface SecurityEvent {
  id: string;
  timestamp: string;
  source_ip: string;
  destination_ip?: string;
  http_method: string;
  url: string;
  user_agent: string;
  attack_type: string;
  severity: Severity;
  is_attack: boolean;
  confidence_score: number;
  processing_latency_ms: number;
  web_application?: string;
  alert_status?: AlertStatus;
  created_at: string;
}

export interface SecurityEventDetail extends SecurityEvent {
  raw_request: Record<string, unknown>;
  predictions: ModelPrediction[];
  alert?: SecurityAlert;
}

export interface SecurityAlert {
  id: string;
  event_id: string;
  source_ip: string;
  attack_type: string;
  url: string;
  title: string;
  description: string;
  severity: Severity;
  status: AlertStatus;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  assigned_to?: string;
  assigned_to_username?: string;
  analyst_notes: string;
  automated_response_taken: string[];
}

export interface MLModel {
  id: string;
  name: string;
  version: string;
  is_active: boolean;
  accuracy: number;
  f1_score: number;
  auc_roc: number;
  false_positive_rate: number;
  trained_on_samples: number;
  training_duration_seconds: number;
  created_at: string;
}

export interface ModelPrediction {
  id: string;
  model_name: string;
  predicted_label: string;
  confidence: number;
  raw_probabilities: Record<string, number[]>;
  inference_time_ms: number;
  created_at: string;
}

export interface OverviewStats {
  active_alerts: number;
  events_last_24h: number;
  attacks_last_24h: number;
  normal_last_24h: number;
  detection_rate: number;
  false_positive_rate: number;
  avg_latency_ms: number;
  attack_type_distribution: { attack_type: string; count: number }[];
  severity_breakdown: Record<string, number>;
  top_attacking_ips: { source_ip: string; count: number }[];
  generated_at: string;
}

export interface TimelinePoint {
  hour: string;
  total: number;
  attacks: number;
  normal: number;
  detection_rate: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  meta: {
    count: number;
    next?: string;
    previous?: string;
    page: number;
    total_pages: number;
  };
  error: null | string;
}

export interface ApiResponse<T> {
  data: T;
  meta: Record<string, unknown>;
  error: null | string | Record<string, unknown>;
}

export interface User {
  id: string;
  username: string;
  email: string;
  is_staff: boolean;
  first_name: string;
  last_name: string;
}

export interface AuthState {
  user: User | null;
  access: string | null;
  refresh: string | null;
  isAuthenticated: boolean;
}
