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
				<button type="button" id="asset-search-button">Search</button><br><br><br><br>
            </form>
			<br><br>
			<div id="result-container"></div>
        `;
        this.page.main.html(body);
		$("#item-input").on("keypress", (event) => {
			if (event.key === "Enter") {
				event.preventDefault();
				this.submitForm();
				$("#item-input").val("");
			}
		});
		$("#asset-search-button").on("click", () => {
			this.submitForm();
			$("#item-input").val("");
		});
	}

	

	submitForm() {
		let item = $("#item-input").val().trim();
	
		frappe.call({
			method: "masar_miraaya.masar_miraaya.page.batch_count.batch_count.get_item",
			args: item ? { item: item } : {},
			callback: (response) => {
				let resultContainer = $("#result-container");
				resultContainer.empty();
	
				if (response.message && response.message.length > 0) {
					const items = response.message;
					const itemsPerPage = 50;
					const totalPages = Math.ceil(items.length / itemsPerPage);
					let currentPage = 1;
	
					const renderTable = (page) => {
						const start = (page - 1) * itemsPerPage;
						const end = start + itemsPerPage;
						const pageItems = items.slice(start, end);
	
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
	
						$.each(pageItems, (index, item) => {
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
	
						const paginationControls = `
							<div class="pagination-controls">
								<br>
								<button ${page === 1 ? "disabled" : ""} id="prev-page">Previous</button>
								<span>Page ${page} of ${totalPages}</span>
								<button ${page === totalPages ? "disabled" : ""} id="next-page">Next</button>
							</div>
						`;
	
						resultContainer.append(paginationControls);
	
						$("#prev-page").off("click").on("click", () => {
							if (currentPage > 1) {
								currentPage--;
								renderTable(currentPage);
							}
						});
	
						$("#next-page").off("click").on("click", () => {
							if (currentPage < totalPages) {
								currentPage++;
								renderTable(currentPage);
							}
						});
					};
	
					renderTable(currentPage);
				} else {
					resultContainer.html("No data found for the given Barcode.");
				}
			}
		});
	}	
}