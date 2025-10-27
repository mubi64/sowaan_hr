import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import (SalarySlip, calculate_tax_by_tax_slab)
from sowaan_hr.sowaan_hr.api.api import create_salary_adjustment_for_negative_salary
from datetime import datetime, timedelta
from frappe.utils import cint, flt
from frappe.query_builder import DocType
from frappe import (_,utils)
from frappe.utils import today
from frappe.utils import nowdate
from hrms.hr.doctype.leave_application.leave_application import get_leave_details

def process_scheduler_doc(self, method):
    """
    Called automatically when Leave Adjustment Scheduler is submitted or state changes.
    """
    frappe.logger("leave_adjustment_scheduler").info(f"Triggered for {self.name} | State: {self.workflow_state}")

    #frappe.msgprint("I've been called")
    #return
    # Only run if workflow state is 'Execute' or document is submitted
    # if self.workflow_state not in ["Execute", "Approved"]:
    #    return   

    process_leave_adjustment_for_all_employees(self)

    # Update doc to mark it done
    #self.db_set("workflow_state", "Completed")
    frappe.msgprint(_("✅ Leave Adjustment Completed Successfully"))


def process_leave_adjustment_for_all_employees(self):
    """
    Run your existing logic for all active employees.
    """
    employees = frappe.get_all(
    "Employee",
    filters={
        "status": "Active",
        "company": self.custom_company,  # employees of selected company only        
    },
    pluck="name"
)


     # Run adjustments using given date range
    from_date = self.from_date
    to_date = self.to_date or self.post_date or today()

    #frappe.msgprint(f"Employees {employees}")

    #frappe.msgprint(f"Running leave adjustments from {from_date} to {to_date}")

    for emp in employees:
        try:

            hr_setting = frappe.db.get_list('Sowaan HR Setting')

            #frappe.msgprint(f"HR Setting {hr_setting}")

            if not hr_setting:
                frappe.msgprint(f"HR Setting {hr_setting}")
                return            
            
            salary_structure = frappe.db.get_value(
                "Salary Structure Assignment",
                {
                    "employee": emp,
                    "from_date": ["<=", from_date],
                    "docstatus": 1
                },
                "salary_structure",
                order_by="from_date desc"
            )
            #frappe.msgprint(f"Salary Structure {salary_structure}")

            if not salary_structure:
                #frappe.msgprint(f"Salary Structure {salary_structure}")
                frappe.log_error(f"No Salary Structure found for Employee {emp}")
                continue

            parent_to_use = get_deduction_parent(emp, salary_structure)

            #frappe.msgprint(f"parent_to_use {parent_to_use}")
            if not parent_to_use:                
                continue           

            employee_doc = frappe.get_doc("Employee", emp)
            company_currency = frappe.db.get_value("Company", employee_doc.company, "default_currency")    

            #frappe.msgprint(f"Currency {company_currency}")

            # 3️⃣ Build a temporary "self" object (mimics Salary Slip)
            temp_self = frappe._dict({
                "employee": emp,
                "salary_structure": salary_structure,
                "from_date": self.from_date,
                "to_date": self.to_date,
                "posting_date": self.post_date,                
                "company": employee_doc.company,
                "currency": company_currency
            })

            #frappe.msgprint(f"temp_self {temp_self}")           

            #for late arrival, early departure, and half days
            create_leave_application(temp_self, parent_to_use)       

            frappe.logger("leave_adjustment_scheduler").info(f"Processing {emp}")
            
        except Exception as e:
            frappe.log_error(f"Error processing {emp}: {str(e)}", "Leave Adjustment Error")

def create_leave_application(doc, parent_to_use):
    """Fetch component, ensure company is in accounts, then create Additional Salary."""
    
    #frappe.msgprint("create leave application called")

    hr_settings = frappe.get_doc('Sowaan HR Setting', parent_to_use)
    if not any([hr_settings.is_late_deduction_applicable,
                hr_settings.is_early_deduction_applicable,
                hr_settings.is_half_day_deduction_applicable]):
        return
    #frappe.throw('funchello')

    #frappe.msgprint(f"temp_self {doc}")

    assign_shift = frappe.db.get_value('Shift Assignment',
        {'employee': doc.employee, 'start_date': ['<=', doc.from_date]},
        'shift_type', order_by='start_date desc') or frappe.db.get_value('Employee', doc.employee, 'default_shift')

    if not assign_shift:
        return

    shift = frappe.db.get_value('Shift Type', assign_shift, ['start_time', 'end_time'], as_dict=True)
    if not shift:
        return

    shift_start_time = shift.start_time
    shift_end_time = shift.end_time    
   
    #frappe.msgprint(f"start date {doc.from_date} end date {doc.to_date}")

    attendance = frappe.db.get_list('Attendance', filters={
        'employee': doc.employee,
        'status': ['in', ['Present', 'Half Day']],
        'attendance_date': ['between', [doc.from_date, doc.to_date]],
        'docstatus': 1
    }, fields=['in_time', 'out_time', 'status', 'late_entry', 'early_exit', 'attendance_date'], order_by='attendance_date asc')

    #frappe.msgprint(f"Attendance {attendance}")
      
    if not attendance:
        return        

    late_flag_count = cint(hr_settings.get('late_flag_count', 0))
    early_flag_count = cint(hr_settings.get('early_flag_count', 0))
    half_day_flag_count = cint(hr_settings.get('half_day_flag_count', 0))


    exemptions = {
        'half_day': cint(hr_settings.get('half_day_exemptions', 0)),
        'early_exit': cint(hr_settings.get('early_exit_exemptions', 0)),
        'late_entry': cint(hr_settings.get('late_entry_exemptions', 0))
    }


    late_count = early_departure_count = half_day_count = 0
    total_late_minutes = total_early_minutes = 0
    total_late_count = total_early_departure_count = deduction_half_day_count = 0
    
    half_day_violations = []
    early_departure_violations = []
    late_arrival_violations = []
    
    for a in attendance:
        # frappe.msgprint(f"in_time{a['in_time'] } out_time {a['out_time']}")

        #frappe.msgprint(f"attendance {a}")

        if not a['in_time'] or not a['out_time']:
            continue

        in_time = timedelta(hours=a['in_time'].hour, minutes=a['in_time'].minute, seconds=a['in_time'].second)
        out_time = timedelta(hours=a['out_time'].hour, minutes=a['out_time'].minute, seconds=a['out_time'].second)     
               
        ## Half Day Work ##
        if hr_settings.is_half_day_deduction_applicable and a['status'] == 'Half Day':
            half_day_count += 1

            if half_day_count < half_day_flag_count + exemptions["half_day"]:
                pass
            else:
                excess_half_days = flt(half_day_count) - flt(half_day_flag_count)
                if half_day_flag_count == 0:
                    deduction_half_day_count += 1
                    half_day_violations.append({
                        "date": a['attendance_date'],
                        "half_day": 1                        
                    })
                elif excess_half_days % half_day_flag_count == 0:
                    deduction_half_day_count += 1
                    half_day_violations.append({
                        "date": a['attendance_date'],
                        "half_day": 1                        
                    })
        ## Early Work ##
        if hr_settings.is_early_deduction_applicable and a['status'] == 'Present' and a['early_exit']:
            early_departure_count += 1
            if early_departure_count < early_flag_count + exemptions["early_exit"]: 
                pass
            else:
                excess_early_days = early_departure_count - early_flag_count
                if early_flag_count == 0:
                    total_early_minutes += (shift_end_time - out_time).seconds // 60
                    total_early_departure_count += 1
                    early_departure_violations.append({
                        "date": a['attendance_date'],
                        "early_departure": 1                        
                    })
                elif excess_early_days % early_flag_count == 0:
                    total_early_minutes += (shift_end_time - out_time).seconds // 60
                    total_early_departure_count += 1
                    early_departure_violations.append({
                        "date": a['attendance_date'],
                        "early_departure": 1                        
                    })
                    
        ## Late Work ##
        if hr_settings.is_late_deduction_applicable and a['status'] == 'Present' and a['late_entry']:         
                
                if check_late_approval(doc.employee, a['attendance_date']):
                    #frappe.msgprint(f"Late is approved in attendance for {self.employee}")
                    continue  # skip this record and move to next                

                late_count += 1

                if late_count < late_flag_count + exemptions["late_entry"]:
                    pass
                else:
                    excess_late_days = late_count - late_flag_count
                    ## if condition neccessary (flag_count == 0) ##
                    if late_flag_count == 0:
                        total_late_minutes += (in_time - shift_start_time).seconds // 60
                        total_late_count += 1 
                        #frappe.msgprint(f"Late is approved in attendance for {a['attendance_date']}")
                        late_arrival_violations.append({
                            "date": a['attendance_date'],
                            "late_arrival": 1                        
                        })
                    elif excess_late_days % late_flag_count == 0:
                        total_late_minutes += (in_time - shift_start_time).seconds // 60
                        total_late_count += 1
                        #frappe.msgprint(f"Late is approved in attendance for {a['attendance_date']}")
                        late_arrival_violations.append({
                            "date": a['attendance_date'],
                            "late_arrival": 1                        
                        })
    
    if hr_settings.calculation_method == 'Counts':
        
        #add a leave application in the case of employee absent
        #if late deduction is applicable
        if hr_settings.custom_is_absent_adjustment_in_leaves: 
            adjust_absent_leaves(doc.employee, doc.from_date, doc.to_date, hr_settings)
        
        #if late deduction is applicable
        if hr_settings.is_late_deduction_applicable and hr_settings.deduct_from_leaves and late_arrival_violations:
            
            #frappe.msgprint(f"Total Late Count In Late{total_late_count}") 

            #add new condition here.... if duduct from leaves is selected then adjust late in leaves
              
            #if deduct from leaves late deduction factor are selected and late deduction factor is not 0
            if  hr_settings.late_deduction_factor and hr_settings.late_deduction_factor != 0:               
                remaining_deduction = adjust_late_deduction(doc.employee, late_arrival_violations, hr_settings.late_deduction_factor, hr_settings, doc)
                frappe.msgprint(f"{remaining_deduction} late arrival remaining for adjustment in leave application")

        #if early deduction is applicable            
        if hr_settings.is_early_deduction_applicable and hr_settings.custom_early_deduct_from_leaves and early_departure_violations:

            #add new condition here.... if duduct from leaves is selected then adjust early in leaves

            #if deduct from leaves early deduction factor are selected and early deduction factor is not 0
            if hr_settings.custom_early_deduct_from_leaves and hr_settings.early_deduction_factor and hr_settings.early_deduction_factor != 0:               
               #adjust in leaves
               remaining_deduction = adjust_early_deduction(doc.employee, early_departure_violations, hr_settings.early_deduction_factor, hr_settings, doc)
               frappe.msgprint(f"{remaining_deduction} early departure remaining for adjustment in leave application")  
        # #end early arrival deduction case

        #if half day deduction is applicable            
        if hr_settings.is_half_day_deduction_applicable and hr_settings.custom_half_day_deduct_from_leaves and half_day_violations:

            #add new condition here.... if duduct from leaves is selected then adjust half day in leaves

            #if deduct from leaves half day deduction factor are selected and half day deduction factor is not 0
            if hr_settings.custom_half_day_deduct_from_leaves and hr_settings.half_day_deduction_factor and hr_settings.half_day_deduction_factor != 0:               
               #adjust in leaves
               remaining_deduction = adjust_halfday_deduction(doc.employee, half_day_violations, hr_settings.half_day_deduction_factor, hr_settings, doc)
               frappe.msgprint(f"{remaining_deduction} half days remaining for adjustment in leave application") 
        #end of half day deduction case
       
@frappe.whitelist()

#for late deducton from leaves
def adjust_late_deduction(employee, violations, late_deduction_factor, hr_settings, doc):
    """
    Deduct lateness days from the employee's leave balances in the same order
    as defined in 'Sowaan HR Setting' → late_adjustment_leave_types child table.
    """
    try:
        attendance_date = today()        

        #frappe.msgprint(f"late_arrival_violations {violations}") 

        if not violations:
            frappe.msgprint("No violations found — no leave adjustments needed.")
            return
    
        for v in violations:
            attendance_date = v["date"]
            deduction = v["late_arrival"]

            if not check_late_approval(employee, attendance_date):

                #frappe.msgprint(f"Attendance Date: {attendance_date}")

                #total_late_days = deduction * late_deduction_factor
                total_late_days = round(deduction * late_deduction_factor, 2)
                #frappe.msgprint(f"Total Late Days: {total_late_days}")

                if not employee or not total_late_days:
                    frappe.throw("Employee and total late days are required")       

                # Get leave types from child table (in the order they appear)
                leave_types = [
                    row.leave_type
                    for row in sorted(hr_settings.custom_leave_types, key=lambda x: x.idx)
                    if row.leave_type
                ]

                if not leave_types:
                    frappe.throw("No leave types defined in 'Sowaan HR Setting' for late adjustment")
                

                # Ensure a valid Leave Period exists
                leave_period = frappe.db.get_value(
                    "Leave Period",
                    {"from_date": ["<=", attendance_date], "to_date": [">=", attendance_date]},
                    "name"
                )

                #frappe.msgprint(f"Leave period: {leave_period}")

                if not leave_period:
                    frappe.throw("No active Leave Period found for today")        

                # Fetch all leave details for the employee
                available_leave = get_leave_details(employee, today())

                frappe.msgprint(f"Late deduction process started for Employee: {employee}")

                #frappe.msgprint(f"Late Days {total_late_days}")

                remaining_deduction = total_late_days
                current_balance = 0
                
                if remaining_deduction <= 0:
                    frappe.throw("Deduction days must be greater than zero.")

                for lt in leave_types:
                    if remaining_deduction <= 0:
                        break

                    leave_info = available_leave.get("leave_allocation", {}).get(lt, {})

                    if leave_info:
                        current_balance = leave_info.get("remaining_leaves", 0)
                        #frappe.msgprint(f"{lt} balance: {current_balance}")
                    else:
                        frappe.msgprint(f"No data found for {lt}")

                    
                    #frappe.msgprint(f"Current Balance {current_balance} Leave Type {lt}")

                    if not current_balance or current_balance <= 0:
                        continue  # skip leave types with zero balance

                    deduction = min(current_balance, remaining_deduction)

                    leave_app = frappe.get_doc({
                    "doctype": "Leave Application",
                    "employee": employee,
                    "leave_type": lt,
                    "from_date": attendance_date,
                    "to_date": attendance_date,
                    "half_day": 0,
                    "total_leave_days": deduction,  # directly set fractional amount
                    "status": "Approved",
                    "custom_is_adjusted_leave" : True,
                    "leave_approver": "Administrator",             
                    "description":  "Adjustment for late entry",
                    "custom_salary_slip_reference": doc.name,
                    })

                    # ignore the restrictions to submit the leave application
                    leave_app.flags.ignore_validate = True
                    leave_app.flags.ignore_validate_update_after_submit = True
                    leave_app.flags.ignore_links = True
                    leave_app.flags.ignore_mandatory = True

                    # insert & submit the leave application
                    leave_app.insert(ignore_permissions=True)
                    leave_app.submit()

                    frappe.msgprint(f"Leave Application {leave_app.name} created and submitted.")

                    frappe.msgprint(f"✅ Deducted {deduction} day(s) from {lt}")
                    remaining_deduction -= deduction

                    frappe.msgprint(f"remaining balance ⚠️ {remaining_deduction} day(s).")
                    

        if remaining_deduction and remaining_deduction > 0:
            frappe.msgprint(f"⚠️ {remaining_deduction} day(s) could not be deducted — insufficient leave balance.")
            return remaining_deduction
        else:
            frappe.msgprint("✅ Late deduction completed successfully.")
            
            return remaining_deduction
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        frappe.log_error("Error in late adjustment in leaves", str(e))

#for early deduction from leaves
def adjust_early_deduction(employee, violations, early_deduction_factor, hr_settings, doc):
    """
    Deduct early arrival days from the employee's leave balances in the same order
    as defined in 'Sowaan HR Setting' → early_adjustment_leave_types child table.
    """
    try:
        attendance_date = today()        

        #frappe.msgprint(f"late_arrival_violations {violations}") 

        if not violations:
            frappe.msgprint("No violations found — no leave adjustments needed.")
            return
    
        for v in violations:
            attendance_date = v["date"]
            deduction = v["early_departure"]

            total_early_days = deduction * early_deduction_factor

            frappe.msgprint(f"Total Early Days: {total_early_days}")

            if not employee or not total_early_days:
                frappe.throw("Employee and total early days are required")       

            # Get leave types from child table (in the order they appear)
            leave_types = [
                row.leave_type
                for row in sorted(hr_settings.custom_leave_types, key=lambda x: x.idx)
                if row.leave_type
            ]

            if not leave_types:
                frappe.throw("No leave types defined in 'Sowaan HR Setting' for ealry arrival adjustment")
            
            # Ensure a valid Leave Period exists
            leave_period = frappe.db.get_value(
                "Leave Period",
                {"from_date": ["<=", attendance_date], "to_date": [">=", attendance_date]},
                "name"
            )

            #frappe.msgprint(f"Leave period: {leave_period}")

            if not leave_period:
                frappe.throw("No active Leave Period found for today")        

            # Fetch all leave details for the employee
            available_leave = get_leave_details(employee, today())

            frappe.msgprint(f"Early Arrival deduction process started for Employee: {employee}")

            remaining_deduction = total_early_days
            current_balance = 0
            
            if remaining_deduction <= 0:
                frappe.throw("Deduction days must be greater than zero.")

            for lt in leave_types:
                if remaining_deduction <= 0:
                    break

                leave_info = available_leave.get("leave_allocation", {}).get(lt, {})

                if leave_info:
                    current_balance = leave_info.get("remaining_leaves", 0)
                    frappe.msgprint(f"{lt} balance: {current_balance}")
                else:
                    frappe.msgprint(f"No data found for {lt}")
                
                #frappe.msgprint(f"Current Balance {current_balance} Leave Type {lt}")

                if not current_balance or current_balance <= 0:
                    continue  # skip leave types with zero balance
            
                deduction = min(current_balance, remaining_deduction)

                leave_app = frappe.get_doc({
                "doctype": "Leave Application",
                "employee": employee,
                "leave_type": lt,
                "from_date": attendance_date,
                "to_date": attendance_date,
                "half_day": 0,
                "total_leave_days": deduction,  # directly set fractional amount
                "status": "Approved",
                "custom_is_adjusted_leave" : True,
                "leave_approver": "Administrator",             
                "description":  "Adjustment for early departure",
                "custom_salary_slip_reference": doc.name,
                })

                # ignore the restrictions to submit the leave application
                leave_app.flags.ignore_validate = True
                leave_app.flags.ignore_validate_update_after_submit = True
                leave_app.flags.ignore_links = True
                leave_app.flags.ignore_mandatory = True

                # insert & submit the leave application
                leave_app.insert(ignore_permissions=True)
                leave_app.submit()

                frappe.msgprint(f"Leave Application {leave_app.name} created and submitted.")               
                
                
                frappe.msgprint(f"✅ Deducted {deduction} day(s) from {lt}")
                remaining_deduction -= deduction

                #frappe.msgprint(f"remaining balance ⚠️ {remaining_deduction} day(s).")

                #for checking only
                leave_info = available_leave.get("leave_allocation", {}).get(lt, {})

                if leave_info:
                    current_balance = leave_info.get("remaining_leaves", 0)
                    frappe.msgprint(f"{lt} balance: {current_balance}")
                else:
                    frappe.msgprint(f"No data found for {lt}")
                #end checking block

        if remaining_deduction and remaining_deduction > 0:
            frappe.msgprint(f"⚠️ {remaining_deduction} day(s) could not be deducted — insufficient leave balance.")
            return remaining_deduction
        else:
            frappe.msgprint("✅ Early deduction completed successfully.")
            
            return remaining_deduction
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        frappe.log_error("Error in early adjustment in leaves", str(e))

#for half days deduction from leaves
def adjust_halfday_deduction(employee, violations, halfday_deduction_factor, hr_settings, doc):
    """
    Deduct half days from the employee's leave balances in the same order
    as defined in 'Sowaan HR Setting' → half_adjustment_leave_types child table.
    """
    try:

        attendance_date = today()
       
        if not violations:
            frappe.msgprint("No violations found — no leave adjustments needed.")
            return
    
        for v in violations:
            attendance_date = v["date"]
            deduction = v["half_day"]
        
        total_half_days = deduction * halfday_deduction_factor

        #frappe.msgprint(f"Total Half Days: {total_half_days}")

        if not employee or not total_half_days:
            frappe.throw("Employee and total half days are required")       

        # Get leave types from child table (in the order they appear)
        leave_types = [
            row.leave_type
            for row in sorted(hr_settings.custom_leave_types, key=lambda x: x.idx)
            if row.leave_type
        ]

        if not leave_types:
            frappe.throw("No leave types defined in 'Sowaan HR Setting' for half days adjustment")              

        # Ensure a valid Leave Period exists
        leave_period = frappe.db.get_value(
            "Leave Period",
            {"from_date": ["<=", attendance_date], "to_date": [">=", attendance_date]},
            "name"
        )

        #frappe.msgprint(f"Leave period: {leave_period}")

        if not leave_period:
            frappe.throw("No active Leave Period found for today")        

        # Fetch all leave details for the employee
        available_leave = get_leave_details(employee, today())

        frappe.msgprint(f"Hald days deduction process started for Employee: {employee}")

        remaining_deduction = total_half_days
        current_balance = 0
        
        if remaining_deduction <= 0:
           frappe.throw("Deduction days must be greater than zero.")

        for lt in leave_types:
            if remaining_deduction <= 0:
                break

            leave_info = available_leave.get("leave_allocation", {}).get(lt, {})

            if leave_info:
                current_balance = leave_info.get("remaining_leaves", 0)
                #frappe.msgprint(f"{lt} balance: {current_balance}")
            else:
                frappe.msgprint(f"No data found for {lt}")
            
            #frappe.msgprint(f"Current Balance {current_balance} Leave Type {lt}")

            if not current_balance or current_balance <= 0:
                continue  # skip leave types with zero balance
            

            deduction = min(current_balance, remaining_deduction)

            leave_app = frappe.get_doc({
            "doctype": "Leave Application",
            "employee": employee,
            "leave_type": lt,
            "from_date": attendance_date,
            "to_date": attendance_date,
            "half_day": 0,
            "total_leave_days": deduction,  # directly set fractional amount
            "status": "Approved",
            "custom_is_adjusted_leave" : True,
            "leave_approver": "Administrator",             
            "description":  "Adjustment for half day leave",
            "custom_salary_slip_reference": doc.name,
            })

            # ignore the restrictions to submit the leave application
            leave_app.flags.ignore_validate = True
            leave_app.flags.ignore_validate_update_after_submit = True
            leave_app.flags.ignore_links = True
            leave_app.flags.ignore_mandatory = True
            
            # insert & submit the leave application
            leave_app.insert(ignore_permissions=True)
            leave_app.submit()

            frappe.msgprint(f"Leave Application {leave_app.name} created and submitted.")            
            
            frappe.msgprint(f"✅ Deducted {deduction} day(s) from {lt}")
            remaining_deduction -= deduction

            frappe.msgprint(f"remaining balance ⚠️ {remaining_deduction} day(s).")

            #for checking only
            leave_info = available_leave.get("leave_allocation", {}).get(lt, {})

            if leave_info:
                current_balance = leave_info.get("remaining_leaves", 0)
                frappe.msgprint(f"{lt} balance: {current_balance}")
            else:
                frappe.msgprint(f"No data found for {lt}")
            #end checking block

        if remaining_deduction and remaining_deduction > 0:
            frappe.msgprint(f"⚠️ {remaining_deduction} day(s) could not be deducted — insufficient leave balance.")
            return remaining_deduction
        else:
            frappe.msgprint("✅ Half days deduction completed successfully.")
            
            return remaining_deduction
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        frappe.log_error("Error in half days adjustment in leaves", str(e))

#adjust absent in 
def adjust_absent_leaves(employee, start_date, end_date, hr_settings):
    """Automatically adjust 'Absent' attendance records into Casual Leave applications."""

    try:

         # Fetch all absences for this employee in the date range
        absents = frappe.get_all(
            "Attendance",
            filters={
                "employee": employee,
                "status": "Absent",
                "attendance_date": ["between", [start_date, end_date]],
                "docstatus": 1
            },
            fields=["name", "attendance_date"]
        )

        if not absents:
           return  # nothing to process

        # Get leave types from child table (in the order they appear)
        leave_types = [
            row.leave_type
            for row in sorted(hr_settings.custom_leave_types, key=lambda x: x.idx)
            if row.leave_type
        ]

        if not leave_types:
            frappe.throw("No leave types defined in 'Sowaan HR Setting' for absent adjustment")       
        
        #check if any casual leave is available of employee
        for lt in leave_types:            

            available_leave = get_leave_details(employee, today())
            leave_info = available_leave.get("leave_allocation", {}).get(lt, {})

            if leave_info:
                current_balance = leave_info.get("remaining_leaves", 0)
                if current_balance == 0:                  
                    frappe.msgprint(f"No remaining {lt} balance for {employee}")
                    return
            else:
                frappe.msgprint(f"No data found for {lt}")
                return         
            
            used_leaves = 0

            for att in absents:            

                if used_leaves >= current_balance:
                    frappe.msgprint(f"{employee} has used all {lt} balance during adjustment.")
                    break

                # Check if a Leave Application already exists for that date
                existing_leave = frappe.db.exists(
                    "Leave Application",
                    {
                        "employee": employee,
                        "from_date": att.attendance_date,
                        "to_date": att.attendance_date,
                        "leave_type": "Casual Leave",
                        "docstatus": ["!=", 2],  # not cancelled
                    }
                )    
                        
                if not existing_leave:
                    leave_app = frappe.get_doc({
                    "doctype": "Leave Application",
                    "employee": employee,
                    "leave_type": "Casual Leave",
                    "from_date": att.attendance_date,
                    "to_date": att.attendance_date,
                    "half_day": 0,
                    "total_leave_days": 1,  # directly set fractional amount
                    "status": "Approved",
                    "custom_is_adjusted_leave" : True,
                    "leave_approver": "Administrator",             
                    "description":  "Adjustment for absent",                
                    })

                    # ignore the restrictions to submit the leave application
                    leave_app.flags.ignore_validate = True
                    leave_app.flags.ignore_validate_update_after_submit = True
                    leave_app.flags.ignore_links = True
                    leave_app.flags.ignore_mandatory = True
                    
                    # insert & submit the leave application
                    leave_app.insert(ignore_permissions=True)
                    leave_app.submit()

                    used_leaves += 1
                    frappe.msgprint(f"Leave application has been submitted for {employee} for {att.attendance_date}")


    except Exception as e:
        frappe.log_error(
            message=frappe.get_traceback(),
            title=f"Error in absent adjustment for {employee}"
        )
        frappe.msgprint(f"Error adjusting absent leave for {employee}: {e}")

#checkin if late approval is there
def check_late_approval(employee, late_date):
   
        """Check if attendance exists and late is approved"""
        att = frappe.db.get_value(
            "Attendance",
            {"employee": employee, "attendance_date": late_date},
            ["late_entry", "late_approved"],
            as_dict=True,
        )        

        #frappe.msgprint(f"Attendance {att}")

        if not att:
            return False  # no attendance found

        if att.late_entry and att.late_approved:
            frappe.msgprint(f"Late is approved in attendance for {employee} on {late_date}")

            frappe.logger().info(f"Late is approved in attendance for {employee} on {late_date}")
            return True


@frappe.whitelist()
def get_deduction_parent(employee, salary_structure):
    if not frappe.db.exists("DocType", "Deduction Employees") or not frappe.db.exists("DocType", "Deduction Salary Structures"):
        return None
    ded_emp_list = frappe.get_all(
        "Deduction Employees",
        filters={"parenttype": "Sowaan HR Setting"},
        fields=["employee", "parent"],
        ignore_permissions=True
    )
    #frappe.msgprint(f"Deduction Employees {ded_emp_list}")

    ded_ss_list = frappe.get_all(
        "Deduction Salary Structures",
        filters={"parenttype": "Sowaan HR Setting"},
        fields=["salary_structure", "parent"],
        ignore_permissions=True
    )    
    
    #frappe.msgprint(str(type(ded_ss_list)))

    if not ded_emp_list and not ded_ss_list:
        return None

    emp_dict = {emp["employee"]: emp["parent"] for emp in ded_emp_list if isinstance(emp, dict)}
    ss_dict = {ss["salary_structure"]: ss["parent"] for ss in ded_ss_list if isinstance(ss, dict)}
   

    if employee not in emp_dict and salary_structure not in ss_dict:
        return None
    
    return emp_dict.get(employee) or ss_dict.get(salary_structure)

    



