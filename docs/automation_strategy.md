# Automation Strategy

## Overview

This document describes and example/proposal on how to automate the data pipeline using **Azure Data Factory (ADF)**. The goal is to run the entire pipeline automatically on a weekly schedule, without manual intervention.

**Pipeline Flow**:
```
Data Acquisition → Data Processing → Data Integration → Data Loading
```

It is scheduled to run every Sunday at 2:00 AM, ensuring refreshed and validated data is available for analysis by Monday morning.


## Why Azure Data Factory?

Azure Data Factory was selected as the orchestration tool because it integrates seamlessly with Azure Databricks, Azure Storage, and other Azure-native services. It provides a user-friendly visual interface for pipeline design, built-in scheduling and monitoring, and a serverless cost model—meaning costs are only incurred during execution.
Its strong integration, reliability, and scalability make it a natural and strong choice for this solution.

## Pipeline Architecture

### Pipeline Flow

The ADF pipeline runs 5 sequential activities:

```
Activity 1: Acquire Data
  → Fetch from EPA, NHTSA, DOE APIs
  → Output: data/raw/ (3 CSV files)

Activity 2: Process Data
  → Clean, validate, standardize
  → Output: data/processed/ (3 CSV files)

Activity 3: Integrate Data
  → Join EPA+NHTSA, EPA+DOE, EPA+NHTSA+DOE
  → Output: data/integrated/ (3 CSV files)

Activity 4: Load to Delta Lake
  → Create Delta tables in Databricks
  → Output: 3 tables in automotive_data.analytics

Activity 5: Validate
  → Check row counts, data quality
  → Alert on failures
```

Each activity depends on the previous one succeeding. If any step fails, the pipeline stops and sends an alert.

## Pipeline Components

### 1. Linked Services

Linked services are connections to external resources. We need:

**Azure Databricks Linked Service**:
- **Purpose**: Connect to Databricks workspace to run notebooks
- **Authentication**: Azure Key Vault for access token
- **Configuration**:
  - Workspace URL: `https://dbc-a1b2c3d4-e5f6.cloud.databricks.com`
  - Cluster: Auto-create job cluster (to save costs, because the cluster only runs during the pipeline execution and terminates after, instead of running 24/7)

**Azure Data Lake Storage Gen2 Linked Service**:
- **Purpose**: Read/write CSV files from storage. Stores raw, processed and integrated datasets, with authentication handled through Managed Identity.
- **Authentication**: Managed Identity (secure, no passwords)
- **Configuration**:
  - Account Name: `automotivestorage`
  - Container: `datalake`

**Azure Key Vault Linked Service**:
- **Purpose**: Securely store secrets (API keys, tokens)
- **Configuration**:
  - Store NREL API key for DOE data
  - Store Databricks access token

### 2. Datasets

Datasets define where data is stored:

- **Raw Data**: `data/raw/*.csv` in Azure Storage
- **Processed Data**: `data/processed/*.csv` in Azure Storage
- **Integrated Data**: `data/integrated/*.csv` in Azure Storage

### 3. Pipeline Activities

All activities run Databricks notebooks sequentially:

| Activity | Notebook | Timeout | Retry | Notes |
|----------|----------|---------|-------|-------|
| Acquire Data | `notebooks/acquire_data.ipynb` | 30 min | 2x | Retry twice for API failures |
| Process Data | `notebooks/process_data.ipynb` | 20 min | 1x | - |
| Integrate Data | `notebooks/integrate_data.ipynb` | 15 min | 1x | - |
| Load to Delta | `notebooks/load_data.ipynb` | 20 min | 1x | - |
| Validate | `notebooks/validate_data.ipynb` | 10 min | 0x | Email alert on failure |

Each activity waits for the previous one to succeed before starting.

## Schedule Configuration Proposal
The pipeline is triggered weekly, every Sunday at 2:00 AM.
This timing minimizes interference with production systems, ensures data freshness for the start of the workweek and provides enough time to address potential issues before business hours.

If data freshness becomes a higher priority, the schedule can easily be updated to run daily or use event-based triggers that respond to new file uploads.

## Error Handling

### Retry Logic

Each activity automatically retries on failure:
- **Acquisition**: Retry 2 times (API might be temporarily down)
- **Processing**: Retry 1 time (usually code errors, not transient)
- **Integration**: Retry 1 time
- **Loading**: Retry 1 time

There's 5 minutes between retries.

### Failure Alerts
When the pipeline fails, SDF automaticallly sends an email alert with detailed error information, logs the event to **Azure Monitor** and marks the pieplun run as failed in ADF dashboard.

### Data Quality Checks

In the validation activity, check:
- Minimum expected row counts for each dataset
- Verification of key columns (should not be empty)
- Type checks for numeric columns

If validation fails, the issue is reported but not rolled back. Since each run performs a full refresh, the next successful run will overwrite any bad data.

## Monitoring and Logging

### Azure Data Factory Monitoring
Azure Data Factory provides a detailed monitoring interface that allows you to track the health and performance of the pipeline at every stage.

**Pipeline Runs View**:
- See all pipeline executions (success, failed, in progress)
- View duration of each run
- Drill down to see individual activity details

**Key Metrics to Monitor**:
- **Success Rate**: Percentage of successful runs (target: >95%)
- **Duration**: Average time to complete of under 60 minutes per weekly run
- **Cost**: Track total pipeline execution cost per month to ensure efficiency

### Azure Monitor Integration
For long-term observability and alerting, logs are exported to Azure Monitor, which enables:
- Long-term storage (ADF only keeps 45 days)
- Custom dashboards and alerts
- Integration with other Azure services

**Key Metrics Dashboard**:
```
┌─────────────────────────────────────────────────────────┐
│  Automotive Data Pipeline - Weekly Status               │
├─────────────────────────────────────────────────────────┤
│  Last Run: 2025-11-10 02:00 AM                          │
│  Status:   Success                                      │
│  Duration: 42 minutes                                   │
│  Records Loaded: 67,234                                 │
├─────────────────────────────────────────────────────────┤
│  Success Rate (Last 4 Weeks): 98%                       │
│  Average Duration: 45 minutes                           │
│  Failed Runs: 1 (API timeout on 2025-10-27)             │
└─────────────────────────────────────────────────────────┘
```

## Security Best Practices

### 1. Secrets Management
Credentials should never be hard-coded in scripts or configuration files. All sensitive information, like API Keys, Databricks tokens and connection strings must be securely stored and managed through Azure Key Vault.

**Accessing Secrets in ADF (example)**:
```json
{
  "type": "AzureKeyVaultSecret",
  "store": {
    "referenceName": "AzureKeyVault_LinkedService",
    "type": "LinkedServiceReference"
  },
  "secretName": "nrel-api-key"
}
```
This ensures all credentials are securely retrieved at runtime and never exposed in code.

### 2. Access Control
Access to Azure Data Factory and related services should follow the **principle of least privilege**, managed through RBAC (Role-Based Access Control)

**Recomended Roles (RBAC)**:
- **Data Engineers**: Full access to ADF pipelines, datasets, linked services
- **Data Analysts**: Read-only access to view pipeline runs
- **Operations Team**: Can trigger manual runs, view monitoring

### 3. Data Encryption

- **At Rest**: Azure Storage encryption (automatic)
- **In Transit**: HTTPS for all API calls and data transfers
- **Within Databricks**: Data encrypted in Delta Lake tables

Together, these measures ensure that all data flowing through the pipeline remains fully secured and compliant with enterprise standards.

## Cost Optimization

### 1. Auto-Terminate Clusters
Running Databricks clusters continuously can be costly. ADF should be configured to **automatically create and terminate job clusters** during each run. This way, compute resources are only used when **needed**. 

### 2. Optimize Pipeline Frequency
The current configuration runs weekly at 2:00 AM every Sunday, which provides a good balance between cost and data freshness.

**Alternative Options**:
- **Daily**: Fresher data but a lot more costly
- **Weekly**: Balanced in cost and freshness
- **Monthly**: Lowest cost, but data may become outdated

**Recommendation**: Start with weekly execution and adjust based on business requirements and data volatility.

### 3. Right-Size Databricks Clusters
Cluster sizing should match data volume to avoid over-provisioning. 
It could be arranged in a way that small datasets (<100k rows) have 1 worker node, medium (<1M rows) 2-6 workers and large data sets (>1M rows) 8+ worker nodes.

For the current project, 1 worker node is sufficient.

## Deployment Strategy

### Infrastructure as Code (IaC)

Use Terraform or ARM templates to deploy Azure Data Factory resources in a consistent, repeatable way.

**Benefits**:
- Full version control of infrastructure configurations
- Easy replication across development, test, and production environments
- Faster recovery if resources are accidentally deleted or corrupted

**Example Terraform Structure**:
```
terraform/
├── main.tf                  # Define ADF resources
├── linked_services.tf       # Databricks, Storage connections
├── pipelines.tf             # Pipeline definitions
└── triggers.tf              # Schedule configuration
```

### CI/CD Pipeline

Automate deployments using Azure DevOps or GitHub Actions to ensure consistent and traceable changes across environments.

Suggested Workflow:
1.	Code Commit: Developer pushes updates to Git.
2.	Automated Tests: Run unit and integration tests on updated scripts.
3.	Deploy to Dev: Deploy pipeline to the development environment.
4.	Integration Tests: Execute full data pipeline with sample data.
5.	Deploy to Production: Promote changes after successful validation.

**Rollback Strategy**: If a production deployment fails, the pipeline automatically reverts to the previous stable version to maintain reliability.


## Implementation Steps

To implement this automation:

### Step 1: Convert Python Scripts to Databricks Notebooks
- Copy scripts from `scripts/` folder
- Convert to `.ipynb` notebook format
- Upload to Databricks workspace at `/notebooks/`

### Step 2: Create Azure Data Factory Instance
- Go to Azure Portal
- Create new Data Factory resource
- Choose region close to Databricks workspace (lower latency)

### Step 3: Set Up Linked Services
- Create Databricks linked service (connect to workspace)
- Create ADLS Gen2 linked service (connect to storage)
- Create Key Vault linked service (for secrets)

### Step 4: Create Pipeline
- Use ADF visual designer
- Add 5 Databricks Notebook activities
- Connect activities with dependencies
- Configure retry policies and timeouts

### Step 5: Create Schedule Trigger
- Add new trigger
- Choose "Schedule"
- Set to weekly, Sunday 2:00 AM
- Associate with pipeline

### Step 6: Test
- Trigger pipeline manually (don't wait for Sunday)
- Monitor execution in ADF dashboard
- Verify all activities complete successfully
- Check Delta Lake tables have data

### Step 7: Set Up Monitoring
- Configure email alerts for failures
- Create Azure Monitor dashboard
- Set up cost alerts (notify if pipeline costs exceed budget)

## Summary

This strategy ensures that the data pipeline runs automatically, securely, and cost-efficiently every week.
By combining Azure Data Factory orchestration with Databricks processing and Key Vault security, the process remains fully automated and easy to maintain — providing fresh, validated data for analysis without requiring manual oversight.


