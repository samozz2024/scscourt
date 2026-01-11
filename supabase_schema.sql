-- Create cases table
CREATE TABLE IF NOT EXISTS cases (
    case_number TEXT PRIMARY KEY,
    type TEXT,
    style TEXT,
    file_date TEXT,
    status TEXT,
    court_location TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create parties table
CREATE TABLE IF NOT EXISTS parties (
    id BIGSERIAL PRIMARY KEY,
    case_number TEXT NOT NULL REFERENCES cases(case_number) ON DELETE CASCADE,
    type TEXT,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    nick_name TEXT,
    business_name TEXT,
    full_name TEXT,
    is_defendant BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create attorneys table
CREATE TABLE IF NOT EXISTS attorneys (
    id BIGSERIAL PRIMARY KEY,
    case_number TEXT NOT NULL REFERENCES cases(case_number) ON DELETE CASCADE,
    first_name TEXT,
    middle_name TEXT,
    last_name TEXT,
    representing TEXT,
    bar_number TEXT,
    is_lead BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create hearings table
CREATE TABLE IF NOT EXISTS hearings (
    id BIGSERIAL PRIMARY KEY,
    case_number TEXT NOT NULL REFERENCES cases(case_number) ON DELETE CASCADE,
    hearing_id TEXT,
    calendar TEXT,
    type TEXT,
    date TEXT,
    time TEXT,
    hearing_result TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create documents table
CREATE TABLE IF NOT EXISTS documents (
    id BIGSERIAL PRIMARY KEY,
    case_number TEXT NOT NULL REFERENCES cases(case_number) ON DELETE CASCADE,
    document_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_parties_case_number ON parties(case_number);
CREATE INDEX IF NOT EXISTS idx_attorneys_case_number ON attorneys(case_number);
CREATE INDEX IF NOT EXISTS idx_hearings_case_number ON hearings(case_number);
CREATE INDEX IF NOT EXISTS idx_documents_case_number ON documents(case_number);
