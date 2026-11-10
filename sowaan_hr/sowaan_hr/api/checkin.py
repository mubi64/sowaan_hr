from __future__ import unicode_literals
import json
from tabnanny import check
import frappe
from frappe.utils import nowdate, flt, cstr, cint, getdate, get_datetime
from frappe import _
from datetime import datetime
from pytz import timezone
from timezonefinder import TimezoneFinder
from math import sin, cos, sqrt, atan2, radians
from hrms.hr.doctype.shift_assignment.shift_assignment import (
    get_actual_start_end_datetime_of_shift, get_shifts_for_date, get_shift_details
)
from sowaan_hr.sowaan_hr.api.employee import get_allowed_locations, get_employee_devices, resolve_employee
from sowaan_hr.sowaan_hr.api.api import gen_response


@frappe.whitelist()
def get_my_today_checkins(employee):
    employee = resolve_employee(employee)
    employee_detail = frappe.get_doc("Employee", employee)
    shifts = get_shifts_for_date(
        employee, get_datetime()
    )
    
    today_shift = employee_detail.default_shift if len(shifts) == 0 else shifts[0].shift_type

    today_shift_details = get_shift_details(today_shift, get_datetime())
    if (not today_shift_details):
        today_shift_details = {}
        today_shift_details["actual_start"] = get_datetime().replace(
            hour=0, minute=0, second=0)
        today_shift_details["actual_end"] = get_datetime().replace(
            hour=23, minute=59, second=59)

    # return today_shift
    today_shift_details["employee"] = employee

    checkins = {}
    checkins["ShowCheckInOut"] = "IN"
    st_list = {}
    if today_shift_details.get("shift_type"):
        st_list = frappe.get_doc("Shift Type", today_shift_details.shift_type.name, fields=["*"]) 
    else:
        frappe.throw("Shift is not set")

    if not hasattr(today_shift_details, 'shift_type'):
        return checkins

    checkins["data"] = frappe.db.sql("""
            select 
                log_type, time
                from 
                `tabEmployee Checkin` 
                where 
                employee = %(employee) s and time between %(actual_start) s and %(actual_end) s order by time desc

            """, values=today_shift_details, as_dict=1)

    if st_list:
        if st_list.working_hours_calculation_based_on == "First Check-in and Last Check-out":
            if len(checkins["data"]) > 0:
                checkins["ShowCheckInOut"] = "OUT"
            else:
                checkins["ShowCheckInOut"] = "IN"

        elif st_list.working_hours_calculation_based_on == "Every Valid Check-in and Check-out":
            if len(checkins["data"]) > 0:
                # print(checkins["data"][0].log_type, "Checking check")
                if checkins["data"][0].log_type == "IN":
                    checkins["ShowCheckInOut"] = "OUT"
                else:
                    checkins["ShowCheckInOut"] = "IN"
            else:
                checkins["ShowCheckInOut"] = "IN"

    return checkins


@frappe.whitelist()
def get_checkins(employee, status, from_date, to_date, page):
    # print(employee, status, from_date, to_date, page , "pages checing \n\n\n")
    try:
        pageSize = 20
        page = int(page)

        if (page <= 0):
            return "Page should be greater or equal of 1"

        filters = {
            "time": ["between", (getdate(from_date), getdate(to_date))]
        }
        if (employee):
            filters["employee"] = employee

        if status:
            filters["log_type"] = status

        checkins = frappe.db.get_list(
            "Employee Checkin",
            filters=filters,
            fields=["name", "employee_name", "log_type", "time"],
            order_by="creation desc",
            start=(page-1)*pageSize,
            page_length=pageSize,
        )

        return checkins
    except frappe.PermissionError:
        return gen_response(500, "Not permitted")
    except Exception as e:
        frappe.local.response['http_status_code'] = 500
        frappe.local.response['error_message'] = str(e) 


@frappe.whitelist()
def create_employee_checkin(logtype, employee, time, gps, deviceId, client_id=None, time_verified=None, is_offline_sync=None):
    success = True
    message = ''
    # The app may hold a stale (renamed) Employee ID - see resolve_employee.
    employee = resolve_employee(employee)

    # Idempotency: the mobile app retries a sync if a response is lost (e.g.
    # connection drops right after the server processed the request). If
    # this exact check-in was already recorded, return the existing result
    # instead of inserting a duplicate Employee Checkin.
    if client_id:
        existing = frappe.db.get_value(
            "Employee Checkin",
            {"custom_client_id": client_id},
            ["log_type"],
            as_dict=True,
        )
        if existing:
            return {"success": True, "message": existing.log_type + " already recorded"}

    if (not logtype or not logtype in ('IN', 'OUT') or not employee or not time or not gps or not deviceId):
        success = False
        message = "Something is not right, Attendance cannot be marked"

    if (success):

        # Getting the datetime information from the GPS location came from device
        source_loc = split_string_to_float(gps, ',')
        obj = TimezoneFinder()
        gps_timezone = obj.timezone_at(lat=source_loc[0], lng=source_loc[1])
        if not gps_timezone:
            # No timezone for these coordinates (e.g. near a boundary or
            # offshore): fall back to the site timezone instead of crashing
            # with a 500, which the mobile app reports as "You're offline".
            gps_timezone = frappe.utils.get_system_timezone()

        is_offline_sync = cint(is_offline_sync)
        time_verified = cint(time_verified)

        if is_offline_sync and time_verified:
            # Offline check-in being synced after the fact: `datetime.now()`
            # here would be the moment of sync, not the moment the employee
            # actually checked in. `time` was reconstructed on-device from a
            # tamper-resistant monotonic clock anchored to a trusted server
            # timestamp (see the sowaanerp_hr app's DeviceClock) rather than
            # the device's editable wall clock, so it can be trusted here.
            # The app sends it as a naive UTC string (no timezone suffix), so
            # it must be localized to UTC explicitly before converting to the
            # GPS location's timezone - otherwise Python's astimezone() would
            # silently assume the server's own local timezone instead.
            gps_time = timezone('UTC').localize(get_datetime(time)).astimezone(timezone(gps_timezone))
        else:
            # Live check-in (or an offline one whose time could never be
            # verified): never trust the device's wall clock - stamp with
            # the server's own clock at the moment of the request.
            gps_time = datetime.now(timezone(gps_timezone))

        gps_time_formatted = gps_time.strftime('%Y-%m-%d %H:%M:%S')

        # verifying registered device
        devices = get_employee_devices(employee)
        if (len(devices) > 0):
            for idx, x in enumerate(devices['devices']):
                if (deviceId == x['device_id']):
                    success = True
                    break
                else:
                    success = False
                    message = "Device is not registered, Attendance cannot be marked\n\nDevice Id: "+deviceId

        else:
            if not frappe.db.exists("Employee Device Registration", [["Employee Device Registration Item", "device_id", "=", deviceId]]):
                new_device_registeration = frappe.new_doc(
                    "Employee Device Registration")
                new_device_registeration.user = frappe.session.user,
                new_device_registeration.employee = employee
                new_device_registeration.append("employee_devices", {
                    "device_id": deviceId
                })
                new_device_registeration.insert(ignore_permissions=True)
            else:
                success = False
                message = "Device ID already exists. Please choose a different one."


        # verifying allowed location
        if (success):
            locations = get_allowed_locations(employee=employee)
            matched_location = {}
            if len(locations) > 0:
                for idx, x in enumerate(locations['locations']):
                    distance = round(get_distance(x['location_gps'], gps), 0)
                    if (distance <= x['allowed_radius']):
                        matched_location = x
                        success = True
                        break
                    else:
                        success = False
                        message = "Not in a allowed location, Attendance cannot be marked\n\nGPS: "+gps
            else:
                success = False
                message = "Not in a allowed location, Attendance cannot be marked\n\nGPS: "+gps

        # marking checkin
        if (success and matched_location):
            # shift_actual_timings = get_actual_start_end_datetime_of_shift(
            #     employee, get_datetime(), True
            # )
            # today_shift = shift_actual_timings[2]

            checkin = frappe.new_doc("Employee Checkin")
            checkin.user = frappe.session.user
            # if(today_shift):
            #     checkin.shift = today_shift.shift_type.name
            checkin.employee = employee
            checkin.log_type = logtype
            # datetime.strptime(gps_time, '%d-%m-%Y %H:%M')
            checkin.time = gps_time_formatted
            checkin.device_id = deviceId
            checkin.marked_gps = gps
            # HRMS rejects check-ins without latitude/longitude when
            # HR Settings > "Allow Geolocation Tracking" is enabled (and
            # validates the distance from the shift location with them).
            if checkin.meta.has_field("latitude"):
                checkin.latitude = source_loc[0]
                checkin.longitude = source_loc[1]
            checkin.gps_location = x['name']
            if client_id:
                checkin.custom_client_id = client_id
            checkin.custom_time_verified = time_verified

            checkin.insert(ignore_permissions=True)
            if checkin.shift:
                shift = frappe.get_doc("Shift Type", checkin.shift)
                print(shift, "Checking Shift Values \n\n\n\n")
                if shift:
                    shift.last_sync_of_checkin = gps_time_formatted
                    shift.save(ignore_permissions=True)

            success = True
            message = logtype+" recorded from " + \
                matched_location['location_name']+" at " + \
                gps_time_formatted+"\n\nGPS: "+gps

    return {"success": success, "message": message}
    # print(logtype, employee, time, gps, deviceId)
    # return logtype, employee, time, gps, deviceId


@frappe.whitelist()
def create_employee_checkin_multi(data):
    checkin_data = json.loads(data)
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
