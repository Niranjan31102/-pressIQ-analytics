from pathlib import Path
import re

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

PRODUCT_MASTER_PATH = ROOT / "backend_data" / "product_master.xlsx"

PREDICTION_MASTER_PATH = (
    ROOT
    / "backend_data"
    / "PressIQ_Prediction_Master_v1.xlsx"
)


# ============================================================
# BASIC HELPERS
# ============================================================

def norm(value):
    if pd.isna(value):
        return ""

    return re.sub(
        r"\s+",
        " ",
        str(value).strip(),
    ).upper()


def col(df, *names):
    column_map = {
        norm(column_name): column_name
        for column_name in df.columns
    }

    for name in names:
        normalized_name = norm(name)

        if normalized_name in column_map:
            return column_map[normalized_name]

    return None


def num(value, default=0.0):
    number = pd.to_numeric(
        value,
        errors="coerce",
    )

    if pd.isna(number):
        return default

    return float(number)


def normalize_yes_no(value):
    value = norm(value)

    if value in {
        "YES",
        "Y",
        "1",
        "TRUE",
        "UV",
    }:
        return "YES"

    return "NO"


# ============================================================
# PRODUCT MASTER
# ============================================================

def load_product_master():

    if not PRODUCT_MASTER_PATH.exists():
        raise FileNotFoundError(
            f"Product Master not found: {PRODUCT_MASTER_PATH}"
        )

    df = pd.read_excel(
        PRODUCT_MASTER_PATH,
        sheet_name="Product_Master",
    )

    required_columns = [
        "Priority",
        "Match Text",
        "Display Code",
        "Report Type",
        "Status",
    ]

    missing_columns = [
        column_name
        for column_name in required_columns
        if column_name not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Product Master missing columns: "
            + ", ".join(missing_columns)
        )

    df = df.dropna(
        subset=[
            "Match Text",
            "Display Code",
        ]
    ).copy()

    df["Priority"] = pd.to_numeric(
        df["Priority"],
        errors="coerce",
    ).fillna(9999)

    df["_match"] = df["Match Text"].map(norm)
    df["_type"] = df["Report Type"].map(norm)
    df["_status"] = df["Status"].map(norm)

    df = df[
        df["_status"].isin(
            [
                "ACTIVE",
                "YES",
                "Y",
                "TRUE",
                "1",
            ]
        )
    ]

    return (
        df
        .sort_values("Priority")
        .reset_index(drop=True)
    )


def match_product(
    product,
    edition,
    report_type,
    master,
):

    combined_text = norm(
        f"{product} {edition}"
    )

    rules = master[
        master["_type"]
        == norm(report_type)
    ]

    for _, rule in rules.iterrows():

        match_text = rule["_match"]

        if (
            match_text
            and match_text in combined_text
        ):

            display_code = str(
                rule["Display Code"]
            ).strip()

            return (
                display_code,
                "Auto Matched",
                str(
                    rule["Match Text"]
                ).strip(),
            )

    if not pd.isna(product):
        fallback = str(product).strip()

    elif not pd.isna(edition):
        fallback = str(edition).strip()

    else:
        fallback = ""

    return (
        fallback or "Unnamed Product",
        "Review Required",
        "Not Found in Product Master",
    )


# ============================================================
# PREDICTION MASTER
# ============================================================

def load_prediction_rules():
    """
    Read the exact structure of:

    PressIQ_Prediction_Master_v1.xlsx

    IMPORTANT:
    Row 1 = workbook title
    Row 2 = blank
    Row 3 = actual Excel table headers

    Therefore header=2 is intentional.
    """

    if not PREDICTION_MASTER_PATH.exists():

        raise FileNotFoundError(
            "Prediction Master not found: "
            f"{PREDICTION_MASTER_PATH}"
        )

    excel_file = pd.ExcelFile(
        PREDICTION_MASTER_PATH
    )

    required_sheets = {
        "Base Prediction Rules",
        "Additional Waste Rules",
    }

    missing_sheets = (
        required_sheets
        - set(excel_file.sheet_names)
    )

    if missing_sheets:

        raise ValueError(
            "Prediction Master missing sheet(s): "
            + ", ".join(
                sorted(missing_sheets)
            )
        )

    # --------------------------------------------------------
    # Actual headings begin on Excel row 3.
    # pandas header index is zero-based -> header=2
    # --------------------------------------------------------

    base = pd.read_excel(
        PREDICTION_MASTER_PATH,
        sheet_name="Base Prediction Rules",
        header=2,
    )

    additional = pd.read_excel(
        PREDICTION_MASTER_PATH,
        sheet_name="Additional Waste Rules",
        header=2,
    )

    # Remove completely blank rows
    base = base.dropna(
        how="all"
    ).copy()

    additional = additional.dropna(
        how="all"
    ).copy()

    # Remove completely blank columns
    base = base.dropna(
        axis=1,
        how="all",
    )

    additional = additional.dropna(
        axis=1,
        how="all",
    )

    # --------------------------------------------------------
    # Validate Base Prediction Rules
    # --------------------------------------------------------

    base_required = [
        "Production Type",
        "Pages From",
        "Pages To",
        "UV (Yes/No)",
        "Machine Family",
        "Base Prediction (Copies)",
    ]

    base_missing = [
        column_name
        for column_name in base_required
        if column_name not in base.columns
    ]

    if base_missing:

        raise ValueError(
            "Base Prediction Rules missing columns: "
            + ", ".join(base_missing)
        )

    # --------------------------------------------------------
    # Validate Additional Waste Rules
    # --------------------------------------------------------

    additional_required = [
        "Rule Type",
        "Parameter",
        "UV (Yes/No)",
        "Waste Addition (Copies)",
        "Status",
    ]

    additional_missing = [
        column_name
        for column_name in additional_required
        if column_name not in additional.columns
    ]

    if additional_missing:

        raise ValueError(
            "Additional Waste Rules missing columns: "
            + ", ".join(
                additional_missing
            )
        )

    # --------------------------------------------------------
    # Clean Base Prediction Rules
    # --------------------------------------------------------

    base["Pages From"] = pd.to_numeric(
        base["Pages From"],
        errors="coerce",
    )

    base["Pages To"] = pd.to_numeric(
        base["Pages To"],
        errors="coerce",
    )

    base[
        "Base Prediction (Copies)"
    ] = pd.to_numeric(
        base[
            "Base Prediction (Copies)"
        ],
        errors="coerce",
    )

    base = base.dropna(
        subset=[
            "Production Type",
            "Pages From",
            "Pages To",
            "Machine Family",
            "Base Prediction (Copies)",
        ]
    ).copy()

    # --------------------------------------------------------
    # Clean Additional Waste Rules
    # --------------------------------------------------------

    additional[
        "Waste Addition (Copies)"
    ] = pd.to_numeric(
        additional[
            "Waste Addition (Copies)"
        ],
        errors="coerce",
    )

    additional["_status"] = (
        additional["Status"]
        .map(norm)
    )

    additional = additional[
        additional["_status"].isin(
            [
                "ACTIVE",
                "YES",
                "Y",
                "TRUE",
                "1",
            ]
        )
    ].copy()

    additional = additional.dropna(
        subset=[
            "Rule Type",
            "Parameter",
            "Waste Addition (Copies)",
        ]
    )

    # --------------------------------------------------------
    # Separate Book and Innovation Rules
    # --------------------------------------------------------

    rule_type_normalized = (
        additional["Rule Type"]
        .map(norm)
    )

    book = additional[
        rule_type_normalized
        == "BOOK"
    ].copy()

    innovation = additional[
        rule_type_normalized
        == "INNOVATION"
    ].copy()

    return {
        "base": base.reset_index(
            drop=True
        ),
        "book": book.reset_index(
            drop=True
        ),
        "innovation": innovation.reset_index(
            drop=True
        ),
    }


# ============================================================
# BASE PREDICTION
# ============================================================

def _base_prediction(
    rules,
    machine,
    pages,
    uv,
    production_type,
):

    df = rules["base"].copy()

    machine_column = (
        "Machine Family"
    )

    pages_from_column = (
        "Pages From"
    )

    pages_to_column = (
        "Pages To"
    )

    uv_column = (
        "UV (Yes/No)"
    )

    production_type_column = (
        "Production Type"
    )

    waste_column = (
        "Base Prediction (Copies)"
    )

    # --------------------------------------------------------
    # Machine
    # --------------------------------------------------------

    df = df[
        df[
            machine_column
        ].map(norm)
        == norm(machine)
    ].copy()

    # --------------------------------------------------------
    # Production Type
    #
    # >
    # >||>
    # >>
    # --------------------------------------------------------

    production_type_clean = (
        str(
            production_type
        ).strip()
    )

    if production_type_clean:

        df = df[
            df[
                production_type_column
            ].astype(str).str.strip()
            == production_type_clean
        ].copy()

    # --------------------------------------------------------
    # UV
    # --------------------------------------------------------

    wanted_uv = (
        normalize_yes_no(uv)
    )

    df = df[
        df[
            uv_column
        ].map(
            normalize_yes_no
        )
        == wanted_uv
    ].copy()

    # --------------------------------------------------------
    # Page Range
    # --------------------------------------------------------

    pages_numeric = num(
        pages,
        0,
    )

    hit = df[
        (
            df[
                pages_from_column
            ]
            <= pages_numeric
        )
        &
        (
            df[
                pages_to_column
            ]
            >= pages_numeric
        )
    ]

    if hit.empty:
        return None

    prediction = num(
        hit.iloc[0][
            waste_column
        ],
        default=0,
    )

    return int(
        round(prediction)
    )


# ============================================================
# BOOK ADDITION
# ============================================================

def _book_addition(
    rules,
    book_count,
    uv,
):

    df = rules.get(
        "book",
        pd.DataFrame(),
    )

    if (
        df.empty
        or book_count <= 1
    ):
        return 0

    wanted_uv = (
        normalize_yes_no(uv)
    )

    query = df[
        pd.to_numeric(
            df["Parameter"],
            errors="coerce",
        )
        == int(book_count)
    ].copy()

    if query.empty:
        return 0

    query = query[
        query[
            "UV (Yes/No)"
        ].map(
            normalize_yes_no
        )
        == wanted_uv
    ]

    if query.empty:
        return 0

    addition = num(
        query.iloc[0][
            "Waste Addition (Copies)"
        ],
        default=0,
    )

    return int(
        round(addition)
    )


# ============================================================
# INNOVATION ADDITION
# ============================================================

def _innovation_addition(
    rules,
    innovations,
    uv,
):

    df = rules.get(
        "innovation",
        pd.DataFrame(),
    )

    if (
        df.empty
        or not innovations
    ):
        return 0

    wanted_uv = (
        normalize_yes_no(uv)
    )

    total = 0

    # Important:
    # Same innovation must not be counted twice
    unique_innovations = sorted(
        {
            norm(value)
            for value in innovations
            if norm(value)
        }
    )

    for innovation_name in (
        unique_innovations
    ):

        query = df[
            df[
                "Parameter"
            ].map(norm)
            == innovation_name
        ].copy()

        if query.empty:
            continue

        query = query[
            query[
                "UV (Yes/No)"
            ].map(
                normalize_yes_no
            )
            == wanted_uv
        ]

        if query.empty:
            continue

        addition = num(
            query.iloc[0][
                "Waste Addition (Copies)"
            ],
            default=0,
        )

        total += int(
            round(addition)
        )

    return total


# ============================================================
# PHYSICAL BOOK COUNT
# ============================================================

def _book_map(book_df):

    if book_df.empty:
        return {}

    run_id_column = col(
        book_df,
        "RunID",
        "Run ID",
        "Run Id",
    )

    type_column = col(
        book_df,
        "Integrated/Pullout",
        "Integrated / Pullout",
        "Book Type",
        "Type",
    )

    if (
        run_id_column is None
        or type_column is None
    ):
        return {}

    result = {}

    for run_id, group in (
        book_df.groupby(
            run_id_column
        )
    ):

        book_types = (
            group[
                type_column
            ].map(norm)
        )

        # Business Rule:
        #
        # Main = 1 physical book
        # Integrated = does NOT increase count
        # Pullout = +1 physical book

        pullout_count = int(
            book_types
            .str.contains(
                "PULLOUT",
                na=False,
            )
            .sum()
        )

        physical_book_count = (
            1
            + pullout_count
        )

        result[
            norm(run_id)
        ] = physical_book_count

    return result


# ============================================================
# INNOVATION MAP
# ============================================================

def _innovation_map(
    innovation_df,
):

    if innovation_df.empty:
        return {}

    run_id_column = col(
        innovation_df,
        "RunID",
        "Run ID",
        "Run Id",
    )

    innovation_column = col(
        innovation_df,
        "Specific Innovation",
        "Innovation",
        "Innovation Name",
    )

    if (
        run_id_column is None
        or innovation_column is None
    ):
        return {}

    result = {}

    for run_id, group in (
        innovation_df.groupby(
            run_id_column
        )
    ):

        # Deduplicate repeated innovation entries
        innovations = sorted(
            {
                str(value).strip()
                for value in group[
                    innovation_column
                ].dropna()
                if str(value).strip()
            }
        )

        result[
            norm(run_id)
        ] = innovations

    return result


# ============================================================
# PRODUCTION REPORT PROCESSING
# ============================================================

def process_report(
    uploaded_file,
):

    uploaded_file.seek(0)

    sheets = pd.read_excel(
        uploaded_file,
        sheet_name=None,
    )

    # --------------------------------------------------------
    # Required General sheet
    # --------------------------------------------------------

    general = sheets.get(
        "General"
    )

    if general is None:

        raise ValueError(
            "Production Report must contain General sheet."
        )

    # --------------------------------------------------------
    # Optional supporting sheets
    # --------------------------------------------------------

    book = sheets.get(
        "Book Wise Details",
        pd.DataFrame(),
    )

    innovation = sheets.get(
        "Innovation",
        sheets.get(
            "Innovations",
            pd.DataFrame(),
        ),
    )

    # --------------------------------------------------------
    # General Sheet Columns
    # --------------------------------------------------------

    c_date = col(
        general,
        "Issue Date",
        "Edition Date",
    )

    c_product = col(
        general,
        "Products",
        "Product Name",
        "Product",
    )

    c_edition = col(
        general,
        "Edition",
        "Edition Name",
    )

    c_type = col(
        general,
        "Main/Supplement",
        "Main / Supplement",
        "Main Supplement",
    )

    c_machine = col(
        general,
        "Machine",
        "Machine Name",
    )

    c_po = col(
        general,
        "Print Order",
        "PO",
        "PrintOrder",
    )

    c_waste = col(
        general,
        "Waste",
        "Actual Waste",
        "Total Waste",
    )

    c_incharge = col(
        general,
        "Machine In-Charge",
        "Machine Incharge",
        "Machine In-charge",
    )

    c_pages = col(
        general,
        "Sum of Pages",
        "Pages",
        "Total Pages",
    )

    c_uv = col(
        general,
        "UV",
        "UV Yes/No",
        "UV Yes No",
    )

    c_run = col(
        general,
        "RunID",
        "Run ID",
        "Run Id",
    )

    c_folder = col(
        general,
        "Folder",
        "Press",
        "Folder/Press",
    )

    # Production Type contains:
    # >
    # >||>
    # >>

    c_production_type = col(
        general,
        "Production Type",
    )

    required = {
        "Issue Date": c_date,
        "Products": c_product,
        "Edition": c_edition,
        "Main/Supplement": c_type,
        "Machine": c_machine,
        "PO": c_po,
        "Waste": c_waste,
        "Sum of Pages": c_pages,
        "Production Type": c_production_type,
    }

    missing = [
        name
        for name, value
        in required.items()
        if value is None
    ]

    if missing:

        raise ValueError(
            "General sheet missing: "
            + ", ".join(missing)
        )

    # --------------------------------------------------------
    # Load backend masters
    # --------------------------------------------------------

    product_master = (
        load_product_master()
    )

    prediction_rules = (
        load_prediction_rules()
    )

    physical_books = (
        _book_map(book)
    )

    innovations_by_run = (
        _innovation_map(
            innovation
        )
    )

    output_rows = []

    # ========================================================
    # PROCESS EACH PRODUCTION RUN
    # ========================================================

    for index, row in (
        general.iterrows()
    ):

        product = row.get(
            c_product,
            "",
        )

        edition = row.get(
            c_edition,
            "",
        )

        combined_text = norm(
            f"{product} {edition}"
        )

        # ----------------------------------------------------
        # TRIAL exclusion
        # ----------------------------------------------------

        if "TRIAL" in combined_text:
            continue

        # ----------------------------------------------------
        # MAIN / SUPPLEMENT
        # ----------------------------------------------------

        report_type = norm(
            row.get(
                c_type,
                "",
            )
        )

        if report_type not in {
            "MAIN",
            "SUPPLEMENT",
        }:
            continue

        # ----------------------------------------------------
        # MACHINE
        # ----------------------------------------------------

        machine = str(
            row.get(
                c_machine,
                "",
            )
        ).strip()

        # ----------------------------------------------------
        # PAGES
        # ----------------------------------------------------

        pages = int(
            round(
                num(
                    row.get(
                        c_pages
                    ),
                    0,
                )
            )
        )

        # ----------------------------------------------------
        # UV
        # ----------------------------------------------------

        if c_uv:

            uv = row.get(
                c_uv,
                "NO",
            )

        else:

            uv = "NO"

        # ----------------------------------------------------
        # RUN ID
        # ----------------------------------------------------

        if c_run:

            run_id = norm(
                row.get(
                    c_run,
                    "",
                )
            )

        else:

            run_id = str(
                index
            )

        # ----------------------------------------------------
        # FOLDER / PRESS
        # ----------------------------------------------------

        if c_folder:

            folder = str(
                row.get(
                    c_folder,
                    "",
                )
            ).strip()

        else:

            folder = ""

        # ----------------------------------------------------
        # PRODUCTION TYPE SYMBOL
        # ----------------------------------------------------

        production_type = str(
            row.get(
                c_production_type,
                "",
            )
        ).strip()

        # ----------------------------------------------------
        # PRESS-4 DISPLAY RULE
        # ----------------------------------------------------

        normalized_folder = (
            norm(folder)
            .replace(
                " ",
                "",
            )
        )

        if (
            normalized_folder
            in {
                "PRESS4",
                "PRESS-4",
            }
            and norm(machine)
            == "COLORMAN-B"
        ):

            display_machine = (
                "Press-4 / Colorman-B"
            )

        else:

            display_machine = (
                machine
            )

        # ----------------------------------------------------
        # PRODUCT MATCHING
        # ----------------------------------------------------

        (
            publication_code,
            match_status,
            matched_text,
        ) = match_product(
            product,
            edition,
            report_type.title(),
            product_master,
        )

        # ----------------------------------------------------
        # PHYSICAL BOOKS
        # ----------------------------------------------------

        book_count = (
            physical_books.get(
                run_id,
                1,
            )
        )

        # ----------------------------------------------------
        # INNOVATIONS
        # ----------------------------------------------------

        innovations = (
            innovations_by_run.get(
                run_id,
                [],
            )
        )

        # ----------------------------------------------------
        # BASE PREDICTION
        # ----------------------------------------------------

        base_prediction = (
            _base_prediction(
                prediction_rules,
                machine,
                pages,
                uv,
                production_type,
            )
        )

        # ----------------------------------------------------
        # MANUAL PAGE EXCEPTION
        #
        # Examples:
        # 9, 17, 25, 33
        #
        # or any other page count not covered
        # by Prediction Master.
        # ----------------------------------------------------

        manual_prediction_required = (
            base_prediction is None
        )

        if manual_prediction_required:

            predicted_waste = None

            book_addition = 0

            innovation_addition = 0

        else:

            book_addition = (
                _book_addition(
                    prediction_rules,
                    book_count,
                    uv,
                )
            )

            innovation_addition = (
                _innovation_addition(
                    prediction_rules,
                    innovations,
                    uv,
                )
            )

            predicted_waste = (
                base_prediction
                + book_addition
                + innovation_addition
            )

        # ----------------------------------------------------
        # PO / ACTUAL WASTE
        # ----------------------------------------------------

        po = num(
            row.get(
                c_po
            ),
            0,
        )

        actual_waste = num(
            row.get(
                c_waste
            ),
            0,
        )

        # ----------------------------------------------------
        # MACHINE INCHARGE
        # ----------------------------------------------------

        if c_incharge:

            machine_incharge = str(
                row.get(
                    c_incharge,
                    "—",
                )
            ).strip()

        else:

            machine_incharge = "—"

        # ----------------------------------------------------
        # BUILD WORKING ROW
        # ----------------------------------------------------

        output_rows.append(
            {
                "Row ID": str(index),

                "RunID": run_id,

                "Edition Date":
                    pd.to_datetime(
                        row.get(
                            c_date
                        ),
                        errors="coerce",
                    ),

                "Report Type":
                    report_type.title(),

                "Machine":
                    display_machine,

                "Calc Machine":
                    machine,

                "Machine In-charge":
                    machine_incharge,

                "Product Name":
                    str(product),

                "Edition":
                    str(edition),

                "Publication":
                    publication_code,

                "Match Status":
                    match_status,

                "Matched Text":
                    matched_text,

                "PO":
                    int(
                        round(po)
                    ),

                "Pages":
                    pages,

                "Production Type":
                    production_type,

                "UV":
                    str(uv),

                "Book Count":
                    book_count,

                "Innovations":
                    (
                        ", ".join(
                            innovations
                        )
                        if innovations
                        else "—"
                    ),

                "Base Prediction":
                    base_prediction,

                "Book Addition":
                    book_addition,

                "Innovation Addition":
                    innovation_addition,

                "Predicted Waste":
                    predicted_waste,

                "Manual Prediction Required":
                    manual_prediction_required,

                "Actual Waste":
                    int(
                        round(
                            actual_waste
                        )
                    ),

                "Reason for Extra Waste":
                    "NA",
            }
        )

    working_df = pd.DataFrame(
        output_rows
    )

    if working_df.empty:

        raise ValueError(
            "No Main/Supplement production rows found "
            "after Trial exclusion."
        )

    return working_df


# ============================================================
# FINAL CALCULATIONS
# ============================================================

def finalize_calculations(df):

    output = df.copy()

    output[
        "Predicted Waste"
    ] = pd.to_numeric(
        output[
            "Predicted Waste"
        ],
        errors="coerce",
    )

    output["PO"] = pd.to_numeric(
        output["PO"],
        errors="coerce",
    ).fillna(0)

    output[
        "Actual Waste"
    ] = pd.to_numeric(
        output[
            "Actual Waste"
        ],
        errors="coerce",
    ).fillna(0)

    # --------------------------------------------------------
    # Edition Predicted %
    # --------------------------------------------------------

    output[
        "Predicted %"
    ] = (
        output[
            "Predicted Waste"
        ]
        /
        output[
            "PO"
        ].replace(
            0,
            pd.NA,
        )
        * 100
    ).round(2)

    # --------------------------------------------------------
    # Edition Actual %
    # --------------------------------------------------------

    output[
        "Actual %"
    ] = (
        output[
            "Actual Waste"
        ]
        /
        output[
            "PO"
        ].replace(
            0,
            pd.NA,
        )
        * 100
    ).round(2)

    # --------------------------------------------------------
    # Extra Waste
    #
    # Never show negative extra waste.
    # --------------------------------------------------------

    output[
        "Extra Waste"
    ] = (
        output[
            "Actual Waste"
        ]
        -
        output[
            "Predicted Waste"
        ]
    ).clip(
        lower=0
    )

    # --------------------------------------------------------
    # No extra waste -> Reason NA
    # --------------------------------------------------------

    no_extra_mask = (
        output[
            "Extra Waste"
        ]
        .fillna(0)
        <= 0
    )

    output.loc[
        no_extra_mask,
        "Reason for Extra Waste",
    ] = "NA"

    return output


# ============================================================
# MACHINE-WISE SUMMARY
# ============================================================

def machine_summary(df):
    """
    IMPORTANT BUSINESS RULE:

    Machine percentage is NOT the average
    of edition percentages.

    Machine Predicted %
        =
        Total Machine Predicted Waste
        /
        Total Machine PO
        * 100

    Machine Actual %
        =
        Total Machine Actual Waste
        /
        Total Machine PO
        * 100
    """

    data = (
        finalize_calculations(
            df
        )
    )

    summary_rows = []

    for machine, group in (
        data.groupby(
            "Calc Machine"
        )
    ):

        total_po = (
            group[
                "PO"
            ].sum()
        )

        total_predicted = (
            group[
                "Predicted Waste"
            ].sum(
                min_count=1
            )
        )

        total_actual = (
            group[
                "Actual Waste"
            ].sum()
        )

        if (
            total_po
            and pd.notna(
                total_predicted
            )
        ):

            predicted_percent = round(
                (
                    total_predicted
                    /
                    total_po
                )
                * 100,
                2,
            )

        else:

            predicted_percent = None

        if total_po:

            actual_percent = round(
                (
                    total_actual
                    /
                    total_po
                )
                * 100,
                2,
            )

        else:

            actual_percent = None

        summary_rows.append(
            {
                "Machine":
                    machine,

                "Predicted %":
                    predicted_percent,

                "Actual %":
                    actual_percent,
            }
        )

    # ========================================================
    # OVERALL
    # ========================================================

    overall_po = (
        data[
            "PO"
        ].sum()
    )

    overall_predicted = (
        data[
            "Predicted Waste"
        ].sum(
            min_count=1
        )
    )

    overall_actual = (
        data[
            "Actual Waste"
        ].sum()
    )

    if (
        overall_po
        and pd.notna(
            overall_predicted
        )
    ):

        overall_predicted_percent = (
            round(
                (
                    overall_predicted
                    /
                    overall_po
                )
                * 100,
                2,
            )
        )

    else:

        overall_predicted_percent = None

    if overall_po:

        overall_actual_percent = (
            round(
                (
                    overall_actual
                    /
                    overall_po
                )
                * 100,
                2,
            )
        )

    else:

        overall_actual_percent = None

    overall = {
        "Predicted %":
            overall_predicted_percent,

        "Actual %":
            overall_actual_percent,
    }

    return (
        pd.DataFrame(
            summary_rows
        ),
        overall,
    )
