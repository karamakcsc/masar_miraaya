frappe.pages['batch-count'].on_page_load = function(wrapper) {
	new MyPage(wrapper);
};

class MyPage {
    constructor(wrapper) {
        this.wrapper = $(wrapper);
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: 'Batch Count',
            single_column: true
        });
        this.make();
    }
	make() {
        const body = `
           <h1>Batch Count</h1>
            <form id="item-form"> 
                <label for="item-input">Barcode:</label>
                <input type="text" id="item-input" name="item"> &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
				<button type="button" id="asset-back-button">Search</button><br><br><br><br>
            </form>
			<br><br>
			<div id="result-container"></div>
        `;
        this.page.main.html(body);
		$("#item-input").on("keypress", (event) => {
			if (event.key === "Enter") {
				event.preventDefault();
				console.log($("#item-input").val())
				this.submitForm();
				$("#item-input").val("");
			}
		});
	}

	

	submitForm() {
        let item = $("#item-input").val().trim();
        if (!item) return;

        frappe.call({
            method: "masar_miraaya.masar_miraaya.page.batch_count.batch_count.get_item",
            args: {item: item },
            callback: (response) => {
                let resultContainer = $("#result-container");
                resultContainer.empty();

                if (response.message && response.message.length > 0) {
                    let message = `
                        <b>Result:</b>
                        <br>
                        <table class='datatable'>
                            <thead>
                                <tr>
                                    <th style='width:200px'>Item Code</th>
                                    <th style='width:200px'>Item Name</th>
									<th style='width:200px'>UOM</th>
                                    <th style='width:200px'>Warehouse</th>
                                    <th style='width:200px'>Batch</th>
                                    <th style='width:200px'>Reserved Qty</th>
                                    <th style='width:200px'>Actual Qty</th>
                                </tr>
                            </thead>
                            <tbody>`;

                    $.each(response.message, (index, item) => {
                        message += `
                            <tr>
                                <td>${item.item_code || ''}</td>
                                <td>${item.item_name || ''}</td>
								<td>${item.stock_uom || ''}</td>
								<td>${item.warehouse || ''}</td>
                                <td>${item.batch || ''}</td>
                                <td>${item.reserved_qty || ''}</td>
                                <td>${item.actual_qty || ''}</td>
                            </tr>`;
                    });

                    message += `</tbody></table>`;
                    resultContainer.html(message);
                    $('.datatable').DataTable();

                    // Display QR code if available
                    if (response.custom_qr_code_text) {
                        $("#qr_code_image").html(`<img src="${response.custom_qr_code_text || ''}">`);
                    }
                } else {
                    resultContainer.html("No data found for the given Barcode.");
                }
            }
        });
    }
}