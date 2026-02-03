import frappe
from frappe.utils import today, add_days
from frappe.utils import today, add_months, getdate
from frappe.utils import add_months, today, formatdate
from frappe.utils import get_first_day, get_last_day
from collections import defaultdict

def onload(self):
    if not frappe.db.exists(
        "Employee",
        {"user_id": frappe.session.user, "status": "Active"}
    ):
        frappe.throw("Access denied", frappe.PermissionError)

# =========================================================
# KPI SUMMARY
# =========================================================
@frappe.whitelist()
def get_kpi_summary():
    """
    Top KPI numbers for ESS dashboard
    - Reporting To You
    - Active Employees (self + subordinates)
    - Pending Requests (workflow only, pending to current user)
    - Pending Appraisals
    - Gender split for Active Employees
    """

    user = frappe.session.user

    # =====================================================
    # CURRENT EMPLOYEE
    # =====================================================
    emp = frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},
        "name"
    )

    if not emp:
        return {}

    emp_name = frappe.db.get_value(
        "Employee",
        emp,
        "employee_name"
    )

    # =====================================================
    # REPORTING EMPLOYEES
    # =====================================================
    reporting_employees = frappe.get_all(
        "Employee",
        filters={
            "reports_to": emp,
            "status": "Active"
        },
        pluck="name"
    )

    reporting_count = len(reporting_employees)

    # =====================================================
    # ACTIVE EMPLOYEES (SELF + SUBORDINATES)
    # =====================================================
    active_employee_list = [emp] + reporting_employees
    active_employees = len(active_employee_list)

    # =====================================================
    # GENDER SPLIT (ACTIVE EMPLOYEES)
    # =====================================================
    gender_split = {"Male": 0, "Female": 0}

    if active_employee_list:
        rows = frappe.db.sql("""
            SELECT gender, COUNT(*) AS total
            FROM `tabEmployee`
            WHERE
                name IN %s
                AND status = 'Active'
                AND gender IS NOT NULL
            GROUP BY gender
        """, (tuple(active_employee_list),), as_dict=True)

        for r in rows:
            if r.gender in gender_split:
                gender_split[r.gender] = r.total

    # =====================================================
    # PENDING REQUESTS (WORKFLOW ONLY)
    # Pending to CURRENT USER (manager)
    # =====================================================
    pending_requests = frappe.db.count(
        "Workflow Action",
        {
            "status": "Open",
            "user": user
        }
    )

    # =====================================================
    # PENDING APPRAISALS (SUBORDINATES ONLY)
    # =====================================================
    pending_appraisals = 0
    pending_appraisal_days = 0

    if reporting_employees and frappe.db.table_exists("Appraisal"):
        pending_appraisals = frappe.db.count(
            "Appraisal",
            {
                "docstatus": 0,
                "employee": ["in", reporting_employees]
            }
        )

        if pending_appraisals:
            oldest = frappe.db.sql("""
                SELECT DATEDIFF(CURDATE(), MIN(creation))
                FROM `tabAppraisal`
                WHERE
                    docstatus = 0
                    AND employee IN %s
            """, (tuple(reporting_employees),))[0][0]

            pending_appraisal_days = int(oldest or 0)

    # =====================================================
    # FINAL RESPONSE
    # =====================================================
    return {
        "current_employee": emp,
        "current_employee_name": emp_name,

        "reporting_count": reporting_count,
        "reporting_employees": reporting_employees,

        "active_employees": active_employees,
        "active_employee_list": active_employee_list,
        "active_gender_split": gender_split,

        "pending_requests": pending_requests,

        "pending_appraisals": pending_appraisals,
        "pending_appraisal_days": pending_appraisal_days,
        "pending_appraisal_employees": reporting_employees,
    }



# =========================================================
# EMPLOYEE HEADCOUNT BREAKDOWN
# =========================================================
@frappe.whitelist()
def get_headcount_breakdown(by="department"):

    group_field_map = {
        "department": "department",
        "branch": "branch",
        "employment_type": "employment_type"
    }

    group_field = group_field_map.get(by)
    if not group_field:
        return {}

    employees = get_accessible_employees()
    if not employees:
        return {}

    rows = frappe.db.sql(f"""
        SELECT
            IFNULL({group_field}, 'Not Set') AS label,
            COUNT(*) AS value,
            GROUP_CONCAT(name) AS employees
        FROM `tabEmployee`
        WHERE
            status = 'Active'
            AND name IN %(employees)s
        GROUP BY {group_field}
        ORDER BY value DESC
    """, {
        "employees": tuple(employees)
    }, as_dict=True)

    return {
        "labels": [r.label for r in rows],
        "datasets": [{
            "name": "Headcount",
            "values": [r.value for r in rows]
        }],
        # 🔑 INDEX-BASED (not label-based)
        "employees_by_index": [
            r.employees.split(",") if r.employees else []
            for r in rows
        ]
    }

@frappe.whitelist()
def get_accessible_employees():
    """
    Returns employees accessible to current user:
    - Always includes self
    - Includes subordinates (if any)
    """

    user = frappe.session.user

    # Current employee
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},
        "name"
    )

    if not employee:
        return []

    # Subordinates
    reports = frappe.get_all(
        "Employee",
        filters={
            "reports_to": employee,
            "status": "Active"
        },
        pluck="name"
    )

    # 🔑 ALWAYS include self
    return [employee] + reports



# =========================================================
# NATIONALITY RATIO (CUSTOM FIELD SAFE)
# =========================================================
@frappe.whitelist()
def get_employee_ratio_by_nationality():
    """
    Returns employee count by nationality
    LIMITED to current user + subordinates
    """

    allowed_employees = get_accessible_employees()
    if not allowed_employees:
        return {}

    data = frappe.db.sql("""
        SELECT
            e.custom_nationality AS nationality,
            COUNT(*) AS total
        FROM `tabEmployee` e
        WHERE
            e.status = 'Active'
            AND e.custom_nationality IS NOT NULL
            AND e.name IN %(employees)s
        GROUP BY e.custom_nationality
        ORDER BY total DESC
    """, {
        "employees": tuple(allowed_employees)
    }, as_dict=True)

    if not data:
        return {}

    return {
        "labels": [d.nationality for d in data],
        "datasets": [
            {
                "values": [d.total for d in data]
            }
        ]
    }


@frappe.whitelist()

def get_compliance_summary():
    """
    Employee Compliance & Expiry Summary
    - Pending Confirmations (always)
    - Missing Leave Allocation (always)
    - Expiry items (configurable via ESS Dashboard Setup)
    """

    t = today()
    t30 = add_days(t, 30)

    allowed_employees = get_accessible_employees()
    if not allowed_employees:
        return []

    results = []

    # ======================================================
    # 1️⃣ PENDING CONFIRMATIONS (UNCHANGED)
    # ======================================================
    emp_meta = frappe.get_meta("Employee")
    emp_fields = {f.fieldname for f in emp_meta.fields}

    confirmation_filters = {
        "status": "Active",
        "name": ["in", allowed_employees]
    }

    if "confirmation_date" in emp_fields:
        confirmation_filters["confirmation_date"] = ["is", "not set"]
    if "final_confirmation_date" in emp_fields:
        confirmation_filters["final_confirmation_date"] = ["is", "not set"]

    pending_confirmation_employees = frappe.db.get_all(
        "Employee",
        filters=confirmation_filters,
        pluck="name"
    )

    if pending_confirmation_employees:
        results.append({
            "label": "Pending Confirmations",
            "count": len(pending_confirmation_employees),
            "employees": pending_confirmation_employees
        })

    # ======================================================
    # 2️⃣ MISSING LEAVE ALLOCATION (UNCHANGED)
    # ======================================================
    missing_leave_employees = [
        r[0] for r in frappe.db.sql("""
            SELECT DISTINCT e.name
            FROM `tabEmployee` e
            LEFT JOIN `tabLeave Allocation` la
                ON la.employee = e.name AND la.docstatus = 1
            WHERE
                e.status = 'Active'
                AND e.name IN %s
                AND la.name IS NULL
        """, (tuple(allowed_employees),))
    ]

    if missing_leave_employees:
        results.append({
            "label": "Missing Leave Allocation",
            "count": len(missing_leave_employees),
            "employees": missing_leave_employees
        })

    # ======================================================
    # 3️⃣ EXPIRY ITEMS (CONFIGURABLE)
    # ======================================================
    default_expiry_map = {
        "Contract End Date (30 Days)": {
            "doctype": "Employee",
            "field": "contract_end_date"
        },
        "Visa Expiry (30 Days)": {
            "doctype": "Employee",
            "field": "custom_visa_expiry"
        },
        "Iqama Expiry (30 Days)": {
            "doctype": "Employee",
            "field": "custom_iqama_expiry_date"
        },
        "Passport Expiry (30 Days)": {
            "doctype": "Employee",
            "field": "valid_upto"
        },
        "Labor Card Expiry (30 Days)": {
            "doctype": "Employee",
            "field": "custom_labour_card_expiry"
        },
        "Emirates ID Expiry (30 Days)": {
            "doctype": "Employee",
            "field": "custom_emirates_id_expiry"
        }
    }

    setup_config = get_ess_expiry_config()  # None if no setup exists

    #frappe.msgprint(f"setup config {setup_config}")

    for label, default_rule in default_expiry_map.items():

        # 🔑 Precedence logic
        if setup_config is None:
            rule = default_rule
        else:
            rule = setup_config.get(label, default_rule)

        doctype = rule["doctype"]
        field = rule["field"]

        #frappe.msgprint(f"doctype {setup_config} field {field}")

        # 🔒 Safety checks
        # if not frappe.db.table_exists(f"tab{doctype}"):
        #     continue

        meta = frappe.get_meta(doctype)

        #frappe.msgprint(f"meta {meta}")
        
        if not meta.has_field(field):
            continue

        params = {
            "start": t,
            "end": t30,
            "emps": tuple(allowed_employees)
        }

        # 🔐 Employee scoping
        if meta.has_field("employee"):
            emp_filter = "AND employee IN %(emps)s"
        elif meta.has_field("parent"):
            emp_filter = "AND parent IN %(emps)s"
        else:
            emp_filter = "AND name IN %(emps)s"

        rows = frappe.db.sql(f"""
            SELECT DISTINCT name
            FROM `tab{doctype}`
            WHERE
                `{field}` IS NOT NULL
                AND `{field}` BETWEEN %(start)s AND %(end)s
                {emp_filter}
        """, params, pluck="name")

        if rows:
            results.append({
                "label": label,
                "count": len(rows),
                "employees": rows
            })

    return results



@frappe.whitelist()
def get_today_attendance_summary():
    today = frappe.utils.today()
    user = frappe.session.user

    # --------------------------------
    # Step 1: Current employee
    # --------------------------------
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    if not employee:
        return {}

    # --------------------------------
    # Step 2: Reporting employees
    # --------------------------------
    # reporting_employees = frappe.get_all(
    #     "Employee",
    #     filters={"reports_to": employee, "status": "Active"},
    #     pluck="name"
    # )
    reporting_employees = get_accessible_employees()

    # Manager → subordinates
    # Employee → self
    employees = reporting_employees if reporting_employees else [employee]

    # --------------------------------
    # Step 3: Fetch today’s attendance
    # --------------------------------
    attendance = frappe.get_all(
        "Attendance",
        filters={
            "attendance_date": today,
            "employee": ["in", employees]
        },
        fields=[
            "employee",
            "status",
            "late_entry",
            "early_exit"
        ]
    )


    # --------------------------------
    # Step 4: Build summary (count + names)
    # --------------------------------
    summary = {
        "present": {"count": 0, "employees": []},
        "absent": {"count": 0, "employees": []},
        "late": {"count": 0, "employees": []},
        "leave": {"count": 0, "employees": []},
        "early_exit": {"count": 0, "employees": []},
        "half_day": {"count": 0, "employees": []}
    }

    for a in attendance:
        #frappe.msgprint(f"{a}")
        # 🔑 Priority checks (flags first)
        if a.status == "Present" and a.late_entry:
            summary["late"]["count"] += 1
            summary["late"]["employees"].append(a.employee)

        elif a.status == "Present" and a.early_exit:
            summary["early_exit"]["count"] += 1
            summary["early_exit"]["employees"].append(a.employee)

        elif a.status == "Half Day":
            summary["half_day"]["count"] += 1
            summary["half_day"]["employees"].append(a.employee)

        elif a.status == "On Leave":
            summary["leave"]["count"] += 1
            summary["leave"]["employees"].append(a.employee)

        elif a.status == "Absent":
            summary["absent"]["count"] += 1
            summary["absent"]["employees"].append(a.employee)

        elif a.status == "Present":
            summary["present"]["count"] += 1
            summary["present"]["employees"].append(a.employee)


    return summary


@frappe.whitelist()
def get_pending_approvals_for_me():
    """
    Pending workflow approvals for current user
    Supports ROLE-based and USER-based workflows
    Cached per user
    """

    user = frappe.session.user
    cache_key = f"pending_approvals::{user}"

    # 🔹 1️⃣ Return from cache if exists
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

    user_roles = set(frappe.get_roles(user))
    result = {}

    allowed_employees = get_accessible_employees()

    self_emp = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if self_emp in allowed_employees:
        allowed_employees.remove(self_emp)

    # 🔹 2️⃣ Fetch open workflow actions
    workflow_rows = frappe.db.sql("""
        SELECT
            wa.reference_doctype,
            wa.reference_name,
            wa.user,
            wa.creation
        FROM `tabWorkflow Action` wa
        WHERE wa.status = 'Open'
        ORDER BY wa.creation DESC
    """, as_dict=True)

    for row in workflow_rows:
        doctype = row.reference_doctype
        name = row.reference_name
        assigned_user = row.user

        # 🔹 User-based workflow check
        if assigned_user and assigned_user != user:
            continue

        workflow = frappe.db.get_value(
            "Workflow",
            {"document_type": doctype, "is_active": 1},
            ["name"],
            as_dict=True
        )
        if not workflow:
            continue
        
        
        state = frappe.db.get_value(doctype, name, "workflow_state")
        if not state:
            continue

        # 🔹 Role-based workflow check
        if assigned_user is None:
            allowed_roles = frappe.db.get_all(
                "Workflow Transition",
                filters={
                    "parent": workflow.name,
                    "state": state
                },
                pluck="allowed"
            )

            if not user_roles.intersection(set(allowed_roles)):
                continue

        # 🔹 Optional employee filtering
        meta = frappe.get_meta(doctype)
        if meta.has_field("employee"):
            emp = frappe.db.get_value(doctype, name, "employee")
            if emp and emp not in allowed_employees:
                continue
        
        if not frappe.has_permission(doctype, "read", name):
            continue
        
        try:
            doc = frappe.get_doc(doctype, name)
            #frappe.msgprint(f"doc {doc}")
            if doc.workflow_state in ["Rejected", "Rejected by HOD"]:
                continue
        except:
            continue

        result.setdefault(doctype, []).append(name)

    final_result = {
        dt: {
            "count": len(names),
            "names": names
        }
        for dt, names in result.items()
    }

    #🔹 3️⃣ Store in cache (5 minutes)
    frappe.cache().set_value(
        cache_key,
        final_result,
        expires_in_sec=300
    )

    return final_result

@frappe.whitelist()
def get_pending_requests_sent_by_me():
    """
    Pending workflow requests created by current user
    Optimized: single-pass, minimal queries
    """

    user = frappe.session.user
    cache_key = f"pending_requests::{user}"

    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

    result = {}

    # 🔑 1. Fetch all open workflow actions
    rows = frappe.db.sql("""
        SELECT
            wa.reference_doctype AS doctype,
            wa.reference_name AS name
        FROM `tabWorkflow Action` wa
        WHERE
            wa.status = 'Open'
            AND wa.owner = %(user)s
        ORDER BY wa.creation DESC
    """, {"user": user}, as_dict=True)

    if not rows:
        frappe.cache().set_value(cache_key, {}, expires_in_sec=300)
        return {}

    # 🔑 2. Group documents by doctype
    docs_by_doctype = {}
    for r in rows:
        docs_by_doctype.setdefault(r.doctype, []).append(r.name)

    # 🔑 3. Validate documents in bulk per doctype
    for doctype, names in docs_by_doctype.items():

        if not frappe.db.table_exists(f"tab{doctype}"):
            continue

        meta = frappe.get_meta(doctype)
        if not meta.has_field("workflow_state"):
            continue

        # 🔑 Bulk validation query
        valid_docs = frappe.db.sql(f"""
            SELECT name
            FROM `tab{doctype}`
            WHERE
                name IN %(names)s
                AND docstatus = 0
                AND workflow_state IS NOT NULL
                AND workflow_state NOT IN (
                    'Rejected',
                    'Rejected by HOD',
                    'Cancelled'
                )
        """, {"names": tuple(names)}, pluck="name")

        if not valid_docs:
            continue

        # 🔑 Final permission filter (light)
        permitted = [
            d for d in valid_docs
            if frappe.has_permission(doctype, "read", d)
        ]

        if permitted:
            result[doctype] = {
                "count": len(permitted),
                "names": permitted
            }

    frappe.cache().set_value(cache_key, result, expires_in_sec=300)
    return result


# @frappe.whitelist()
# def get_pending_requests_sent_by_me():
#     """
#     Pending workflow requests created by current user
#     (Still waiting for approval)
#     """

#     user = frappe.session.user
#     cache_key = f"pending_requests::{user}"

#     cached = frappe.cache().get_value(cache_key)
#     if cached is not None:
#         return cached

#     result = {}

#     workflows = frappe.get_all(
#         "Workflow",
#         filters={"is_active": 1},
#         fields=["name", "document_type"]
#     )

#     for wf in workflows:
#         doctype = wf.document_type

#         # Safety: table exists
#         # if not frappe.db.table_exists(f"tab{doctype}"):
#         #     continue

#         # Load workflow once
#         workflow_doc = frappe.get_doc("Workflow", wf.name)

#         final_states = {
#             row.state
#             for row in workflow_doc.states
#             if row.allow_edit == 0   # final-ish states
#         }

#         docs = frappe.db.sql(f"""
#             SELECT name, workflow_state
#             FROM `tab{doctype}`
#             WHERE owner = %s
#               AND docstatus = 0
#               AND workflow_state IS NOT NULL
#         """, user, as_dict=True)

#         for row in docs:
#             docname = row.name
#             state = row.workflow_state

#             # Skip final / rejected
#             if state in final_states:
#                 continue
#             if state in ("Rejected", "Rejected by HOD"):
#                 continue

#             # Hard safety
#             if not frappe.db.exists(doctype, docname):
#                 continue

#             # # Permission check (light)
#             if not frappe.has_permission(doctype, "read", docname):
#                 continue

#             result.setdefault(doctype, []).append(docname)

#     final_result = {
#         dt: {
#             "count": len(names),
#             "names": names
#         }
#         for dt, names in result.items()
#     }

#     frappe.cache().set_value(cache_key, final_result, expires_in_sec=300)
#     return final_result


def has_workflow(doctype):
    return bool(
        frappe.db.exists(
            "Workflow",
            {
                "document_type": doctype,
                "is_active": 1
            }
        )
    )


@frappe.whitelist()
def get_leave_balance_employees():
    user = frappe.session.user

    current_emp = frappe.db.get_value(
        "Employee",
        {"user_id": user, "status": "Active"},
        ["name", "employee_name"],
        as_dict=True
    )

    if not current_emp:
        return []

    subordinates = frappe.get_all(
        "Employee",
        filters={
            "reports_to": current_emp.name,
            "status": "Active"
        },
        fields=["name", "employee_name"],
        order_by="employee_name asc"
    )

    employees = [current_emp]
    employees.extend(subordinates)
    
    #frappe.msgprint(f"employees {employees}")
    return employees


@frappe.whitelist()

def get_leave_balance_for_employee(employee=None):
    if not employee:
        return []

    allowed = get_leave_balance_employees()
    allowed_names = [e["name"] for e in allowed]

    if employee not in allowed_names:
        frappe.throw("Not permitted")

    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "docstatus": 1
        },
        fields=[
            "leave_type",
            "total_leaves_allocated"
        ]
    )
    used = frappe.db.sql("""
    SELECT
        leave_type,
        ABS(SUM(leaves)) AS used
    FROM `tabLeave Ledger Entry`
    WHERE
        employee = %s
        AND docstatus = 1
        AND transaction_type = 'Leave Application'
        AND leaves < 0
    GROUP BY leave_type
""", employee, as_dict=True)


    #frappe.msgprint(f"used {used}")
    used_map = {u.leave_type: abs(u.used or 0) for u in used}

    #frappe.msgprint(f"used_map {used_map}")
    result = []
    for a in allocations:
        balance = round((a.total_leaves_allocated or 0) - used_map.get(a.leave_type, 0), 2)
        result.append({
            "leave_type": a.leave_type,
            "balance": balance
        })

    return result


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def employee_leave_access_query(doctype, txt, searchfield, start, page_len, filters):

    allowed_employees = get_accessible_employees()

    page_len = min(int(page_len or 20), 20)

    conditions = ["status = 'Active'"]
    values = {
        "txt": f"%{txt}%",
        "start": int(start or 0),
        "page_len": page_len
    }

    if allowed_employees:
        conditions.append("name IN %(emps)s")
        values["emps"] = tuple(allowed_employees)

    where_clause = " AND ".join(conditions)

    return frappe.db.sql(f"""
        SELECT
            name,
            employee_name AS description   -- 🔥 THIS IS THE KEY
        FROM `tabEmployee`
        WHERE
            {where_clause}
            AND (
                name LIKE %(txt)s
                OR employee_name LIKE %(txt)s
            )
        ORDER BY employee_name
        LIMIT %(start)s, %(page_len)s
    """, values)


@frappe.whitelist()
def get_net_payroll_breakdown(month, by):
    """
    month: YYYY-MM
    by: department | branch | employment_type

    Shows payroll ONLY for:
    - current user
    - subordinates (if any)
    """

    # -----------------------------
    # Date range (month overlap)
    # -----------------------------
    month_start = f"{month}-01"
    month_end = frappe.utils.get_last_day(month_start)

    # -----------------------------
    # Allowed employees (SECURITY)
    # -----------------------------
    allowed_employees = get_accessible__sub_employees()
    #frappe.msgprint(f"allowed_employees {allowed_employees}")
    if not allowed_employees:
        return {}

    # -----------------------------
    # Safe grouping fields
    # -----------------------------
    field_map = {
        "department": "department",
        "branch": "branch",
        "employment_type": "employment_type"
    }

    field = field_map.get(by)
    if not field:
        return {}

    # -----------------------------
    # Payroll aggregation
    # -----------------------------
    data = frappe.db.sql(f"""
        SELECT
            e.{field} AS label,
            SUM(s.net_pay) AS value
        FROM `tabSalary Slip` s
        INNER JOIN `tabEmployee` e ON e.name = s.employee
        WHERE
            s.docstatus = 1
            AND s.start_date <= %(month_end)s
            AND s.end_date >= %(month_start)s
            AND e.name IN %(allowed)s
        GROUP BY e.{field}
        ORDER BY value DESC
    """, {
        "month_start": month_start,
        "month_end": month_end,
        "allowed": tuple(allowed_employees)
    }, as_dict=True)

    # -----------------------------
    # Prepare chart data
    # -----------------------------
    labels = [d.label or "Not Set" for d in data]
    values = [float(d.value or 0) for d in data]

    return {
        "labels": labels,
        "datasets": [{
            "name": "Net Payroll",
            "values": values
        }]
    }

def get_accessible__sub_employees():
    """
    Returns Employee.name for:
    - self
    - direct subordinates (if any)
    """

    user = frappe.session.user

    emp = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )

    if not emp:
        return []

    # self + subordinates
    employees = frappe.get_all(
        "Employee",
        filters={
            "name": ["in", [emp]],
            "status": "Active"
        },
        pluck="name"
    )

    subs = frappe.get_all(
        "Employee",
        filters={
            "reports_to": emp,
            "status": "Active"
        },
        pluck="name"
    )

    return list(set(employees + subs))


@frappe.whitelist()
def get_employees_for_net_payroll_filter(by, value, month):

    field_map = {
        "department": "department",
        "branch": "branch",
        "employment_type": "employment_type"
    }

    field = field_map.get(by)
    if not field:
        return []

    month_start = f"{month}-01"
    month_end = frappe.utils.get_last_day(month_start)

    allowed_employees = get_accessible__sub_employees()
    
    conditions = []
    params = {
        "month_start": month_start,
        "month_end": month_end,
        "value": value
    }

    # month overlap (ERPNext standard)
    conditions.append("""
        s.start_date <= %(month_end)s
        AND s.end_date >= %(month_start)s
    """)

    # field filter (Employee)
    conditions.append(f"e.{field} = %(value)s")

    # 🔑 apply allowed employees ONLY if present
    if allowed_employees:
        conditions.append("e.name IN %(allowed)s")
        params["allowed"] = tuple(allowed_employees)

    query = f"""
        SELECT DISTINCT s.employee
        FROM `tabSalary Slip` s
        INNER JOIN `tabEmployee` e ON e.name = s.employee
        WHERE
            s.docstatus = 1
            AND {' AND '.join(conditions)}
    """

    result = frappe.db.sql(query, params, pluck="employee")

    #frappe.msgprint(f"Resolved employees: {query} month_start {month_start} month_end {month_end}")
    return result



@frappe.whitelist()
def get_expiry_soon_summary():
    """
    Returns expiring compliance items (next 30 days)
    Role-based: Self / Subordinates / HR
    Returns COUNT + EMPLOYEE IDS (dashboard-safe)
    """

    start_date = today()
    end_date = add_days(start_date, 30)

    allowed_employees = get_accessible_employees()

    # 🚫 No access
    if allowed_employees == []:
        return {}

    result = {}

    # --------------------------------
    # Common employee filter
    # --------------------------------
    emp_condition = ""
    params = {
        "start": start_date,
        "end": end_date
    }

    # ✅ IMPORTANT: only apply filter when list is NON-EMPTY
    if allowed_employees:
        emp_condition = "AND e.name IN %(employees)s"
        params["employees"] = tuple(allowed_employees)

    # ======================================================
    # CONTRACT EXPIRY (Employee field)
    # ======================================================
    if frappe.db.has_column("Employee", "contract_end_date"):
        contract_employees = [
            r[0] for r in frappe.db.sql(f"""
                SELECT DISTINCT e.name
                FROM `tabEmployee` e
                WHERE
                    e.status = 'Active'
                    {emp_condition}
                    AND e.contract_end_date BETWEEN %(start)s AND %(end)s
            """, params)
        ]

        if contract_employees:
            result["Contract Expiry (30 Days)"] = {
                "count": len(contract_employees),
                "employees": contract_employees
            }

    # ======================================================
    # VISA EXPIRY (Child Table)
    # ======================================================
    visa_employees = [
        r[0] for r in frappe.db.sql(f"""
            SELECT DISTINCT vd.parent
            FROM `tabVisa Details` vd
            JOIN `tabEmployee` e ON e.name = vd.parent
            WHERE
                vd.parenttype = 'Employee'
                AND vd.visa_expiry_date BETWEEN %(start)s AND %(end)s
                AND e.status = 'Active'
                {emp_condition}
        """, params)
    ]

    if visa_employees:
        result["Visa Expiry (30 Days)"] = {
            "count": len(visa_employees),
            "employees": visa_employees
        }

    # ======================================================
    # PASSPORT EXPIRY
    # ======================================================
      
    if frappe.db.exists("DocType", "Passport"):    
        
        passport_employees = [
            r[0] for r in frappe.db.sql(f"""
                SELECT DISTINCT p.parent
                FROM `tabPassport` p
                JOIN `tabEmployee` e ON e.name = p.parent
                WHERE
                    p.parenttype = 'Employee'
                    AND p.passport_expiry_date BETWEEN %(start)s AND %(end)s
                    AND e.status = 'Active'
                    {emp_condition}
            """, params)
        ]

        if passport_employees:
            result["Passport Expiry (30 Days)"] = {
                "count": len(passport_employees),
                "employees": passport_employees
            }


    # ======================================================
    # LABOR CARD EXPIRY
    # ======================================================    
       
    labor_card_employees = [
        r[0] for r in frappe.db.sql(f"""
            SELECT DISTINCT lc.parent
            FROM `tabLabor Card` lc
            JOIN `tabEmployee` e ON e.name = lc.parent
            WHERE
                lc.parenttype = 'Employee'
                AND lc.labor_card_expiry_date BETWEEN %(start)s AND %(end)s
                AND e.status = 'Active'
                {emp_condition}
        """, params)
    ]

    if labor_card_employees:
        result["Labor Card Expiry (30 Days)"] = {
            "count": len(labor_card_employees),
            "employees": labor_card_employees
        }

    return result


@frappe.whitelist()
def get_monthly_attendance_trend():
    """
    Monthly attendance trend (last 6 months)
    Role-based: Self / Subordinates
    """

    from frappe.utils import (
        today,
        add_months,
        get_first_day,
        get_last_day,
        formatdate
    )

    allowed_employees = get_accessible_employees()
    if not allowed_employees:
        return {}

    today_date = today()

    months = []
    present = []
    absent = []
    late = []
    on_leave = []

    for i in range(5, -1, -1):
        ref_date = add_months(today_date, -i)
        month_start = get_first_day(ref_date)
        month_end = get_last_day(ref_date)

        label = formatdate(month_start, "MMM YYYY")
        months.append(label)

        def count(status):
            return frappe.db.count(
                "Attendance",
                {
                    "attendance_date": ["between", [month_start, month_end]],
                    "employee": ["in", allowed_employees],
                    "status": status
                }
            )

        present.append(count("Present"))
        absent.append(count("Absent"))
        late.append(count("Late"))
        on_leave.append(count("On Leave"))

    return {
        "months": months,
        "present": present,
        "absent": absent,
        "late": late,
        "on_leave": on_leave
    }


@frappe.whitelist()
def get_employees_with_visa_expiry():
    start_date = today()
    end_date = add_days(start_date, 30)

    allowed_employees = get_accessible_employees()

    # 🚫 No access
    if allowed_employees == []:
        return []

    condition = ""
    params = [start_date, end_date]

    if allowed_employees is not None:
        condition = "AND parent IN %s"
        params.append(tuple(allowed_employees))

    rows = frappe.db.sql(f"""
        SELECT DISTINCT parent
        FROM `tabVisa Details`
        WHERE
            visa_expiry_date BETWEEN %s AND %s
            AND parenttype = 'Employee'
            {condition}
    """, params, as_list=True)

    return [r[0] for r in rows]


@frappe.whitelist()
def get_employees_missing_leave_allocation():
    allowed_employees = get_accessible_employees()

    if allowed_employees == []:
        return []

    condition = ""
    params = []

    if allowed_employees is not None:
        condition = "AND e.name IN %s"
        params.append(tuple(allowed_employees))

    rows = frappe.db.sql(f"""
        SELECT DISTINCT e.name
        FROM `tabEmployee` e
        LEFT JOIN `tabLeave Allocation` la
            ON la.employee = e.name
            AND la.docstatus = 1
        WHERE
            e.status = 'Active'
            AND la.name IS NULL
            {condition}
    """, params, as_list=True)

    return [r[0] for r in rows]


@frappe.whitelist()
def get_performance_appraisal_summary():
    # ----------------------------
    # 1. STATUS SUMMARY (DONUT)
    # ----------------------------
    status_rows = frappe.db.sql("""
        SELECT
            status,
            COUNT(*) AS count
        FROM `tabAppraisal`
        WHERE docstatus < 2
        GROUP BY status
    """, as_dict=True)

    status_map = {
        "Pending": 0,
        "Completed": 0,
        "Overdue": 0
    }

    for r in status_rows:
        if r.status in status_map:
            status_map[r.status] = r.count

    # ----------------------------
    # 2. RATING TREND (LINE)
    # ----------------------------
    rating_rows = frappe.db.sql("""
        SELECT
            DATE_FORMAT(start_date, '%%b %%Y') AS period,
            ROUND(AVG(final_score), 2) AS rating
        FROM `tabAppraisal`
        WHERE docstatus = 1
          AND final_score IS NOT NULL
        GROUP BY YEAR(start_date), MONTH(start_date)
        ORDER BY start_date DESC
        LIMIT 6
    """, as_dict=True)

    rating_rows.reverse()  # chronological order

    return {
        "status": {
            "labels": list(status_map.keys()),
            "values": list(status_map.values())
        },
        "rating_trend": {
            "labels": [r.period for r in rating_rows],
            "values": [float(r.rating) for r in rating_rows]
        }
    }

@frappe.whitelist()

def is_employee_user():
    user = frappe.session.user

    #frappe.msgprint(f"user {user}")
    # Allow System Manager always
    # if "System Manager" in frappe.get_roles(user):
    #     return True

    # Check employee link (do NOT over-filter)
    emp = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        "name"
    )
    #frappe.msgprint(f"Employee {emp}")
    return bool(emp)

def get_employees_with_pending_appraisals():
    allowed_employees = get_accessible_employees()

    if not allowed_employees:
        return []

    rows = frappe.db.sql("""
        SELECT DISTINCT employee
        FROM `tabAppraisal`
        WHERE docstatus = 0
          AND employee IN %(employees)s
    """, {
        "employees": tuple(allowed_employees)
    }, as_list=True)

    return [r[0] for r in rows]

@frappe.whitelist()
def get_logged_in_employee_profile():
    user = frappe.session.user

    emp = frappe.db.get_value(
        "Employee",
        {"user_id": user},
        ["name", "employee_name", "designation", "department", "image"],
        as_dict=True
    )
    #frappe.msgprint(f"{emp}")
    return emp or {}

@frappe.whitelist()
def get_net_payroll_summary(month):
    """
    Total net payroll for a month
    Role-based: self / subordinates
    """

    if not month:
        return 0

    start_date = f"{month}-01"
    end_date = get_last_day(start_date)

    allowed_employees = get_accessible_employees()
    if not allowed_employees:
        return 0

    total = frappe.db.sql("""
        SELECT SUM(s.net_pay)
        FROM `tabSalary Slip` s
        WHERE
            s.docstatus = 1
            AND s.start_date >= %(start)s
            AND s.end_date <= %(end)s
            AND s.employee IN %(emps)s
    """, {
        "start": start_date,
        "end": end_date,
        "emps": tuple(allowed_employees)
    })[0][0]

    return float(total or 0)

@frappe.whitelist()
def get_net_payroll_breakdown_by_year(year, by):
    """
    Yearly net payroll breakdown
    by: department | branch | employment_type
    """

    if not year:
        return {}

    year_start = f"{year}-01-01"
    year_end = f"{year}-12-31"

    allowed_employees = get_accessible_employees()
    if not allowed_employees:
        return {}

    field_map = {
        "department": "department",
        "branch": "branch",
        "employment_type": "employment_type"
    }

    field = field_map.get(by)
    if not field:
        return {}

    rows = frappe.db.sql(f"""
        SELECT
            e.{field} AS label,
            SUM(s.net_pay) AS value
        FROM `tabSalary Slip` s
        INNER JOIN `tabEmployee` e ON e.name = s.employee
        WHERE
            s.docstatus = 1
            AND s.start_date >= %(start)s
            AND s.end_date <= %(end)s
            AND e.name IN %(emps)s
        GROUP BY e.{field}
        ORDER BY value DESC
    """, {
        "start": year_start,
        "end": year_end,
        "emps": tuple(allowed_employees)
    }, as_dict=True)

    return {
        "labels": [r.label or "Not Set" for r in rows],
        "datasets": [{
            "name": "Net Payroll",
            "values": [float(r.value or 0) for r in rows]
        }]
    }


    """
    Returns:
    {
        "Visa Expiry": {
            "doctype": "Employee",
            "field": "custom_visa_expiry"
        },
        ...
    }
    """
    rules = {}

    setup = frappe.get_all(
        "ESS Dashboard Setup",
        fields=["name"],
        limit=1
    )

    if not setup:
        return rules

    rows = frappe.get_all(
        "ESS Dashboard Setup Item",
        filters={"parent": setup[0].name},
        fields=["expiry_type", "ref_doctype", "expiry_field"]
    )

    for r in rows:
        if r.expiry_type and r.ref_doctype and r.expiry_field:
            rules[r.expiry_type] = {
                "doctype": r.ref_doctype,
                "field": r.expiry_field
            }

    return rules

def get_ess_expiry_config():
    """
    Returns expiry configuration map
    Works with SINGLE DocType: ESS Dashboard Setup
    """

    config = {}

    # 🔹 SINGLE doctype → always use get_single
    setup = frappe.get_single("ESS Dashboard Setup")

    # 🔹 Child table lives on the single doc
    rows = setup.get("expiry_configurations") or []

    #frappe.msgprint(f"rows {rows}")

    for r in rows:
        if r.expiry_type and r.ref_doctype and r.expiry_field:
            config[r.expiry_type] = {
                "doctype": r.ref_doctype,
                "field": r.expiry_field
            }

    # 🔑 If no rows configured → treat as NO SETUP
    return config or None


@frappe.whitelist()
def get_turnover_breakdown(month, by):
    """
    Employee Turnover (Joined vs Left)
    Grouped by department / branch / employment_type
    """

    if not month:
        return {}

    field_map = {
        "department": "department",
        "branch": "branch",
        "employment_type": "employment_type"
    }

    group_field = field_map.get(by)
    if not group_field:
        return {}

    month_start = f"{month}-01"
    month_end = frappe.utils.get_last_day(month_start)

    rows = frappe.db.sql(f"""
        SELECT
            IFNULL(e.{group_field}, 'Not Set') AS label,

            SUM(
                CASE
                    WHEN e.date_of_joining BETWEEN %(start)s AND %(end)s
                    THEN 1 ELSE 0
                END
            ) AS joined_count,

            SUM(
                CASE
                    WHEN e.relieving_date BETWEEN %(start)s AND %(end)s
                    THEN 1 ELSE 0
                END
            ) AS left_count
        FROM `tabEmployee` e
        GROUP BY e.{group_field}
        ORDER BY label
    """, {
        "start": month_start,
        "end": month_end
    }, as_dict=True)

    labels = []
    joined = []
    left = []


    for r in rows:
        labels.append(r.label)
        joined.append(int(r.joined_count or 0))
        left.append(int(r.left_count or 0))

    # 🔑 THIS IS THE CRITICAL FIX
    return {
        "labels": labels,
        "joined": joined,
        "left": left
    }


