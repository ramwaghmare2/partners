
        document.addEventListener("DOMContentLoaded", function () {
            // Export CSV button
            document.querySelector('#exportCSV').addEventListener('click', function () {
                exportTableToCSV();
            });
            
            // Export Excel button
            document.querySelector('#exportExcel').addEventListener('click', function () {
                exportTableToExcel();
            });

            // Export PDF button
            document.querySelector('#exportPDF').addEventListener('click', function () {
                exportTableToPDF();
            });

            // Export button for dropdown
            document.querySelector('#export').addEventListener('click', function () {
                // Assuming you will trigger an export action here
                alert('Exporting...');
            });
        });

        // CSV Export
        function exportTableToCSV() {
            const table = document.querySelector('.export');
            const rows = Array.from(table.rows);
            const csvArray = rows.map(row => {
                const cells = Array.from(row.cells).map(cell => cell.innerText);
                return cells.join(",");
            });
            const csvData = csvArray.join("\n");
            const blob = new Blob([csvData], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            if (link.download !== undefined) {
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', 'sales_data.csv');
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
        }

        // Excel Export
        function exportTableToExcel() {
            const table = document.querySelector('.export');
            const wb = XLSX.utils.table_to_book(table, { sheet: "Sales Data" });
            XLSX.writeFile(wb, 'sales_data.xlsx');
        }

        // PDF Export
        function exportTableToPDF() {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
        
            // Get the table data
            const table = document.querySelector('.export');
            const rows = Array.from(table.rows);
            
            // Prepare table headers and rows for jsPDF autoTable
            const headers = Array.from(rows[0].cells).map(cell => cell.innerText);
            const data = rows.slice(1).map(row => {
                return Array.from(row.cells).map(cell => cell.innerText);
            });
        
            // Use jsPDF autoTable to add the table to the PDF
            doc.autoTable({
                head: [headers], // Set the table header
                body: data, // Set the table rows
                startY: 20, // Start the table a little lower on the page
                theme: 'striped', // Apply striped theme for better visibility
                headStyles: {
                    fillColor: [0, 123, 255], // Set header background color (blue)
                    textColor: [255, 255, 255] // Set header text color (white)
                },
                margin: { top: 10, left: 10, right: 10, bottom: 10 } // Add margins
            });
        
            // Save the generated PDF
            doc.save("sales_data.pdf");
        }