// Type definitions for the SquiidWiki application

export interface Member {
  id: number;
  name: string;
  set_id: number;
  set_name?: string;
  status: 'active' | 'locked_up' | 'deceased';
  locked_up_date?: string;
  release_date?: string;
  death_date?: string;
  created_at: string;
  updated_at: string;
}

export interface Set {
  id: number;
  name: string;
  description: string;
  location: string;
  founded_date: string;
  created_at: string;
  updated_at: string;
  members_count?: number;
}

export interface Alliance {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
  sets: Array<{
    id: number;
    name: string;
  }>;
}

export interface Event {
  id: number;
  title: string;
  description: string;
  date: string;
  type: 'general' | 'murder' | 'shooting' | 'assist';
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export interface FormValidationRules {
  [field: string]: {
    required?: boolean;
    minLength?: number;
    maxLength?: number;
    pattern?: RegExp;
    validate?: (value: any) => boolean;
    message?: string;
  };
} 