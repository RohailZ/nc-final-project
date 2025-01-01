# Dimensional Transformers: NC Final Project

 ## Overview

This project is a data engineering solution that extracts, transforms, and loads (ETL) data from a PostgreSQL database hosted on AWS RDS into a data warehouse.  This project automates data workflows using AWS services and showcases skills in Python, database modeling, CI/CD automation, good operational practices and Agile methodologies. It adheres to the Minimum Viable Product (MVP) requirements, providing a solid foundation for extensions and enhancements.

---

## Features

 ### Minimum Viable Product (MVP)
#### ETL Workflow
##### 1. Data Extraction:
   - Python application (Lambda function) extracts data from a source PostgreSQL database hosted on AWS RDS.
   - Extracted data is saved in Parquet format to an immutable "ingestion" S3 bucket.
   - Automation through AWS EventBridge ensures regular scheduling.
   - Logging and monitoring are handled via CloudWatch, with email alerts for failures.
##### 2. Data Transformation:
  - Python application (Lambda function) processes data from the "ingestion" bucket, transforming it to align with the target warehouse schema.
 - Trasformed data is saved in Parquet format to a "processed" S3 bucket.
 - Includes logging, monitoring, and error alerting.
##### 3. Data Loading:
 - Python application (Lambda function) loads the transformed data from the "processed" S3 bucket into a PostgreSQL data warehouse using SQLAlchemy
 - Fact and dimension tables are created and updated as per schema requirements.
 - Includes logging, monitoring, and error alerting.
#### Visualization
 * Tableau dashboard connects directly to the data warehouse to provide actionable insights.
#### Security & Quality:
 * Credentials managed using AWS Secrets Manager.
 * Python applications are PEP8-compliant, tested with Pytest, and scanned for vulnerabilities using Bandit and Safety.
 * Test coverage exceeds 80%.
#### Automation:
 * Infrastructure deployed using Terraform.
 * CI/CD pipelines configured with GitHub Actions for seamless deployments and testing.
---
### Project Structure
### Infrastructure
 **AWS Services:**
- S3 for data storage.
- CloudWatch for logging and alerting.
- Lambda for Python-based ETL processes.
- PostgreSQL RDS for the source database and the warehouse.
- Secrets Manager for secure credential management.

**Terraform:**
  - Automates creation of Lambda functions, S3 buckets, IAM roles, and other resources.

**Data Buckets**
1. **Ingestion S3 Bucket:**
   - Stores raw data ingested from the `totesys` database.
   - Organized and immutable to maintain data integrity
2. **Processed S3 Bucket:**
   - Stores transformed data conforming to the data warehouse schema.
  
#### Data Warehouse Schema
- **Fact Table:** `fact_sales_order`
- **Dimension Tables:** `dim_staff`, `dim_location`, `dim_design`, `dim_date`, `dim_currency`, `dim_counterparty`
 ### CI/CD Pipeline
#### GitHub Actions Workflow
1. **Run Tests:** Installs dependencies, lints, and executes tests.
2. **Deploy Infrastructure:** Configures Terraform to deploy necessary AWS resources.
3. **Reset Secrets:** Sets up secrets and triggers the first ETL job.
4. **Deploy Lambda:** Updates Lambda functions for ETL processes.
---
### Setup Steps
1. Clone the repository
2. Configure AWS credentials:
   Add credentials as GitHib Secrets for CI/CD automation.
3. Create Virtual Environment
 ```make create-environment```
4. Install Python dependencies:
 ```make dev-setup```
5. Run tests and checks:
   ```make run-checks```
6. Perform the initial data extraction and secret setup:
 ```make run-reset-secrets```
7. Deploy infrastructure:
 ```terraform init```
 ```terraform apply -auto-approve```
8. Trigger ETL jobs: Jobs run automatically based on scheduled events or S3 bucket triggers.
### Testing
To run the full test suite:
```make run-checks```
## Future Enhancements
  - Expand the warehouse to include all `totesys` tables.
  - Ingest from external APIs for supplementary data.