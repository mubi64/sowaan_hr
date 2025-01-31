# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    # Fetch columns and data
    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    # Define the report columns
    return [
        {"fieldname": "employee_code", "label": "Employee Code", "fieldtype": "Link", "options": "Employee", "width": 150},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "fund_type", "label": "Fund Type", "fieldtype": "Data", "width": 150},
        {"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 150},
        {"fieldname": "amount", "label": "Amount", "fieldtype": "Currency", "width": 150},
        {"fieldname": "type", "label": "Type", "fieldtype": "Data", "width": 150},
    ]


def get_data(filters):
    # Validate filters
    if not filters.get("from_date") or not filters.get("to_date"):
        frappe.throw("Please select both From Date and To Date")

    # Build the query
    query = """
		SELECT 
			emp.name AS employee_code,
			emp.employee_name AS employee_name,
			fce.contribution_type AS fund_type,
			fce.date AS date,
			ABS(fce.amount) AS amount,
			CASE 
				WHEN fce.is_opening_balance = 1 THEN 'Opening Fund'
				WHEN fce.is_profit_fund = 1 THEN 'Profit Fund'
				WHEN fce.is_fund_withdrawal = 1 THEN 'Fund Withdrawal'
               	WHEN fce.reference_doctype = "Salary Slip" THEN 'Salary Slip'
				ELSE 'Other' 
			END AS type
		FROM 
			`tabFund Contribution` fc
		INNER JOIN 
			`tabFund Contribution Entry` fce ON fc.name = fce.parent
		INNER JOIN
			`tabEmployee` emp ON fc.employee = emp.name
		WHERE 
			fc.docstatus = 1
			AND fce.date BETWEEN %(from_date)s AND %(to_date)s
        ORDER BY 
    CASE 
        WHEN fce.is_opening_balance = 1 THEN 1  -- Opening Fund
        WHEN fce.reference_doctype = "Salary Slip" THEN 2 -- Salary Slip
        WHEN fce.is_fund_withdrawal = 1 THEN 3 -- Fund Withdrawal
        WHEN fce.is_profit_fund = 1 THEN 4 -- Profit Fund
        ELSE 5 -- Other
    END,
    fce.date ASC    
            
        
"""

    # Apply additional filters
    conditions = []
    if filters.get("employee"):
        conditions.append("fc.employee = %(employee)s")
    if filters.get("branch"):
        conditions.append("emp.branch = %(branch)s")
    if filters.get("department"):
        conditions.append("emp.department = %(department)s")
    if filters.get("designation"):
        conditions.append("emp.designation = %(designation)s")
    if filters.get("company"):
        conditions.append("emp.company = %(company)s")

    # Add conditions to the query
    if conditions:
        query += " AND " + " AND ".join(conditions)

    # Execute the query and return results
    data = frappe.db.sql(query, filters, as_dict=True)
    return data
