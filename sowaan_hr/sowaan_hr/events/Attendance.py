import frappe
from datetime import timedelta
from frappe.utils import get_datetime

def late_approval(self, method):
    # frappe.msgprint("Late Approval")
    approval = frappe.get_all("Late Approval Request", filters={
    "employee":["=",self.employee],
    "docstatus": ["=", 1],
    "late_date": ["=", self.attendance_date]
    })

    if(len(approval) > 0):
        self.late_approved = True



def handle_half_day(self, method):
    if self.shift:
        is_half_day = frappe.db.get_value('Shift Type', self.shift, ['custom_is_half_day_fix', 'custom_half_day_start_time', 'custom_half_day_end_time', 'start_time', 'end_time', 'required_hours'], as_dict=True)
        if is_half_day.required_hours:
            self.custom_required_hours = is_half_day.required_hours
        if is_half_day.custom_is_half_day_fix:
            start_time = is_half_day.custom_half_day_start_time
            end_time = is_half_day.custom_half_day_end_time
            if not start_time:
                start_time = is_half_day.start_time
            if not end_time:
                end_time = is_half_day.end_time
            if start_time and end_time:
                if self.in_time and self.out_time:
                    # frappe.throw(str(get_datetime(self.in_time).time()))
                    checkin_time = get_datetime(self.in_time).time()
                    checkout_time = get_datetime(self.out_time).time()
                    if checkin_time and checkout_time:
                        checkin_time_td = timedelta(hours=checkin_time.hour, minutes=checkin_time.minute, seconds=checkin_time.second)
                        checkout_time_td = timedelta(hours=checkout_time.hour, minutes=checkout_time.minute, seconds=checkout_time.second)
                        if start_time <= checkin_time_td <= end_time or start_time <= checkout_time_td <= end_time:
                            self.status = 'Half Day'

def after_insert_attendance(doc, method):
    if frappe.db.get_value('Employee', doc.employee, 'custom_allow_overtime'):
        if doc.custom_required_hours and doc.working_hours:
            ot_hours = doc.working_hours - doc.custom_required_hours
            if ot_hours > 0:
                existing_ot = frappe.db.get_value('Employee Overtime',
                    {
                        'employee': doc.employee,
                        'overtime_date': doc.attendance_date
                    },
                    ['name', 'docstatus'], as_dict=True
                )

                if existing_ot:
                    if existing_ot.docstatus == 1:
                        ot_doc = frappe.get_doc('Employee Overtime', existing_ot.name)
                        ot_doc.cancel()
                        
                        create_overtime(doc, ot_hours)

                    elif existing_ot.docstatus == 0:
                        ot_doc = frappe.get_doc('Employee Overtime', existing_ot.name)
                        ot_doc.from_attendance = doc.name
                        ot_doc.overtime_hours = ot_hours
                        ot_doc.approved_overtime_hours = ot_hours
                        ot_doc.save()
                else:
                    create_overtime(doc, ot_hours)


def create_overtime(doc, ot_hours):
    overtime = frappe.new_doc('Employee Overtime')
    overtime.from_attendance = doc.name
    overtime.employee = doc.employee
    overtime.overtime_date = doc.attendance_date
    overtime.overtime_hours = ot_hours
    overtime.approved_overtime_hours = ot_hours
    overtime.insert()
                        
                