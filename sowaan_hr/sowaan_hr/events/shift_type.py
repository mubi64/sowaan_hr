import frappe

def half_day_msg(self, method):
    if self.custom_is_half_day_fix:
        if not self.custom_half_day_start_time and not self.custom_half_day_end_time:
            frappe.throw('Please set the start and end time for half day.')