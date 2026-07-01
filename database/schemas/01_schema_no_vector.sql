-- Base To: схема БД без pgvector (локальная разработка на Windows)
-- AI Q&A и векторный поиск недоступны до установки pgvector

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===================== ENUMS =====================

CREATE TYPE content_status AS ENUM (
    'draft', 'pending_approval', 'published', 'archived'
);

CREATE TYPE maintenance_type AS ENUM (
    'annual', 'semi_annual', 'quarterly', 'monthly', 'weekly', 'daily'
);

CREATE TYPE ai_processing_status AS ENUM (
    'pending', 'processing', 'completed', 'failed'
);

CREATE TYPE ai_task_type AS ENUM (
    'document_parse', 'extract_maintenance', 'generate_instruction',
    'generate_course', 'generate_competencies', 'qa_search', 'reindex'
);

CREATE TYPE ai_task_status AS ENUM (
    'pending', 'processing', 'completed', 'failed', 'cancelled'
);

CREATE TYPE course_progress_status AS ENUM (
    'assigned', 'in_progress', 'completed', 'failed'
);

CREATE TYPE knowledge_source_type AS ENUM (
    'document', 'instruction', 'tech_card', 'course', 'brandbook'
);

CREATE TYPE custom_field_type AS ENUM (
    'text', 'number', 'date', 'select', 'boolean', 'multiselect'
);

CREATE TYPE user_role_code AS ENUM (
    'admin', 'park_owner', 'mentor', 'technician', 'hr'
);

-- ===================== СПРАВОЧНИКИ =====================

CREATE TABLE departments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(100),
    name        VARCHAR(255) NOT NULL,
    parent_id   UUID REFERENCES departments(id),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE roles (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        user_role_code NOT NULL UNIQUE,
    name        JSONB NOT NULL,  -- {"ru": "...", "en": "..."}
    permissions JSONB NOT NULL DEFAULT '[]',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE specializations (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        VARCHAR(50) NOT NULL UNIQUE,
    name        JSONB NOT NULL,
    description JSONB,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE custom_field_definitions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL,
    field_key   VARCHAR(100) NOT NULL,
    field_label JSONB NOT NULL,
    field_type  custom_field_type NOT NULL DEFAULT 'text',
    options     JSONB,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order  INT NOT NULL DEFAULT 0,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (entity_type, field_key)
);

-- ===================== ПОЛЬЗОВАТЕЛИ =====================

CREATE TABLE users (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id      VARCHAR(100),
    email            VARCHAR(255) NOT NULL UNIQUE,
    password_hash    VARCHAR(255),
    full_name        VARCHAR(255) NOT NULL,
    role_id          UUID NOT NULL REFERENCES roles(id),
    specialization_id UUID REFERENCES specializations(id),
    department_id    UUID REFERENCES departments(id),
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    custom_attributes JSONB NOT NULL DEFAULT '{}',
    last_sync_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_department ON users(department_id);
CREATE INDEX idx_users_role ON users(role_id);

-- ===================== ОБОРУДОВАНИЕ =====================

CREATE TABLE equipment (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name              VARCHAR(255) NOT NULL,
    serial_name       VARCHAR(255),
    description       TEXT,
    custom_attributes JSONB NOT NULL DEFAULT '{}',
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_by        UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_equipment_name ON equipment(name);
CREATE INDEX idx_equipment_custom ON equipment USING GIN (custom_attributes);

-- ===================== БРЕНДБУК =====================

CREATE TABLE brandbook_templates (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       VARCHAR(255) NOT NULL,
    template_type VARCHAR(50) NOT NULL,  -- instruction, course, tech_card
    file_path   VARCHAR(500) NOT NULL,
    version     INT NOT NULL DEFAULT 1,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_by  UUID REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===================== ДОКУМЕНТЫ =====================

CREATE TABLE documents (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id         UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    title                VARCHAR(500) NOT NULL,
    description          TEXT,
    file_path            VARCHAR(500),
    mime_type            VARCHAR(100),
    file_size            BIGINT,
    status               content_status NOT NULL DEFAULT 'draft',
    current_version_id   UUID,  -- FK added after versions table
    ai_processing_status ai_processing_status NOT NULL DEFAULT 'pending',
    custom_attributes    JSONB NOT NULL DEFAULT '{}',
    created_by           UUID REFERENCES users(id),
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_equipment ON documents(equipment_id);
CREATE INDEX idx_documents_status ON documents(equipment_id, status);

CREATE TABLE document_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number  INT NOT NULL,
    file_path       VARCHAR(500) NOT NULL,
    change_summary  TEXT,
    status          content_status NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES document_versions(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version_number)
);

ALTER TABLE documents
    ADD CONSTRAINT fk_documents_current_version
    FOREIGN KEY (current_version_id) REFERENCES document_versions(id);

CREATE TABLE document_version_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_id      UUID NOT NULL REFERENCES document_versions(id),
    action          VARCHAR(50) NOT NULL,  -- created, submitted, approved, archived, updated
    performed_by    UUID REFERENCES users(id),
    comment         TEXT,
    snapshot        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===================== ТЕХНОЛОГИЧЕСКИЕ КАРТЫ =====================

CREATE TABLE tech_cards (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id      UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    maintenance_type  maintenance_type NOT NULL,
    title             VARCHAR(500) NOT NULL,
    work_items        JSONB NOT NULL DEFAULT '[]',
    status            content_status NOT NULL DEFAULT 'draft',
    current_version_id UUID,
    source_document_id UUID REFERENCES documents(id),
    custom_attributes JSONB NOT NULL DEFAULT '{}',
    created_by        UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tech_cards_equipment ON tech_cards(equipment_id, maintenance_type);

CREATE TABLE tech_card_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tech_card_id    UUID NOT NULL REFERENCES tech_cards(id) ON DELETE CASCADE,
    version_number  INT NOT NULL,
    work_items      JSONB NOT NULL,
    change_summary  TEXT,
    status          content_status NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES tech_card_versions(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tech_card_id, version_number)
);

-- ===================== КАЛЕНДАРЬ ТО =====================

CREATE TABLE maintenance_calendar (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id    UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    tech_card_id    UUID NOT NULL REFERENCES tech_cards(id) ON DELETE CASCADE,
    scheduled_date  DATE NOT NULL,
    maintenance_type maintenance_type NOT NULL,
    title           VARCHAR(500) NOT NULL,
    is_completed    BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    completed_by    UUID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (equipment_id, tech_card_id, scheduled_date)
);

CREATE INDEX idx_calendar_date ON maintenance_calendar(scheduled_date);
CREATE INDEX idx_calendar_equipment_date ON maintenance_calendar(equipment_id, scheduled_date);

-- ===================== ИНСТРУКЦИИ ТО =====================

CREATE TABLE work_instructions (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id      UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    tech_card_id      UUID REFERENCES tech_cards(id),
    title             VARCHAR(500) NOT NULL,
    purpose           TEXT,
    scope             TEXT,
    status            content_status NOT NULL DEFAULT 'draft',
    current_version_id UUID,
    custom_attributes JSONB NOT NULL DEFAULT '{}',
    created_by        UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_instructions_equipment ON work_instructions(equipment_id, status);

CREATE TABLE instruction_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instruction_id  UUID NOT NULL REFERENCES work_instructions(id) ON DELETE CASCADE,
    version_number  INT NOT NULL,
    purpose         TEXT,
    scope           TEXT,
    safety_requirements TEXT,
    control_operations  TEXT,
    change_summary  TEXT,
    status          content_status NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES instruction_versions(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (instruction_id, version_number)
);

ALTER TABLE work_instructions
    ADD CONSTRAINT fk_instructions_current_version
    FOREIGN KEY (current_version_id) REFERENCES instruction_versions(id);

CREATE TABLE instruction_steps (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instruction_version_id  UUID NOT NULL REFERENCES instruction_versions(id) ON DELETE CASCADE,
    step_number             INT NOT NULL,
    title                   TEXT NOT NULL,
    description             TEXT,
    safety_notes            TEXT,
    tools                   JSONB NOT NULL DEFAULT '[]',
    consumables             JSONB NOT NULL DEFAULT '[]',
    control_params          JSONB NOT NULL DEFAULT '{}',
    UNIQUE (instruction_version_id, step_number)
);

CREATE TABLE step_key_points (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id     UUID NOT NULL REFERENCES instruction_steps(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE step_reasons (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id     UUID NOT NULL REFERENCES instruction_steps(id) ON DELETE CASCADE,
    content     TEXT NOT NULL,
    sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE step_media (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    step_id     UUID NOT NULL REFERENCES instruction_steps(id) ON DELETE CASCADE,
    file_path   VARCHAR(500) NOT NULL,
    media_type  VARCHAR(50) NOT NULL,  -- image, diagram, video
    caption     TEXT,
    sort_order  INT NOT NULL DEFAULT 0
);

CREATE TABLE instruction_version_history (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instruction_id  UUID NOT NULL REFERENCES work_instructions(id) ON DELETE CASCADE,
    version_id      UUID NOT NULL REFERENCES instruction_versions(id),
    action          VARCHAR(50) NOT NULL,
    performed_by    UUID REFERENCES users(id),
    comment         TEXT,
    snapshot        JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ===================== TWI-КУРСЫ =====================

CREATE TABLE twi_courses (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instruction_id    UUID NOT NULL REFERENCES work_instructions(id),
    equipment_id      UUID NOT NULL REFERENCES equipment(id),
    title             VARCHAR(500) NOT NULL,
    content           JSONB NOT NULL DEFAULT '{}',
    -- preparation, typical_mistakes, self_check_questions, reinforcement_tips, slides
    status            content_status NOT NULL DEFAULT 'draft',
    current_version_id UUID,
    created_by        UUID REFERENCES users(id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE course_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id       UUID NOT NULL REFERENCES twi_courses(id) ON DELETE CASCADE,
    version_number  INT NOT NULL,
    content         JSONB NOT NULL,
    status          content_status NOT NULL DEFAULT 'draft',
    parent_version_id UUID REFERENCES course_versions(id),
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (course_id, version_number)
);

CREATE TABLE course_assignments (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id   UUID NOT NULL REFERENCES twi_courses(id) ON DELETE CASCADE,
    user_id     UUID NOT NULL REFERENCES users(id),
    status      course_progress_status NOT NULL DEFAULT 'assigned',
    assigned_by UUID REFERENCES users(id),
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    score       NUMERIC(5,2),
    notes       TEXT,
    UNIQUE (course_id, user_id)
);

CREATE INDEX idx_course_assignments_user ON course_assignments(user_id, status);

-- ===================== КОМПЕТЕНЦИИ =====================

CREATE TABLE competencies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code        VARCHAR(50) NOT NULL UNIQUE,
    name        JSONB NOT NULL,
    description JSONB,
    category    VARCHAR(100),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE skills (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    competency_id   UUID NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,
    code            VARCHAR(50) NOT NULL,
    name            JSONB NOT NULL,
    description     JSONB,
    sort_order      INT NOT NULL DEFAULT 0,
    UNIQUE (competency_id, code)
);

CREATE TABLE competency_levels (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    level_value INT NOT NULL UNIQUE,
    name        JSONB NOT NULL,
    description JSONB
);

CREATE TABLE equipment_competencies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id    UUID NOT NULL REFERENCES equipment(id) ON DELETE CASCADE,
    competency_id   UUID NOT NULL REFERENCES competencies(id) ON DELETE CASCADE,
    required_level  INT NOT NULL DEFAULT 1,
    instruction_id  UUID REFERENCES work_instructions(id),
    UNIQUE (equipment_id, competency_id)
);

CREATE TABLE user_competencies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill_id        UUID NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
    level_value     INT NOT NULL DEFAULT 0,
    assessed_by     UUID REFERENCES users(id),
    assessed_at     TIMESTAMPTZ,
    valid_until     DATE,
    notes           TEXT,
    UNIQUE (user_id, skill_id)
);

CREATE INDEX idx_user_competencies_user ON user_competencies(user_id);

-- ===================== ВЕКТОРНАЯ БЗ / Q&A =====================

CREATE TABLE knowledge_chunks (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    equipment_id UUID REFERENCES equipment(id) ON DELETE SET NULL,
    source_type knowledge_source_type NOT NULL,
    source_id   UUID NOT NULL,
    chunk_index INT NOT NULL DEFAULT 0,
    content     TEXT NOT NULL,
    embedding   REAL[],
    metadata    JSONB NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_knowledge_equipment ON knowledge_chunks(equipment_id);
CREATE INDEX idx_knowledge_source ON knowledge_chunks(source_type, source_id);
-- HNSW index for vector search (create after data load for better performance)
-- CREATE INDEX idx_knowledge_embedding ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);

-- ===================== AI ЗАДАЧИ =====================

CREATE TABLE ai_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_type       ai_task_type NOT NULL,
    status          ai_task_status NOT NULL DEFAULT 'pending',
    equipment_id    UUID REFERENCES equipment(id),
    source_type     VARCHAR(50),
    source_id       UUID,
    input_payload   JSONB NOT NULL DEFAULT '{}',
    result_payload  JSONB,
    error_message   TEXT,
    celery_task_id  VARCHAR(255),
    created_by      UUID REFERENCES users(id),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ai_tasks_status ON ai_tasks(status);
CREATE INDEX idx_ai_tasks_source ON ai_tasks(source_type, source_id);

-- ===================== HR СИНХРОНИЗАЦИЯ =====================

CREATE TABLE hr_sync_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sync_type       VARCHAR(50) NOT NULL,  -- full, incremental, webhook
    status          VARCHAR(20) NOT NULL,  -- success, partial, failed
    records_created INT NOT NULL DEFAULT 0,
    records_updated INT NOT NULL DEFAULT 0,
    records_failed  INT NOT NULL DEFAULT 0,
    error_details   JSONB,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ===================== АУДИТ =====================

CREATE TABLE audit_log (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id),
    action      VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id   UUID,
    old_values  JSONB,
    new_values  JSONB,
    ip_address  INET,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_created ON audit_log(created_at);
