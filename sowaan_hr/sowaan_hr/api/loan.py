import frappe
from frappe.desk.form.load import getdoc , getdoctype
from sowaan_hr.sowaan_hr.api.workflow import apply_actions
from sowaan_hr.sowaan_hr.api.employee import get_allowed_employees, get_current_emp, get_employee_info



@frappe.whitelist()
def get_loans(employee, page):
    pageSize = 15
    page = int(page)

    if(page <= 0):
        return "Page should be greater or equal of 1"

    filters = {}

    allowed_employees = get_allowed_employees()
    
    if employee:
        if (len(allowed_employees) > 0 and employee in allowed_employees) or len(allowed_employees) == 0:
            filters["employee"] = employee
        else:
            filters["employee"] = get_current_emp()
    elif len(allowed_employees) > 0:
        filters["employee"] = ["in", allowed_employees]
    
    loans = frappe.db.get_list(
        "Loan Application",
        filters={"applicant":employee},
        fields=[
           "name",
           "applicant",
           "applicant_name",
           "description",
            "posting_date",
            "status",
            "loan_type",
            "is_term_loan",
            "loan_amount",
            "repayment_method",
            "total_payable_amount",
            "repayment_periods",
            "repayment_amount",
            "workflow_state",
        ],
        order_by="modified DESC",
        start=(page-1)*pageSize,
        page_length=pageSize
    )
    
    return loans


@frappe.whitelist()
def get_loan_types():
    data=frappe.db.get_list("Loan Type",fields = ['name','is_term_loan'])
    return data


@frappe.whitelist()
def create_loan(employee,loanType,loanAmount,isTermLoan,repaymentMethod,repaymentAmount,repaymentMonths,loanApprover):
    try:
        print("hello",{
                   "doctype": "Loan Application",
                    "applicant": employee,
                    "loan_type":loanType,
                    "loan_amount":float(loanAmount),
                    "repayment_amount":float(repaymentAmount),
                    "repayment_method":repaymentMethod,
                    "loan_approver":loanApprover,
                    "is_term":isTermLoan
        })
                 
                
        if(isTermLoan == '1'):
            if(repaymentMethod=="no repayment"):
                    raise Exception("Repayment Method should not empty")
            
            if(repaymentMethod == "Repay Fixed Amount per Period"):
                print("in if")
                loan = frappe.get_doc({
                    "doctype": "Loan Application",
                    "applicant": employee,
                    "loan_type":loanType,
                    "loan_amount":float(loanAmount),
                    "repayment_amount":float(repaymentAmount),
                    "repayment_method":repaymentMethod,
                    "loan_approver":loanApprover
                })
                loan.insert()
            else:
               
                loan = frappe.get_doc({
                            "doctype": "Loan Application",
                            "applicant": employee,
                            "loan_type":loanType,
                            "loan_amount":float(loanAmount),
                            "repayment_method":repaymentMethod,
                            "repayment_periods":int(repaymentMonths),
                            "loan_approver":loanApprover
                        })
                loan.insert()


        else:
             loan = frappe.get_doc({
                    "doctype": "Loan Application",
                    "applicant": employee,
                    "loan_type":loanType,
                    "loan_amount":float(loanAmount),
                    "loan_approver":loanApprover
                })
             loan.insert()

             

        # frappe.db.commit()

        name = get_first_doc_name("Loan Application", orderBy="modified DESC")
        
        return name
    
    except frappe.ValidationError as e:
        raise Exception(str(e))


@frappe.whitelist()
def update_loan(name,employee,loanType,loanAmount,isTermLoan,repaymentMethod,repaymentAmount,repaymentMonths,loanApprover):
    print('termLoan',repaymentAmount)
    # try:
    doc = frappe.get_doc('Loan Application',name)               
    if(isTermLoan == 1):
        if(repaymentMethod == "Repay Fixed Amount per Period"):
            print("in if")
            doc.applicant = employee
            doc.loan_type=loanType
            doc.loan_amount=float(loanAmount)
            doc.repayment_amount=float(repaymentAmount)
            doc.repayment_method=repaymentMethod
            doc.loan_approver=loanApprover
            doc.save()
            # frappe.db.set_value('Loan Application',name, {
            #         "applicant": employee,
            #         "loan_type":loanType,
            #         "loan_amount":float(loanAmount),
            #         "repayment_amount":float(repaymentAmount),
            #         "repayment_method":repaymentMethod,
            #         "loan_approver":loanApprover
            #     })
           
    
        else:
            doc.applicant = employee
            doc.loan_type=loanType
            doc.loan_amount=float(loanAmount)
            doc.repayment_periods=int(repaymentMonths)
            doc.repayment_method=repaymentMethod
            doc.loan_approver=loanApprover
            doc.save() 
            # frappe.db.set_value('Loan Application',name, {
            #             "applicant": employee,
            #             "loan_type":loanType,
            #             "loan_amount":float(loanAmount),
            #             "repayment_method":repaymentMethod,
            #             "repayment_periods":int(repaymentMonths),
            #             "loan_approver":loanApprover
            #     })
                
    else:
        doc.applicant = employee
        doc.loan_type=loanType
        doc.loan_amount=float(loanAmount)
        doc.loan_approver=loanApprover
        doc.save() 
        # frappe.db.set_value('Loan Application',name, {
        #             "applicant": employee,
        #             "loan_type":loanType,
        #             "loan_amount":float(loanAmount),
        #             "loan_approver":loanApprover
        # })

    data = get_first_doc_name("Loan Application", orderBy="modified DESC")
    
    return data

    # except frappe.ValidationError as e:
    #     raise Exception(str(e))



@frappe.whitelist()
def loan_up_sbm(name, action):
    doc = frappe.db.get_list("Loan Application", filters={
                             "name": name}, fields=["*"])

    print('myaction',action)
    check_state = frappe.db.get_list('Workflow State',filters={'name': action}, fields=['*'])
    print(check_state,'myval')
    if(len(check_state) != 0):
        frappe.db.set_value('Loan Application',name, {
        'status' :action,
        })
        data = frappe.get_doc("Loan Application",name)
        val = apply_actions(frappe.parse_json(data),action)
        frappe.db.set_value('Loan Application',name, {
        'workflow_state' :val.workflow_state,
        })
        
        return val
    else:
        frappe.db.set_value('Loan Application',name, {
        'status' :'Open',
        })
        data = frappe.get_doc("Loan Application",name)
        val = apply_actions(frappe.parse_json(data),action)
        frappe.db.set_value('Loan Application',name, {
        'workflow_state' :val.workflow_state,
        })
        
        return val


def get_first_doc_name(doctype, orderBy):
    doc = frappe.db.get_list(doctype, order_by=orderBy)
    if doc:
        return doc[0]
    else:
        return None