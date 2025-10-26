# Sample Contract Dataset

This directory contains references to public contract PDFs used for testing and evaluation of the Contract Intelligence API.

## Sample Contracts

### 1. Standard NDA (Non-Disclosure Agreement)
- **Source**: SEC EDGAR Database
- **URL**: https://www.sec.gov/Archives/edgar/data/1018724/000119312513171970/d527744dex101.htm
- **Type**: Mutual Non-Disclosure Agreement
- **License**: Public domain (SEC filings)
- **Description**: Standard mutual NDA with confidentiality obligations

### 2. Master Service Agreement (MSA)
- **Source**: Open Source Initiative
- **URL**: https://opensource.org/MSA
- **Type**: Master Service Agreement
- **License**: CC0 1.0 Universal
- **Description**: Template MSA for service providers

### 3. Software License Agreement
- **Source**: SPDX License List
- **URL**: https://spdx.org/licenses/
- **Type**: Commercial Software License
- **License**: Public domain
- **Description**: Standard commercial software licensing terms

### 4. Employment Agreement
- **Source**: U.S. Department of Labor Sample Contracts
- **URL**: https://www.dol.gov/agencies/oasam/business-operations-center/procurement
- **Type**: Employment Contract
- **License**: Public domain (U.S. Government)
- **Description**: Standard employment agreement template

### 5. Terms of Service
- **Source**: GitHub Terms of Service
- **URL**: https://docs.github.com/en/site-policy/github-terms/github-terms-of-service
- **Type**: Terms of Service Agreement
- **License**: CC BY 4.0
- **Description**: Online platform terms of service

## Usage Notes

These contracts are public documents and can be used for testing purposes. For evaluation:

1. Download the PDFs or HTML versions
2. Convert HTML to PDF if necessary using a tool like wkhtmltopdf
3. Place the PDFs in this directory
4. Use the ingest endpoint to upload them

## Alternative Test Contracts

If the above links are unavailable, you can use any of these alternatives:

- Sample contracts from LawDepot (public samples)
- Template contracts from Rocket Lawyer (free tier)
- Academic legal document repositories
- Open-source project contributor agreements

## Creating Test PDFs

For quick testing without downloading, you can create simple test PDFs with contract-like content using tools like:

- LibreOffice Writer (export to PDF)
- Google Docs (download as PDF)
- LaTeX with contract templates

Ensure any test documents include typical contract elements:
- Party names
- Effective dates
- Terms and conditions
- Liability clauses
- Termination provisions
- Signature blocks
