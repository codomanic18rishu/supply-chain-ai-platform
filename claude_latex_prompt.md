# Prompt for Claude.ai: Final Year Project Report Generator in LaTeX

Copy and paste the entire prompt below into **Claude.ai** to generate the modular, compile-safe LaTeX code for your final year project report.

---

### **SYSTEM DIRECTIVE & CONTEXT**
You are an expert LaTeX developer and a Senior Software Engineer specializing in Supply Chain Management and AI Systems. Your task is to generate a comprehensive, highly professional, modular, and compile-safe LaTeX project report for a final-year Bachelor of Technology (B.Tech) degree in Computer Science & Engineering at **Bihar Engineering University, Patna**.

The report is for a real, fully implemented project: a **"Supply Chain AI Platform"** which includes:
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS, Recharts, Lucide Icons, Axios.
- **Backend**: FastAPI (Python), SQL Alchemy ORM, SQLite database (`supply_chain_ai.db`), Python-jose (JWT), bcrypt.
- **Core AI/ML Services**:
  1. **Demand Forecasting**: Custom recursive multi-step forecasting utilizing an **XGBoost Regressor** per product. Features engineered: lag features (1, 7, 14 days), rolling means (7, 14 days), rolling standard deviations (7 days), and time-based calendar features (day of week, day of month, month, quarter, year, weekend flag).
  2. **Inventory Optimization**: Statistical calculations for Safety Stock ($SS = Z \times \sigma_{demand} \times \sqrt{LT}$), Reorder Point ($ROP = (d_{avg} \times LT) + SS$), Economic Order Quantity (EOQ Wilson Formula: $EOQ = \sqrt{2 D S / H}$), and Days of Inventory (DOI).
  3. **Supply Chain Risk Detection**: Heuristics to identify Stockout risks, Overstock risks, Demand spikes, and Declining demand, classifying severity from Low to Critical.
  4. **AI-Driven Automated Insights**: LLM-driven synthesis (via OpenAI API) that aggregates demand forecasts and inventory metrics to generate executive summaries, urgent action items, and structural recommendations.

---

### **TECHNICAL UNIVERSITY FORMATTING GUIDELINES**
You must strictly adhere to the following formatting requirements in the generated LaTeX code:
1. **Margins**: Left margin = 4.0 cm, Right margin = 2.5 cm, Top margin = 4.0 cm, Bottom margin = 2.5 cm. (Use the `geometry` package).
2. **Line Spacing**: Exactly 1.5 line spacing for the body text. (Use `\setspace` package with `\onehalfspacing`).
3. **Typography**:
   - **Main Body**: Arial font (approximated in standard pdfLaTeX using the `helvet` package set to `\familydefault`). Size: 12pt.
   - **Title**: Bold, Arial (Helvetica), 14pt, Centered.
   - **Subtitles**: Bold, Arial (Helvetica), 12pt, Left-justified.
   - **Title Page (Times New Roman)**: The title page MUST be in Times New Roman (approximated using the `mathptmx` package or custom `\fontfamily{ptm}\selectfont` groupings).
4. **Layout**: Double-sided print styling (`twoside` in `\documentclass[12pt,a4paper,twoside]{report}`).
5. **Document Architecture**:
   - Title Page
   - Student's Declaration & Copyright Transfer + Copyright Notice (Must be signed by candidate, showing Roll No & Reg No)
   - Acknowledgments
   - Abstract
   - Table of Contents, List of Figures, List of Tables
   - Abbreviations
   - Chapters (Chapters 1 to 6)
   - References (IEEE style)
   - Appendices

---

### **PREVENTING OVERLEAF COMPILATION TIMEOUTS**
To ensure this document compiles successfully on Overleaf (within the 1-2 minute free compiling window) and remains modular:
1. **Modular Code Structure**: Break the report into multiple separate `.tex` files. Provide the code for each file separately:
   - `main.tex` (Core document settings, packages, imports)
   - `titlepage.tex` (Exact font sizes and formatting for Bihar Engineering University)
   - `declaration.tex` (Declaration and Copyright Transfer)
   - `acknowledgments.tex`
   - `abstract.tex`
   - `abbreviations.tex`
   - `chapter1.tex` (Introduction)
   - `chapter2.tex` (Background & Literature Review)
   - `chapter3.tex` (Problem Definition)
   - `chapter4.tex` (Proposed Solution & System Architecture)
   - `chapter5.tex` (Discussion of Results)
   - `chapter6.tex` (Conclusion & Future Work)
   - `references.bib` (IEEE Bibliography)
2. **Compilation Safe Images**: Do NOT use computationally heavy inline packages (like `pgfplots` or massive recursive `tikz` loops). Instead, write clear placeholder figures using `\begin{figure}` and `\includegraphics` with standard bounding boxes, so the user can easily drop in PNG/PDF diagrams of their React dashboard and FastAPI backend flow.

---

### **REQUIRED FILE CONTENTS & BOILERPLATE**

Generate the complete, robust LaTeX code for each of the files below. Replace brackets (e.g. `[STUDENT_NAME]`) with generic placeholders that can be easily customized.

#### **1. `main.tex`**
Provide a robust root document that imports all necessary packages, configures margins, spacing, headers, footers, and dynamically inputs the subfiles.
- Setup geometry: `\usepackage[left=4cm, right=2.5cm, top=4cm, bottom=2.5cm]{geometry}`
- Font setup: Use `\usepackage{helvet}` and `\renewcommand{\familydefault}{\sfdefault}` for Arial body, and define a custom command `\TNR` for Times New Roman font on the title page: `\newcommand{\TNR}[1]{{\fontfamily{ptm}\selectfont #1}}`.
- Spacing: `\usepackage{setspace}` and `\onehalfspacing`.
- Headers/footers: Clear page numbers for chapters, roman numerals for front matter.

#### **2. `titlepage.tex`**
Construct the title page exactly as per university specifications, using Times New Roman (via `\TNR`):
- **Title of Topic**: [TOPIC_NAME] e.g., "AI-DRIVEN MULTI-PRODUCT DEMAND FORECASTING AND INVENTORY OPTIMIZATION PLATFORM" (20pt, Bold, Centered)
- **Report Designation**: "A Project Report" (16pt, Centered)
- **Context text**: "Submitted in Partial Fulfillment of the Requirements for the Award of the Degree of" (Centered)
- **Degree**: "Bachelor of Technology" (20pt, Bold, Centered)
- **In**: "In" (Italics, Centered)
- **Branch**: "Computer Science \& Engineering" (14pt, Bold, Centered)
- **Submission Details**: "Submitted by"
- **Student details**: "[STUDENT_NAME] (14pt, Bold), Registration No. [REG_NUMBER] (12pt, Bold), Roll No. [ROLL_NUMBER]"
- **Supervision Details**: "Under the supervision of \par \textbf{[SUPERVISOR_NAME]} (12pt, Bold), Assistant Professor (10pt)"
- **Logos**: Side-by-side boxes or placeholders for College Logo and University Logo.
- **Affiliation**:
  - "Department of Computer Science \& Engineering" (12pt, Bold)
  - "[INSTITUTE_NAME]" (14pt, Bold)
  - "Bihar Engineering University, Patna" (16pt, Bold)
  - "JUNE 2026" (or [MONTH] [YEAR])

#### **3. `declaration.tex`**
Must contain the exact legal phrasing from the university:
- **DECLARATION AND COPYRIGHT TRANSFER** (to be signed by the candidate)
- Exact text:
  *"I [STUDENT_NAME] Roll No. [ROLL_NUMBER] Registration No. [REG_NUMBER] a registered candidate for Undergraduate Programme (B.Tech) under department of Computer Science \& Engineering of [INSTITUTE_NAME], declare that this is my own original work and does not contain material for which the copyright belongs to a third party and that it has not been presented and will not be presented to any other University/ Institute for a similar or any other Degree award.*
  *I further confirm that for all third-party copyright material in my thesis/ dissertation (including any electronic attachments) is "blanked out" third party material from the copies of the thesis/dissertation/book/articles etc; fully referenced the deleted materials and where possible, provided links (URL) to electronic sources of the material.*
  *I hereby transfer exclusive copyright for this thesis to [INSTITUTE_NAME]. The following rights are reserved by the author:*
  *a) The right to use, free of charge, all or part of this article in future work of their own, such as books and lectures, giving reference to the original place of publication and copyright holding.*
  *b) The right to reproduce the article or thesis for their own purpose provided the copies are not offered for sale."*
- Signatures and Dates placeholders.
- **COPYRIGHT NOTICE**:
  *"COPYRIGHT © [YEAR] by [INSTITUTE_NAME]. All rights reserved.*
  *No part of this publication may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission, except in the case of brief quotations embodied in critical scholarly reviews and certain other non-commercial uses with an acknowledgment/reference permitted by the copyright law."*

#### **4. `acknowledgments.tex` & `abstract.tex` & `abbreviations.tex`**
Generate professional placeholders with high-quality, relevant supply chain context.

#### **5. `chapter1.tex` (Introduction)**
Outline:
- Background of Supply Chain operations, challenges in forecasting multiple product lines, and the necessity of automation.
- Role of Machine Learning (XGBoost) and Large Language Models (LLMs) in replacing manual heuristics.
- Scope and objectives of the Supply Chain AI Platform.

#### **6. `chapter2.tex` (Background & Literature Review)**
Outline:
- Traditional forecasting models: Moving Averages, Exponential Smoothing, ARIMA/SARIMA.
- Modern forecasting approaches: Machine learning models (XGBoost, Prophet) vs classic statistical methods.
- Inventory optimization models: Wilson's EOQ model, safety stock calculation using varying lead times and service levels.
- LLMs in enterprise business intelligence: Automated report synthesis and structured insight generation.

#### **7. `chapter3.tex` (Problem Definition)**
Outline:
- Core constraints of modern small-to-medium enterprise supply chains (SMEs): Demand volatility, inventory holding cost vs stockout cost, and lack of expert data analysts.
- Specific problems addressed by the platform: Predicting demand spikes, preventing overstocking, and providing actionable business insights from raw CSV sales records.

#### **8. `chapter4.tex` (Proposed Solution & Architecture)**
Provide rich, technical descriptions:
- **System Architecture**: Flowchart/block description of React SPA frontend communicating with FastAPI backend, storing data in SQLite via SQLAlchemy.
- **Data Ingestion**: CSV parser that dynamically maps uploaded columns (date, product_id, product_name, sales) using a custom `column_mapper.py` service.
- **Machine Learning Core**: Detailed LaTeX equations and mathematical writeups of:
  - XGBoost recursive multi-step forecasting: explain how the model predicts $t+1$ and recursively feeds it back for $t+2$ up to $t+7$ horizon. Write out feature engineering details (lag features $y_{t-1}, y_{t-7}, y_{t-14}$ and rolling means).
  - Safety Stock formula: $SS = Z \times \sigma_{demand} \times \sqrt{LT}$ and Reorder Point formula: $ROP = (d_{avg} \times LT) + SS$.
  - Economic Order Quantity formula (EOQ): $EOQ = \sqrt{\frac{2 D S}{H}}$.
- **Heuristic Risk Detection Engine**: Mathematical thresholds for Stockout risks, Overstock risks ($DOI \ge 60$ days), and Demand Spikes ($growth \ge 50\%$).
- **AI Synthesis Layer**: Explain the schema mapping that formats inventory metrics and risk alerts into structured JSON sent to the OpenAI API for localized, relevant executive summaries.

#### **9. `chapter5.tex` (Discussion of Results)**
Outline:
- Performance metrics of the XGBoost forecaster compared to standard rolling averages.
- Visual breakdown of the React Dashboard showing Recharts graphs, risk alert counts, and the custom multi-product forecast views.
- Sample output of the AI-generated Executive Summary and urgent action lists.

#### **10. `chapter6.tex` (Conclusion & Future Work)**
Outline:
- Summary of achievements: A fully integrated, real-time Supply Chain forecasting and optimization platform.
- Future work: Incorporating external features (weather, regional holidays, promotional calendars), transitioning to deep learning architectures (LSTMs, Transformers), and supporting multi-warehouse network routing.

#### **11. `references.bib`**
Provide a collection of 8-10 high-quality, real references in BibTeX format matching IEEE standards (academic papers on XGBoost forecasting, inventory models, FastAPI, and LLMs in business).

---

### **OUTPUT INSTRUCTIONS**
- Return code blocks that are **100% complete** and can be immediately copy-pasted into separate files on Overleaf.
- Write highly formal, academic, and technical prose. Do NOT write simple boilerplate text or short paragraphs. Every chapter should have substantial technical descriptions, mathematical formulations in LaTeX equations (`\begin{equation}`), and beautifully structured tables (`booktabs`).
- Ensure no compilation syntax errors exist (such as unescaped underscores `_` in normal text or unclosed brackets).
