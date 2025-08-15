from database.sqlqueries import exec_procedure_for
from database.sqldbdictionary import PATIENT_CBC_RESULT_SQL
from gui.views.report_component import ReportPatientInfo, ReportPatientResult
from log.logger import log_info, log_error
import flet as ft
import os
import subprocess


async def fetch_patient_cbc_result(patient_id=None):
    """
    Fetches patient data based on the provided filters.
    """
    try:
        params = {
            "PATIENT_ID": patient_id or None,
        }

        return await exec_procedure_for(PATIENT_CBC_RESULT_SQL, params) or []
    except Exception as e:
        log_error(f"Error fetching patient cbc result: {e}")
        return []


# Function to load SVG content
def load_svg_icon(file_path):
    """Loads the content of an SVG file."""
    try:
        # Ensure the path is absolute for robustness, or relative to the script's directory
        script_dir = os.path.dirname(
            __file__
        )  # Get the directory of the current script
        absolute_path = os.path.join(script_dir, file_path)
        with open(absolute_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        log_error(f"SVG icon file not found: {file_path}")
        return ""  # Return empty string if file not found
    except Exception as e:
        log_error(f"Error loading SVG icon {file_path}: {e}")
        return ""


async def cbc_report_view(page: ft.Page, patient_id):
    """
    CBC report view content.
    """

    result_data = await fetch_patient_cbc_result(patient_id)

    # Ensure result_data is not empty before proceeding
    if not result_data:
        page.snack_bar = ft.SnackBar(ft.Text("No result found for this patient ID."))
        page.snack_bar.open = True
        page.update()
        return

    result_data = result_data[0]  # Assuming we always take the first result

    def close_report_view(e):
        if report_view:  # Check if report_view is defined
            report_view.open = False
            page.update()  # Update the page to reflect changes

    async def save_report_as_html(e):
        try:
            # Log all keys in result_data for debugging
            log_info(f"CBC HTML export result_data keys: {list(result_data.keys())}")
            # Get patient name for filename, fallback to patient ID
            patient_name = result_data.get("Name")
            import datetime

            request_date_raw = (
                result_data.get("Requested Date")
                or result_data.get("Requested_Date")
                or "unknown"
            )
            # Remove time from date if present
            if isinstance(request_date_raw, str) and len(request_date_raw) > 10:
                request_date = request_date_raw[:10]
            elif hasattr(request_date_raw, "strftime"):
                request_date = request_date_raw.strftime("%d-%m-%Y")
            else:
                request_date = str(request_date_raw)
            log_info(
                f"Extracted patient name: {patient_name}, request date: {request_date}"
            )

            # Sanitize for filename
            def sanitize(val):
                return "".join(c if c.isalnum() else "_" for c in str(val))

            if patient_name:
                safe_name = sanitize(patient_name)
            else:
                safe_name = str(result_data.get("PATIENT_ID", "unknown"))
            safe_date = sanitize(request_date)
            log_info(f"Safe filename base: {safe_name}, date: {safe_date}")

            # --- CBC Table Logic ---
            from gui.views.cbc_normal_ranges import (
                NORMAL_RANGES,
                get_normal_range,
                determine_age_group,
                set_flag,
            )

            style_map = {
                "Hemoglobin (HGB)": dict(size=16, space=0, icon="❤️"),
                "Red Blood Cells (RBC)": dict(size=16, space=0, icon="🩸"),
                "Hematocrit (HCT)": dict(size=14, space=15, icon="🩸"),
                "Mean Corpuscular Volume (MCV)": dict(size=14, space=15, icon="🩸"),
                "Mean Corpuscular Hemoglobin (MCH)": dict(size=14, space=15, icon="🩸"),
                "Mean Corpuscular Hemoglobin Concentration (MCHC)": dict(
                    size=14, space=15, icon="🩸"
                ),
                "Red Cell Distribution Width (RDW)": dict(size=14, space=15, icon="🩸"),
                "Platelets (PLT)": dict(size=16, space=0, icon="🧫"),
                "Plateletcrit (PCT)": dict(size=14, space=15, icon="🧫"),
                "Mean Platelet Volume (MPV)": dict(size=14, space=15, icon="🧫"),
                "Platelet Distribution Width (PDW)": dict(size=14, space=15, icon="🧫"),
                "White Blood Cells (WBC)": dict(size=16, space=0, icon="🛡️"),
                "Neutrophils": dict(size=14, space=15, icon="🛡️"),
                "Lymphocytes": dict(size=14, space=15, icon="🛡️"),
                "Monocytes": dict(size=14, space=15, icon="🛡️"),
                "Eosinophils": dict(size=14, space=15, icon="🛡️"),
                "Basophils": dict(size=14, space=15, icon="🛡️"),
            }

            # Pre-load SVG content
            svg_content_map = {
                "❤️": load_svg_icon("icons/heart.svg"),
                "🩸": load_svg_icon("icons/blood.svg"),
                "🧫": load_svg_icon("icons/petri.svg"),
                "🛡️": load_svg_icon("icons/shield.svg"),
            }

            color_map = {
                "YELLOW_700": "#fbc02d",
                "RED_700": "#d32f2f",
                "GREEN_700": "#388e3c",
                "GREY_600": "#757575",
            }
            skip = {"Patient ID", "Name", "Age", "Age Unit", "Gender", "Requested Date"}
            age = int(result_data.get("Age", 0))
            age_unit = result_data.get("Age Unit", "years")
            gender = result_data.get("Gender", "male")
            age_group = determine_age_group(age, age_unit)

            # --- Build CBC Table Rows ---
            table_rows = ""
            for test_name, test_value in result_data.items():
                if test_name in skip or test_value in (None, ""):
                    continue
                s = style_map.get(test_name, dict(size=14, space=0, icon=""))
                normal_range = get_normal_range(test_name, age_group, gender)
                unit = NORMAL_RANGES.get(test_name, {}).get("unit", "")
                range_txt = (
                    f"{normal_range[0]} - {normal_range[1]}"
                    if normal_range and isinstance(normal_range, tuple)
                    else "N/A"
                )
                flag, flag_color = set_flag(test_value, normal_range)
                # Map Flet color to hex
                if flag_color == ft.Colors.YELLOW_700:
                    flag_color_hex = color_map["YELLOW_700"]
                elif flag_color == ft.Colors.RED_700:
                    flag_color_hex = color_map["RED_700"]
                elif flag_color == ft.Colors.GREEN_700:
                    flag_color_hex = color_map["GREEN_700"]
                else:
                    flag_color_hex = "#222"

                # Use inline SVG if available, otherwise fallback to emoji
                icon_html = svg_content_map.get(s["icon"])
                if icon_html:
                    icon_html = icon_html.replace(
                        "<svg",
                        '<svg width="18" height="18" style="vertical-align:middle;margin-right:4px;"',
                    )
                else:
                    icon_html = s["icon"]

                # Inline visualization: mini bar for value vs normal range
                def render_inline_bar(value, normal_range):
                    try:
                        v = float(value)
                        if (
                            normal_range
                            and isinstance(normal_range, tuple)
                            and all(isinstance(x, (int, float)) for x in normal_range)
                        ):
                            min_v, max_v = normal_range
                            if min_v == max_v:
                                return ""  # Avoid division by zero
                            percent = (v - min_v) / (max_v - min_v)
                            percent = max(0, min(1, percent))
                            color = (
                                "#388e3c"
                                if min_v <= v <= max_v
                                else (
                                    "#d32f2f" if v < min_v or v > max_v else "#fbc02d"
                                )
                            )
                            return f"""<div style="position:relative;width:90px;height:12px;background:#eee;border-radius:6px;display:inline-block;margin-left:8px;vertical-align:middle;">
                                <div style="position:absolute;left:0;top:0;height:100%;width:100%;background:linear-gradient(90deg,#e0e0e0 0%,#fafafa 100%);border-radius:6px;"></div>
                                <div style="position:absolute;left:0;top:0;height:100%;width:{percent*100:.1f}%;background:{color};border-radius:6px;"></div>
                                <div style="position:absolute;left:{percent*100:.1f}%;top:0;width:2px;height:100%;background:#222;"></div>
                            </div>"""
                        else:
                            return ""
                    except Exception:
                        return ""

                def render_inline_bar_only(value, normal_range):
                    try:
                        v = float(value)
                        if (
                            normal_range
                            and isinstance(normal_range, tuple)
                            and all(isinstance(x, (int, float)) for x in normal_range)
                        ):
                            min_v, max_v = normal_range
                            # Bar span covers min_v/max_v and outlier value, with margin
                            span = max_v - min_v if max_v != min_v else 1.0
                            margin = span * 0.15 or 1.0
                            # ALWAYS symmetric yellow/red (buffer) for best visualization
                            if v < min_v:
                                buf = max((min_v - v), 0) + margin
                                min_bar = min_v - buf
                                max_bar = max_v + buf
                            elif v > max_v:
                                buf = max((v - max_v), 0) + margin
                                min_bar = min_v - buf
                                max_bar = max_v + buf
                            else:
                                min_bar = min_v - margin
                                max_bar = max_v + margin
                            if min_bar == max_bar:
                                max_bar = min_bar + 1.0
                            # Ensure value is never at the left/right edge
                            total_span = max_bar - min_bar
                            pad = total_span * 0.075  # 7.5% of bar on each side
                            min_bar -= pad
                            max_bar += pad
                            percent = (v - min_bar) / (max_bar - min_bar)
                            percent = max(0, min(1, percent))
                            # Locations for regions
                            yellow_perc = (min_v - min_bar) / (max_bar - min_bar)
                            green_perc = (max_v - min_bar) / (max_bar - min_bar)
                            # Clamp percents
                            yellow_perc = max(0, min(1, yellow_perc))
                            green_perc = max(0, min(1, green_perc))
                            # HTML bar sections
                            bar_html = f"""
                            <div style='position:relative;width:90px;height:14px;background:#eee;border-radius:2px;border:1.5px solid #222;display:inline-block;vertical-align:middle;'>
                                <div style='position:absolute;left:0;top:0;height:100%;width:{yellow_perc*100:.1f}%;background:#fbc02d;'></div>
                                <div style='position:absolute;left:{yellow_perc*100:.1f}%;top:0;height:100%;width:{(green_perc-yellow_perc)*100:.1f}%;background:#388e3c;'></div>
                                <div style='position:absolute;left:{green_perc*100:.1f}%;top:0;height:100%;width:{(1-green_perc)*100:.1f}%;background:#d32f2f;'></div>
                                <div style='position:absolute;left:calc({percent*100:.1f}% - 5px);top:0;width:0;height:0;border-left:5.25px solid transparent;border-right:5.25px solid transparent;border-top:6px solid #222;z-index:3;'></div>
                            </div>
                            """
                            return bar_html
                        else:
                            return ""
                    except Exception:
                        return ""

                # Color the value in the Result column based on status
                def get_value_color(value, normal_range):
                    try:
                        v = float(value)
                        if (
                            normal_range
                            and isinstance(normal_range, tuple)
                            and all(isinstance(x, (int, float)) for x in normal_range)
                        ):
                            min_v, max_v = normal_range
                            if min_v == max_v:
                                return "#222"
                            if v < min_v:
                                return "#fbc02d"  # yellow for low
                            if min_v <= v <= max_v:
                                return "#388e3c"  # green for normal
                            if v > max_v:
                                return "#d32f2f"  # red for high
                            return "#222"
                        else:
                            return "#222"
                    except Exception:
                        return "#222"

                inline_bar = render_inline_bar_only(test_value, normal_range)
                value_color = get_value_color(test_value, normal_range)
                table_rows += f"""
                <tr>
                    <td style="padding-left:{s['space']}px;font-size:{s['size']}px;">{icon_html} {test_name}</td>
                    <td style="font-size:{s['size']}px;color:{value_color};font-weight:bold;">{test_value}</td>
                    <td style="font-size:{s['size']}px;">{inline_bar}</td>
                    <td style="font-size:{s['size']}px;">{range_txt} <span style="color:{color_map['GREY_600']};">{unit}</span></td>
                </tr>
                """

            html_filename = f"Report_{safe_name}_{safe_date}.html"
            html_path = os.path.join(os.getcwd(), html_filename)

            import datetime

            # Robust extraction for patient info fields
            def get_field(keys, default="N/A"):
                for k in keys:
                    v = result_data.get(k)
                    if v:
                        return v
                return default

            patient_id = get_field(["PATIENT_ID", "Patient ID", "ID", "patient_id"])
            patient_name_disp = get_field(
                ["PATIENT_NAME", "Name", "NAME", "PatientName", "patient_name"]
            )
            age = get_field(["Age", "AGE", "age"])
            age_unit = get_field(["Age Unit", "AGE_UNIT", "age_unit"], "years")
            gender = get_field(["Gender", "GENDER", "gender"])
            requested_date = get_field(
                ["Requested Date", "Requested_Date", "requested_date"]
            )
            report_date = datetime.date.today().strftime("%d-%m-%Y")

            html_content = f"""
            <!DOCTYPE html>
            <html lang=\"en\">
            <head>
                <meta charset=\"UTF-8\">
                <title>{patient_name_disp}</title>
                <style>
                    @page {{ size: A4; margin: 20mm; }}
                    html, body {{
                        height: 100%;
                        margin: 0;
                        padding: 0;
                        background: #f4f6fa;
                    }}
                    body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #222; }}
                    .container {{
                        width: 210mm;
                        min-height: 297mm;
                        margin: 0 auto;
                        padding: 0;
                        border-radius: 16px;
                        background: #fff;
                        /* box-shadow: 0 4px 24px rgba(0,0,0,0.10); */
                        box-sizing: border-box;
                        display: flex;
                        flex-direction: column;
                        justify-content: flex-start;
                        overflow: visible;
                        page-break-after: always;
                    }}
                    .header-bar {{
                        background: linear-gradient(90deg, #b71c1c 60%, #1976d2 100%);
                        height: 32px;
                        width: 100%;
                    }}
                    .header-content {{
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 24px 32px 8px 32px;
                    }}
                    .logo {{
                        width: 48px;
                        height: 48px;
                        background: #eee;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 28px;
                        color: #b71c1c;
                        font-weight: bold;
                        margin-right: 16px;
                    }}
                    .report-title {{
                        font-size: 2.1rem;
                        font-weight: 700;
                        color: #b71c1c;
                        letter-spacing: 1px;
                        margin: 0;
                    }}
                    .info-row {{
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        margin: 0 32px 18px 32px;
                        padding-bottom: 12px;
                        border-bottom: 1.5px solid #e0e0e0;
                    }}
                    .info-left, .info-group-right {{
                        display: flex;
                        flex-direction: column;
                        gap: 4px;
                    }}
                    .info-group-right {{
                        min-width: 180px;
                        align-items: flex-start;
                    }}
                    .label {{
                        font-weight: 600;
                        color: #1976d2;
                        font-size: 1rem;
                    }}
                    .value {{
                        margin-left: 8px;
                        font-weight: 400;
                        color: #333;
                    }}
                    .cbc-section-title {{
                        font-size: 1.15rem;
                        font-weight: 600;
                        color: #333;
                        margin: 24px 32px 8px 32px;
                        border-left: 4px solid #b71c1c;
                        padding-left: 10px;
                        letter-spacing: 0.5px;
                    }}
                                        table.cbc-table {{
                        width: calc(100% - 64px);
                        margin: 0 32px 0 32px;
                        border-collapse: collapse;
                        background: #fafbfc;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                    }}
                    table.cbc-table th, table.cbc-table td {{
                        border: none;
                        padding: 10px 8px;
                        text-align: left;
                        font-size: 1rem;
                    }}
                    table.cbc-table th {{
                        background: #e3eaf4;
                        color: #b71c1c;
                        font-weight: 700;
                        position: sticky;
                        top: 0;
                        z-index: 2;
                        border-bottom: 2px solid #b71c1c;
                    }}
                    table.cbc-table tr:nth-child(even) td {{
                        background: #f6f8fa;
                    }}
                    table.cbc-table tr:hover td {{
                        background: #f1f1f1;
                    }}
                    svg {{ vertical-align: middle; margin-right: 4px; }}
                </style>
            </head>
            <body>
                                <div class=\"container\">
                    <div class=\"header-bar\"></div>
                    <div class=\"header-content\">
                        <div class=\"logo\">🩺</div>
                        <div class=\"report-title\">YourLab</div>
                        <div style=\"width:48px;\"></div>
                    </div>
                    <div class=\"info-row\">
                        <div class=\"info-left\">
                            <span><span class=\"label\">Name:</span><span class=\"value\">{patient_name_disp}</span></span>
                            <span><span class=\"label\">Age:</span><span class=\"value\">{age} {age_unit}</span></span>
                            <span><span class=\"label\">Sex:</span><span class=\"value\">{gender}</span></span>
                        </div>
                        <div class=\"info-group-right\">
                            <span><span class=\"label\">Patient ID:</span><span class=\"value\">{patient_id}</span></span>
                            <span><span class=\"label\">Requested Date:</span><span class=\"value\">{request_date}</span></span>
                            <span><span class=\"label\">Report Date:</span><span class=\"value\">{report_date}</span></span>
                        </div>
                    </div>
                    <table class=\"cbc-table\">
                        <tr>
                            <th>Investigation</th>
                            <th>Result</th>
                            <th>Flag</th>
                            <th>Reference</th>
                        </tr>
                        {table_rows}
                    </table>
                </div>
                                                    </body>
            </html>
            """
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            log_info(f"HTML report written to: {html_path}")

            page.snack_bar = ft.SnackBar(ft.Text(f"HTML saved: {html_path}"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            log_error(f"Failed to save HTML: {ex}")
            import traceback

            log_error(traceback.format_exc())
            page.snack_bar = ft.SnackBar(ft.Text(f"Failed to save HTML: {ex}"))
            page.snack_bar.open = True
            page.update()

    # Define report_view outside the if block to ensure it's always defined
    # or handle the case where result_data is empty
    report_view = ft.AlertDialog(
        modal=True,
        scrollable=True,
        title=ft.Text("Hematology Report"),
        content=ft.Column([ReportPatientInfo(result_data), ReportPatientResult(result_data)]),  # type: ignore
        actions=[
            ft.ElevatedButton("Save as HTML", on_click=save_report_as_html),
            ft.ElevatedButton("Close", on_click=close_report_view),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    if result_data:
        page.overlay.append(report_view)
        report_view.open = True
    else:
        # If no result data, show a different dialog or message
        no_result_dialog = ft.AlertDialog(
            title=ft.Text("No Result Found"),
            actions=[
                ft.ElevatedButton("Close", on_click=close_report_view),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(no_result_dialog)
        no_result_dialog.open = True

    page.update()
