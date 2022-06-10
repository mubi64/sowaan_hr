from __future__ import unicode_literals
import json
from tabnanny import check
import frappe
from frappe.utils import nowdate, flt, cstr, getdate, get_datetime
from frappe import _
from datetime import datetime
import pytz
from tzwhere import tzwhere
from math import sin, cos, sqrt, atan2, radians
from erpnext.hr.doctype.shift_assignment.shift_assignment import (
	get_actual_start_end_datetime_of_shift,
)
from sowaan_hr.sowaan_hr.api.employee import get_allowed_locations, get_employee_devices


@frappe.whitelist()
def get_my_today_checkins(employee):
    shift_actual_timings = get_actual_start_end_datetime_of_shift(
        employee, get_datetime(), True
    )
    today_shift = shift_actual_timings[2]
    if(not today_shift):
        today_shift = {}
        today_shift["actual_start"] = get_datetime().replace(hour=0, minute=0, second=0)
        today_shift["actual_end"] = get_datetime().replace(hour=23, minute=59, second=59)
    
    #return today_shift
    today_shift["employee"] = employee
    
    checkins = frappe.db.sql("""
        select 
            log_type,
            case when log_type='IN' then min(time)
            else max(time)
            end time
            from 
            `tabEmployee Checkin` 
            where 
            employee = %(employee) s and time between %(actual_start) s and %(actual_end) s group by log_type

        """, values=today_shift, as_dict=1)
   
    return checkins

@frappe.whitelist()
def get_checkins(employee, from_date, to_date):
    filters = {
        "time": ["between", (getdate(from_date), getdate(to_date))]
    }
    if(employee):
        filters["employee"] = employee
    
    checkins = frappe.db.get_list(
        "Employee Checkin",
        filters=filters,
        fields=["name","employee_name","log_type","time"],
        order_by="creation desc"
    )
  
    return checkins

@frappe.whitelist()
def create_employee_checkin(logtype, employee, time, gps, deviceId):
    success = True
    message = ''

    if(not logtype or not logtype in ('IN', 'OUT') or not employee or not time or not gps or not deviceId):
        success = False
        message = "Something is not right, Attendance cannot be marked"

    if(success):

        # source_loc = split_string_to_float(gps, ',')
        # tzwhere_obj = tzwhere.tzwhere()
        # timezone_str = tzwhere_obj.tzNameAt(source_loc[0], source_loc[1]) # Seville coordinates
        
        # timezone = pytz.timezone(timezone_str)
        # time = datetime.now()
        
        #verifying registered device
        devices = get_employee_devices(employee)
        if(len(devices) > 0):
            for idx, x in enumerate(devices['devices']):
                if(deviceId == x['device_id']):
                    success = True
                    break
                else:
                    success = False
                    message = "Device is not registered, Attendance cannot be marked"

        else:
            new_device_registeration = frappe.new_doc("Employee Device Registration")
            new_device_registeration.user = frappe.session.user,
            new_device_registeration.employee = employee
            new_device_registeration.append("employee_devices",{
                "device_id":deviceId
            })
            new_device_registeration.insert(ignore_permissions=True)
    
        #verifying allowed location
        if(success):
            locations = get_allowed_locations(employee=employee)
            matched_location = {}
            if len(locations) > 0:
                for idx, x in enumerate(locations['locations']):
                    distance = round(get_distance(x['location_gps'], gps),0)
                    if(distance <= x['allowed_radius']):
                        matched_location = x
                        success = True
                        break
                    else:
                        success = False
                        message = "Not in a allowed location, Attendance cannot be marked"
            else:
                success = False
                message = "Not in a allowed location, Attendance cannot be marked"

        #marking checkin
        if(success and matched_location):
            checkin = frappe.new_doc("Employee Checkin")
            checkin.user = frappe.session.user,
            checkin.employee = employee
            checkin.log_type = logtype
            checkin.time = datetime.strptime(time, '%d-%m-%Y %H:%M')
            checkin.device_id = deviceId
            checkin.marked_gps = gps
            checkin.gps_location = x['name']
           
            checkin.insert(ignore_permissions=True)
            
            success = True
            message = logtype+" recorded from "+matched_location['location_name']
        

    
    return {"success":success, "message":message}
    print(logtype, employee, time, gps, deviceId)
    return logtype, employee, time, gps, deviceId

@frappe.whitelist()
def create_employee_checkin_multi(data):
    checkin_data = json.loads(data)
    print(checkin_data)
    return checkin_data

def split_string_to_float(text, symbol):
 return [float(s) for s in text.split(symbol)]

def get_distance(source, destination):
    # approximate radius of earth in km
    R = 6373.0
    source_loc = split_string_to_float(source, ',')
    dest_loc = split_string_to_float(destination, ',')

    lat1 = radians(source_loc[0])
    lon1 = radians(source_loc[1])
    lat2 = radians(dest_loc[0])
    lon2 = radians(dest_loc[1])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c

    return distance*1000