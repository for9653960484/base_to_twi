export type ContentStatus = 'draft' | 'pending_approval' | 'published' | 'archived';

export type MaintenanceType =
  | 'annual'
  | 'semi_annual'
  | 'quarterly'
  | 'monthly'
  | 'weekly'
  | 'daily';

export type AIProcessingStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Equipment {
  id: string;
  name: string;
  serial_name?: string;
  description?: string;
  custom_attributes: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Document {
  id: string;
  equipment_id: string;
  equipment_name?: string;
  title: string;
  description?: string;
  file_path?: string;
  mime_type?: string;
  file_size?: number;
  status: ContentStatus;
  ai_processing_status: AIProcessingStatus;
  current_version_number?: number;
  custom_attributes: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
}

export interface InstructionStep {
  step_number: number;
  title: string;
  description?: string;
  safety_notes?: string;
  tools: string[];
  key_points: { content: string }[];
  reasons: { content: string }[];
  media: { file_path: string; caption?: string }[];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface KnowledgeSource {
  source_type: string;
  source_id: string;
  title: string;
  excerpt: string;
  relevance_score: number;
}

export interface KnowledgeSearchResponse {
  answer: string;
  sources: KnowledgeSource[];
  equipment_id?: string;
}

export interface TechCardWorkItem {
  order: number;
  description: string;
  tools: string[];
  safety: string[];
  control_params: Record<string, unknown>;
}

export interface TechCard {
  id: string;
  equipment_id: string;
  equipment_name?: string;
  maintenance_type: MaintenanceType;
  title: string;
  work_items: TechCardWorkItem[];
  status: ContentStatus;
  created_at: string;
  updated_at?: string;
}
