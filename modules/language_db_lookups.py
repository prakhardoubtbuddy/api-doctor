# Helper lookups for language, framework, db, and signals detection
LANGUAGE_EXTENSIONS = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript', '.rb': 'ruby', '.go': 'go', '.java': 'java', '.php': 'php', '.cs': 'csharp', '.rs': 'rust',
}
SKIP_DIRS = {'.git', 'node_modules', 'vendor', 'dist', 'build', '__pycache__', '.next', 'venv', '.venv', 'coverage', 'target'}
PACK_MANAGERS = [ ('package.json', 'npm'), ('requirements.txt', 'pip'), ('pyproject.toml', 'pip'), ('Pipfile', 'pipenv') ]
FRAMEWORKS = {
    'package.json': {
        'express': 'express', 'fastify': 'fastify', 'koa': 'koa', 'next': 'next', 'react': 'react', 'vue': 'vue', '@angular/core': 'angular', '@nestjs/core': 'nestjs',
    },
    'requirements.txt': {'flask': 'flask', 'django': 'django', 'fastapi': 'fastapi', 'tornado': 'tornado'}
}
DB_DEPS = {
    'package.json': {'pg': 'postgres', 'mysql': 'mysql', 'mysql2': 'mysql', 'mongoose': 'mongodb', 'redis': 'redis', 'ioredis': 'redis', 'sequelize': 'sql-orm', 'typeorm': 'sql-orm', 'prisma': 'sql-orm'},
    'requirements.txt': {'psycopg2': 'postgres', 'asyncpg': 'postgres', 'pymongo': 'mongodb', 'mysql': 'mysql', 'redis': 'redis', 'sqlalchemy': 'sql-orm'},
    'pyproject.toml': {'sqlalchemy': 'sql-orm', 'psycopg2': 'postgres', 'fastapi': 'fastapi'},
}
LEGACY_SIGNALS = [
    {'pattern': 'angular.module(', 'signal': 'AngularJS 1.x — EOL Jan 2022', 'weight': 40},
    {'pattern': 'python_requires.*>=.*2', 'signal': 'Python 2 requirement', 'weight': 30},
    {'pattern': 'mysql_query(', 'signal': 'Deprecated PHP mysql_* API', 'weight': 30},
    {'pattern': "require('request')", 'signal': "Deprecated 'request' npm package", 'weight': 10},
    {'pattern': 'componentWillMount', 'signal': 'Deprecated React lifecycle', 'weight': 8},
    {'pattern': 'componentWillReceiveProps', 'signal': 'Deprecated React lifecycle', 'weight': 8},
]
