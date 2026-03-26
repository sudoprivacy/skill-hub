-- Create skills table
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    author_id UUID NOT NULL,
    description TEXT,
    category VARCHAR(100),
    emoji VARCHAR(10),
    homepage VARCHAR(500),
    star_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Add indexes for better query performance
--    CONSTRAINT fk_author FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for frequently queried columns
CREATE INDEX idx_skills_name ON skills(name);
CREATE INDEX idx_skills_author_id ON skills(author_id);
CREATE INDEX idx_skills_category ON skills(category);
CREATE INDEX idx_skills_star_count ON skills(star_count DESC);
CREATE INDEX idx_skills_created_at ON skills(created_at DESC);

-- Create a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_skills_updated_at 
    BEFORE UPDATE ON skills 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing
INSERT INTO skills (id, name, display_name, author_id, description, category, emoji, homepage, star_count, created_at, updated_at) VALUES
    ('11111111-1111-1111-1111-111111111111', 'weather', 'Weather Forecast Expert', '00000000-0000-0000-0000-000000000001', 'A skill that provides accurate weather forecasts and climate information.', 'AI/Vision', '🌤️', 'https://example.com/weather', 150, '2026-03-01 10:00:00+00', '2026-03-10 14:30:00+00'),
    ('22222222-2222-2222-2222-222222222222', 'translator', 'Multi-language Translator', '00000000-0000-0000-0000-000000000002', 'Translate text between multiple languages with high accuracy.', 'Tools', '🌐', 'https://example.com/translator', 89, '2026-03-05 09:15:00+00', '2026-03-12 11:45:00+00'),
    ('33333333-3333-3333-3333-333333333333', 'code-review', 'Code Review Assistant', '00000000-0000-0000-0000-000000000003', 'Helps developers review code for bugs, security issues, and best practices.', 'Tools', '💻', 'https://example.com/code-review', 210, '2026-02-28 14:20:00+00', '2026-03-15 16:10:00+00'),
    ('44444444-4444-4444-4444-444444444444', 'fitness', 'Personal Fitness Coach', '00000000-0000-0000-0000-000000000004', 'Provides personalized workout plans and fitness advice.', 'Social', '💪', 'https://example.com/fitness', 75, '2026-03-10 08:45:00+00', '2026-03-17 09:30:00+00'),
    ('55555555-5555-5555-5555-555555555555', 'finance', 'Personal Finance Advisor', '00000000-0000-0000-0000-000000000005', 'Helps with budgeting, investment advice, and financial planning.', 'Tools', '💰', 'https://example.com/finance', 120, '2026-03-03 11:30:00+00', '2026-03-14 13:15:00+00');
