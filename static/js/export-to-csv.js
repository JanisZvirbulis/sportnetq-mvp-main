
function convertTableToCSV(table) {
    const rows = Array.from(table.querySelectorAll('tbody tr'));
    const headers = Array.from(table.querySelectorAll('thead th')).map(header => header.innerText);

    let csvRows = [headers.join(',')];

    rows.forEach(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        const data = cells.map(cell => cell.innerText.trim() || 'N/A').join(',');
        if (data.trim() !== '') {
            csvRows.push(data);
        }
    });

    return csvRows.join('\n');
}

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: 'text/csv' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

document.getElementById('exportButton').addEventListener('click', function () {
    const table = document.getElementById('physical-assessment-table');
    let team = table.dataset.teamname
    let pa_name = table.dataset.title
    const csv = convertTableToCSV(table);
    const filename =  `${pa_name}_${team}.csv`;
    downloadCSV(csv, filename);
});