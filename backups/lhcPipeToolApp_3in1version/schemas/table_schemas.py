"""데이터베이스 테이블 스키마 정의"""

TABLES = {
    'projects': """
        CREATE TABLE projects (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            path VARCHAR(500),
            description BLOB SUB_TYPE TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    
    'sequences': """
        CREATE TABLE sequences (
            id INTEGER NOT NULL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description BLOB SUB_TYPE TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """,
    
    'shots': """
        CREATE TABLE shots (
            id INTEGER NOT NULL PRIMARY KEY,
            sequence_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            description BLOB SUB_TYPE TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE
        )
    """,
    
    'versions': """
        CREATE TABLE versions (
            id INTEGER NOT NULL PRIMARY KEY,
            version_type VARCHAR(20) NOT NULL,  -- 'project', 'sequence', 'shot'
            version_number INTEGER NOT NULL,
            worker_id INTEGER,
            project_id INTEGER,
            sequence_id INTEGER,
            shot_id INTEGER,
            file_path VARCHAR(500),
            preview_path VARCHAR(500),
            render_path VARCHAR(500),
            comment BLOB SUB_TYPE TEXT,
            is_latest BOOLEAN DEFAULT TRUE,
            status VARCHAR(50) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (worker_id) REFERENCES workers(id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (sequence_id) REFERENCES sequences(id) ON DELETE CASCADE,
            FOREIGN KEY (shot_id) REFERENCES shots(id) ON DELETE CASCADE
        )
    """,

    'workers': """
        CREATE TABLE workers (
            id INTEGER NOT NULL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            department VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    
    'settings': """
        CREATE TABLE settings (
            setting_key VARCHAR(100) NOT NULL PRIMARY KEY,
            setting_value VARCHAR(500) NOT NULL,
            description BLOB SUB_TYPE 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
}