$(document).ready(function () {
    console.log("Checking if jQuery and DataTables are available...");
    
    if (typeof jQuery === "undefined") {
        console.error("Error: jQuery is not loaded! Check script order.");
        return;
    }

    if (typeof $.fn.DataTable === "undefined") {
        console.error("Error: DataTables is not loaded! Check script order.");
        return;
    }

    console.log("Initializing DataTable...");

    let table = $('#OrderTable').DataTable({
        dom: 'Bfrtip',
        buttons: [
            {
                extend: 'csv',
                text: 'Download CSV',
                className: 'btn btn-primary',
                filename: 'Sales_Data'
            },
            {
                extend: 'excel',
                text: 'Download Excel',
                className: 'btn btn-success',
                filename: 'Sales_Data'
            },
            {
                extend: 'pdf',
                text: 'Download PDF',
                className: 'btn btn-danger',
                filename: 'Sales_Data',
                orientation: 'landscape',
                pageSize: 'A4',
                exportOptions: { columns: ':visible' }
            }
        ]
    });

    $("#exportCSV").click(function () {
        table.button('.buttons-csv').trigger();
    });

    $("#exportExcel").click(function () {
        table.button('.buttons-excel').trigger();
    });

    $("#exportPDF").click(function () {
        table.button('.buttons-pdf').trigger();
    });

    // Image Export (Convert table to PNG)
    $("#exportImage").click(function () {
        html2canvas(document.querySelector("#OrderTable")).then(canvas => {
            let link = document.createElement("a");
            link.href = canvas.toDataURL("image/png");
            link.download = "Sales_Data.png";
            link.click();
        });
    });
});
