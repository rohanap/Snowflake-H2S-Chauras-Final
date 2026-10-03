USE ROLE SECURITYADMIN;

-- 1. Create the role for your read-only Streamlit viewers
CREATE ROLE streamlit_viewer_role;

USE ROLE ACCOUNTADMIN;

-- 2. Grant usage on the warehouse used to run the app
GRANT USAGE ON WAREHOUSE your_warehouse_name TO ROLE streamlit_viewer_role;

-- 3. Grant usage on the database and schema containing the app
GRANT USAGE ON DATABASE your_database_name TO ROLE streamlit_viewer_role;
GRANT USAGE ON SCHEMA your_database_name.your_schema_name TO ROLE streamlit_viewer_role;

-- 4. Grant read-only usage directly to the Streamlit app object
GRANT USAGE ON STREAMLIT your_database_name.your_schema_name.your_app_name TO ROLE streamlit_viewer_role;
