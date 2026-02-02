frappe.pages["ess"].on_page_show = function (wrapper) {

    if (wrapper.__ess_initialized) return;
    wrapper.__ess_initialized = true;

    guard_and_render_ess(wrapper);

    
};

let ess_guard_checked = false;
let turnover_month_control = null;
let current_turnover_by = "department";


function guard_and_render_ess(wrapper) {

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.is_employee_user",
        callback: r => {

            //console.log("ESS access:", r.message);

            if (!r.message) {
                frappe.msgprint({
                    title: __("Access Not Permitted"),
                    message: __("You are not allowed to access the Employee Self Service dashboard."),
                    indicator: "red"
                });

                setTimeout(() => frappe.set_route("home"), 2000);
                return;
            }

            // ✅ ACCESS OK → BUILD DASHBOARD
            render_ess_page(wrapper);
        }
    });
}
function render_ess_page(wrapper) {

    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Employee Self Service",
        single_column: true
    });

    setTimeout(() => {
    const titleWrap = wrapper.querySelector(".page-title");
    const titleText = wrapper.querySelector(".page-title .title-text");

    if (!titleWrap || !titleText) return;

    titleText.innerHTML = `
        <span class="ess-title-icon">
            <i class="fa fa-id-card"></i>
        </span>
        <span class="ess-title-label">Employee Self Service</span>
    `;
}, 0);

    const container = wrapper.querySelector(".layout-main-section");
    if (!container) return;

    container.innerHTML = `
    <div class="ess-dashboard" id="ess-dashboard">       

            <!-- KPI STRIP -->
            <div class="ess-kpi-strip">

                <div class="ess-kpi-card ess-profile-card kpi-orange">
                    <div class="ess-card-title"><i class="fa fa-user"></i> Profile</div>
                    <div class="ess-profile-body" id="ess-login-profile">
                        <div class="ess-muted">Loading...</div>
                    </div>
                    <div class="kpi-line"></div>
                </div>

                <div class="ess-kpi-card kpi-blue">
                    <div class="ess-card-title"><i class="fa fa-users"></i> Reporting To You</div>
                    <div class="kpi-main" id="kpi-reporting">–</div>
                    <div class="kpi-sub" id="kpi-reporting-name">–</div>
                    <div class="kpi-line"></div>
                </div>

                <div class="ess-kpi-card kpi-green" data-route="/app/employee?status=Active">
                    <div class="ess-card-title"><i class="fa fa-check-circle"></i> Active Employees</div>
                    <div class="kpi-main" id="kpi-active">–</div>
                    <div class="kpi-sub">Company Wise</div>
                    <div class="kpi-line"></div>
                </div>

                <div class="ess-kpi-card kpi-purple" data-route="/app/appraisal?docstatus=0">
                    <div class="ess-card-title"><i class="fa fa-hourglass-half text-warning"></i>Pending Appraisals</div>
                    <div class="kpi-main" id="kpi-appraisal-days">– Days</div>
                    <div class="kpi-sub" id="kpi-appraisal-count">– Appraisals</div>
                    <div class="kpi-line"></div>
                </div> 

                <div class="ess-card ess-pending-requests-card kpi-silver">
                    <div class="ess-card-header">
                        <div class="ess-card-header-row">
                            <div class="ess-card-title">
                                <i class="fa fa-clock-o ess-card-title-icon"></i>
                                Pending Requests & Approvals
                            </div>
                        </div>

                        <!-- 🔹 Tabs -->
                        <div class="ess-tabs" id="ess-pending-tabs">
                            <div class="ess-tab active" data-tab="pending_for_me">
                                Approvals
                            </div>
                            <div class="ess-tab" data-tab="sent_by_me">
                                Requests
                            </div>
                        </div>
                        <div class="kpi-line"></div>
                    </div>

                    <!-- 🔹 Scrollable content -->
                    <div id="ess-pending-requests" class="ess-pending-list">

                        <!-- 🔹 Loading placeholder (DEFAULT) -->
                        <div class="ess-loading" data-loading="pending_for_me">
                            Loading pending approvals…
                        </div>

                    </div>
                </div>


                <div class="ess-kpi-card ess-compliance-expiry-card kpi-purple">
                    <div class="ess-card-title">
                        <i class="fa fa-shield"></i>
                        Employee Compliance & Expiry
                    </div>

                    <div class="ess-compliance-expiry-list" id="ess-compliance-expiry">
                        <div class="ess-muted">Loading...</div>
                    </div>

                    <div class="kpi-line"></div>
                </div>



                <div class="ess-kpi-card ess-leave-card kpi-blue">
                    <div class="ess-card-title">Leave Balance</div>               

                    <!-- Leave list -->
                   <div id="leave-employee-link-control"></div>
                    <div id="ess-leave-balance-list">
                        <div class="ess-muted">
                            Select an employee to view leave balance
                        </div>
                    </div>
                    <div class="kpi-line"></div>
                </div>

                <div class="ess-kpi-card ess-attendance-card">

                    <div class="ess-card-header-row">
                        <div class="ess-card-title">
                            Today’s Attendance <span class="ess-sub">(Reporting Employees</span>
                        </div>
                        <i class="fa fa-home ess-card-action"></i>
                        </div>                        

                        <div class="ess-attendance-grid" id="ess-today-attendance">
                            <div class="ess-muted">Loading...</div>
                        </div>

                        <!-- ✅ MUST BE LAST CHILD OF CARD -->
                        <div class="kpi-line"></div>

                        </div>
                    </div>
                    <div class="ess-charts-grid">

                    <!-- HEADCOUNT -->
                    <div class="ess-card ess-headcount-card">
                        <div class="ess-card-header-row">
                            <div class="ess-card-title">
                                Employee Headcount Breakdown
                            </div>
                            <i class="fa fa-external-link ess-card-action"></i>
                    </div>

                    <div class="ess-tabs">
                        <button class="ess-tab active" data-headcount="department">Department</button>
                        <button class="ess-tab" data-headcount="branch">Branch</button>
                        <button class="ess-tab" data-headcount="employment_type">Employment Type</button>
                    </div>

                    <!-- 🔑 size controller -->
                    <div class="ess-chart-wrap">
                        <div id="ess-headcount-chart"></div>
                    </div>
                    
                </div>                         

                <!-- NATIONALITY -->
                <div class="ess-card">
                    <div class="ess-card-header">
                        Employee Nationality
                        <i class="fa fa-external-link chart-action"
                        onclick="window.open('/app/employee','_blank')"></i>
                    </div>

                    <!-- 🔑 size controller -->
                    <div class="ess-chart-wrap ess-chart-wrap--donut">
                        <div id="nationality-chart"></div>
                    </div>                   
                </div>            


                <div class="ess-card ess-turnover-card kpi-silver">

                    <!-- HEADER -->
                    <div class="ess-card-header">

                        <!-- Row 1: Title -->
                        <div class="ess-card-header-row">
                            <div class="ess-card-title">
                                <i class="fa fa-random ess-card-title-icon"></i>
                                Employee Turnover Ratio
                            </div>
                        </div>

                        <!-- Row 2: Month picker (moved here) -->
                        <div class="ess-card-header-row">
                            <div class="ess-card-control">Month
                                <div id="turnover-month-picker"></div>
                            </div>
                        </div>

                        <!-- Tabs (unchanged) -->
                        <div class="ess-tabs" id="ess-turnover-tabs">
                            <div class="ess-tab active" data-by="department">Department</div>
                            <div class="ess-tab" data-by="branch">Branch</div>
                            <div class="ess-tab" data-by="employment_type">Employment Type</div>
                        </div>

                    </div>

                    <!-- BODY -->
                    <div class="ess-card-body">
                        <div
                            id="ess-turnover-chart"
                            class="ess-chart-container ess-turnover-chart">
                        </div>
                    </div>

                </div>


                <div class="ess-card">
                    <div class="ess-card-header">
                        Monthly Attendance Trend (Last 6 Months)
                    </div>
                    <div id="monthly-attendance-trend-2"></div>
                </div>

                <!-- NET PAYROLL -->
                <div class="ess-card ess-netpay-box">
                    <div class="ess-card-header" id="net-payroll-title">Net Payroll Breakdown (Monthly)</div>
                    <div class="ess-filter-label">Month</div>
                    <div id="net-payroll-month-field"></div>

                    <div class="ess-tabs">
                        <button class="ess-tab active" data-netpay="department">Department</button>
                        <button class="ess-tab" data-netpay="branch">Branch</button>
                        <button class="ess-tab" data-netpay="employment_type">Employment Type</button>
                    </div>
                    
                    <!-- 🔑 size controller -->
                    <div class="ess-chart-wrap">
                        <div id="net-payroll-chart"></div>
                    </div>
                   
                </div> 

                
                <!-- NET PAYROLL SUMMARY -->
                    <div class="ess-card ess-netpay-summary-card ess-netpay-box">
                        <div class="ess-card-header">
                            Net Payroll Summary
                        </div>
                        
                        <!-- Month -->
                        <div id="net-payroll-summary-month"></div>

                        <!-- Tabs (same as chart) -->
                        <div class="ess-tabs">
                            <button class="ess-tab active" data-netpay-summary="department">
                                Department
                            </button>
                            <button class="ess-tab" data-netpay-summary="branch">
                                Branch
                            </button>
                            <button class="ess-tab" data-netpay-summary="employment_type">
                                Employment Type
                            </button>
                        </div>

                        <!-- Breakdown list -->
                        <div class="ess-netpay-summary-list" id="net-payroll-summary-list">
                            <div class="ess-muted">Loading...</div>
                        </div>

                        
                    </div>

                    <div class="ess-card ess-netpay-summary-card">
                        <div class="ess-card-header">
                            Net Payroll Summary (Year)
                        </div>
                        <div class="ess-filter-label">Year</div>
                        <!-- Year Picker -->
                       <select id="net-payroll-year-select" class="input-with-feedback">
                        </select>


                        <!-- Tabs -->
                        <div class="ess-tabs">
                            <button class="ess-tab active" data-netpay-year="department">
                                Department
                            </button>
                            <button class="ess-tab" data-netpay-year="branch">
                                Branch
                            </button>
                            <button class="ess-tab" data-netpay-year="employment_type">
                                Employment Type
                            </button>
                        </div>

                        <!-- Breakdown -->
                        <div class="ess-netpay-summary-list" id="net-payroll-year-summary-list">
                            <div class="ess-muted">Loading...</div>
                        </div>
                    </div>


            </div>


        </div>  
`;

    let ESS_ALLOWED_EMPLOYEES = [];
    let turnover_month_control = null;

    inject_styles();
    bind_events();

    // 🔥 DATA LOADERS (SAFE)
    setTimeout(() => {
        init_ess_data();
    }, 0);
}




/* =====================================================
   INIT DATA
===================================================== */

function init_ess_data() {
    
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_accessible_employees",
        callback: r => {
            ESS_ALLOWED_EMPLOYEES = r.message || [];
        }
    });

    // =============================
// 🔹 FAST / USER-CRITICAL
// =============================
load_login_employee_profile();
init_leave_balance_card();        // ✅ should appear instantly
load_kpis();

// =============================
// 🔹 MEDIUM
// =============================
load_today_attendance();
load_compliance_and_expiry();

// =============================
// 🔹 HEAVY → defer to next tick
// =============================
setTimeout(() => {
    init_pending_requests_tabs();
}, 0);

// =============================
// 🔹 VERY HEAVY (charts) → defer more
// =============================
setTimeout(() => {
    load_headcount_chart("department");
    load_nationality_chart();
    load_monthly_attendance_trend();

    make_net_payroll_month_picker();
    load_net_payroll_chart("department");

    make_net_payroll_summary_month_picker();
    load_net_payroll_summary();

    init_net_payroll_year_dropdown();
    load_net_payroll_year_summary();

    init_turnover_month_picker();
    init_turnover_tabs();
    load_turnover_chart("department");


}, 50);

    

}

/* =====================================================
   STYLES
===================================================== */

function inject_styles() {
    if (document.getElementById("ess-style")) return;

    const style = document.createElement("style");
    style.id = "ess-style";
    style.innerHTML = `

        /* ================= PAGE TITLE – EMPLOYEE SELF SERVICE ================= */   
         
        /* =====================================================
        DASHBOARD TITLE CARD
        ===================================================== */
        /* ================= PAGE TITLE – ESS ================= */

        [data-page-route="ess"] .page-title {
            display: flex;
            align-items: center;
            gap: 10px;

            padding: 10px 16px;
            border-radius: 14px;

            background: linear-gradient(
                90deg,
                rgba(59,130,246,0.08),
                rgba(99,102,241,0.04)
            );
        }

        /* Icon badge */
        [data-page-route="ess"] .ess-title-icon {
            width: 34px;
            height: 34px;
            border-radius: 10px;

            display: flex;
            align-items: center;
            justify-content: center;

            background: linear-gradient(135deg, #3b82f6, #6366f1);
            color: #fff;

            font-size: 16px;
            box-shadow: 0 6px 14px rgba(59,130,246,.35);
        }

        /* Title text */
        [data-page-route="ess"] .ess-title-label {
            font-size: 18px;
            font-weight: 800;
            letter-spacing: 0.02em;
            color:rgb(10, 39, 107);
        }

        /* Subtle underline */
        [data-page-route="ess"] .page-title::after {
            content: "";
            display: block;
            height: 3px;
            width: 140px;
            margin-top: 6px;
            border-radius: 4px;
            background: linear-gradient(90deg, #60a5fa, #818cf8);
        }

        
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            [data-page-route="ess"] .ess-title-text {
                font-size: 18px;
            }
        }

        [data-page-route="ess"] .page-head {
            border-bottom: none !important;
            box-shadow: none !important;
            padding-bottom: 2px;
        }

        /* Title container */
        [data-page-route="ess"] .page-title {
            display: flex;
            align-items: center;
            gap: 2px;
        }

        /* ICON */
        .ess-title-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;

            display: flex;
            align-items: center;
            justify-content: center;

            background: linear-gradient(135deg, #3b82f6, #6366f1);
            color: #ffffff;

            font-size: 18px;
            box-shadow: 0 6px 14px rgba(59, 130, 246, 0.35);

            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        /* ICON HOVER */
        [data-page-route="ess"] .page-title:hover .ess-title-icon {
            transform: translateY(-2px) scale(1.05);
            box-shadow: 0 10px 24px rgba(59, 130, 246, 0.45);
        }

        /* TITLE TEXT */
        .ess-title-text {
            font-size: 14px;
            font-weight: 500;
            color: #0f172a;
            letter-spacing: -0.3px;
        }

        /* SUBTLE FADE-IN */
        .ess-title-icon,
        .ess-title-text {
            animation: essTitleFade 0.35s ease-out;
        }

        @keyframes essTitleFade {
            from {
                opacity: 0;
                transform: translateY(4px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* ================= ESS PAGE TOP SPACE FIX ================= */

        /* Remove extra page head padding */
        [data-page-route="ess"] .page-head {
            padding-top: 4px !important;
            padding-bottom: 4px !important;
            min-height: unset !important;
        }

        /* Reduce content top padding */
        [data-page-route="ess"] .page-content {
            padding-top: 4px !important;
        }

        /* Remove extra margin above dashboard */
        [data-page-route="ess"] .ess-dashboard {
            margin-top: 0 !important;
            padding-top: 4px !important;
        }

        /* Reduce navbar shadow gap effect */
        .navbar {
            box-shadow: none;
        }

        /* ================= REMOVE DEFAULT PAGE TITLE LINE ================= */

        [data-page-route="ess"] .page-head {
            border-bottom: none !important;
            box-shadow: none !important;
        }

        [data-page-route="ess"] .page-head {
            padding-bottom: 6px !important;
        }

        [data-page-route="ess"] .page-content {
            padding-top: 0 !important;
        }
        

        [data-page-route="ess"] .title-area {
        padding-top: 6px !important;
        padding-bottom: 6px !important;
        }

        /* ================= FORCE SINGLE-LINE TITLE ================= */

        [data-page-route="ess"] .page-title {
            flex-wrap: nowrap !important;
            white-space: nowrap !important;
        }

        [data-page-route="ess"] .ess-title-text {
            white-space: nowrap !important;
        }

        .ess-title-icon {
            width: 20px;
            height: 20px;
            font-size: 14px;
        }

        /* ================= PAGE BACKGROUND ================= */

        body[data-route="ess"],
        [data-page-route="ess"] {
            background: #fff !important;
            ) ;
        }

        /* ================= DASHBOARD GLASS CONTAINER ================= */

        [data-page-route="ess"] .layout-main-section {
            background: transparent !important;
        }

        /* main dashboard shell */
        [data-page-route="ess"] .ess-dashboard {
            margin: 24px auto;
            padding: 22px;

            max-width: 1600px;

            background: linear-gradient(
                180deg,
                rgba(241, 245, 249, 0.85),
                rgba(226, 232, 240, 0.85)
            );

            border-radius: 28px;

            box-shadow:
                0 30px 80px rgba(15, 23, 42, 0.55),
                inset 0 1px 0 rgba(255,255,255,0.4);

            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
        }

        /* ================= PAGE TITLE ================= */

        [data-page-route="ess"] .page-title {
            color: #e0e7ff !important;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        [data-page-route="ess"] .page-title::after {
            content: "";
            display: block;
            height: 3px;
            width: 120px;
            margin-top: 6px;
            border-radius: 4px;
            background: linear-gradient(90deg, #60a5fa, #818cf8);
        }

        /* ================= REMOVE DEFAULT WHITE BACK ================= */

        [data-page-route="ess"] .page-body {
            background: transparent !important;
        }

        .ess-dashboard {
            padding: 20px;
            background: #f1f5f9;
            font-family: Inter, system-ui;
        }

        .ess-kpi-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(220px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }

        /* ================= DONUT FIX ================= */

        /* Donut chart wrapper */
            .ess-chart-wrap--donut {
                height: 220px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

                    /* SVG must not be clipped */
                    /* Donut SVG fix */
            #nationality-chart svg {
                width: 100% !important;
                height: 100% !important;
                max-height: 200px;
            }

            /* Donut legend control */
            #nationality-chart .chart-legend {
                max-height: 48px;
                overflow: hidden;
            }


            @media (max-width: 1400px) {
                .ess-kpi-strip {
                    grid-template-columns: repeat(4, 1fr);
                }
            }

            @media (max-width: 1100px) {
                .ess-kpi-strip {
                    grid-template-columns: repeat(3, 1fr);
                }
            }

            @media (max-width: 768px) {
                .ess-kpi-strip {
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            .ess-kpi-card {
                background: linear-gradient(180deg, #f8fafc, #eef2f7);
                border-radius: 14px;
                padding: 10px 12px;
                position: relative;
                box-shadow: 0 4px 14px rgba(0,0,0,.08);
                cursor: pointer;
                height: 86px;
            }

            .ess-attendance-card,
            .ess-compliance-card,
            .ess-leave-card
            {
                max-height: 220px !important;
                min-height: 150px;
            }

            .kpi-line {
                z-index: 15;
            }

            .ess-attendance-card {
                padding-bottom: 18px;
            }

            .ess-attendance-card .kpi-line {
                background: linear-gradient(90deg, #06b6d4, #3b82f6);
    }

            .kpi-header {
                font-size: 12px;
                font-weight: 600;
                display: flex;
                gap: 6px;
                align-items: center;
            }

            .kpi-main {
                font-size: 16px;
                font-weight: 700;
            }

            .kpi-sub {
                font-size: 12px;
                color: #475569;
            }

            .kpi-line {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 2px;
                width: 100%;
            }

            /* Allow bottom line inside content cards */
            .ess-card {
                position: relative;
            }

            /* Bottom line shared for KPI + content cards */
            .kpi-line {
                position: absolute;
                bottom: 0;
                left: 0;
                height: 2px;
                width: 100%;
                border-radius: 0 0 14px 14px;
            }

            /* Color variants */
            .kpi-blue   { background:rgb(225, 229, 235); }
            .kpi-green  { background:rgb(225, 229, 235); }
            .kpi-orange { background:rgb(225, 229, 235);}
            .kpi-purple { background:rgb(225, 229, 235);}

            /* ================= ICON COLORS ================= */
            

            /* icon pill */
            .kpi-header i {
                padding: 6px;
                border-radius: 8px;
                font-size: 14px;
            }
        
            .kpi-blue i {
                color: #3b82f6;
                background: #eff6ff;
            }

            .kpi-green i {
                color: #22c55e;
                background: #ecfdf5;
            }

            .kpi-orange i {
                color:rgb(10, 33, 163);
                background: #fff7ed;
            }

            .kpi-purple i {
                color: #8b5cf6;
                background: #f5f3ff;
            }

            /* icon pill */
            .kpi-header i {
                padding: 6px;
                border-radius: 8px;
                font-size: 14px;
            }

            .kpi-blue .kpi-line { background:#3b82f6; }
            .kpi-green .kpi-line { background:#22c55e; }
            .kpi-orange .kpi-line { background:#f97316; }
            .kpi-purple .kpi-line { background:#8b5cf6; }

            .ess-charts {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 14px;
            }

            .ess-card {
                background: linear-gradient(180deg, #ffffff, #f8fafc);
                border-radius: 14px;
                padding: 14px;
                box-shadow: 0 4px 14px rgba(0,0,0,.08);
            }

            .ess-card-header {
                font-weight: 700;
                margin-bottom: 10px;
            }

            .ess-attendance-inline {
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
            }

            .ess-att-inline-item {
                background: #f8fafc;
                padding: 6px 8px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                cursor: pointer;
            }

            .ess-pending-row,
            .ess-compliance-row,
            .ess-leave-row {
                background: #f8fafc;
                padding: 8px 10px;
                border-radius: 10px;
                display: flex;
                justify-content: space-between;
                cursor: pointer;
            }

            .ess-leave-employee {
                width: 100%;
                padding: 6px;
                border-radius: 8px;
                margin-bottom: 8px;
            }

        /* ================= EXPIRING SOON – COMPLIANCE STYLE ================= */

            .exp-visa {
                background: #eef2ff !important;      /* soft blue */
            }

            .exp-passport {
                background: #ecfeff !important;      /* soft teal */
            }

            .exp-labor {
                background: #fff7ed !important;      /* soft orange */
            }

            /* keep hover consistent */
            .exp-visa:hover,
            .exp-passport:hover,
            .exp-labor:hover {
                background: #e0e7ff !important;
            }

        
        /* ================= LEAVE BALANCE CARD ================= */

        .ess-leave-list {
            display: grid;
            gap: 8px;
        }

        .ess-leave-row {
            background: #f8fafc;
            padding: 10px 12px;
            border-radius: 10px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 13px;
        }

        .ess-leave-row b {
            font-size: 14px;
            font-weight: 700;
            color: #0f172a;
        }

        .ess-leave-row:hover {
            background: #eef2ff;
        }

        .ess-leave-employee {
            width: 100%;
            padding: 6px 8px;
            border-radius: 8px;
            border: 1px solid #c7d2fe;
            background: #f8fafc;
            font-size: 13px;
            margin-bottom: 10px;       }

        

            /* ================= SIMPLE PENDING REQUESTS ================= */

            .ess-pending-text {
                font-size: 13px;
                font-weight: 400;
                color:#475569;
                line-height: 1.5;
            }

            .ess-pending-link {
                color:#475569;
                text-decoration: none;
                cursor: pointer;
            }

            .ess-pending-link:hover {
                color:rgba(0, 3, 7, 0.93);
                text-decoration: none;
                cursor: pointer;
            }

     



        
        /* ================= TODAY ATTENDANCE – IMAGE MATCH ================= */

        // .ess-attendance-card {
        //     background: linear-gradient(180deg, #f8fafc, #eef2f7);
        //     border-radius: 16px;
        //     padding: 14px;
        //     height: auto !important;
        //     min-height: 170px;
        // }

        /* header row */
        .ess-card-header-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .ess-card-title {
            font-size: 12px;
            font-weight: 600;
            color: #0f172a;
        }

        .ess-card-title .ess-sub {
            font-weight: 500;
            color: #64748b;
            font-size: 12px;
        }

        .ess-card-action {
            font-size: 14px;
            color: #64748b;
            cursor: pointer;
        }

        /* subtitle */
        .ess-att-subtitle {
            font-size: 12px;
            margin: 6px 0 10px;
        }

        /* grid */
        /* ===== TODAY ATTENDANCE GRID – RESPONSIVE ===== */

        .ess-attendance-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 6px;
        }

        /* medium screens */
        @media (max-width: 1200px) {
            .ess-attendance-grid {
                grid-template-columns: repeat(3, 1fr);
            }
        }

        /* small screens */
        @media (max-width: 768px) {
            .ess-attendance-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }


        /* ===== ATTENDANCE GRID ===== */

        .ess-attendance-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-top: 8px;
        }

        /* ===== ATTENDANCE PILL ===== */

        .ess-att-inline-item {
            display: flex;
            align-items: center;
            justify-content: space-between;

            gap: 8px;
            padding: 8px 10px;

            background: #f8fafc;
            border-radius: 10px;

            font-size: 12px;
            font-weight: 500;

            white-space: nowrap;        /* 🔑 PREVENT WRAP */
            overflow: hidden;
            text-overflow: ellipsis;

            cursor: pointer;
        }

        /* left side (icon + label) */
        .ess-att-left {
            display: flex;
            align-items: center;
            gap: 6px;
            min-width: 0;
        }

        /* label text */
        .ess-att-left span {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        /* count */
        .ess-att-inline-item b {
            font-weight: 700;
            flex-shrink: 0;
        }


            /* icon wrapper */
            .ess-att-icon {
                width: 18px;
                height: 18px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 11px;
            }

            /* color mapping */
            .att-present { background:#ecfdf5; color:#047857; }
            .att-absent  { background:#eff6ff; color:#b91c1d; }
            .att-late    { background:#fef2f2; color:#b91c1c; }
            .att-leave   { background:#fff7ed; color:#c2410c; }
            .att-early   { background:#f1f5f9; color:#334155; }
            .att-half    { background:#ecfeff; color:#0f766e; }
            .att-wfh     { background:#eef2ff; color:#4338ca; }
            .att-visit   { background:#fdf4ff; color:#86198f; }

            /* value */
            .ess-att-pill b {
                margin-left: auto;
                font-weight: 700;
            }

            @media (max-width: 1100px) {
                .ess-attendance-grid {
                    grid-template-columns: repeat(3, 1fr);
                }
            }

            @media (max-width: 768px) {
                .ess-attendance-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }


            /* ================= EMPLOYEE COMPLIANCE ================= */

            .ess-compliance-list {
                display: grid;
                gap: 10px;
                margin-top: 8px;
            }

            .ess-compliance-row {
                display: flex;
                justify-content: space-between;
                align-items: center;

                background: #f8fafc;
                padding: 8px 12px;
                border-radius: 10px;

                font-size: 13px;
                cursor: pointer;
            }

            .ess-compliance-row:hover {
                background: #eef2ff;
            }

            .ess-compliance-left {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            /* 🔵 SMALL COLORED BULLET */
            .ess-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                flex-shrink: 0;
            }

            /* COLOR VARIANTS */
            .dot-green  { background: #22c55e; }   /* Pending Confirmation */
            .dot-orange { background: #f97316; }   /* Expiring Contracts */
            .dot-red    { background: #ef4444; }   /* Missing Leave */
            .dot-purple { background: #8b5cf6; }   /* Iqama */
            .dot-blue   { background: #3b82f6; }   /* Visa */

            /* Compliance bullets */
            .ess-compliance-left {
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .ess-dot {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                flex-shrink: 0;
            }

            .dot-green  { background:#22c55e; }
            .dot-orange { background:#f97316; }
            .dot-red    { background:#ef4444; }
            .dot-purple { background:#8b5cf6; }
            .dot-blue   { background:#3b82f6; }


            /* ================= LEAVE BALANCE CARD ================= */

            // .ess-leave-card {
            //     background: linear-gradient(180deg, #f8fafc, #eef2f7);
            // }

            /* Dropdown wrapper like card */
            .ess-leave-select-wrap {
                background: #f8fafc;
                border-radius: 12px;
                padding: 6px;
                margin-bottom: 10px;
                box-shadow: inset 0 0 0 1px #e2e8f0;
            }

            /* Styled dropdown */
            .ess-leave-employee {
                width: 100%;
                border: none;
                outline: none;
                background: transparent;
                font-size: 13px;
                font-weight: 600;
                color: #0f172a;
                cursor: pointer;
            }

            /* ================= LEAVE ROWS ================= */

            .ess-leave-list {
                display: grid;
                gap: 8px;
            }

            .ess-leave-row {
                background: #f8fafc;
                border-radius: 12px;
                padding: 10px 12px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 13px;
                transition: background .15s ease, transform .15s ease;
            }

            /* subtle hover */
            .ess-leave-row:hover {
                background: #eef2ff;
                transform: translateY(-1px);
            }

            /* Leave name */
            .ess-leave-row span {
                color: #334155;
                font-weight: 500;
            }

            /* Leave balance */
            .ess-leave-row b {
                font-size: 15px;
                font-weight: 700;
                color: #0f172a;
            }

            .ess-leave-row b {
                color: #16a34a; /* green */
            }

            .ess-leave-row b:empty,
            .ess-leave-row b:contains("0") {
                color: #64748b;
            }
                
            /* ======================================================
            COMPACT ONLY: Attendance, Compliance, Leave Balance
            ====================================================== */

            /* Allow these cards to shrink naturally */
            .ess-attendance-card,
            .ess-compliance-card,
            .ess-leave-card {
            
                min-height: unset !important;
                padding: 10px 12px !important;
            }

            /* Reduce header spacing */
            .ess-attendance-card .ess-card-header-row,
            .ess-compliance-card .kpi-header,
            .ess-leave-card .ess-card-header {
                margin-bottom: 6px !important;
            }

            /* Reduce subtitle spacing (Attendance only) */
            .ess-attendance-card .ess-att-subtitle {
                margin: 4px 0 6px !important;
                font-size: 12px;
            }

            /* Tighten grids/lists */
            .ess-attendance-grid,
            .ess-compliance-list,
            .ess-leave-list {
                gap: 6px !important;
            }

            /* Tighten rows inside cards */
            .ess-att-inline-item,
            .ess-compliance-row,
            .ess-leave-row {
                padding: 6px 8px !important;
                font-size: 12px !important;
                line-height: 1.3;
            }

            /* Reduce icon padding inside rows */
            .ess-att-icon,
            .ess-dot {
                width: 14px;
                height: 14px;
            }

            /* Leave balance dropdown compact */
            .ess-leave-select-wrap {
                padding: 4px !important;
            }

            .ess-leave-employee {
                padding: 6px 8px !important;
                font-size: 12px;
            }

            /* ======================================================
            FORCE AUTO HEIGHT FOR NON-KPI CONTENT CARDS
            ====================================================== */
           

            /* ================= SECOND ROW CARD HEIGHT SYNC ================= */

            /* All cards in second row */
            .ess-kpi-strip .ess-attendance-card,
            .ess-kpi-strip .ess-compliance-card,
            .ess-kpi-strip .ess-leave-card,
            {
                min-height: 135px;        /* same as attendance */
                display: flex;
                flex-direction: column;
            }

            .ess-kpi-strip .ess-expiry-card {
                min-height: 210px;        
                display: flex;
                flex-direction: column;
            }

            /* Keep content aligned nicely inside equal-height cards */
            .ess-attendance-card > *,
            .ess-compliance-card > *,
            .ess-leave-card > *,
            .ess-expiry-card > * {
                flex-shrink: 0;
            }

            /* ================= TODAY ATTENDANCE WIDTH FIX ================= */

            .ess-attendance-card {
                grid-column: span 1;   /* 🔥 makes it wider */
            }

            @media (max-width: 1100px) {
                .ess-attendance-card {
                    grid-column: span 1;
                }
            }

            .ess-kpi-card,
                .ess-card {
                    cursor: pointer;
                }

            .ess-kpi-card:hover,
                .ess-card:hover {
                    transform: translateY(-2px);
                }

            .ess-kpi-card {
                cursor: pointer;
            }

            .ess-kpi-card::before,
                .kpi-line {
                    pointer-events: none;
                }

            /* ================= HEADCOUNT CARD ================= */

            .ess-headcount-card {
                max-width: 100%;
                min-height: 260px;
                padding-bottom: 12px;
            }

            /* Chart container size */
            #ess-headcount-chart {
                width: 100%;
                max-width: 100%;
                height: 240px;
                margin-top: 6px;
            }

            /* ================= TABS ================= */

            .ess-tabs {
                display: flex;
                gap: 6px;
                margin: 8px 0 6px;
                flex-wrap: wrap;
            }

            .ess-tab {
                padding: 4px 10px;
                font-size: 12px;
                font-weight: 600;
                border-radius: 8px;
                border: 1px solid #e2e8f0;
                background: #f8fafc;
                color: #334155;
                cursor: pointer;
                transition: all .15s ease;
            }

            .ess-tab:hover {
                background: #eef2ff;
                border-color: #c7d2fe;
            }

            .ess-tab.active {
                background: #3b82f6;
                color: #fff;
                border-color: #3b82f6;
            }
            
            /* ================= CHART FIX ================= */

            /* ================= CHART SIZE CONTROL ================= */

            .ess-chart-wrap {
                width: 100%;
                max-width: 520px;        /* 👈 little bigger than card content */
                margin: 8px auto 0;      /* center horizontally */
            }

            /* ================= DONUT CHART FIX ================= */

            .ess-chart-wrap--donut {
                height: 230px;
                padding: 6px 6px 0;
                overflow: hidden;            /* 🔑 prevents spill */
            }

            /* keep donut centered */
            #nationality-chart svg {
                display: block;
                margin: 0 auto;
            }

            /* ===== LEGEND CONTAINER ===== */
            #nationality-chart .chart-legend {
                margin-top: 6px;
                padding: 0 6px;

                display: grid !important;
                grid-template-columns: repeat(3, minmax(0, 1fr)); /* 🔑 3 per row */
                gap: 4px 6px;

                max-width: 100%;
                box-sizing: border-box;

                width: 100%;
                text-align: left;
            }

            /* individual legend item */
            #nationality-chart .chart-legend-item {
                font-size: 11px;
                line-height: 1.2;

                display: flex;
                align-items: center;
                gap: 6px;

                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            /* legend color dot */
            #nationality-chart .chart-legend-item .legend-dot {
                flex-shrink: 0;
            }


            /* force SVG to respect wrapper */
            .ess-chart-wrap svg {
                width: 100% !important;
                max-height: 220px !important;
            }

            /* ================= CHART SIZE CONTROL ================= */

            .ess-chart-wrap {
                width: 100%;
                height: 100px;           /* 🔑 CONTROLLED HEIGHT */
                padding: 8px 4px 0;
            }

            /* tighten donut label spacing */
            #nationality-chart text {
                font-size: 11px !important;
            }       

            /* ================= DONUT LEGEND LAYOUT FIX ================= */

            #nationality-chart .chart-legend {
                display: grid !important;
                grid-template-columns: repeat(3, 1fr);  /* 🔑 3 per row */
                gap: 4px 8px;
                margin-top: 6px;
            }

            #nationality-chart .chart-legend-item {
                font-size: 11px;
                white-space: nowrap;
            }

            /* donut needs more vertical room */
            .ess-chart-wrap--donut {
                height: 260px;           /* 🔑 prevents donut cut */
            }

            /* force SVG to fit wrapper */
            .ess-chart-wrap svg {
                width: 100% !important;
                height: 100% !important;
                overflow: visible !important;
            }

            .ess-card svg {
                max-width: 100% !important;
                height: auto !important;
            }

            .ess-card svg text {
                font-size: 11px;
            }

            /* reduce card padding for chart cards only */
            .ess-charts-grid .ess-card {
                padding: 12px 14px 10px;
            }

            /* Donut specific fix */
            #nationality-chart {
                padding-top: 10px;
            }

            /* ================= DASHBOARD GRID ================= */

            .ess-charts {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
                gap: 14px;
                align-items: start;
            }

            #ess-headcount-chart,
            #ess-headcount-chart svg,
            #ess-headcount-chart svg * {
                cursor: pointer !important;
            }

            /* ================= CHART WIDTH FIX (CRITICAL) ================= */

            .ess-charts-wrapper {
                max-width: 1200px;        /* controls dashboard width */
                margin: 0 auto;           /* center it */
                width: 100%;
            }

            .ess-charts {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 14px;
            }
            
            
            /* ======================================================
            LIMIT CHART WIDTH (ONLY CHART, NOT CARD)
            ====================================================== */

            /* chart wrapper */
            #headcount-chart,
            #salary-chart,
            #nationality-chart {
                display: flex;
                align-items: center;   /* center chart */
                justify-content: center;
            }

            /* actual SVG */
            #headcount-chart svg,
            #salary-chart svg,
            #nationality-chart svg {
            width: 100% !important;
            max-width: 260px;
            height: auto !important;
}

            /* tablet */
            @media (max-width: 1100px) {
                #headcount-chart svg,
                #salary-chart svg,
                #nationality-chart svg {
                    width: 90% !important;
                }
            }

            /* mobile */
            @media (max-width: 768px) {
                #headcount-chart svg,
                #salary-chart svg,
                #nationality-chart svg {
                    width: 100% !important;
                }
            }

            #headcount-chart {
                width: 100%;
                max-width: 100%;
                height: 220px;
            }

            /* responsive */
            @media (max-width: 1200px) {
                .ess-charts {
                    grid-template-columns: 1fr;
                }
}

            @media (max-width: 768px) {
                .ess-charts {
                    grid-template-columns: 1fr;
                }
            }

            /* ================= CHARTS GRID ================= */

            .ess-charts-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr); /* 🔑 EXACTLY 3 charts */
                gap: 16px;
                align-items: stretch;
            }

            /* Limit SVG height inside cards */
            .ess-card svg {
                max-height: 210px;
                width: 100% !important;
            }

            /* On smaller screens → single column */
            /* fallback for smaller screens */
            @media (max-width: 1200px) {
                .ess-charts-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
            }

            @media (max-width: 768px) {
                .ess-charts-grid {
                    grid-template-columns: 1fr;
                }
            }

            svg, svg * {
                cursor: pointer !important;
            }            
            
            /* =====================================================
            REMOVE STICKY HEADER – MAKE TITLE STATIC
            ===================================================== */

            /* Remove any sticky/fixed behavior */
            [data-page-route="ess"] .page-head,
            [data-page-route="ess"] .page-head-content,
            [data-page-route="ess"] .page-title {
                position: static !important;
                top: auto !important;
                z-index: auto !important;
            }

            /* Ensure title is visible and static */
            [data-page-route="ess"] .page-title {
                display: flex !important;
                align-items: center;
                padding: 12px 16px !important;
                background: transparent !important;
            }

            /* Title text styling (static) */
            [data-page-route="ess"] .page-title .title-text {
                display: inline-flex !important;
                align-items: center;
                gap: 10px;

                font-size: 20px;
                font-weight: 800;
                color: #0f172a;

                white-space: nowrap;
            }

            /* Remove any underline / separator line */
            [data-page-route="ess"] .page-title::after,
            [data-page-route="ess"] .page-head::after {
                display: none !important;
            }

            /* Remove extra spacing around title */
            [data-page-route="ess"] .page-head {
                margin-bottom: 6px !important;
                padding-bottom: 0 !important;
            }

            /* KPI card default order */
            .ess-kpi-card {
                order: 10;
            }

            /* Explicit first-row order */
            .ess-kpi-card.kpi-reporting { order: 1; }
            .ess-kpi-card.kpi-active    { order: 2; }
            .ess-kpi-card.kpi-pending   { order: 3; }
            .ess-kpi-card.kpi-expiry  { order: 4; }
            .ess-kpi-card.kpi-appraisal { order: 5; }

            /* ================= TODAY'S ATTENDANCE ================= */

            /* Grid: exactly 2 per row */
            .ess-attendance-grid {
                display: grid;
                grid-template-columns: repeat(2, 1fr);   /* 🔑 ONLY 2 PER ROW */
                gap: 10px;
                margin-top: 8px;
            }

            /* Attendance pill */
            .ess-att-inline-item {
                background: #f8fafc;
                border-radius: 10px;
                padding: 8px 10px;

                display: flex;
                justify-content: space-between;
                align-items: center;

                font-size: 12.5px;
                line-height: 1.2;

                min-height: 40px;        /* keeps card compact */
                cursor: pointer;
            }

            /* Left side (icon + label) */
            .ess-att-left {
                display: flex;
                align-items: center;
                gap: 6px;

                white-space: nowrap;    /* 🔑 prevent label wrapping */
                overflow: hidden;
                text-overflow: ellipsis;
            }

            /* Count */
            .ess-att-inline-item b {
                font-weight: 700;
                font-size: 13px;
                flex-shrink: 0;
            }           
}
            
    
            /* ================= EMPTY CARD STATE ================= */

            .ess-kpi-card.is-empty {
                cursor: default !important;
                pointer-events: none;
                box-shadow: none !important;
                opacity: 0.75;
            }

            .ess-kpi-card.is-empty:hover {
                transform: none !important;
                box-shadow: none !important;
            }

            /* ================= TOOLTIP STACKING FIX ================= */

            /* 1. Allow overflow at ALL levels */
            .ess-dashboard,
            .ess-kpi-strip,
            .ess-kpi-strip > *,
            .ess-kpi-card {
                overflow: visible !important;
            }

            

            /* ================= LIMIT NATIONALITY LEGEND TO 2 ITEMS ================= */

            #nationality-chart .chart-legend .legend-item {
                display: none;
            }

            /* show only first 2 */
            #nationality-chart .chart-legend .legend-item:nth-child(1),
            #nationality-chart .chart-legend .legend-item:nth-child(2) {
                display: flex;
            }

            #nationality-chart .chart-legend::after {
            content: "+ more";
            font-size: 11px;
            color: #64748b;
            margin-left: 6px;
        }

        .ess-compliance-row.is-disabled {
            pointer-events: none;   /* 🔥 hard block */
            opacity: 0.55;
            cursor: default;
        }

        /* ================= APPRAISAL CHART FIX ================= */

            .ess-appraisal-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
            }

            .ess-chart-box {
                height: 220px;        /* 🔥 REQUIRED */
                width: 100%;
            }

            @media (max-width: 768px) {
                .ess-appraisal-grid {
                    grid-template-columns: 1fr;
                }
            }

            /* ================= FIRST ROW CHART HEIGHT FIX ================= */

            .ess-charts-grid {
                align-items: stretch; /* 🔑 make all cards equal height */
            }

            /* First-row chart cards */
            .ess-charts-grid .ess-card {
                min-height: 320px;      /* adjust as needed */
                display: flex;
                flex-direction: column;
            }

            /* ================= CHART INNER HEIGHT CONTROL ================= */

            .ess-card .ess-chart-wrap,
            .ess-card canvas,
            .ess-card svg {
                max-height: 220px;      /* keeps charts consistent */
            }

            /* For line charts specifically */
            .ess-card svg {
                width: 100% !important;
            }

            /* Space for tabs above charts */
            .ess-card .ess-tabs {
                min-height: 36px;
                margin-bottom: 6px;
            }

            /* Header height consistency */
            .ess-card-header-row {
                min-height: 36px;
            }

            #appraisal-status-chart {
                height: 220px;
                position: relative;
            }

            #appraisal-status-chart canvas {
                width: 100% !important;
                height: 100% !important;
            }

            .ess-appraisal-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 14px;
            }

            .ess-chart-box {
                position: relative;
                height: 220px;     /* 🔑 REQUIRED */
                width: 100%;
            }

            .ess-chart-title {
                font-size: 13px;
                font-weight: 600;
                color: #334155;
                margin-bottom: 6px;
            }

            .ess-muted {
                text-align: center;
                font-size: 12px;
                color: #94a3b8;
                padding-top: 60px;
            }

            .ess-chart-box {
                height: 220px;
                position: relative;
            }

            .ess-kpi-card.is-empty {
                    opacity: 0.85;
                }
            
            
            
            
            /* Container */
                .ess-pending-inline {
                    display: flex;
                    flex-wrap: wrap;          /* allow wrap if very tight */
                    gap: 6px;
                    margin-top: 4px;
                    font-size: 12px;
                }

                /* Item */
                .ess-pending-pill {
                    background: none !important;
                    border: none !important;
                    padding: 0 !important;

                    font-weight: 500;
                    color:rgb(30, 39, 56);           /* pleasant link-blue */
                    cursor: pointer;

                    white-space: nowrap;
                }

                /* Separator */
                .ess-pending-pill::after {
                    content: "•";
                    margin-left: 6px;
                    color: #94a3b8;
                }

                /* Remove separator from last item */
                .ess-pending-pill:last-child::after {
                    content: "";
                }

                .ess-dashboard-grid {
                    display: grid;
                    grid-template-columns: repeat(4, minmax(0, 1fr));
                    gap: 16px;
                    align-items: stretch;
                }
                
                .ess-kpi-card,
                    .ess-card {
                        height: 100%;
                        display: flex;
                        flex-direction: column;
                    }

                .ess-kpi-card,
                    .ess-card {
                        background: linear-gradient(
                            180deg,
                            #f1f5f9,
                            #e9eef5
                        );
                        border-radius: 16px;
                    }
                    .ess-kpi-card {
                        min-height: 92px;   /* adjust once, applies everywhere */
                    
                    .ess-card {
                        min-height: 120px;
                    }

}
                .ess-muted {
                    font-size: 13px;
                    color: #94a3b8;
                    text-align: center;
                    padding: 6px 0;
                }

                .ess-pending-requests-card.is-empty {
                    opacity: 0.85;
                    cursor: default;
                }

                .ess-dashboard-link .control-input {
                    background: #f8fafc;
                    border-radius: 10px;
                    font-size: 13px;
                }

                .ess-leave-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 8px 10px;
                    background: #f8fafc;
                    border-radius: 10px;
                    font-size: 13px;
                }

                .ess-muted {
                    font-size: 13px;
                    color: #94a3b8;
                    text-align: center;
                }

                    /* 🔥 FIX: allow dropdowns to overflow */
                    .ess-dashboard,
                    .ess-kpi-strip,
                    .ess-kpi-card,
                    .ess-leave-card {
                        overflow: visible !important;
                    }

                    /* 🔥 Frappe Link dropdown */
                    .awesomplete {
                        z-index: 99999 !important;
                    }

                    /* Dropdown list itself */
                    .awesomplete ul {
                        z-index: 99999 !important;
                    }


                    .ess-charts-grid {
                        position: relative;
                        z-index: 1;
                    }

                    .ess-kpi-strip {
                        position: relative;
                        z-index: 10;   /* KPI row above charts */
                    }

                    .awesomplete ul {
                        background: #ffffff;
                        border-radius: 10px;
                        box-shadow: 0 18px 45px rgba(15,23,42,.25);
                        border: 1px solid #e2e8f0;
                    }
                    
                    .ess-dashboard-link .control-input:disabled {
                        background: #f1f5f9;
                        cursor: not-allowed;
                        opacity: 0.85;
                    }
                    
                    /* ================= ESS Leave Dropdown Cleanup ================= */

                    /* Remove label spacing entirely */
                    .ess-leave-card .control-label {
                        display: none !important;
                    }

                    /* Remove top border / white line */
                    .ess-leave-card .control-input-wrapper {
                        border: none !important;
                        box-shadow: none !important;
                        padding-top: 0 !important;
                    }

                    /* Remove input border */
                    .ess-leave-card .form-control {
                        border: none !important;
                        box-shadow: none !important;
                        background: transparent !important;
                    }

                    /* Remove extra margin above control */
                    .ess-leave-card .frappe-control {
                        margin-top: 0 !important;
                    }

                    .ess-dashboard-link .awesomplete input {
                        font-weight: 600;
                        font-size: 13px;
                    }

                    #net-payroll-chart {
                        min-height: 220px;
                    }
                    
                    /* Rotate Net Payroll x-axis labels */
                    #net-payroll-chart text[x] {
                        transform: rotate(-40deg);
                        text-anchor: end;
                    }
                    
                    /* Hide month label row above picker */
                    #net-payroll-month-field .control-label {
                        display: none !important;
                    }

                    /* Rotate Net Payroll x-axis labels */
                    #net-payroll-chart svg text[x] {
                        transform: rotate(-40deg);
                        text-anchor: end;
                    }

                    /* ALL chart cards */
                .ess-charts-grid .ess-card {
                    min-height: 340px;
                    display: flex;
                    flex-direction: column;
                }

                /* Chart container */
                .ess-chart-wrap {
                    flex: 1;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                /* Actual chart holder */
                .ess-chart-wrap > div {
                    width: 100%;
                    height: 220px;   /* 🔥 THE MAGIC NUMBER */
                }

                /* Frappe charts */
                .ess-chart-wrap svg {
                    width: 100% !important;
                    height: 100% !important;
                }

                /* Chart.js */
                .ess-chart-wrap canvas {
                    width: 100% !important;
                    height: 100% !important;
                }

                /* Chart headers */
                .ess-card-header,
                .ess-card-header-row {
                    min-height: 36px;
                    margin-bottom: 6px;
                }

                /* Legends */
                .ess-card .chart-legend {
                    max-height: 48px;
                    overflow: hidden;
                }

                axisOptions: {
                    yAxisMode: "span",
                    yMin: 0,
                    yMax: Math.max(...values) * 0.6
                }

                /* Enable clicking ONLY on bars */
                #net-payroll-chart rect.bar {
                    pointer-events: all;
                    cursor: pointer;
                }
                #net-payroll-chart rect.bar {
                    pointer-events: all;
                    cursor: pointer;
                }

                /* Give space for rotated x-axis labels */
                #net-payroll-chart svg {
                    overflow: visible !important;
                }

                #net-payroll-chart {
                    padding-bottom: 32px; /* 🔑 space for labels */
                }
                    #net-payroll-chart svg text[x] {
                    transform: rotate(-25deg);
                    text-anchor: end;
                }

                new frappe.Chart(container, {
                    data: chartData,
                    type: "bar",
                    height: 220,   // 🔥 was 220
                    ...
                });

                #nationality-chart {
                display: flex;
                flex-direction: column;
                align-items: center;
                }

                #nationality-chart svg {
                    margin-top: -85px;
                    margin-left: -75px;
                }

                #net-payroll-chart .x.axis text {
                    transform: translateY(2px);
                }

                /* Keep headcount x-axis labels inside card */
                #ess-headcount-chart .x.axis text {
                    transform: translateY(-8px);
                    font-size: 11px;
                }

                #nationality-chart .donut-slice {
                    cursor: pointer;
                }

                /* Re-enable interaction for donut chart */
                #nationality-chart svg,
                #nationality-chart svg * {
                    pointer-events: all !important;
                }

                /* Nationality ranked list layout */
                #nationality-chart {
                    max-width: 420px;
                    margin: 0 auto;
                }

                .ess-rank-row {
                    display: grid;
                    grid-template-columns: 140px 1fr 32px; /* 🔑 FIXED LABEL WIDTH */
                    align-items: center;
                    gap: 12px;
                    padding: 8px 4px;
                    cursor: pointer;
                }

                .ess-rank-row:not(:last-child) {
                    border-bottom: 1px dashed #e5e7eb;
                }

                .ess-rank-row:hover {
                    background: #f8fafc;
                    border-radius: 6px;
                }

                /* Label */
                .ess-rank-label {
                    font-size: 13px;
                    font-weight: 500;
                    color: #334155;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }

                /* Bar */
                .ess-rank-bar {
                    height: 10px;
                    background: #e5e7eb;
                    border-radius: 999px;
                    overflow: hidden;
                }

                .ess-rank-bar span {
                    display: block;
                    height: 100%;
                    background: linear-gradient(90deg, #2563eb, #3b82f6);
                    border-radius: 999px;
                }

                /* Value */
                .ess-rank-value {
                    text-align: right;
                    font-size: 12px;
                    font-weight: 600;
                    color: #0f172a;
                }


                .ess-card:has(#nationality-chart) {
                    padding-bottom: 12px;
                }
                /* 🔥 RESET layout inside nationality chart */
                #nationality-chart {
                    display: block !important;
                }

                #nationality-chart > * {
                    display: block !important;
                }

                /* Nationality ranked list */
                #nationality-chart {
                    max-width: 420px;
                    margin: 0 auto;
                }

                #nationality-chart .ess-rank-row {
                    display: grid !important;
                    grid-template-columns: 140px 1fr 32px;
                    align-items: center;
                    gap: 12px;
                    padding: 8px 4px;
                    cursor: pointer;
                }

                #nationality-chart .ess-rank-row:not(:last-child) {
                    border-bottom: 1px dashed #e5e7eb;
                }

                #nationality-chart .ess-rank-label {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    font-size: 13px;
                    font-weight: 500;
                    color: #334155;
                }

                #nationality-chart .ess-rank-bar {
                    height: 10px;
                    background: #e5e7eb;
                    border-radius: 999px;
                    overflow: hidden;
                }

                #nationality-chart .ess-rank-bar span {
                    display: block;
                    height: 100%;
                    background: linear-gradient(90deg, #2563eb, #3b82f6);
                }

                #nationality-chart .ess-rank-value {
                    text-align: right;
                    font-size: 12px;
                    font-weight: 600;
                }

                /* Shared bar chart container */
                .ess-chart-wrap {
                    height: 260px;              /* 🔑 SAME HEIGHT */
                    padding: 8px 12px 16px;
                    display: flex;
                    align-items: flex-end;      /* 🔑 Align bars to bottom */
                }

                new frappe.Chart(container, {
                    data,
                    type: "bar",
                    height: 220,   // 🔑 same
                    ...
                });                

                axisOptions: {
                    xAxisMode: "tick",
                    yAxisMode: "span",
                    xIsSeries: true
                },

                barOptions: {
                    spaceRatio: 0.6   // slightly wider bars = less label crowding
                }

                .frappe-chart text {
                    fill: #94a3b8;       /* slate-400 */
                    font-size: 11px;
                }

                barOptions: {
                    spaceRatio: 0.55
                }

                .ess-chart-wrap {
                padding-top: 200px;   /* 🔑 spacing without breaking tooltips */
            }

            /* Pending Requests List */
            .ess-pending-list {
                max-height: 230px;          /* 🔑 prevents cropping */
                overflow-y: auto;
                padding: 4px 0;
            }

            .ess-pending-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 5px 7px;
                border-bottom: 1px solid #e5e7eb;
                cursor: pointer;
            }

            .ess-pending-item:last-child {
                border-bottom: none;
            }

            .ess-pending-item:hover {
                background: #f8fafc;
            }

            /* Left side (icon + label) */
            .ess-pending-left {
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .ess-pending-icon {
                width: 28px;
                height: 28px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                color: white;
            }

            /* Right side (count) */
            .ess-pending-count {
                font-size: 13px;
                font-weight: 600;
                background: #e0e7ff;
                color: #1e40af;
                padding: 2px 8px;
                border-radius: 999px;
            }

            /* Title icon */
            .ess-card-title-icon {
                margin-right: 5px;
                color: #2563eb;
            }

            /* Pending Requests scroll container */
            #ess-pending-requests {
                max-height: 220px;        /* 🔑 fixed visible area */
                overflow-y: auto;         /* 🔑 vertical scroll */
                padding: 4px 0;
            }

            /* Keep list items clean */
            .ess-pending-list {
                padding: 0;
            }
            
            /* Card layout stays intact */
            .ess-pending-requests-card {
                display: flex;
                flex-direction: column;
            }

            /* Header fixed */
            .ess-pending-requests-card .ess-card-header {
                flex: 0 0 auto;
            }

            /* 🔥 Scrollable content area */
            .ess-pending-requests-card #ess-pending-requests {
                flex: 1 1 auto;
                overflow-y: auto;
                min-height: 0;      /* 🔑 critical for flex scrolling */
                padding: 4px 0;
            }

            /* Footer stays fixed */
            .ess-pending-requests-card .kpi-line {
                flex: 0 0 auto;
            }

            /* Limit height ONLY for Pending Requests card */
            .ess-pending-requests-card {
                max-height: 220px;          /* 🔑 matches other KPI cards */
                display: flex;
                flex-direction: column;
            }

            /* Scrollable body */
            .ess-pending-requests-card #ess-pending-requests {
                flex: 1 1 auto;
                overflow-y: auto;
                min-height: 0;              /* 🔥 critical */
            }

            .ess-pending-requests-card .ess-card-header,
            .ess-pending-requests-card .kpi-line {
                flex: 0 0 auto;
            }

            /* Keep Pending Requests in original position */
            .ess-pending-requests-card {
                order: 4; /* adjust to match where it should appear */
            }


            /* Merge card layout */
            .ess-compliance-expiry-card {
                display: flex;
                flex-direction: column;
                max-height: 210px;   /* 🔑 matches KPI cards */
            }

            /* Scrollable content */
            .ess-compliance-expiry-list {
                flex: 1 1 auto;
                overflow-y: auto;
                min-height: 280;       /* 🔥 critical */
                padding: 6px 0;
            }

            /* Row style */
            .ess-compliance-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                border-bottom: 1px solid #e5e7eb;
                cursor: pointer;
            }

            .ess-compliance-row:last-child {
                border-bottom: none;
            }

            .ess-compliance-row:hover {
                background: #f8fafc;
            }

            /* Left side */
            .ess-compliance-left {
                display: flex;
                align-items: center;
                gap: 10px;
            }

            /* Icon bubble */
            .ess-compliance-icon {
                width: 26px;
                height: 26px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-size: 13px;
            }

            /* Count badge */
            .ess-compliance-count {
                font-size: 12px;
                font-weight: 600;
                background: #e0e7ff;
                color: #1e40af;
                padding: 2px 8px;
                border-radius: 999px;
            }

            /* KPI-compatible merged card */
            .ess-compliance-expiry-card {
                display: flex;
                flex-direction: column;
            }

            /* Scrollable content inside KPI card */
            .ess-compliance-expiry-card .ess-compliance-expiry-list {
                flex: 1 1 auto;
                overflow-y: auto;
                min-height: 280;      /* 🔑 REQUIRED */
                padding: 4px 0;
            }            

            .ess-compliance-icon {
                width: 26px;
                height: 26px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-size: 13px;
                flex-shrink: 0;
            }

            .ess-compliance-label {
                font-size: 13px;
                color: #374151;
            }           
            
            /* ===============================
            Login Employee Profile Card
            =============================== */

            .ess-profile-card {
                display: flex;
                flex-direction: column;
            }

            .ess-profile-body {
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 4px;
                flex: 1;
            }

            .ess-profile-avatar {
                width: 56px;
                height: 50px;
                border-radius: 12px;
                background: #e5e7eb;
                overflow: hidden;
                flex-shrink: 0;
            }

            .ess-profile-avatar img {
                width: 100%;
                height: 100%;
                object-fit: cover;
            }

            .ess-profile-info {
                display: flex;
                flex-direction: column;
                gap: 2px;
            }

            .ess-profile-name {
                font-size: 11px;
                font-weight: 400;
                color: #111827;
            }

            .ess-profile-meta {
                font-size: 10px;
                color: #6b7280;
            }

            .ess-profile-avatar {
                width: 75px;
                height: 50px;
                min-width: 16px;   /* 🔑 important in flex */
                min-height: 12px;
                border-radius: 10px;
                background: #e5e7eb;
                overflow: hidden;
                flex-shrink: 0;
            }

            .ess-profile-avatar img {
                width: 100%;
                height: 100%;
                object-fit: cover;
                display: block;
            }
            .kpi-line {
                height: 4px;              /* 👈 thickness */
                background: currentColor; /* keeps card color theme */
                border-radius: 4px;
                margin-top: 12px;
}
                .kpi-line {
                height: 5px;
                border-radius: 6px;
                box-shadow: 0 2px 6px rgba(0,0,0,.15);
            }

            /* Pending Requests rows – compact height */
            .ess-pending-list .ess-pending-row {
                padding: 6px 12px;     /* 🔻 reduced from ~10–12px */
                min-height: 26px;      /* 🔻 tighter row */
                line-height: 1.0;
            }
            .ess-pending-row i {
                font-size: 14px;
            }
            

            /* Reset order for all KPI cards */
            .ess-kpi-strip > .ess-kpi-card,
            .ess-kpi-strip > .ess-card {
                order: 100;
            }

            /* Reset everything first */
            .ess-kpi-strip > .ess-kpi-card,
            .ess-kpi-strip > .ess-card {
                order: 100 !important;
            }

            /* =======================
            FIRST ROW
            ======================= */

            /* 1️⃣ My Profile — FORCE FIRST */
            .ess-kpi-strip .ess-profile-card {
                order: 1 !important;
            }

            /* 2️⃣ Reporting To You */
            .ess-kpi-strip .kpi-blue:not(.ess-leave-card):not(.ess-profile-card) {
                order: 2 !important;
            }

            /* 3️⃣ Active Employees */
            .ess-kpi-strip .kpi-green {
                order: 3 !important;
            }

            /* 4️⃣ Pending Appraisals */
            .ess-kpi-strip .kpi-purple:not(.ess-compliance-expiry-card) {
                order: 4 !important;
            }

            /* =======================
            SECOND ROW
            ======================= */

            /* 5️⃣ Pending Requests */
            .ess-kpi-strip .ess-pending-requests-card {
                order: 5 !important;
            }

            /* 6️⃣ Employee Compliance */
            .ess-kpi-strip .ess-compliance-expiry-card {
                order: 6 !important;
            }

            /* 7️⃣ Leave Balance */
            .ess-kpi-strip .ess-leave-card {
                order: 7 !important;
            }

            /* 8️⃣ Today’s Attendance */
            .ess-kpi-strip .ess-attendance-card {
                order: 8 !important;
            }



            /* Tighten spacing below Pending Requests title */
            .ess-pending-requests-card .ess-card-header {
                margin-bottom: 6px;   /* 🔻 reduce gap (default is ~12–16px) */
                padding-bottom: 2px;
            }

            /* Reduce top padding of list */
            .ess-pending-requests-card .ess-pending-list {
                padding-top: 2px;     /* 🔻 was larger */
            }
            .ess-pending-requests-card .ess-pending-row:first-child {
                margin-top: 0;
            }

            /* 🔑 Reduce space below Pending Requests title */
            .ess-pending-requests-card .ess-card-header {
                margin-bottom: 2px !important;
                padding-bottom: 2px !important;
            }

            /* 🔑 Kill extra spacing before list */
            .ess-pending-requests-card .ess-pending-list {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }

            /* 🔑 Reduce top spacing of first item */
            .ess-pending-requests-card .ess-pending-row:first-child,
            .ess-pending-requests-card .ess-pending-item:first-child {
                margin-top: 0 !important;
                padding-top: 6px !important;
            }

            #nationality-chart .ess-rank-row:nth-child(3n+1) .ess-rank-bar span {
                background-color: #3b82f6; /* blue */
            }

            #nationality-chart .ess-rank-row:nth-child(3n+2) .ess-rank-bar span {
                background-color: #22c55e; /* green */
            }

            #nationality-chart .ess-rank-row:nth-child(3n+3) .ess-rank-bar span {
                background-color: #f59e0b; /* amber */
            }

            /* Enable vertical scrolling for nationality list */
            #nationality-chart {
                max-height: 260px;     /* adjust as needed */
                overflow-y: auto;
                padding-right: 6px;    /* space for scrollbar */
            }

            .nat-bar-fill {
                border-radius: 6px;
                height: 8px;
            }

            .ess-netpay-summary-list {
                max-height: 220px;
                overflow-y: auto;
                margin-top: 8px;
            }

            .ess-netpay-summary-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 6px 4px;
                font-size: 13px;
            }

            .ess-netpay-summary-label {
                color: #334155;
            }

            .ess-netpay-summary-value {
                font-weight: 600;
            }

            /* 🔑 Force border on Net Payroll chart + summary cards */
            // .ess-charts-grid .ess-card.ess-netpay-box {
            //     /*border: 5px solidrgb(24, 65, 148) !important;*/
            //     border-radius: 12px !important;
            //     box-shadow: none !important;
            //     background: #f8fafc !important;;
            //     border: 1px solid #e5e7eb !important;;
            // }


            .ess-netpay-box .kpi-line {
                opacity: 0.9;
            }

            /* Make Net Payroll cards match other cards */
            .ess-netpay-box {
                background: #e5e7eb !important;
            }

            .ess-pending-requests-card .ess-pending-list {
                    max-height: 260px;
                    overflow-y: auto;
                }

                /* Leave Balance scroll */
            .ess-leave-card #ess-leave-balance-list {
                max-height: 210px;        /* adjust if needed */
                overflow-y: auto;
                padding-right: 6px;       /* space for scrollbar */
            }

            .ess-leave-card #ess-leave-balance-list::-webkit-scrollbar {
                width: 6px;
            }

            .ess-leave-card #ess-leave-balance-list::-webkit-scrollbar-thumb {
                background: #cbd5f5;
                border-radius: 6px;
            }

            .ess-leave-card #ess-leave-balance-list::-webkit-scrollbar-track {
                background: transparent;
            }
            /* Fix Leave Balance card height */
            .ess-kpi-strip .ess-leave-card {
                height: 100px;              /* adjust to match other cards */                
                display: flex;
                flex-direction: column;
            }

            /* Scroll only the leave list */
            .ess-kpi-strip .ess-leave-card #ess-leave-balance-list {
                flex: 1;                    /* 🔑 takes remaining space */
                overflow-y: auto;
                padding-right: 6px;
            }
            .ess-kpi-strip .ess-leave-card > *:not(#ess-leave-balance-list) {
                flex-shrink: 0;
            }

            /* Lock Leave Balance card height */
            .ess-kpi-strip .ess-leave-card {
                height: 220px;              /* 🔑 REQUIRED */
                display: flex;
                flex-direction: column;
            }

            /* Scroll area */
            .ess-kpi-strip .ess-leave-card #ess-leave-balance-list {
                flex: 1;                    /* 🔑 consumes remaining space */
                overflow-y: auto;
                min-height: 0;              /* 🔥 critical for flex overflow */
                padding-right: 6px;
            }
            .ess-kpi-strip .ess-leave-card > *:not(#ess-leave-balance-list) {
                flex-shrink: 0;
            }

            .ess-kpi-strip .ess-leave-card{
                max-height: 210px !important;;
            }
            
            /* 🔥 THIS is what was missing */
            .ess-leave-card #ess-leave-balance-list {
                flex: 1;
                min-height: 0;      /* CRITICAL */
                overflow-y: auto;
            }

            /* First row KPI cards */
            .ess-kpi-strip > .ess-kpi-card,
            .ess-kpi-strip > .ess-card {
                padding-top: 12px;
                padding-bottom: 10px;
            }

            .ess-kpi-strip .kpi-line {
                height: 3px;          /* was 4–6 */
            }

            /* Reduce overall height of first row cards */
            .ess-kpi-strip > .ess-kpi-card,
            .ess-kpi-strip > .ess-card {
                max-height: 60px !imortant;    /* adjust to taste: 130–150 */
            }

            .layout-main-section {
            padding-left: 4px !important;
            padding-right: 4px !important;
            }

            .ess-fullwidth {
                margin-left: -12px;
                margin-right: -12px;
            }
            
            layout-main-section{
            margin-left: 2px;
                margin-right: 2px;
            }
            
            /* Align KPI content with title text */
            .ess-kpi-card .kpi-main,
            .ess-kpi-card .kpi-sub {
                padding-left: 28px; /* aligns with title text after icon */
            }

            /* =====================================================
            KPI CARD HEIGHT + TITLE ↔ CONTENT GAP TUNING
            (SAFE OVERRIDE)
            ===================================================== */

            /* Reduce overall KPI card height */
            .ess-kpi-strip > .ess-kpi-card {
                padding-top: 10px !important;
                padding-bottom: 8px !important;
                min-height: 70px !important;   /* 🔽 was taller */
            }

            /* Increase gap between title row and main value */
            .ess-kpi-card .kpi-header {
                margin-bottom: 10px !important;   /* 🔼 space after title */
            }

            /* Tighten main value block slightly */
            .ess-kpi-card .kpi-main {
                line-height: 1.2;
            }

            /* Optional: slightly reduce subtitle spacing */
            .ess-kpi-card .kpi-sub {
                margin-top: 2px;
            }

            /* =====================================================
            PROFILE CARD – COMPACT HEIGHT FIX
            ===================================================== */

            /* Reduce overall card padding */
            .ess-profile-card {
                padding-top: 10px !important;
                padding-bottom: 8px !important;
            }

            /* Reduce gap between title and content */
            .ess-profile-card .ess-card-header {
                margin-bottom: 6px !important;   /* 🔻 was larger */
            }

            /* Tighten profile body */
            .ess-profile-body {
                padding: 4px !important;        /* 🔻 was ~14px */
                gap: 4px !important;
            }

            /* Slightly reduce avatar size (critical for height) */
            .ess-profile-avatar {
                width: 60px !important;
                height: 60px !important;
            }

            /* Reduce text spacing */
            .ess-profile-info {
                gap: 1px !important;
            }

            /* Optional: tighten name line-height */
            .ess-profile-name {
                line-height: 1.2;
            }

            /* =====================================================
            FIX: Pending Requests card breaking KPI layout
            ===================================================== */

            /* Treat Pending Requests as a KPI card */
            .ess-pending-requests-card {
                grid-column: span 1 !important;   /* 🔑 SAME as other cards */
                max-width: 100% !important;
            }

            /* Ensure it stays inside KPI strip */
            .ess-kpi-strip > .ess-pending-requests-card {
                width: 100% !important;
            }

            /* Prevent it from behaving like full-width section */
            .ess-pending-requests-card {
                align-self: stretch;
            }

            /* Tighten Pending Requests tabs */
            .ess-pending-requests-card .ess-tabs {
                margin-top: 4px !important;
                margin-bottom: 4px !important;
                gap: 4px;
            }

            .ess-pending-requests-card .ess-tab {
                padding: 4px 10px;
                font-size: 12px;
            }

            /* Lock Pending Requests card height like others */
            .ess-pending-requests-card {
                max-height: 220px;               /* same as KPI cards */
                display: flex;
                flex-direction: column;
            }

            /* Scroll only list */
            .ess-pending-requests-card #ess-pending-requests {
                flex: 1;
                overflow-y: auto;
                min-height: 0;                   /* 🔥 REQUIRED for flex scroll */
            }

            #ess-yearly-payroll-amount {
                text-align: right;
            }

            /* Net Payroll Year dropdown – match other filters */
            #net-payroll-year-select {
                background: linear-gradient( 180deg, #f1f5f9, #e9eef5 );
                border-radius: 16px;
            }
            
            .ess-card {
                background: #e5e7eb !important;
            }

            /* Make Year dropdown match Month input (Net Payroll) */
            #net-payroll-year-select {
                background: #f8fafc;              /* same soft bg */
                border: none !important;          /* 🔥 remove black border */
                border-radius: 10px;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: 600;
                color: #0f172a;
                box-shadow: inset 0 0 0 1px #e5e7eb;  /* subtle outline like Frappe */
            }

            [data-page-route="ess"] #ess-dashboard {
                max-width: 99%;
                margin: 0px auto;
            }

            /* Make chart/card borders visible but subtle */
            .ess-card {
                border: 2px solid rgba(15, 23, 42, 0.08); /* slate outline */
            }

            .ess-card:hover {
                border-color: rgba(59, 130, 246, 0.35);
            }

            /* ================= ESS CARD – VISIBLE BUT SUBTLE BORDER ================= */

            [data-page-route="ess"] .ess-card,
            [data-page-route="ess"] .ess-kpi-card {
                background: #e5e7eb; /* keep existing bg */
                border: 1px solid rgba(15, 23, 42, 0.10);  /* 🔑 visible outline */
                border-radius: 16px;
                box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08); /* keep depth */
            }

            .ess-turnover-kpi {
                text-align: center;
                margin-bottom: 12px;
            }

            .ess-turnover-value {
                font-size: 28px;
                font-weight: 700;
                color: #0f172a;
            }

            .ess-turnover-label {
                font-size: 12px;
                color: #64748b;
            }

                        /* Match payroll monthly spacing */
            .ess-turnover-card .ess-field-label {
                font-size: 12px;
                color: #6b7280;
                margin: 12px 0 6px;
            }

            .ess-turnover-body {
                margin-top: 24px;
                text-align: center;
            }

            .ess-turnover-value {
                font-size: 32px;
                font-weight: 600;
                color: #1f2937;
            }

            .ess-turnover-label {
                margin-top: 6px;
                font-size: 13px;
                color: #64748b;
            }

            /* Remove extra gap between label and control (Turnover only) */
            .ess-turnover-card .ess-field-label {
                margin-bottom: 4px;   /* ↓ reduce gap */
            }

            .ess-turnover-card .frappe-control {
                margin-top: 0;
            }

            /* Remove extra space caused by clearfix in Turnover card only */
            .ess-turnover-card .clearfix {
                display: none;
            }

            /* Match height with other ESS cards */
            .ess-turnover-card {
                height: 360px;              /* 🔥 match other cards */
                display: flex;
                flex-direction: column;
            }

            /* Body should manage internal layout */
            .ess-turnover-card .ess-turnover-body {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: flex-start;
            }

            /* Chart occupies fixed space like others */
            .ess-turnover-card .ess-turnover-chart {
                height: 160px;              /* 🔥 same chart height */
                width: 100%;
                margin-top: 12px;
            }

            /* Ensure canvas fills chart area */
            .ess-turnover-card .ess-turnover-chart canvas {
                width: 100% !important;
                height: 100% !important;
            }

            /* Prevent extra spacing inside turnover card */
            .ess-turnover-card .clearfix {
                display: none;
            }

            /* ---------- Turnover Card Fixes ---------- */

            .ess-turnover-card .ess-card-body {
                padding-top: 12px;
            }

            .ess-turnover-kpi {
                margin-bottom: 12px;
                text-align: center;
            }

            .ess-turnover-chart {
                height: 240px;
            }

            /* Prevent random clearfix spacing */
            .ess-turnover-card .clearfix {
                display: none;
            }

            /* Tabs spacing consistency */
            #ess-turnover-tabs {
                margin-top: 8px;
            }

            /* ---------- Month Picker Alignment ---------- */

            .ess-turnover-card .ess-filter {
                margin-bottom: 10px;
            }

            .ess-turnover-card .ess-filter-label {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 4px;
            }

            .ess-turnover-card .control-input {
                margin-top: 0 !important;
            }

            .ess-turnover-card .form-control {
                background: #f9fafb;
            }

            /* Turnover chart MUST be taller */
            .ess-turnover-chart {
                height: 300px;   /* 
                margin-top: 8px;
                height: 300px;   /* 🔑 critical */
            }

            /* ---------- Turnover Month Picker FIX ---------- */

            .ess-turnover-card .control-input-wrapper {
                margin-top: 0 !important;
            }

            .ess-turnover-card .control-input {
                margin-top: 0 !important;
                padding-top: 0 !important;
            }

            .ess-turnover-card .control-input .clearfix {
                display: none !important;   /* 🔑 removes extra space */
            }

            .ess-turnover-card .form-control {
                height: 36px;
                background: #f9fafb;
            }

            /* Label alignment */
            .ess-turnover-card .ess-filter-label {
                margin-bottom: 2px;
                line-height: 1.2;
            }

            /* ===== Turnover Header Layout FIX ===== */

            .ess-turnover-card .ess-card-header-row {
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                gap: 12px;
            }

            /* Left: title */
            .ess-turnover-card .ess-card-title {
                flex: 1;
            }

            /* Right: month picker */
            .ess-turnover-card .ess-filter {
                min-width: 180px;
                text-align: left;
            }

            /* 🔥 Kill Frappe label inside turnover card */
            .ess-turnover-card .control-label {
                display: none !important;
            }

            .ess-turnover-card .control-input-wrapper,
            .ess-turnover-card .control-input {
                margin: 0 !important;
                padding: 0 !important;
            }

            .ess-turnover-card .form-control {
                width: 100%;
                height: 36px;
                background: #f9fafb;
                text-align: left;
            }

            /* Remove hidden spacing culprit */
            .ess-turnover-card .control-input .clearfix {
                display: none !important;
            }

            .ess-turnover-chart {
                height: 320px;
            }

            /* ================================
            TURNOVER MONTH PICKER POLISH
            ================================ */

            .ess-turnover-card .ess-card-control {
                width: 100%;
            }

            /* Full-width input */
            .ess-turnover-card .form-control {
                width: 100%;
                height: 40px;              /* 🔑 thicker */
                padding: 8px 12px;         /* 🔑 better vertical feel */
                font-size: 14px;
                border-radius: 10px;
                background: #f9fafb;
            }

            /* Remove any inherited max-width */
            .ess-turnover-card .control-input-wrapper,
            .ess-turnover-card .control-input {
                max-width: none !important;
                width: 100%;
            }

            /* Remove extra spacing injected by Frappe */
            .ess-turnover-card .clearfix {
                display: none !important;
            }


        }   

    `;              

                document.head.appendChild(style);
            }


function bind_events() {
    document.addEventListener("click", e => {

        /* ================= CHART TABS (HANDLE FIRST) ================= */

        if (e.target.dataset.headcount) {
            e.preventDefault();
            e.stopPropagation();

            document
                .querySelectorAll("[data-headcount]")
                .forEach(b => b.classList.remove("active"));

            e.target.classList.add("active");
            load_headcount_chart(e.target.dataset.headcount);
            return;
        }

        if (e.target.dataset.netpay) {
            e.preventDefault();
            e.stopPropagation();

            document
                .querySelectorAll("[data-netpay]")
                .forEach(b => b.classList.remove("active"));

            e.target.classList.add("active");
            load_net_payroll_chart(e.target.dataset.netpay);
            return;
        }

        /* ================= KPI CARDS ONLY ================= */

        const card = e.target.closest(".ess-kpi-card");
        if (!card) return;

        // 🚫 Disabled KPI
        if (card.classList.contains("is-disabled")) {
            e.preventDefault();
            return;
        }

        // 🚫 Ignore clicks from tooltips / pills
        if (e.target.closest(".ess-pending-tooltip-row")) return;
        if (e.target.closest(".ess-pending-pill")) return;

        // ✅ Navigate KPI
        if (card.dataset.route) {
            window.open(card.dataset.route, "_blank");
        }
    });
}


/* =====================================================
   DATA LOADERS (SAFE)
===================================================== */

const setText = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.innerText = val;
};

/* KPI */
function load_kpis() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_kpi_summary",
        callback: r => {
            const d = r.message || {};

            /* ================= Reporting To You ================= */

            setText(
                "kpi-reporting",
                `${d.reporting_count || 0} Employees`
            );

            const reportingNames = d.reporting_employees || [];
            // setText(
            //     "kpi-reporting-name",
            //     reportingNames.length
            //         ? `${reportingNames.length} Direct Reports`
            //         : "—"
            // );

            const reportingCard = document
                .getElementById("kpi-reporting")
                ?.closest(".ess-kpi-card");

            if (reportingCard && d.reporting_employees?.length) {
                const params = new URLSearchParams();
                params.append(
                    "name",
                    JSON.stringify(["in", d.reporting_employees])
                );
                reportingCard.dataset.route =
                    `/app/employee?${params.toString()}`;
            } else if (reportingCard) {
                reportingCard.removeAttribute("data-route");
            }

            toggle_kpi_click("kpi-reporting", d.reporting_count);

            /* ================= Active Employees ================= */

            setText(
                "kpi-active",
                `${d.active_employees || 0} Employees`
            );

            const g = d.active_gender_split || {};
            const genderText =
                (g.Female || 0) + (g.Male || 0) > 0
                    ? `${g.Female || 0} Female · ${g.Male || 0} Male`
                    : "—";

            setText("kpi-active-sub", genderText);

            const activeCard = document
                .getElementById("kpi-active")
                ?.closest(".ess-kpi-card");

            if (activeCard && d.active_employee_list?.length) {
                const params = new URLSearchParams();
                params.append(
                    "name",
                    JSON.stringify(["in", d.active_employee_list])
                );
                activeCard.dataset.route =
                    `/app/employee?${params.toString()}`;
            } else if (activeCard) {
                activeCard.removeAttribute("data-route");
            }

            toggle_kpi_click("kpi-active", d.active_employees);

            /* ================= Pending Appraisals ================= */

            setText(
                "kpi-appraisal-days",
                `${d.pending_appraisal_days || 0} Days`
            );

            setText(
                "kpi-appraisal-count",
                `${d.pending_appraisals || 0} Appraisals`
            );

            const appraisalCard = document
                .getElementById("kpi-appraisal-count")
                ?.closest(".ess-kpi-card");

            if (
                appraisalCard &&
                d.pending_appraisals > 0 &&
                d.pending_appraisal_employees?.length
            ) {
                const params = new URLSearchParams({
                    docstatus: 0,
                    employee: JSON.stringify([
                        "in",
                        d.pending_appraisal_employees
                    ])
                });

                appraisalCard.dataset.route =
                    `/app/appraisal?${params.toString()}`;
            } else if (appraisalCard) {
                appraisalCard.removeAttribute("data-route");
            }

            toggle_kpi_click(
                "kpi-appraisal-count",
                d.pending_appraisals
            );
        }
    });
}



function toggle_kpi_click(elementId, count) {
    const el = document.getElementById(elementId);
    if (!el) return;

    const card = el.closest(".ess-kpi-card");
    if (!card) return;

    if (!count || count <= 0) {
        card.classList.add("is-disabled");
        card.removeAttribute("data-route");
    } else {
        card.classList.remove("is-disabled");
    }
}


const ESS_TEST_MODE = false;   // 🔥 set false in production

/* Pending Requests (List View Style) */

function load_pending_requests_for_me() {
    const box = document.getElementById("ess-pending-requests");
    //console.log(box);
    if (!box) return;

    const card = box.closest(".ess-pending-requests-card");

    // Known icon + color mapping (optional, extensible)
    const iconMap = {
        "Leave Application": { icon: "fa-calendar-check-o", color: "#22c55e" },
        "Expense Claim": { icon: "fa-money", color: "#3b82f6" },
        "Material Request": { icon: "fa-cubes", color: "#8b5cf6" },
        "Loan Application": { icon: "fa-bank", color: "#f59e0b" }
    };

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_pending_approvals_for_me",
        callback: r => {
            render_pending_request_list(
            r.message,
            "ess-pending-approvals"
        );
            //console.log(r.message);
            const data = r.message || {};
            const entries = Object.entries(data);

            // Clear container (do NOT create nested list)
            box.innerHTML = "";

            /* ================= EMPTY STATE ================= */
            if (!entries.length) {
                card?.classList.add("is-empty");
                box.innerHTML = `
                    <div class="ess-muted" style="padding:12px">
                        No Pending Requests
                    </div>
                `;
                return;
            }

            card?.classList.remove("is-empty");

            /* ================= LIST VIEW ================= */
            entries.forEach(([doctype, info]) => {
                const count = info?.count || 0;
                const names = info?.names || [];
                if (!count || !names.length) return;

                const meta = iconMap[doctype] || {
                    icon: "fa-file-text-o",
                    color: "#64748b"
                };

                const row = document.createElement("div");
                row.className = "ess-pending-item";

                row.innerHTML = `
                    <div class="ess-pending-left">
                        <div class="ess-pending-icon"
                             style="background:${meta.color}">
                            <i class="fa ${meta.icon}"></i>
                        </div>
                        <div class="ess-pending-title">
                            ${doctype}
                        </div>
                    </div>
                    <div class="ess-pending-count">
                        ${count}
                    </div>
                `;

                /* ===== CLICK → OPEN LIST (NEW TAB) ===== */
                row.addEventListener("click", () => {
                    const params = new URLSearchParams();
                    params.append(
                        "name",
                        JSON.stringify(["in", names])
                    );

                    window.open(
                        `/app/${frappe.router.slug(doctype)}?${params.toString()}`,
                        "_blank"
                    );
                });

                box.appendChild(row);
            });
        }
    });
}



/* Attendance */
function load_today_attendance() {
    const box = document.getElementById("ess-today-attendance");
    if (!box) return;

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_today_attendance_summary",
        callback: r => {
            const d = r.message || {};
            box.innerHTML = "";

            add_att_inline(box, "Present",    d.present,     "Present");
            add_att_inline(box, "Absent",     d.absent,      "Absent");
            add_att_inline(box, "On Leave",   d.leave,       "On Leave");
            add_att_inline(box, "Late",       d.late,        "Late");
            add_att_inline(box, "Early Exit", d.early_exit,  "Early Exit");
            add_att_inline(box, "Half Day",   d.half_day,    "Half Day");
        }
    });
}


function add_att_inline(parent, label, data, status) {
    const config = {
        "Present":    { icon: "fa-check",    cls: "att-present" },
        "Absent":     { icon: "fa-times",    cls: "att-absent" },
        "On Leave":   { icon: "fa-plane",    cls: "att-leave" },
        "Late":       { icon: "fa-clock-o",  cls: "att-late" },
        "Early Exit": { icon: "fa-sign-out", cls: "att-early" },
        "Half Day":   { icon: "fa-adjust",   cls: "att-half" }
    };

    const cfg = config[status] || { icon: "fa-circle", cls: "" };
    const today = frappe.datetime.get_today();

    const count = data?.count || 0;
    const employees = data?.employees || [];

    const clickable = count > 0 && employees.length > 0;

    parent.insertAdjacentHTML("beforeend", `
        <div class="ess-att-inline-item ${!clickable ? "is-disabled" : ""}"
             ${clickable ? "data-clickable='1'" : ""}>

            <span class="ess-att-left">
                <span class="ess-att-icon ${cfg.cls}">
                    <i class="fa ${cfg.icon}"></i>
                </span>
                <span>${label}</span>
            </span>

            <b>${count}</b>
        </div>
    `);

    if (!clickable) return;

    const row = parent.lastElementChild;

    row.onclick = () => {
        const params = new URLSearchParams({
            employee: JSON.stringify(["in", employees]),
            attendance_date: JSON.stringify(["=", today]),
            status: status
        });

        // ✅ OPEN IN NEW TAB
        window.open(`/app/attendance?${params.toString()}`, "_blank");
    };
}


/* Compliance */

function load_compliance_summary() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_compliance_summary",
        callback: r => {
            const data = r.message || {};
            const entries = Object.entries(data);

            if (!entries.length) {
                console.warn("No compliance data found");
                return;
            }

            const box = document.querySelector(".ess-compliance-list");
            if (!box) {
                console.error("Compliance container not found (.ess-compliance-list)");
                return;
            }

            box.innerHTML = "";

            const COLOR_MAP = {
                pending_confirmations: "dot-green",
                expiring_contracts: "dot-orange",
                missing_leave_allocations: "dot-red",
                visa_expiry: "dot-blue"
            };

            const LABEL_MAP = {
                pending_confirmations: "Pending Confirmations",
                expiring_contracts: "Expiring Contracts (30 Days)",
                missing_leave_allocations: "Missing Leave Allocation",
                visa_expiry: "Visa Expiry (30 Days)"
            };

            entries.forEach(([key, value]) => {
                const count = value?.count || 0;
                const employees = value?.employees || [];

                const row = document.createElement("div");
                row.className = "ess-compliance-row";

                if (count <= 0) {
                    row.classList.add("is-disabled");
                }

                row.innerHTML = `
                    <div class="ess-compliance-left">
                        <span class="ess-dot ${COLOR_MAP[key] || "dot-blue"}"></span>
                        <span>${LABEL_MAP[key] || key}</span>
                    </div>
                    <b>${count}</b>
                `;

                /* 🔴 NO NAVIGATION WHEN COUNT = 0 */
                if (count <= 0 || !employees.length) {
                    box.appendChild(row);
                    return;
                }

                /* ✅ SINGLE, CORRECT DRILL-DOWN */
                row.onclick = () => {
                    if (!employees || !employees.length) return;

                    const params = new URLSearchParams({
                        name: JSON.stringify(["in", employees])
                    });

                    window.open(`/app/employee?${params.toString()}`, "_blank");
                };


                box.appendChild(row);
            });
        }
    });
}

/* Leave Balance */
function load_leave_employee_list() {
    const select = document.getElementById("ess-leave-employee");
    if (!select) return;

    frappe.call({
    method: "sowaan_hr.sowaan_hr.page.ess.ess.get_leave_balance_employees",
    callback: r => {
        const employees = r.message || [];

        if (!employees.length) return;
        //console.log(employees.length);
        // 🔑 IMPORTANT: use set_data (NOT options)
        leave_employee_link_control.set_data(employees);

        // 🔑 Auto-select self (first item)
        leave_employee_link_control.set_value(employees[0].name);

        // 🔑 Disable clearing if only one employee
        if (employees.length === 1) {
            leave_employee_link_control.$input.prop("disabled", true);
            leave_employee_link_control.$input
                .closest(".control-input")
                .find(".clear")
                .hide();
        }
    }
});

}

function load_leave_balance(emp) {
    const box = document.getElementById("ess-leave-balance");
    if (!box) return;

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_leave_balances",
        args: { employee: emp },
        callback: r => {
            box.innerHTML = "";
            (r.message || []).forEach(l => {
                box.innerHTML += `
                    <div class="ess-leave-row">
                        <span>${l.leave_type}</span>
                        <b>${l.balance}</b>
                    </div>`;
            });
        }
    });
}

let selectedSalaryMonth = frappe.datetime.month_start().slice(0, 7);

function make_salary_month_picker() {
    const parent = document.getElementById("salary-month-field");
    if (!parent) return;

    const field = frappe.ui.form.make_control({
        parent,
        df: {
            fieldtype: "Date",
            label: "Month",
            onchange() {
                const v = field.get_value();
                if (!v) return;
                selectedSalaryMonth = v.slice(0, 7);
                load_salary_chart("department");
            }
        },
        render_input: true
    });

    field.set_value(frappe.datetime.month_start());
}

let headcountDataCache = {};
function load_headcount_chart(by) {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_headcount_breakdown",
        args: { by },
        callback: r => {
            if (!r.message) return;

            const container = document.getElementById("ess-headcount-chart");
            if (!container) return;

            container.replaceChildren();

            const rawLabels = r.message.labels || [];
            const values = r.message.datasets[0].values || [];

            // 🔑 SHORT LABELS (shown under bars)
            const shortLabels = rawLabels.map(l =>
                l.length > 6 ? l.slice(0, 6) + "…" : l
            );

            // 🔑 CONTEXTUAL TOOLTIP NAME
            const datasetNameMap = {
                department: "Department",
                branch: "Branch",
                employment_type: "Employment Type"
            };

            new frappe.Chart(container, {
                data: {
                    labels: shortLabels,
                    datasets: [{
                        name: datasetNameMap[by] || "Headcount",
                        values
                    }]
                },
                type: "bar",

                // 🔑 KEY: chart geometry (NOT CSS)
                height: 280,                 // gives space for labels
                barOptions: {
                    spaceRatio: 0.55          // bars not touching bottom
                },
                axisOptions: {
                    xAxisMode: "tick",        // labels BELOW bars
                    yAxisMode: "span",
                    xIsSeries: true
                },
                colors: ["#3b82f6"],

                tooltipOptions: {
                    // 🔥 tooltip uses FULL name, not shortened
                    formatTooltipX: d => rawLabels[shortLabels.indexOf(d)] || d,
                    formatTooltipY: d => d
                }
            });

            /* ===============================
               CLICK → OPEN EMPLOYEE LIST
               (subordinates enforced)
            =============================== */

            setTimeout(() => {
                const svg = container.querySelector("svg");
                if (!svg) return;

                svg.onclick = e => {
                    let el = e.target;

                    while (el && el !== svg && !el.classList?.contains("bar")) {
                        el = el.parentNode;
                    }
                    if (!el || !el.classList.contains("bar")) return;

                    const bars = Array.from(svg.querySelectorAll("rect.bar"));
                    const index = bars.indexOf(el);
                    if (index < 0) return;

                    const actualLabel = rawLabels[index];
                    if (!actualLabel) return;

                    // 🔑 get subordinates safely
                    frappe.call({
                        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_accessible_employees",
                        callback: r => {
                            const employees = r.message || [];
                            if (!employees.length) return;

                            frappe.route_options = null;

                            const params = new URLSearchParams();
                            params.append(by, actualLabel);
                            params.append(
                                "name",
                                JSON.stringify(["in", employees])
                            );

                            window.open(
                                `/app/employee?${params.toString()}`,
                                "_blank"
                            );
                        }
                    });
                };
            }, 100);
        }
    });
}



function make_net_payroll_month_picker() {
    const field = frappe.ui.form.make_control({
        parent: document.getElementById("net-payroll-month-field"),
        df: {
            fieldtype: "Date",
            label: "Month",
            onchange() {
                const v = field.get_value();
                if (!v) return;
                selectedNetPayrollMonth = v.slice(0, 7);
                load_net_payroll_chart("department");
            }
        },
        render_input: true
    });

    field.set_value(frappe.datetime.month_start());
}

let selectedNetPayrollMonth = frappe.datetime.month_start().slice(0, 7);
function load_net_payroll_chart(by) {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_net_payroll_breakdown",
        args: {
            month: selectedNetPayrollMonth,
            by
        },
        callback: r => {
            if (!r.message) return;

            const container = document.getElementById("net-payroll-chart");
            if (!container) return;

            // ✅ SAFE CLEANUP (no DOMException)
            container.replaceChildren();

            const chartData = r.message;
            const labels = chartData.labels || [];

            const chart = new frappe.Chart(container, {
            data: chartData,
            type: "bar",
            height: 240,
            colors: ["#2563eb"],

            axisOptions: {
                xAxisMode: "span",   // 🔥 hide category labels completely
                yAxisMode: "tick"    // keep value scale
            },

            barOptions: {
                spaceRatio: 0.45
            },

            //valuesOverPoints: true, // 🔥 show values ON bars (horizontal text)

            tooltipOptions: {
                formatTooltipX: d => d,   // department / branch / type
                formatTooltipY: d =>
                    frappe.format(d, { fieldtype: "Currency" })
            }
        });





            // ✅ Attach click ONCE, after render
            setTimeout(() => {
                const svg = container.querySelector("svg");
                if (!svg) return;

                svg.onclick = (e) => {
                    let el = e.target;

                    while (el && el !== svg && !el.classList?.contains("bar")) {
                        el = el.parentNode;
                    }
                    if (!el || !el.classList.contains("bar")) return;

                    const bars = Array.from(svg.querySelectorAll("rect.bar"));
                    const index = bars.indexOf(el);
                    if (index < 0) return;

                    const label = labels[index];
                    if (!label) return;

                    frappe.call({
                        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_employees_for_net_payroll_filter",
                        args: {
                            by,
                            value: label,
                            month: selectedNetPayrollMonth
                        },
                        callback: r => {
                            const employees = r.message || [];
                            //console.log(employees.length)
                            if (!employees.length) return;

                            const params = new URLSearchParams();
                            params.append(
                                "employee",
                                JSON.stringify(["in", employees])
                            );
                            params.append(
                                "start_date",
                                selectedNetPayrollMonth + "-01"
                            );

                            window.open(
                                `/app/salary-slip?${params.toString()}`,
                                "_blank"
                            );
                        }
                    });
                };
            }, 100); // small delay is important
        }
    });
}

function update_net_payroll_title(month) {
    const el = document.getElementById("net-payroll-title");
    if (!el) return;

    el.innerHTML = `Net Payroll Breakdown <span class="text-muted">(${month})</span>`;
}

function load_expiry_soon() {
    const box = document.getElementById("ess-expiring-soon");
    if (!box) return;

    const STYLE_MAP = {
        "Contract Expiry (30 Days)": {
            icon: "fa-calendar-times-o",
            rowClass: "exp-contract",
            route: "/app/employee"
        },
        "Visa Expiry (30 Days)": {
            icon: "fa-id-card",
            rowClass: "exp-visa",
            route: "/app/employee"
        },
        "Passport Expiry (30 Days)": {
            icon: "fa-book",
            rowClass: "exp-passport",
            route: "/app/employee"
        },
        "Labor Card Expiry (30 Days)": {
            icon: "fa-briefcase",
            rowClass: "exp-labor",
            route: "/app/employee"
        }
    };

    // 🔁 HARD RESET (removes old DOM + handlers)
    box.replaceChildren();

    box.insertAdjacentHTML(
        "beforeend",
        `<div class="ess-muted">Loading...</div>`
    );

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_expiry_soon_summary",
        callback: r => {
            const data = r.message || {};

            // 🔁 CLEAR again after response
            box.replaceChildren();

            if (!Object.keys(data).length) {
                box.insertAdjacentHTML(
                    "beforeend",
                    `<div class="ess-muted">No upcoming expiries</div>`
                );
                return;
            }

            Object.entries(data).forEach(([key, info]) => {
                const cfg = STYLE_MAP[key];
                if (!cfg) return;

                const count = info?.count || 0;
                const employees = info?.employees || [];

                const disabled = count <= 0 || !employees.length;

                const row = document.createElement("div");
                row.className = `ess-compliance-row ${cfg.rowClass} ${
                    disabled ? "is-disabled" : ""
                }`;

                row.innerHTML = `
                    <div class="ess-compliance-left">
                        <i class="fa ${cfg.icon}"></i>
                        <span>${key}</span>
                    </div>
                    <b>${count}</b>
                `;

                if (!disabled) {
                    row.addEventListener(
                        "click",
                        e => {
                            e.preventDefault();
                            e.stopPropagation();

                            // 🔒 DOUBLE-CLICK / DOUBLE-HANDLER GUARD
                            if (row.dataset.clicked === "1") return;
                            row.dataset.clicked = "1";

                            const params = new URLSearchParams({
                                clear_filters: 1,
                                name: JSON.stringify(["in", employees])
                            });

                            window.open(
                                `${cfg.route}?${params.toString()}`,
                                "_blank"
                            );

                            // ♻️ allow future clicks safely
                            setTimeout(() => {
                                delete row.dataset.clicked;
                            }, 400);
                        },
                        { once: false } // explicit (clarity)
                    );
                }

                box.appendChild(row);
            });
        }
    });
}

function load_nationality_chart_BK() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_employee_ratio_by_nationality",
        callback: r => {
            if (!r.message) return;

            const container = document.getElementById("nationality-chart");
            if (!container) return;

            container.replaceChildren();

            const chartData = r.message;
            const labels = chartData.labels || [];

            const chart = new frappe.Chart(container, {
                data: chartData,
                type: "donut",
                height: 240,
                donutOptions: {
                    radius: 60,
                    donutRatio: 0.45,
                    labelThreshold: 2
                },
                legendOptions: {
                    position: "bottom"
                }
            });
                      

        setTimeout(() => {
    const legendItems = container.querySelectorAll(".chart-legend-item");

    legendItems.forEach((item, index) => {
        item.style.cursor = "pointer";

        item.onclick = () => {
            const nationality = labels[index];
            if (!nationality) return;

            frappe.call({
                method: "sowaan_hr.sowaan_hr.page.ess.ess.get_accessible_employees",
                callback: r => {
                    const employees = r.message || [];
                    if (!employees.length) return;

                    const params = new URLSearchParams();
                    params.append(
                        "name",
                        JSON.stringify(["in", employees])
                    );
                    params.append("nationality", nationality);

                    window.open(
                        `/app/employee?${params.toString()}`,
                        "_blank"
                    );
                }
            });
        };
    });
}, 300);
    

    

        }
    });
}

function load_nationality_chart() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_employee_ratio_by_nationality",
        callback: r => {
            if (!r.message) {                
                return;
            }

            renderNationalityList(r.message);
        }
    });
}

function renderNationalityList(data) {
    const container = document.getElementById("nationality-chart");
    if (!container) return;

    container.innerHTML = "";

    const labels = data.labels || [];
    const values = data.datasets?.[0]?.values || [];

    if (!labels.length) {
        container.innerHTML =
            `<div class="ess-muted">No nationality data</div>`;
        return;
    }

    const max = Math.max(...values, 1);

    labels.forEach((label, i) => {
    const value = values[i] || 0;

    const pct = Math.max((value / max) * 100, 12); // 🔑 define pct here

    const row = document.createElement("div");
    row.className = "ess-rank-row";

    row.innerHTML = `
        <div class="ess-rank-label">${label}</div>
        <div class="ess-rank-bar">
            <span style="width:${pct}%"></span>
        </div>
        <div class="ess-rank-value">${value}</div>
    `;

    row.onclick = () => {
        frappe.call({
            method: "sowaan_hr.sowaan_hr.page.ess.ess.get_accessible_employees",
            callback: r => {
                const employees = r.message || [];
                if (!employees.length) return;

                const params = new URLSearchParams();
                params.append(
                    "name",
                    JSON.stringify(["in", employees])
                );
                params.append("custom_nationality", label);

                window.open(
                    `/app/employee?${params.toString()}`,
                    "_blank"
                );
            }
        });
    };

    container.appendChild(row);
});

}



function load_monthly_attendance_trend_bk() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_monthly_attendance_trend",
        callback: r => {
            if (!r.message) return;

            const container = document.getElementById(
                "monthly-attendance-trend-2"
            );
            if (!container) return;

            container.replaceChildren();

            const months = r.message.months || [];
            const present = r.message.present || [];
            const absent_late = r.message.absent_late || [];

            if (!months.length) {
                container.innerHTML =
                    `<div class="ess-muted">No data available</div>`;
                return;
            }

            new frappe.Chart(container, {
                data: {
                    labels: months,
                    datasets: [
                        {
                            name: "Present",
                            values: present
                        },
                        {
                            name: "Absent / Late",
                            values: absent_late
                        }
                    ]
                },
                type: "line",
                height: 260,
                axisOptions: {
                    xAxisMode: "tick",
                    yAxisMode: "span",
                    xIsSeries: true
                },
                colors: ["#22c55e", "#ef4444"],
                lineOptions: {
                    dotSize: 4,
                    regionFill: 0
                }
            });
        }
    });
}

let monthlyAttendanceChart = null;

function load_monthly_attendance_trend() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_monthly_attendance_trend",
        callback: r => {
            if (!r.message) return;

            const container = document.getElementById(
                "monthly-attendance-trend-2"
            );
            if (!container) return;

            container.replaceChildren();

            const {
                months = [],
                present = [],
                absent = [],
                late = [],
                on_leave = []
            } = r.message;

            if (!months.length) {
                container.innerHTML =
                    `<div class="ess-muted">No data available</div>`;
                return;
            }

            new frappe.Chart(container, {
                data: {
                    labels: months,
                    datasets: [
                        {
                            name: "Present",
                            values: present
                        },
                        {
                            name: "Absent",
                            values: absent
                        },
                        {
                            name: "Late",
                            values: late
                        },
                        {
                            name: "On Leave",
                            values: on_leave
                        }
                    ]
                },
                type: "line",
                height: 220, // 🔑 compact like reference
                axisOptions: {
                    xAxisMode: "tick",
                    yAxisMode: "span",
                    xIsSeries: true
                },
                colors: [
                    "#22c55e", // Present (green)
                    "#ef4444", // Absent (red)
                    "#f97316", // Late (orange)
                    "#3b82f6"  // On Leave (blue)
                ],
                lineOptions: {
                    dotSize: 4,
                    regionFill: 0,
                    hideDots: false
                }
            });
        }
    });
}



function monthLabelToYYYYMM(label) {
    const d = moment(label, "MMM YYYY");
    if (!d.isValid()) return null;
    return d.format("YYYY-MM");
}




let appraisalStatusChart = null;
let appraisalRatingChart = null;

function load_performance_appraisal_summary() {
    ensure_chartjs_loaded(() => {

        frappe.call({
            method: "sowaan_hr.sowaan_hr.page.ess.ess.get_performance_appraisal_summary",
            callback: r => {
                const data = r.message || {};

                /* =====================================================
                   DONUT CHART – APPRAISAL STATUS
                ===================================================== */

                const donutWrap = document.getElementById("appraisal-status-chart");
                if (donutWrap && donutWrap.dataset.rendered !== "1") {
                    donutWrap.dataset.rendered = "1";
                    donutWrap.innerHTML = `<canvas></canvas>`;

                    const ctx = donutWrap.querySelector("canvas").getContext("2d");

                    let labels = data.status?.labels || [];
                    let values = data.status?.values || [];

                    let total = values.reduce((a, b) => a + b, 0);
                    let isEmpty = false;

                    // 🔹 Empty fallback
                    if (!total) {
                        isEmpty = true;
                        labels = ["No Appraisals"];
                        values = [1];
                    }

                    new Chart(ctx, {
                        type: "doughnut",
                        data: {
                            labels,
                            datasets: [{
                                data: values,
                                backgroundColor: isEmpty
                                    ? ["#e5e7eb"]
                                    : ["#f59e0b", "#22c55e", "#ef4444"],
                                borderWidth: 0
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            cutout: "65%",
                            plugins: {
                                legend: {
                                    position: "bottom"
                                },
                                tooltip: {
                                    enabled: !isEmpty
                                }
                            },
                            onClick: (_, elements) => {
                                // 🚫 No navigation if empty
                                if (isEmpty || !elements.length) return;

                                const status = labels[elements[0].index];
                                window.open(
                                    `/app/appraisal?status=${encodeURIComponent(status)}`,
                                    "_blank"
                                );
                            }
                        }
                    });
                }

                /* =====================================================
                   LINE CHART – AVG RATING TREND
                ===================================================== */

                const lineWrap = document.getElementById("appraisal-rating-chart");
                if (lineWrap && lineWrap.dataset.rendered !== "1") {
                    lineWrap.dataset.rendered = "1";

                    const labels = data.rating_trend?.labels || [];
                    const values = data.rating_trend?.values || [];

                    // 🔹 No data → show placeholder (heading still visible)
                    if (!labels.length) {
                        lineWrap.innerHTML =
                            `<div class="ess-muted">No rating data</div>`;
                        lineWrap.style.cursor = "default";
                        lineWrap.onclick = null;
                        return;
                    }

                    new frappe.Chart(lineWrap, {
                        data: {
                            labels,
                            datasets: [{
                                name: "Avg Rating",
                                values
                            }]
                        },
                        type: "line",
                        height: 200,
                        colors: ["#3b82f6"],
                        lineOptions: {
                            dotSize: 4,
                            regionFill: 0
                        },
                        axisOptions: {
                            xAxisMode: "tick",
                            yAxisMode: "span"
                        }
                    });

                    // ✅ Navigation only when chart has real data
                    lineWrap.style.cursor = "pointer";
                    lineWrap.onclick = () => {
                        window.open(
                            "/app/appraisal?docstatus=1",
                            "_blank"
                        );
                    };
                }
            }
        });

    });
}

function ensure_chartjs_loaded(cb) {
    if (window.Chart) return cb();

    const s = document.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js";
    s.onload = cb;
    document.head.appendChild(s);
}

let leave_employee_control = null;

let leave_employee_link_control = null;

function render_leave_employee_link_dropdown() {
    const wrapper = document.getElementById("leave-employee-link-control");
    const list = document.getElementById("ess-leave-balance-list");

    if (!wrapper || !list) return;

    wrapper.innerHTML = "";

    leave_employee_link_control = frappe.ui.form.make_control({
        parent: wrapper,
        df: {
            fieldtype: "Link",
            fieldname: "employee",
            label: "",                     // no label
            options: "Employee",
            placeholder: "Select Employee",

            show_title_field: true,   // 👈 REQUIRED
            
            get_query() {
                return {
                    query: "sowaan_hr.sowaan_hr.page.ess.ess.employee_leave_access_query"
                };
            },

            // 🔑 FORMAT DISPLAY VALUE
            formatter(value) {
                if (!value) return "";

                const row = this.last_selected_row;
                if (row && row.employee_name) {
                    return `${row.employee_name} (${value})`;
                }
                return value; // fallback
            },

            onchange() {
                const employee = leave_employee_link_control.get_value();

                // If cleared → reset UI
                if (!employee) {
                    clear_leave_balance_ui();
                    return;
                }

                // Load balances
                load_leave_balance_for_employee(employee);
            }
        },
        render_input: true
    });

    leave_employee_link_control.refresh();

    // Dashboard styling
    leave_employee_link_control.$wrapper.addClass("ess-dashboard-link");

    // Setup behavior (single / multiple employee logic)
    setup_leave_employee_behavior();
}


// function render_leave_employee_link_dropdown() {
//     const wrapper = document.getElementById("leave-employee-link-control");
//     const list = document.getElementById("ess-leave-balance-list");

//     if (!wrapper || !list) return;

//         wrapper.innerHTML = "";

//         leave_employee_link_control = frappe.ui.form.make_control({
//         parent: wrapper,
//         df: {
//             fieldtype: "Link",
//             fieldname: "employee",
//             label: "",              // ✅ remove label
//             options: "Employee",
//             placeholder: "Select Employee",
//             get_query() {
//                 return {
//                     query: "sowaan_hr.sowaan_hr.page.ess.ess.employee_leave_access_query"
//                 };
//             },
//             onchange() {
//                 const employee = leave_employee_link_control.get_value();
//                // 🔴 If cleared → reset UI
//                     if (!employee) {
//                         clear_leave_balance_ui();
//                         return;
//                     }

//                     // 🟢 Load balances
//                     load_leave_balance_for_employee(employee);
//                             }
//                         },
//         render_input: true
//     });


//     leave_employee_link_control.refresh();

//     // Dashboard styling
//     leave_employee_link_control.$wrapper.addClass("ess-dashboard-link");

//     // 🔑 Setup behavior (single / multiple employee logic)
//     setup_leave_employee_behavior();
// }


function clear_leave_balance_ui() {
    const list = document.getElementById("ess-leave-balance-list");
    if (!list) return;

    list.innerHTML = `
        <div class="ess-muted">
            Select an employee to view leave balance
        </div>
    `;
}

function setup_leave_employee_behavior() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_leave_balance_employees",
        callback: r => {
            const employees = r.message || [];
            //console.log("Leave employees:", employees);

            if (!employees.length) return;

            const employeeNames = employees.map(e => e.name);

            frappe.after_ajax(() => {
                setTimeout(() => {
                    const ctrl = leave_employee_link_control;
                    if (!ctrl) return;

                    /* 🔑 CORRECT WAY: restrict Link dropdown */
                    ctrl.get_query = () => {
                        return {
                            filters: {
                                name: ["in", employeeNames]
                            }
                        };
                    };

                    /* ==============================
                       CASE 1: SELF ONLY
                    ============================== */
                    if (employees.length === 1) {
                        const emp = employeeNames[0];

                        ctrl.set_value(emp);

                        // 🔒 lock control
                        ctrl.$input.prop("disabled", true);
                        ctrl.$wrapper.find(".clear").hide();

                        load_leave_balance_for_employee(emp);
                        return;
                    }

                    /* ==============================
                       CASE 2: SELF + SUBORDINATES
                    ============================== */

                    // 🔓 enable control
                    ctrl.$input.prop("disabled", false);
                    ctrl.$wrapper.find(".clear").show();

                    // 🔑 default select SELF (first item)
                    const selfEmp = employeeNames[0];
                    ctrl.set_value(selfEmp);

                    load_leave_balance_for_employee(selfEmp);

                }, 0);
            });
        }
    });
}




function load_leave_balance_for_employee(employee) {
    const list = document.getElementById("ess-leave-balance-list");
    if (!list || !employee) return;

    list.innerHTML = `<div class="ess-muted">Loading...</div>`;

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_leave_balance_for_employee",
        args: { employee },
        callback: r => {
            const data = r.message || [];
            list.innerHTML = "";

            if (!data.length) {
                list.innerHTML =
                    `<div class="ess-muted">No leave allocations found</div>`;
                return;
            }

            data.forEach(row => {
                list.insertAdjacentHTML("beforeend", `
                    <div class="ess-leave-row">
                        <span>${row.leave_type}</span>
                        <b>${row.balance}</b>
                    </div>
                `);
            });
        }
    });
}

function init_leave_balance_card() {
    render_leave_employee_link_dropdown();
    clear_leave_balance_ui(); // ✅ default empty state
}


function guard_ess_access_once() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.is_employee_user",
        callback: r => {
            if (!r.message) {
                // 🚫 Not an employee → redirect
                frappe.set_route("desk");
            }
        }
    });
}

function disable_link_control(ctrl) {
    if (!ctrl || !ctrl.$input) return;
    ctrl.$input.prop("disabled", true);
    ctrl.$input.addClass("disabled");
}

function enable_link_control(ctrl) {
    if (!ctrl || !ctrl.$input) return;
    ctrl.$input.prop("disabled", false);
    ctrl.$input.removeClass("disabled");
}

function lock_link_control(ctrl) {
    if (!ctrl || !ctrl.$input) return;

    // Disable input
    ctrl.$input.prop("disabled", true);
    ctrl.$input.addClass("disabled");

    // 🔥 Hide clear (×) button
    ctrl.$wrapper.find(".clear-link").hide();
}

function protect_leave_employee_value(ctrl, emp) {
    ctrl.$input.on("change.lock", () => {
        if (!ctrl.get_value()) {
            ctrl.set_value(emp);
        }
    });
}

function load_compliance_and_expiry() {
    const container = document.getElementById("ess-compliance-expiry");
    if (!container) return;

        /* ======================================================
        Compliance icon & color map
        ====================================================== */
        const COMPLIANCE_ICON_MAP = {
        "Pending Confirmations": {
            icon: "fa-user-clock",
            color: "#22c55e"
        },
        "Expiring Contracts (30 Days)": {
            icon: "fa-file-contract",
            color: "#f97316"
        },
        "Missing Leave Allocation": {
            icon: "fa-calendar-times",
            color: "#ef4444"
        },
        "Visa Expiry (30 Days)": {
            icon: "fa-id-card",
            color: "#3b82f6"
        },
        "Passport Expiry (30 Days)": {
            icon: "fa-passport",
            color: "#0ea5e9"
        },
        "Labor Card Expiry (30 Days)": {
            icon: "fa-id-badge",
            color: "#8b5cf6"
        }
    };


    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_compliance_summary",
        callback: r => {
            const data = r.message || [];
            //console.log("Compliance data:", data);

            container.innerHTML = "";

            /* ================= EMPTY STATE ================= */
            if (!Array.isArray(data) || !data.length) {
                container.innerHTML = `
                    <div class="ess-muted" style="padding:12px">
                        No compliance issues
                    </div>
                `;
                return;
            }

            /* ================= RENDER LIST ================= */
            data.forEach(item => {
            if (!item.count) return;

            const meta = COMPLIANCE_ICON_MAP[item.label] || {
                icon: "fa-exclamation-circle",
                color: "#64748b"
            };

            const row = document.createElement("div");
            row.className = "ess-compliance-row";

            row.innerHTML = `
                <div class="ess-compliance-left">
                    <div class="ess-compliance-icon"
                        style="background:${meta.color}">
                        <i class="fa ${meta.icon}"></i>
                    </div>
                    <div class="ess-compliance-label">
                        ${item.label}
                    </div>
                </div>
                <div class="ess-compliance-count">
                    ${item.count}
                </div>
            `;

            row.onclick = () => {
                if (!item.employees?.length) return;

                const params = new URLSearchParams();
                params.append(
                    "name",
                    JSON.stringify(["in", item.employees])
                );

                window.open(
                    `/app/employee?${params.toString()}`,
                    "_blank"
                );
            };

            container.appendChild(row);
        });

        }
    });
}

function load_login_employee_profile() {
    const box = document.getElementById("ess-login-profile");
    if (!box) return;

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_logged_in_employee_profile",
        callback: r => {
            //console.log(r.message)
            const emp = r.message;
            if (!emp) {
                box.innerHTML = `<div class="ess-muted">No profile found</div>`;
                return;
            }
            //console.log(emp.image);
            const img = emp.image
            ? encodeURI(frappe.urllib.get_full_url(emp.image))
            : "/files/default-profile.png";


            box.innerHTML = `
                <div class="ess-profile-avatar">
                    <img src="${img}">
                </div>
                <div class="ess-profile-info">
                    <div class="ess-profile-name">
                        ${emp.employee_name}
                    </div>
                    <div class="ess-profile-meta">
                        ${emp.designation || "—"} • ${emp.department || "—"}
                    </div>
                </div>
            `;

            box.onclick = () => {
                window.open(`/app/employee/${emp.name}`, "_blank");
            };
        }
    });
}

let selectedNetPayrollSummaryMonth = frappe.datetime.month_start().slice(0, 7);
let selectedNetPayrollSummaryBy = "department";

function make_net_payroll_summary_month_picker() {
    const field = frappe.ui.form.make_control({
        parent: document.getElementById("net-payroll-summary-month"),
        df: {
            fieldtype: "Date",
            label: "Month",
            onchange() {
                const v = field.get_value();
                if (!v) return;
                selectedNetPayrollSummaryMonth = v.slice(0, 7);
                load_net_payroll_summary();
            }
        },
        render_input: true
    });

    field.set_value(frappe.datetime.month_start());
}

function load_net_payroll_summary() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_net_payroll_breakdown",
        args: {
            month: selectedNetPayrollSummaryMonth,
            by: selectedNetPayrollSummaryBy
        },
        callback: r => {
            const box = document.getElementById(
                "net-payroll-summary-list"
            );
            if (!box) return;

            //console.log(r.message);
            const data = r.message;
            if (!data || !data.labels?.length) {
                box.innerHTML =
                    `<div class="ess-muted">No data</div>`;
                return;
            }

            box.innerHTML = data.labels.map((label, i) => `
                <div class="ess-netpay-summary-row">
                    <div class="ess-netpay-summary-label">
                        ${label}
                    </div>
                    <div class="ess-netpay-summary-value">
                        ${frappe.format(data.datasets[0].values[i], {
                            fieldtype: "Currency"
                        })}
                    </div>
                </div>
            `).join("");
        }
    });
}

/* Tab click handling */
document.addEventListener("click", e => {
    const btn = e.target.closest("[data-netpay-summary]");
    if (!btn) return;

    document
        .querySelectorAll("[data-netpay-summary]")
        .forEach(b => b.classList.remove("active"));

    btn.classList.add("active");

    selectedNetPayrollSummaryBy =
        btn.dataset.netpaySummary;

    load_net_payroll_summary();
});

function load_pending_requests_sent_by_me() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_pending_requests_sent_by_me",
        callback: r => {
            render_pending_request_list(
                r.message || {},
                "ess-pending-requests"
            );
        }
    });
}


function render_pending_request_list(data, containerId) {
    const box = document.getElementById(containerId);
    if (!box) return;

    box.innerHTML = "";

    if (!data || !Object.keys(data).length) {
        box.innerHTML = `
            <div class="ess-muted">No pending requests</div>
        `;
        return;
    }

    const ICON_MAP = {
        "Leave Application": {
            icon: "fa-calendar-check-o",
            color: "#22c55e"
        },
        "Expense Claim": {
            icon: "fa-money",
            color: "#3b82f6"
        },
        "Business Visit Visa Request": {
            icon: "fa-plane",
            color: "#8b5cf6"
        },
        "Loan Application": {
            icon: "fa-bank",
            color: "#f59e0b"
        }
    };

    Object.entries(data).forEach(([doctype, info]) => {
        const count = info?.count || 0;
        const names = info?.names || [];

        if (!count || !names.length) return;

        const meta = ICON_MAP[doctype] || {
            icon: "fa-file-text-o",
            color: "#64748b"
        };

        const row = document.createElement("div");
        row.className = "ess-pending-item";

        row.innerHTML = `
            <div class="ess-pending-left">
                <div class="ess-pending-icon"
                     style="background:${meta.color}">
                    <i class="fa ${meta.icon}"></i>
                </div>
                <div class="ess-pending-title">
                    ${doctype}
                </div>
            </div>
            <div class="ess-pending-count">
                ${count}
            </div>
        `;

        // ✅ Drill-down with SAME filter logic as approvals
        row.onclick = () => {

            if (!names || !names.length) {
                frappe.msgprint("This request no longer exists.");
                return;
            }
            const params = new URLSearchParams();
            params.append(
                "name",
                JSON.stringify(["in", names])
            );

            window.open(
                `/app/${frappe.router.slug(doctype)}?${params.toString()}`,
                "_blank"
            );
        };

        box.appendChild(row);
    });
}



function switch_pending_tab(tab) {
    if (tab === "sent_by_me") {
        console.log(tab);
        load_pending_requests_sent_by_me();
    } else if (tab === "pending_for_me") {
        load_pending_requests_for_me(); // ← your EXISTING function
    }
}

function init_pending_requests_tabs() {
    const tabs = document.querySelectorAll("#ess-pending-tabs .ess-tab");
    const container = document.getElementById("ess-pending-requests");

    function show_loader(key) {
        const text =
            key === "pending_for_me"
                ? "Loading …"
                : "Loading …";

        container.innerHTML = `<div class="ess-loading">${text}</div>`;
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", function () {

            // toggle active state
            tabs.forEach(t => t.classList.remove("active"));
            this.classList.add("active");

            const key = this.dataset.tab;

            // 🔹 show loading immediately
            show_loader(key);

            // 🔹 load async data
            if (key === "pending_for_me") {
                load_pending_requests_for_me();
            } else if (key === "sent_by_me") {
                load_pending_requests_sent_by_me();
            }
        });
    });

    // 🔑 default load (Approvals)
    show_loader("pending_for_me");
    load_pending_requests_for_me();
}


let selectedNetPayrollYear = new Date().getFullYear();
let selectedNetPayrollYearBy = "department";

function make_net_payroll_year_picker() {
    const field = frappe.ui.form.make_control({
        parent: document.getElementById("net-payroll-year-summary"),
        df: {
            fieldtype: "Int",
            label: "Year",
            onchange() {
                selectedNetPayrollYear = field.get_value();
                load_net_payroll_year_summary();
            }
        },
        render_input: true
    });

    field.set_value(selectedNetPayrollYear);
}


function init_yearly_payroll_years() {
    const select = document.getElementById("ess-yearly-payroll-year");
    if (!select) return;

    const currentYear = new Date().getFullYear();

    for (let y = currentYear; y >= currentYear - 5; y--) {
        const opt = document.createElement("option");
        opt.value = y;
        opt.textContent = y;
        select.appendChild(opt);
    }

    select.value = currentYear;

    select.addEventListener("change", () => {
        load_yearly_payroll_summary(select.value);
    });
}


function load_net_payroll_year_summary() {
    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_net_payroll_breakdown_by_year",
        args: {
            year: selectedNetPayrollYear,
            by: selectedNetPayrollYearBy
        },
        callback: r => {
            const box = document.getElementById(
                "net-payroll-year-summary-list"
            );
            if (!box) return;

            const data = r.message;
            if (!data || !data.labels?.length) {
                box.innerHTML = `<div class="ess-muted">No data</div>`;
                return;
            }

            box.innerHTML = data.labels.map((label, i) => `
                <div class="ess-netpay-summary-row">
                    <div class="ess-netpay-summary-label">
                        ${label}
                    </div>
                    <div class="ess-netpay-summary-value">
                        ${frappe.format(data.datasets[0].values[i], {
                            fieldtype: "Currency"
                        })}
                    </div>
                </div>
            `).join("");
        }
    });
}

document.addEventListener("click", e => {
    const btn = e.target.closest("[data-netpay-year]");
    if (!btn) return;

    document
        .querySelectorAll("[data-netpay-year]")
        .forEach(b => b.classList.remove("active"));

    btn.classList.add("active");

    selectedNetPayrollYearBy = btn.dataset.netpayYear;
    load_net_payroll_year_summary();
});

function init_net_payroll_year_dropdown() {
    const select = document.getElementById("net-payroll-year-select");
    if (!select) return;

    const currentYear = new Date().getFullYear();

    select.innerHTML = "";

    for (let i = 0; i < 10; i++) {
        const year = currentYear - i;
        const opt = document.createElement("option");
        opt.value = year;
        opt.textContent = year;
        select.appendChild(opt);
    }

    select.value = currentYear;

    select.addEventListener("change", () => {
        selectedNetPayrollYear = select.value;
        load_net_payroll_year_summary();
    });
}



function init_turnover_month_picker() {
    const wrapper = document.getElementById("turnover-month-picker");

    if (!wrapper) {
        setTimeout(init_turnover_month_picker, 100);
        return;
    }

    wrapper.innerHTML = "";

    turnover_month_control = frappe.ui.form.make_control({
        parent: wrapper,
        df: {
            fieldtype: "Date",
            fieldname: "turnover_month",
            label: "",
            onchange() {
                const val = turnover_month_control.get_value();
                if (!val) return;

                load_turnover_chart(current_turnover_by);
            }
        },
        render_input: true
    });

    turnover_month_control.refresh();

    const monthStart =
        frappe.datetime.month_start(frappe.datetime.get_today());

    turnover_month_control.set_value(monthStart);
}


function init_turnover_tabs() {
    const tabs = document.querySelectorAll(
        "#ess-turnover-tabs .ess-tab"
    );

    if (!tabs.length) {
        setTimeout(init_turnover_tabs, 100);
        return;
    }

    tabs.forEach(tab => {
        tab.addEventListener("click", function () {
            tabs.forEach(t => t.classList.remove("active"));
            this.classList.add("active");

            current_turnover_by = this.dataset.by;

            // 🔑 SAFE reload
            load_turnover_chart(current_turnover_by);
        });
    });
}


function load_turnover_chart(by) {

    if (!turnover_month_control) return;

    const month = turnover_month_control.get_value();
    if (!month) return;

    frappe.call({
        method: "sowaan_hr.sowaan_hr.page.ess.ess.get_turnover_breakdown",
        args: {
            month: month.slice(0, 7),
            by: by
        },
        callback: r => {

            const data = r.message;
            if (!data) return;

            const container =
                document.getElementById("ess-turnover-chart");
            if (!container) return;

            container.replaceChildren();

            /* ======================
               HARD DATA VALIDATION
            ====================== */

            const labels = data.labels || [];
            let joined = data.joined || [];
            let left = data.left || [];

            if (!labels.length) {
                container.innerHTML =
                    `<div class="ess-muted">No data</div>`;
                return;
            }

            // 🔑 FORCE NUMBERS + ALIGN LENGTHS
            joined = labels.map((_, i) => Number(joined[i] || 0));
            left   = labels.map((_, i) => Number(left[i] || 0));

            /* ======================
               SHORT LABELS
            ====================== */
            const shortLabels = labels.map(l =>
                l.length > 7 ? l.slice(0, 7) + "…" : l
            );

            /* ======================
               RENDER CHART
            ====================== */
            new frappe.Chart(container, {
                data: {
                    labels: shortLabels,
                    datasets: [
                        {
                            name: "Joined",
                            values: joined
                        },
                        {
                            name: "Left",
                            values: left
                        }
                    ]
                },
                type: "bar",
                height: 200,
                colors: ["#22c55e", "#ef4444"],
                barOptions: {
                    stacked: false,
                    spaceRatio: 0.4
                },
                axisOptions: {
                    xAxisMode: "tick",
                    yAxisMode: "tick",
                    xIsSeries: true
                },
                legendOptions: {
                    position: "bottom",
                    align: "center"
                },
                tooltipOptions: {
                    formatTooltipX: d =>
                        labels[shortLabels.indexOf(d)] || d,
                    formatTooltipY: d => `${d} Employees`
                }
            });
        }
    });
}



