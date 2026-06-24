-- Начальные данные: роли, уровни компетенций

INSERT INTO roles (code, name, permissions) VALUES
    ('admin', '{"ru": "Администратор", "en": "Administrator"}', '["*"]'),
    ('park_owner', '{"ru": "Владелец парка", "en": "Park Owner"}', '["equipment:*", "documents:approve", "instructions:approve", "courses:*", "competencies:read"]'),
    ('mentor', '{"ru": "Наставник", "en": "Mentor"}', '["equipment:read", "documents:write", "instructions:write", "courses:write", "competencies:assess"]'),
    ('technician', '{"ru": "Техник", "en": "Technician"}', '["equipment:read", "documents:read", "instructions:read", "courses:take"]'),
    ('hr', '{"ru": "HR", "en": "HR"}', '["users:read", "hr:sync", "competencies:read", "competencies:reports"]');

INSERT INTO competency_levels (level_value, name, description) VALUES
    (0, '{"ru": "Не владеет", "en": "No skill"}', '{"ru": "Навык отсутствует", "en": "Skill not present"}'),
    (1, '{"ru": "Начальный", "en": "Beginner"}', '{"ru": "Требуется постоянный контроль", "en": "Requires constant supervision"}'),
    (2, '{"ru": "Базовый", "en": "Basic"}', '{"ru": "Выполняет под руководством", "en": "Performs with guidance"}'),
    (3, '{"ru": "Уверенный", "en": "Proficient"}', '{"ru": "Выполняет самостоятельно", "en": "Performs independently"}'),
    (4, '{"ru": "Продвинутый", "en": "Advanced"}', '{"ru": "Может обучать других", "en": "Can train others"}'),
    (5, '{"ru": "Эксперт", "en": "Expert"}', '{"ru": "Экспертный уровень, наставник", "en": "Expert level, mentor"}');

INSERT INTO specializations (code, name, description) VALUES
    ('mechanic', '{"ru": "Механик", "en": "Mechanic"}', '{"ru": "Механическое обслуживание", "en": "Mechanical maintenance"}'),
    ('electrician', '{"ru": "Электрик", "en": "Electrician"}', '{"ru": "Электротехническое обслуживание", "en": "Electrical maintenance"}'),
    ('operator', '{"ru": "Оператор", "en": "Operator"}', '{"ru": "Эксплуатация аттракционов", "en": "Attraction operation"}');

-- Dev-пользователь для локальной разработки (совпадает с DEV_USER_ID в backend)
INSERT INTO users (id, email, full_name, role_id)
SELECT '00000000-0000-0000-0000-000000000001', 'dev@localhost', 'Dev Admin', id
FROM roles WHERE code = 'admin'
ON CONFLICT (email) DO NOTHING;
