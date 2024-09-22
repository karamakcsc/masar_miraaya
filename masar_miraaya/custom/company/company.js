frappe.ui.form.on('Company', {
    onload: function(frm){
        frm.fields_dict['custom_cost_of_delivery'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        
        frm.fields_dict['custom_lp_expense_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_compensation_expense_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_gift_card_deferred_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0
                }
            };
        };
        frm.fields_dict['custom_digital_wallet_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0
                }
            };
        };
    }, 
    setup:function(frm){
        frm.fields_dict['custom_cost_of_delivery'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_lp_expense_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_compensation_expense_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_gift_card_deferred_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0
                }
            };
        };
        frm.fields_dict['custom_digital_wallet_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0
                }
            };
        };        
    }, 
    refresh:function(frm){
        frm.fields_dict['custom_cost_of_delivery'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_lp_expense_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_compensation_expense_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0,
                    "account_type" : 'Expense Account'
                }
            };
        };
        frm.fields_dict['custom_gift_card_deferred_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0
                }
            };
        };
        frm.fields_dict['custom_digital_wallet_account'].get_query = function(frm) {
            return {
                filters: {
                    "is_group": 0
                }
            };
        };        
    }
});
