app_name = "masar_miraaya"
app_title = "Masar Miraaya"
app_publisher = "KCSC"
app_description = "Masar Miraaya"
app_email = "info@kcsc.com.jo"
app_license = "mit"
# required_apps = []

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/masar_miraaya/css/masar_miraaya.css"
# app_include_js = "/assets/masar_miraaya/js/masar_miraaya.js"

# include js, css files in header of web template
# web_include_css = "/assets/masar_miraaya/css/masar_miraaya.css"
# web_include_js = "/assets/masar_miraaya/js/masar_miraaya.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "masar_miraaya/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "masar_miraaya/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "masar_miraaya.utils.jinja_methods",
# 	"filters": "masar_miraaya.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "masar_miraaya.install.before_install"
# after_install = "masar_miraaya.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "masar_miraaya.uninstall.before_uninstall"
# after_uninstall = "masar_miraaya.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "masar_miraaya.utils.before_app_install"
# after_app_install = "masar_miraaya.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "masar_miraaya.utils.before_app_uninstall"
# after_app_uninstall = "masar_miraaya.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "masar_miraaya.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Brand": {
        "validate" : "masar_miraaya.custom.brand.brand.validate"
    },
	"Item": {
		"validate": "masar_miraaya.custom.item.item.validate"
	},
	"Item Group": {
		"validate": "masar_miraaya.custom.item_group.item_group.validate"
	},
	"Customer": {
		"validate": "masar_miraaya.custom.customer.customer.validate"
	},
	"Customer Group": {
		"validate": "masar_miraaya.custom.customer_group.customer_group.validate"
	}, 
    "Price List": { 
        "validate" : "masar_miraaya.custom.price_list.price_list.validate"
    },
    "Sales Order": {
        "on_submit": "masar_miraaya.custom.sales_order.sales_order.on_submit",
        "validate" : "masar_miraaya.custom.sales_order.sales_order.validate",
        "on_change": "masar_miraaya.custom.sales_order.sales_order.on_change"
    },
    "File": { 
        "validate" : "masar_miraaya.custom.file.file.validate",
        "on_trash" : "masar_miraaya.custom.file.file.on_trash"
    },
    "Item Attribute": {
        "validate" : "masar_miraaya.custom.item_attribute.item_attribute.validate"
    },
    "Sales Invoice": {
        "on_submit": "masar_miraaya.custom.sales_invoice.sales_invoice.on_submit"
    },
    "Item Price": {
        "validate" : "masar_miraaya.custom.item_price.item_price.validate"
    }
}

doctype_js = {
   "Sales Order": "custom/sales_order/sales_order.js",
   "Company": "custom/company/company.js"

}
# Scheduled Tasks
# ---------------

scheduler_events = {
	# "all": [
	# 	"masar_miraaya.override._reorder_item.reorder_item"
	# ],
	# "daily": [
	# 	"masar_miraaya.override._reorder_item.reorder_item"
	# ],
	"hourly": [
		"masar_miraaya.jobs._reorder_item.reorder_item"
	],
	# "weekly": [
	# 	"masar_miraaya.tasks.weekly"
	# ],
	# "monthly": [
	# 	"masar_miraaya.tasks.monthly"
	# ],
	"cron": {
        "*/30 * * * *": [
            "masar_miraaya.api.create_magento_auth"
        ]
    }
}

# Testing
# -------

# before_tests = "masar_miraaya.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#     "erpnext.stock.reorder_item.reorder_item": "masar_miraaya.override._reorder_item.reorder_item"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "masar_miraaya.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["masar_miraaya.utils.before_request"]
# after_request = ["masar_miraaya.utils.after_request"]

# Job Events
# ----------
# before_job = ["masar_miraaya.utils.before_job"]
# after_job = ["masar_miraaya.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"masar_miraaya.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }
fixtures = [
    {"dt": "Custom Field", "filters": [
        [
            "name", "in", [
                "Item-custom_max_qty",
                "Item Group-custom_item_group_id",
                "Item Group-custom_parent_item_group_id",
                "Customer-custom_first_name",
                "Customer-custom_last_name",
                "Customer-custom_email",
                "Customer Group-custom_customer_group_id",
                "Customer-custom_customer_id",
                "Item-custom_item_group_id",
                "Customer-custom_customer_group_id",
                "Item-custom_is_publish",
                "Item Group-custom_is_publish",
                "Item Group-custom_column_break_oilxi",
                "Customer-custom_is_publish",
                "Customer Group-custom_is_publish",
                "Sales Order-custom_sales_order_status",
                "Address-custom_address_id",
                "Sales Order-custom_address_id",
                "Price List-custom_magento_selling",
                "Item-custom_item_id",
                "custom_tax_category_id",
                "Item-custom_ingredients",
                "Item-custom_how_to_use",
                "Item-custom_formulation", 
                "Item-custom_country_of_manufacture",
                "Item-custom_free_from",
                "Item-custom_key_features",
                "Item-custom_magento_item_type",
                "Item Attribute-custom_column_break_7kpvy",
                "Item Attribute-custom_attribute_code",
                "Customer-custom_website_id",
                "Customer-custom_store_id",
                "Customer-custom_middle_name",
                "Customer-custom_is_subscribed",
                "Address-custom_first_name",
                "Address-custom_last_name",
                "Item-custom_magento_variants",
                "Item-custom_shade",
                "Item-custom_color",
                "Item-custom_column_break_zgmvm",
                "Item-custom_size_ml",
                "Item-custom_size",
                "Item-custom_section_break_a7brh",
                "Item-custom_item_name_ar",
                "Customer-custom_magento_address",
                "Customer-custom_street",
                "Customer-custom_address_id",
                "Customer-custom_country",
                "Customer-custom_country_id",
                "Customer-custom_city",
                "Customer-custom_pincode",
                "Customer-custom_column_break_4jgnq",
                "Customer-custom_phone",
                "Customer-custom_address_first_name",
                "Customer-custom_address_last_name",
                "Customer-custom_address_email_id",
                "Customer-custom_is_shipping_address",
                "Customer-custom_is_primary_address",
                "Sales Order-custom_magento_status",
                "Sales Order-custom_payment_channel",
                "Sales Order-custom_payment_channels",
                "Sales Order-custom_total_amount",
                "Company-custom_cost_of_delivery",
                "Customer-custom_is_delivery",
                "Sales Order-custom_delivery_company",
                "Sales Order-custom_magento_id",
                "Customer-custom_is_payment_channel",
                "Company-custom_receivable_payment_channel",
                "File-custom_magento_sync",
                "Item Price-custom_publish_to_magento",
                "Brand-custom_publish_to_magento",
                "Item Attribute-custom_publish_to_magento"

            ]
        ]
    ]}
]
