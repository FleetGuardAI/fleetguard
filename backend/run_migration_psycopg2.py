import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def split_sql(sql):
    statements = []
    current_statement = []
    in_string = False
    in_single_line_comment = False
    in_multi_line_comment = False
    i = 0
    while i < len(sql):
        c = sql[i]
        
        if in_single_line_comment:
            if c == '\n':
                in_single_line_comment = False
            current_statement.append(c)
            i += 1
            continue
            
        if in_multi_line_comment:
            if c == '*' and i + 1 < len(sql) and sql[i+1] == '/':
                in_multi_line_comment = False
                current_statement.append('*/')
                i += 2
            else:
                current_statement.append(c)
                i += 1
            continue
            
        if in_string:
            if c == "'":
                # Check for escaped quote ''
                if i + 1 < len(sql) and sql[i+1] == "'":
                    current_statement.append("''")
                    i += 2
                    continue
                else:
                    in_string = False
            current_statement.append(c)
            i += 1
            continue
            
        if c == '-' and i + 1 < len(sql) and sql[i+1] == '-':
            in_single_line_comment = True
            current_statement.append('--')
            i += 2
            continue
            
        if c == '/' and i + 1 < len(sql) and sql[i+1] == '*':
            in_multi_line_comment = True
            current_statement.append('/*')
            i += 2
            continue
            
        if c == "'":
            in_string = True
            current_statement.append(c)
            i += 1
            continue
            
        if c == ';':
            statements.append(''.join(current_statement).strip())
            current_statement = []
            i += 1
            continue
            
        current_statement.append(c)
        i += 1
        
    if current_statement:
        stmt = ''.join(current_statement).strip()
        if stmt:
            statements.append(stmt)
            
    return statements

def main():
    db_url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg", "postgresql").replace("ssl=require", "sslmode=require")
    
    with open('migration_utf8.sql', 'r', encoding='utf-8') as f:
        sql = f.read()
    
    sql = sql.replace('\ufeff', '')
    statements = split_sql(sql)
    
    print(f"Connecting to {db_url.split('@')[-1]}...")
    conn = psycopg2.connect(db_url)
    conn.autocommit = True
    cur = conn.cursor()
    
    print(f"Executing {len(statements)} statements...", flush=True)
    for i, stmt in enumerate(statements):
        if not stmt or stmt.upper().startswith('BEGIN') or stmt.upper().startswith('COMMIT'):
            continue
        print(f"[{i+1}/{len(statements)}] Executing: {stmt[:50].replace(chr(10), ' ')}...", flush=True)
        try:
            cur.execute(stmt)
        except Exception as e:
            err_msg = str(e)
            print(f"Error: {err_msg.strip()}", flush=True)
            if 'already exists' in err_msg or 'does not exist' in err_msg or 'already a constraint' in err_msg or 'multiple primary keys' in err_msg:
                print("Ignoring and continuing...", flush=True)
            else:
                raise
                
    print("Done!", flush=True)
    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
