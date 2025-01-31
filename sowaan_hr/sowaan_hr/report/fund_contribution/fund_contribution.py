# Copyright (c) 2025, Sowaan and contributors
# For license information, please see license.txt
import frappe

def execute(filters=None):
    # Define Columns
    columns = get_columns()

    # Fetch Data
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"fieldname": "employee_code", "label": "Employee Code", "fieldtype": "Link","options":"Employee", "width": 120},
        {"fieldname": "employee_name", "label": "Employee Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "own_fund", "label": "Own Fund", "fieldtype": "Float", "width": 120},
        {"fieldname": "company_fund", "label": "Company Fund", "fieldtype": "Float", "width": 120},
        {"fieldname": "profit_fund", "label": "Profit Fund", "fieldtype": "Float", "width": 120},
        {"fieldname": "withdrawal_fund", "label": "Withdrawal Fund", "fieldtype": "Float", "width": 150},
        {"fieldname": "total", "label": "Total", "fieldtype": "Float", "width": 120},
    ]


def get_data(filters):
    # Initialize conditions and parameters list
    conditions = []
    params = []

    # # Example: Check if 'options' key exists in filters (if applicable)
    # options = filters.get("options", None)  # Will return None if 'options' is not in filters
    # if options:
    #     # Do something with 'options'
    #     pass

    if filters.get("employee"):
        conditions.append("fc.employee = %s")
        params.append(filters.get("employee"))
    if filters.get("branch"):
        conditions.append("fc.branch = %s")
        params.append(filters.get("branch"))
    if filters.get("department"):
        conditions.append("fc.department = %s")
        params.append(filters.get("department"))
    if filters.get("designation"):
        conditions.append("fc.designation = %s")
        params.append(filters.get("designation"))
    if filters.get("company"):
        conditions.append("fc.company = %s")
        params.append(filters.get("company"))

    # Join conditions and form query string
    conditions_str = " AND ".join(conditions) if conditions else "1=1"

    # SQL query with parameterized placeholders (%s)
    query = f"""
    SELECT 
        fc.employee AS employee_code,
        emp.employee_name AS employee_name,
        
        SUM(
			CASE 
				WHEN fce.contribution_type = 'Own' AND fce.reference_doctype = "Salary Slip" THEN fce.amount 
				ELSE 0 
			END
		) + SUM(
			CASE 
				WHEN fce.contribution_type = 'Own' AND fce.is_opening_balance = 1 THEN fce.amount 
				ELSE 0 
			END
		) AS own_fund,
        
        SUM(
			CASE 
				WHEN fce.contribution_type = 'Company' AND fce.reference_doctype = "Salary Slip" THEN fce.amount
				ELSE 0 
			END
		) + SUM(
			CASE 
				WHEN fce.contribution_type = 'Company' AND fce.is_opening_balance = 1 THEN fce.amount 
				ELSE 0 
			END
		) AS company_fund,
        
        SUM(CASE WHEN fce.is_profit_fund = 1 THEN fce.amount ELSE 0 END) AS profit_fund,
        SUM(CASE WHEN fce.is_fund_withdrawal = 1 THEN ABS(fce.amount) ELSE 0 END) AS withdrawal_fund,
        
        (
        SUM(
            CASE 
                WHEN fce.contribution_type = 'Own' AND fce.reference_doctype = "Salary Slip" THEN fce.amount 
                ELSE 0 
            END
        ) + SUM(
            CASE 
                WHEN fce.contribution_type = 'Own' AND fce.is_opening_balance = 1 THEN fce.amount 
                ELSE 0 
            END
        ) + 
        SUM(
            CASE 
                WHEN fce.contribution_type = 'Company' AND fce.reference_doctype = "Salary Slip" THEN fce.amount 
                ELSE 0 
            END
        ) + SUM(
            CASE 
                WHEN fce.contribution_type = 'Company' AND fce.is_opening_balance = 1 THEN fce.amount 
                ELSE 0 
            END
        ) + 
        SUM(
            CASE 
                WHEN fce.is_profit_fund = 1 THEN fce.amount 
                ELSE 0 
            END
        ) - 
        SUM(
            CASE 
                WHEN fce.is_fund_withdrawal = 1 THEN ABS(fce.amount) 
                ELSE 0 
            END
        )
    ) AS total
        
    FROM 
        `tabFund Contribution` fc
    LEFT JOIN 
        `tabFund Contribution Entry` fce
    ON 
        fc.name = fce.parent
    LEFT JOIN 
        `tabEmployee` emp
    ON 
        fc.employee = emp.name
    WHERE 
        {conditions_str}
    GROUP BY 
        fc.employee
    """

    # Execute the query using frappe.db.sql with proper parameters
    return frappe.db.sql(query, tuple(params), as_dict=True)


