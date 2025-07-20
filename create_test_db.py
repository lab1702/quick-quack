"""
Script to create a test DuckDB database with sample macros
"""
import duckdb
import os

def create_test_database():
    """Create a test database with sample macros"""
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Connect to database
    conn = duckdb.connect("data/database.duckdb")
    
    print("Creating test database with sample macros...")
    
    # Create some sample data
    conn.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER,
        name VARCHAR,
        department VARCHAR,
        salary DECIMAL,
        hire_date DATE
    )
    """)
    
    # Clear existing data and insert fresh data
    conn.execute("DELETE FROM employees")
    
    conn.execute("""
    INSERT INTO employees VALUES
    (1, 'Alice Johnson', 'Engineering', 75000, '2020-01-15'),
    (2, 'Bob Smith', 'Sales', 60000, '2019-03-22'),
    (3, 'Carol Davis', 'Engineering', 80000, '2021-06-10'),
    (4, 'David Wilson', 'Marketing', 55000, '2020-09-05'),
    (5, 'Eve Brown', 'Engineering', 85000, '2018-11-30')
    """)
    
    # Create scalar macros
    print("Creating scalar macros...")
    
    # Simple greeting macro
    conn.execute("""
    CREATE OR REPLACE MACRO greet(name) AS (
        'Hello, ' || name || '!'
    )
    """)
    
    # Calculate annual bonus macro
    conn.execute("""
    CREATE OR REPLACE MACRO calculate_bonus(salary, percentage) AS (
        salary * (percentage / 100.0)
    )
    """)
    
    # Years of service calculation
    conn.execute("""
    CREATE OR REPLACE MACRO years_of_service(hire_date) AS (
        EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM hire_date)
    )
    """)
    
    # Create table macros
    print("Creating table macros...")
    
    # Get employees by department
    conn.execute("""
    CREATE OR REPLACE MACRO employees_by_department(dept_name) AS TABLE (
        SELECT * FROM employees WHERE department = dept_name
    )
    """)
    
    # Get high earners
    conn.execute("""
    CREATE OR REPLACE MACRO high_earners(min_salary) AS TABLE (
        SELECT name, department, salary 
        FROM employees 
        WHERE salary >= min_salary
        ORDER BY salary DESC
    )
    """)
    
    # Employee summary statistics
    conn.execute("""
    CREATE OR REPLACE MACRO employee_summary() AS TABLE (
        SELECT 
            department,
            COUNT(*) as employee_count,
            AVG(salary) as avg_salary,
            MIN(salary) as min_salary,
            MAX(salary) as max_salary
        FROM employees
        GROUP BY department
        ORDER BY avg_salary DESC
    )
    """)
    
    # Create a more complex macro with multiple parameters
    conn.execute("""
    CREATE OR REPLACE MACRO salary_analysis(dept_name, min_years) AS TABLE (
        SELECT 
            name,
            salary,
            years_of_service(hire_date) as years_service,
            calculate_bonus(salary, 10) as annual_bonus
        FROM employees
        WHERE department = dept_name 
          AND years_of_service(hire_date) >= min_years
        ORDER BY salary DESC
    )
    """)
    
    # Test the macros
    print("\nTesting macros...")
    
    # Test scalar macros
    result = conn.execute("SELECT greet('World')").fetchone()
    print(f"greet('World'): {result[0]}")
    
    result = conn.execute("SELECT calculate_bonus(75000, 15)").fetchone()
    print(f"calculate_bonus(75000, 15): {result[0]}")
    
    # Test table macros
    result = conn.execute("SELECT * FROM employees_by_department('Engineering')").fetchall()
    print(f"employees_by_department('Engineering'): {len(result)} rows")
    
    result = conn.execute("SELECT * FROM high_earners(70000)").fetchall()
    print(f"high_earners(70000): {len(result)} rows")
    
    result = conn.execute("SELECT * FROM employee_summary()").fetchall()
    print(f"employee_summary(): {len(result)} departments")
    
    # List all macros including table macros
    print("\nAvailable macros:")
    macros = conn.execute("""
        SELECT function_name, parameters, parameter_types, return_type, macro_definition
        FROM duckdb_functions()
        WHERE function_type = 'macro' AND internal = false
        ORDER BY function_name
    """).fetchall()
    
    for macro in macros:
        macro_def = macro[4][:50] + "..." if len(macro[4]) > 50 else macro[4]
        print(f"  {macro[0]}({', '.join(macro[1])}) -> {macro[3]}")
        print(f"    Definition: {macro_def}")
    
    # Also check for table macros specifically
    print("\nTable macros:")
    table_macros = conn.execute("""
        SELECT function_name, parameters
        FROM duckdb_functions()
        WHERE function_type = 'macro' 
          AND internal = false
          AND (macro_definition LIKE '%TABLE%' OR macro_definition LIKE '%SELECT%')
        ORDER BY function_name
    """).fetchall()
    
    for macro in table_macros:
        print(f"  {macro[0]}({', '.join(macro[1])})")
    
    conn.close()
    print(f"\nTest database created successfully at data/database.duckdb")
    print(f"Found {len(macros)} macros")


if __name__ == "__main__":
    create_test_database()
